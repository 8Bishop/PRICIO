
# Web scraping functionality


import re
import time
import requests
from urllib.parse import urljoin, urlparse, quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import RETAILERS, REQUEST_DELAY_SEC, MAX_PRODUCTS_PER_RETAILER, TIMEOUT_SEC
from core.filters import should_filter_out, relevance_score


class Scraper:
    # Web scraper for Philippine retailers
    
    def __init__(self, logger=None):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        self.logger = logger
        self.stop_flag = False
    
    def log(self, message):
        # Log message if logger is available
        if self.logger:
            self.logger(message)
    
    def set_stop_flag(self, value: bool):
        # Set stop flag for cancellation
        self.stop_flag = value
    
    def search_parallel(self, keyword: str, intent: str) -> list:
        # Search all enabled retailers in parallel
        q = quote_plus(keyword)
        all_results = []
        
        # Search all retailers in parallel
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {}
            for name, cfg in RETAILERS.items():
                if not cfg.get("enabled", True):
                    continue
                future = executor.submit(self._search_retailer, name, cfg, q, keyword, intent)
                futures[future] = name
            
            for future in as_completed(futures):
                if self.stop_flag:
                    break
                name = futures[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    self.log(f"❌ {name}: Error - {e}")
        
        return all_results
    
    def _search_retailer(self, name: str, cfg: dict, q: str, keyword: str, intent: str) -> list:
        # Search a single retailer (called in parallel)
        self.log(f"\n--- Checking {name} ---")
        
        search_url = cfg["search"].format(q=q)
        base = cfg["base"]
        hint_re = re.compile(cfg["product_hint"], re.I)
        
        html = self._get_html(search_url)
        if not html:
            self.log(f"❌ {name}: Failed to get search page")
            return []
        
        self.log(f"✓ {name}: Got search page ({len(html)} chars)")
        
        links = self._extract_links(html, base)
        product_links = [u for u in links if hint_re.search(u)]
        product_links = self._unique(product_links)[:MAX_PRODUCTS_PER_RETAILER]
        
        self.log(f"  Found {len(product_links)} product links")
        
        results = []
        seen = set()
        
        for link in product_links:
            if self.stop_flag or link in seen:
                continue
            seen.add(link)
            
            p_html = self._get_html(link)
            if not p_html:
                continue
            
            title = self._extract_title(p_html) or f"{keyword} ({name})"
            
            if should_filter_out(intent, keyword, title):
                continue
            
            price, cur = self._extract_price(p_html)
            rec = cfg["trusted_score"] >= 85
            store = self._domain_name(link)
            rel = relevance_score(keyword, title)
            
            results.append({
                "title": title[:140],
                "store": store,
                "rec": rec,
                "price": price,
                "price_disp": f"{price:,.2f}" if isinstance(price, (int, float)) else "—",
                "cur": cur or "—",
                "rel": rel,
                "link": link
            })
            
            time.sleep(REQUEST_DELAY_SEC)
        
        self.log(f"✅ {name}: Added {len(results)} products")
        return results
    
    def _get_html(self, url: str) -> str:
        # Fetch HTML from URL
        try:
            r = self.session.get(url, timeout=TIMEOUT_SEC)
            if r.status_code != 200:
                return ""
            return r.text
        except Exception:
            return ""
    
    def _extract_links(self, html: str, base: str) -> list:
        # Extract all links from HTML
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.I)
        out = []
        for h in hrefs:
            h = h.strip()
            if not h:
                continue
            if h.startswith("#") or h.startswith("javascript:") or h.startswith("mailto:"):
                continue
            out.append(urljoin(base, h))
        return out
    
    def _unique(self, items: list) -> list:
        # Remove duplicates while preserving order
        seen = set()
        out = []
        for x in items:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out
    
    def _extract_title(self, html: str) -> str:
        # Extract product title from HTML
        # Try <title> tag
        m = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
        if m:
            t = re.sub(r"\s+", " ", re.sub(r"<.*?>", " ", m.group(1))).strip()
            import html as html_parser
            t = html_parser.unescape(t)  # Decode HTML entities
            return t
        
        # Try og:title
        m = re.search(r'property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', html, flags=re.I)
        if m:
            import html as html_parser
            t = m.group(1).strip()
            t = html_parser.unescape(t)  # Decode HTML entities
            return t
        
        return ""
    
    def _extract_price(self, html: str) -> tuple:
        # Extract price from HTML, returns (price, currency)
        # Try JSON-LD structured data
        blocks = re.findall(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html, flags=re.I | re.S
        )
        for b in blocks:
            m = re.search(r'"price"\s*:\s*"?(?P<p>[\d,.]+)"?', b, flags=re.I)
            if m:
                try:
                    price = float(m.group("p").replace(",", ""))
                    c = re.search(r'"priceCurrency"\s*:\s*"([A-Z]{3})"', b)
                    cur = c.group(1) if c else "PHP"
                    return price, cur
                except Exception:
                    pass
        
        # Try OpenGraph meta tag
        m = re.search(r'product:price:amount"\s+content="([\d,.]+)"', html, flags=re.I)
        if m:
            try:
                return float(m.group(1).replace(",", "")), "PHP"
            except Exception:
                pass
        
        # Try currency symbol pattern
        m = re.search(r"(₱|PHP)\s*([\d,]+(?:\.\d+)?)", html, flags=re.I)
        if m:
            try:
                return float(m.group(2).replace(",", "")), "PHP"
            except Exception:
                pass
        
        return None, None
    
    def _domain_name(self, url: str) -> str:
        # Extract domain name from URL
        try:
            return urlparse(url).netloc.lower().replace("www.", "") or "unknown"
        except Exception:
            return "unknown"
