# PRICIO

**P**ricing **R**egional **I**ntelligence **C**atalogue **I**nsight **O**utput

A price comparison tool for Philippine retailers (ACE Hardware & PCX).


## Project Structure

```
pricio_final/
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── README.md                 # This file
├── config/
│   ├── __init__.py
│   └── retailers.py          # Retailer configurations & constants
├── core/
│   ├── __init__.py
│   ├── scraper.py            # Web scraping logic
│   └── filters.py            # Category filtering & relevance
├── ui/
│   ├── __init__.py
│   └── app.py                # Main application UI
├── utils/
│   ├── __init__.py
│   ├── cache.py              # Search result caching
│   └── helpers.py            # Utility functions
└── data/                      # Created automatically
```

## Features

- 🔍 **Multi-retailer search** - ACE Hardware & PCX (parallel)
- 🏷️ **Auto-category detection** - Materials vs Electronics
- 📊 **Price statistics** - Min, median, max with confidence scores
- 🎯 **Smart filtering** - Removes irrelevant products
- ⚡ **Fast parallel search** - 10-30 second searches
- 💾 **10-minute caching** - Avoid re-fetching
- 📝 **Quote/Cart builder** - Build shopping lists
- 🔄 **Dynamic sorting** - Re-sort without re-searching
- 🐛 **Debug mode** - Toggle detailed logging

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Usage

### Basic Search
1. Enter keyword (e.g., "plywood", "ssd", "cement")
2. Select category (Auto recommended)
3. Choose sort method
4. Click Search

### Advanced Features
- **Double-click** results to open product page
- **Add to quote** to build comparison list
- **Toggle debug log** to see what's happening
- **Change sort** without re-searching

## Supported Retailers

| Retailer | Type | Status | Notes |
|----------|------|--------|-------|
| **ACE Hardware** | Materials/Electronics | ✅ WORKING | Fully functional |
| **PCX** | Electronics | ✅ WORKING | Fully functional |
| Wilcon | Materials | ❌ DISABLED | URL patterns incompatible |
| Handyman | Materials | ❌ DISABLED | URL patterns incompatible |
| Lazada | Marketplace | ❌ DISABLED | Requires JavaScript rendering |
| Shopee | Marketplace | ❌ DISABLED | Requires JavaScript rendering |

**Note:** Only ACE Hardware and PCX are functional. Other retailers require JavaScript rendering (Selenium/Playwright) or have incompatible URL structures.

## Module Overview

### `config/`
- **retailers.py**: All retailer configurations
  - URLs, patterns, trust scores
  - Scraping constants (delays, limits)
  - Category token sets

### `core/`
- **scraper.py**: Web scraping engine
  - Parallel retailer search
  - HTML parsing & link extraction
  - Price extraction
  
- **filters.py**: Filtering & scoring
  - Auto-category detection
  - Relevance scoring
  - Product filtering

### `ui/`
- **app.py**: Main GUI application
  - Tkinter interface
  - Event handlers
  - Results display

### `utils/`
- **cache.py**: Result caching
- **helpers.py**: Price stats, tips, etc.

## Configuration

### Enable/Disable Retailers
Edit `config/retailers.py`:
```python
"Wilcon": {
    "enabled": False,  # Set to True to re-enable (may not work)
    ...
}
```

### Adjust Performance
Edit `config/retailers.py`:
```python
REQUEST_DELAY_SEC = 0.2          # Delay between requests
MAX_PRODUCTS_PER_RETAILER = 5    # Products per retailer
TIMEOUT_SEC = 10                 # Request timeout
CACHE_TTL_SEC = 600              # Cache duration
```

## Known Limitations

### Technical Limitations
- **JavaScript-heavy sites** (Lazada, Shopee) require browser automation (Selenium/Playwright)
- **Dynamic URL structures** (Wilcon, Handyman) don't match expected patterns
- **Anti-bot protection** may occasionally block requests
- **Price extraction** uses pattern matching, may fail on redesigns

### Functional Limitations
- Only 2 retailers currently working (ACE Hardware, PCX)
- No mobile/web version
- No price history tracking (feature incomplete)
- No email alerts

## Why Only 2 Retailers Work?

**ACE Hardware & PCX:**
- Use server-side rendering (HTML available on page load)
- Have predictable URL patterns
- Price data available in HTML/JSON-LD

**Lazada & Shopee:**
- Heavy JavaScript rendering (content loads after page loads)
- Require browser automation tools (Selenium, Playwright)
- Anti-bot protection

**Wilcon & Handyman:**
- Different URL structure than expected
- Would need custom URL pattern detection

## Future Enhancements (Not Implemented)

Potential improvements would include:

- [ ] Selenium/Playwright for JS-heavy sites
- [ ] Dynamic URL pattern detection
- [ ] Export quotes to CSV/PDF
- [ ] Price history tracking & charts
- [ ] CLI version for automation
- [ ] Web scraping with rotating proxies
- [ ] API endpoints for programmatic access

## Testing

```bash
# Run in demo mode
# Select "Offline Demo" in the UI to test without hitting real sites
```

## Troubleshooting

### No Results
1. Enable debug log
2. Check which retailers failed
3. Verify internet connection
4. Try different keywords

### Slow Performance
1. Reduce `MAX_PRODUCTS_PER_RETAILER` in `config/retailers.py`
2. Check network speed
3. Clear cache (restart app)

### Import Errors
```bash
# Make sure you're in the project directory
cd pricio_final
python main.py
```

## Development Notes

This was a learning project for:
- Web scraping with `requests`
- Tkinter GUI development
- Parallel processing with `ThreadPoolExecutor`
- Python project structure
- Category-based filtering

## License

Personal project - use freely for learning purposes

## Author

Price comparison tool experiment for the Philippines  
Built with Python, Tkinter, and requests

