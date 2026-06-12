"""
Fuel stations data service - loads CSV and provides route-based filtering.
"""
import csv
import logging
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class FuelStation:
    """Fuel station data structure."""
    id: str
    name: str
    address: str
    city: str
    state: str
    price: float
    latitude: float
    longitude: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'price': round(self.price, 4),
            'latitude': self.latitude,
            'longitude': self.longitude,
        }


class StationsService:
    """Service for managing fuel stations data with spatial filtering."""
    
    EARTH_RADIUS_MILES = 3959.87433
    MILES_PER_DEGREE_LAT = 69.0
    
    def __init__(self):
        self._stations: List[FuelStation] = []
        self._loaded = False
        self._load_error = None
    
    def load_stations(self, csv_path: Optional[Path] = None) -> bool:
        """Load fuel stations from CSV file."""
        if csv_path is None:
            csv_path = getattr(settings, 'FUEL_STATIONS_CSV', Path('data/fuel_prices_with_coords.csv'))
        
        if not isinstance(csv_path, Path):
            csv_path = Path(csv_path)
        
        if not csv_path.exists():
            error_msg = f"Stations CSV not found: {csv_path}"
            logger.error(error_msg)
            self._load_error = error_msg
            self._loaded = False
            return False
        
        self._stations = []
        success_count = 0
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        lat_str = row.get('latitude', '').strip()
                        lng_str = row.get('longitude', '').strip()
                        
                        if lat_str and lng_str:
                            lat = float(lat_str)
                            lng = float(lng_str)
                            
                            station = FuelStation(
                                id=row.get('OPIS Truckstop ID', ''),
                                name=row.get('Truckstop Name', ''),
                                address=row.get('Address', ''),
                                city=row.get('City', ''),
                                state=row.get('State', ''),
                                price=float(row.get('Retail Price', 0)),
                                latitude=lat,
                                longitude=lng,
                            )
                            self._stations.append(station)
                            success_count += 1
                    except (ValueError, KeyError) as e:
                        logger.debug(f"Skipping row: {e}")
                        continue
            
            self._loaded = True
            self._load_error = None
            logger.info(f"Successfully loaded {success_count} fuel stations from {csv_path}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to load stations: {e}"
            logger.error(error_msg)
            self._load_error = error_msg
            self._loaded = False
            return False
    
    def is_loaded(self) -> bool:
        return self._loaded
    
    def get_load_error(self) -> Optional[str]:
        return self._load_error
    
    def get_count(self) -> int:
        return len(self._stations)
    
    def get_all_stations(self) -> List[FuelStation]:
        if not self._loaded:
            self.load_stations()
        return self._stations
    
    @staticmethod
    def haversine_distance(lat1: float, lng1: float,
                          lat2: float, lng2: float) -> float:
        """Calculate distance between two points in miles."""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * \
            math.sin(delta_lng / 2) ** 2
        c = 2 * math.asin(min(1, math.sqrt(a)))
        
        return StationsService.EARTH_RADIUS_MILES * c
    
    def get_stations_near_route(self, start_lat: float, start_lng: float,
                                finish_lat: float, finish_lng: float,
                                buffer_miles: int = 10) -> List[Dict[str, Any]]:
        """Get all fuel stations within buffer_miles of the route."""
        if not self._loaded:
            self.load_stations()
        
        if not self._stations:
            logger.warning("No stations loaded")
            return []
        
        # Bounding box filter
        lat_buffer = buffer_miles / self.MILES_PER_DEGREE_LAT
        lng_buffer = buffer_miles / (self.MILES_PER_DEGREE_LAT * math.cos(math.radians(start_lat)))
        
        min_lat = min(start_lat, finish_lat) - lat_buffer
        max_lat = max(start_lat, finish_lat) + lat_buffer
        min_lng = min(start_lng, finish_lng) - lng_buffer
        max_lng = max(start_lng, finish_lng) + lng_buffer
        
        # Filter stations
        stations_with_distance = []
        route_length = self.haversine_distance(start_lat, start_lng, finish_lat, finish_lng)
        
        for station in self._stations:
            if (min_lat <= station.latitude <= max_lat and
                min_lng <= station.longitude <= max_lng):
                
                # Calculate distance from start along route
                distance_from_start = self.haversine_distance(
                    start_lat, start_lng,
                    station.latitude, station.longitude
                )
                
                if distance_from_start <= buffer_miles * 2:
                    station_dict = station.to_dict()
                    station_dict['distance_from_start'] = round(distance_from_start, 2)
                    stations_with_distance.append(station_dict)
        
        # Sort by distance from start
        stations_with_distance.sort(key=lambda x: x['distance_from_start'])
        
        logger.info(f"Found {len(stations_with_distance)} stations within {buffer_miles} miles of route")
        return stations_with_distance


stations_service = StationsService()
