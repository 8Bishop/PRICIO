
# Retailer configurations and constants


# RETAILER CONFIGURATIONS

RETAILERS = {
    "Ace": {
        "base": "https://www.acehardware.ph",
        "search": "https://www.acehardware.ph/search?q={q}",
        "product_hint": r"/products/[^/?]+(\?|$)",
        "trusted_score": 90,
        "enabled": True,
    },
    "Wilcon": {
        "base": "https://www.wilcon.com.ph",
        "search": "https://www.wilcon.com.ph/catalogsearch/result/?q={q}",
        "product_hint": r"\.html$|/product",
        "trusted_score": 92,
        "enabled": False,  # DISABLED - URL patterns not compatible
    },
    "Handyman": {
        "base": "https://www.handyman.com.ph",
        "search": "https://www.handyman.com.ph/catalogsearch/result/?q={q}",
        "product_hint": r"\.html$|/product",
        "trusted_score": 88,
        "enabled": False,  # DISABLED - URL patterns not compatible
    },
    "PCX": {
        "base": "https://pcx.com.ph",
        "search": "https://pcx.com.ph/search?q={q}",
        "product_hint": r"/products/[^/?]+(\?|$)",
        "trusted_score": 95,
        "enabled": True,  # WORKING
    },
    "Lazada": {
        "base": "https://www.lazada.com.ph",
        "search": "https://www.lazada.com.ph/catalog/?q={q}",
        "product_hint": r"-i\d+",
        "trusted_score": 80,
        "enabled": False,  # DISABLED - needs javascript rendering
    },
    "Shopee": {
        "base": "https://shopee.ph",
        "search": "https://shopee.ph/search?keyword={q}",
        "product_hint": r"-i\.\d+\.\d+",
        "trusted_score": 82,
        "enabled": False,  # DISABLED - needs javascript rendering
    },
}


# Scraping settings

REQUEST_DELAY_SEC = 0.2
MAX_PRODUCTS_PER_RETAILER = 5
CACHE_TTL_SEC = 10 * 60
TIMEOUT_SEC = 10


# Category token sets

ELECTRONICS_TOKENS = {
    "gpu", "graphics", "rtx", "gtx", "radeon", "rx", "nvidia", "amd",
    "intel", "ryzen", "core", "i3", "i5", "i7", "i9",
    "motherboard", "mobo", "lga", "am4", "am5", "ddr4", "ddr5",
    "ram", "ssd", "hdd", "nvme", "psu", "power supply", "monitor",
    "wifi", "router", "keyboard", "mouse", "case", "tower", "cooler",
    "rgb", "argb", "tempered", "fan", "aio", "heatsink",
    "laptop", "pc", "desktop", "vga"
}

MATERIALS_TOKENS = {
    "wood", "plywood", "lumber", "timber", "board", "plank",
    "cement", "concrete", "mortar", "rebar", "steel", "gi", "roof",
    "sand", "gravel", "aggregate", "hollow block", "chb", "brick",
    "pvc", "pipe", "fitting", "valve", "paint", "primer", "sealant",
    "adhesive", "glue", "epoxy", "tile", "tiles", "nail", "screw",
    "bolt", "washer", "wire", "switch", "breaker", "outlet",
    "hammer", "saw", "drill"
}
