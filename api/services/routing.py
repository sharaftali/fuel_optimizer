"""
Routing service using OSRM (Open Source Routing Machine) with caching.
"""
import logging
import hashlib
from typing import Optional, Dict, Any

import requests
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class RoutingService:
    """Handles route calculation between coordinates using OSRM."""
    
    TIMEOUT_SECONDS = 15
    
    def __init__(self):
        self.base_url = settings.OSRM_API_URL
        self.route_endpoint = "/route/v1/driving/"
    
    def _get_cache_key(self, start_lat: float, start_lng: float,
                       finish_lat: float, finish_lng: float) -> str:
        """Generate cache key from coordinates."""
        key_str = f"{start_lat:.6f},{start_lng:.6f}:{finish_lat:.6f},{finish_lng:.6f}"
        return f"route:{hashlib.md5(key_str.encode()).hexdigest()}"
    
    def _meters_to_miles(self, meters: float) -> float:
        """Convert meters to miles."""
        return round(meters * 0.000621371, 2)
    
    def get_route(self, start_lat: float, start_lng: float,
                  finish_lat: float, finish_lng: float) -> Optional[Dict[str, Any]]:
        """
        Get driving route between two coordinates.
        
        Returns:
            Dict with keys: 'distance_miles', 'polyline', 'duration_seconds', 'cached'
            Returns None if routing fails.
        """
        cache_key = self._get_cache_key(start_lat, start_lng, finish_lat, finish_lng)
        cached = cache.get(cache_key)
        
        if cached:
            logger.info(f"Route cache hit")
            cached['cached'] = True
            return cached
        
        logger.info(f"Routing API call")
        
        # OSRM expects coordinates as lng,lat
        coordinates = f"{start_lng},{start_lat};{finish_lng},{finish_lat}"
        url = f"{self.base_url}{self.route_endpoint}{coordinates}"
        
        params = {
            'overview': 'full',
            'geometries': 'polyline',
            'steps': 'false',
            'alternatives': 'false',
        }
        
        try:
            response = requests.get(url, params=params, timeout=self.TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') == 'Ok' and data.get('routes'):
                route = data['routes'][0]
                distance_miles = self._meters_to_miles(route.get('distance', 0))
                
                result = {
                    'distance_miles': distance_miles,
                    'polyline': route.get('geometry', ''),
                    'duration_seconds': route.get('duration', 0),
                    'distance_meters': route.get('distance', 0),
                    'cached': False,
                }
                
                cache.set(cache_key, result, timeout=settings.ROUTE_CACHE_TIMEOUT)
                logger.info(f"Route calculated: {distance_miles} miles")
                return result
            
            logger.error(f"Routing API error: {data.get('code')}")
            return None
            
        except requests.Timeout:
            logger.error(f"Routing API timeout")
            return None
        except requests.RequestException as e:
            logger.error(f"Routing API request error: {e}")
            return None
