"""
Geocoding service using Nominatim (OpenStreetMap) with caching.
"""
import logging
import hashlib
import re
from typing import Tuple, Optional

import requests
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class GeocodingService:
    """Handles address to coordinate conversion using Nominatim."""
    
    BASE_URL = "https://nominatim.openstreetmap.org/search"
    TIMEOUT_SECONDS = 10
    
    def __init__(self):
        self.user_agent = settings.NOMINATIM_USER_AGENT
    
    def _get_cache_key(self, address: str) -> str:
        """Generate cache key for an address."""
        normalized = address.lower().strip()
        return f"geocode:{hashlib.md5(normalized.encode()).hexdigest()}"
    
    def _clean_address(self, address: str) -> str:
        """Clean address by removing highway exit details."""
        # Remove highway exit patterns
        patterns = [
            r'I-\d+,?\s*EXIT\s*[\d\w&]+\s*',
            r'EXIT\s*[\d\w&]+\s*',
            r'&?\s*US-\d+\s*',
            r'&?\s*SR-\d+\s*',
            r'&?\s*CR-\d+\s*',
            r'&?\s*FM-\d+\s*',
            r'&?\s*HWY\s*\d+\s*',
        ]
        
        cleaned = address
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Clean up extra spaces and commas
        cleaned = re.sub(r'\s+', ' ', cleaned).strip().rstrip(',')
        
        return cleaned if len(cleaned) >= 5 else address
    
    def geocode(self, address: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """
        Convert address to (latitude, longitude, formatted_address).
        
        Returns:
            Tuple of (lat, lng, formatted_address) or (None, None, None) if failed.
        """
        cache_key = self._get_cache_key(address)
        cached = cache.get(cache_key)
        
        if cached:
            logger.info(f"Geocoding cache hit: {address}")
            return cached['lat'], cached['lng'], cached.get('formatted_address', address)
        
        logger.info(f"Geocoding API call: {address}")
        
        # Try cleaned address first, then fallback to original
        addresses_to_try = [self._clean_address(address), address]
        
        for addr in addresses_to_try:
            try:
                params = {
                    'q': addr,
                    'format': 'json',
                    'limit': 1,
                }
                headers = {'User-Agent': self.user_agent}
                
                response = requests.get(
                    self.BASE_URL,
                    params=params,
                    headers=headers,
                    timeout=self.TIMEOUT_SECONDS
                )
                response.raise_for_status()
                data = response.json()
                
                if data:
                    result = data[0]
                    lat = float(result['lat'])
                    lng = float(result['lon'])
                    formatted = result.get('display_name', addr)
                    
                    cache.set(cache_key, {
                        'lat': lat,
                        'lng': lng,
                        'formatted_address': formatted
                    }, timeout=settings.GEOCODE_CACHE_TIMEOUT)
                    
                    logger.info(f"Geocoded: {address} -> ({lat}, {lng})")
                    return lat, lng, formatted
                    
            except requests.RequestException as e:
                logger.warning(f"Geocoding attempt failed for {addr}: {e}")
                continue
        
        logger.error(f"Geocoding failed for: {address}")
        return None, None, None
