"""
Helper utilities
"""
import csv
import statistics
from pathlib import Path


def pick_best_price(results: list):
    """Find result with lowest price"""
    priced = [r for r in results if isinstance(r["price"], (int, float))]
    if not priced:
        return None
    return min(priced, key=lambda r: r["price"])


def calculate_price_stats(results: list) -> dict:
    """Calculate price statistics from results"""
    prices = [r["price"] for r in results if isinstance(r["price"], (int, float))]
    
    if not prices:
        return {
            "min": None,
            "median": None,
            "max": None,
            "count": 0,
            "confidence": "—"
        }
    
    prices_sorted = sorted(prices)
    n = len(prices_sorted)
    
    return {
        "min": min(prices_sorted),
        "median": statistics.median(prices_sorted),
        "max": max(prices_sorted),
        "count": n,
        "confidence": "High" if n >= 10 else "Medium" if n >= 5 else "Low"
    }


def build_tip(keyword: str, intent: str, sort_mode: str, best) -> str:
    """Build tip/advisory text"""
    lines = []
    lines.append(f"Detected category: {intent.upper()}")
    lines.append(f"Sort mode: {sort_mode}")
    lines.append("Tip: Match exact specs before deciding (size/grade/model).")
    lines.append("Tip: Median is a fair reference; outliers are often shipping/bundle differences.")

    if best:
        lines.append("")
        lines.append("✅ BEST DEAL (lowest detected price):")
        lines.append(f"- {best['title']}")
        lines.append(f"- Store: {best['store']}")
        lines.append(f"- Price: {best['cur']} {best['price_disp']}")
        lines.append(f"- Link: {best['link']}")
    else:
        lines.append("")
        lines.append("Best Deal: Prices weren't detected reliably. Try a more specific keyword.")

    return "\n".join(lines)


def init_history_file(filepath: Path):
    """Initialize price history CSV file"""
    if not filepath.exists():
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with filepath.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["timestamp", "keyword", "median", "n"])
