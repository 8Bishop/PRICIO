"""
Caching utilities
"""
import time
from config import CACHE_TTL_SEC


class SearchCache:
    """
    Simple in-memory cache for search results
    """
    
    def __init__(self, ttl_sec: int = CACHE_TTL_SEC):
        self.cache = {}
        self.ttl_sec = ttl_sec
    
    def get(self, keyword: str, intent: str):
        """Get cached results if not expired"""
        cache_key = (keyword.lower().strip(), intent)
        
        if cache_key not in self.cache:
            return None
        
        ts, results = self.cache[cache_key]
        
        if time.time() - ts >= self.ttl_sec:
            # Cache expired
            del self.cache[cache_key]
            return None
        
        return results
    
    def set(self, keyword: str, intent: str, results: list):
        """Store results in cache"""
        cache_key = (keyword.lower().strip(), intent)
        self.cache[cache_key] = (time.time(), results)
    
    def clear(self):
        """Clear all cached results"""
        self.cache.clear()
