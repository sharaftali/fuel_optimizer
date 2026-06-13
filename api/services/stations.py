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
    
    def get_stations_near_route(self, route_points: List[Tuple[float, float]],
                                buffer_miles: int = 10) -> List[Dict[str, Any]]:
        """Get all fuel stations within buffer_miles of the route polyline."""
        if not self._loaded:
            self.load_stations()

        if not self._stations:
            logger.warning("No stations loaded")
            return []

        if not route_points:
            logger.warning("No route points provided")
            return []

        stations_with_distance = []

        for station in self._stations:
            closest_distance = float('inf')
            best_route_index = 0

            for index, (route_lat, route_lng) in enumerate(route_points):
                station_distance = self.haversine_distance(
                    station.latitude, station.longitude,
                    route_lat, route_lng
                )
                if station_distance < closest_distance:
                    closest_distance = station_distance
                    best_route_index = index

            if closest_distance <= buffer_miles:
                # Estimate progression along the route using route point order
                distance_from_start = self._route_distance_to_point(route_points, best_route_index)
                station_dict = station.to_dict()
                station_dict['distance_from_start'] = round(distance_from_start, 2)
                station_dict['distance_to_route'] = round(closest_distance, 2)
                stations_with_distance.append(station_dict)

        # Sort by distance from start along route
        stations_with_distance.sort(key=lambda x: x['distance_from_start'])

        logger.info(
            f"Found {len(stations_with_distance)} stations within {buffer_miles} miles of route"
        )
        return stations_with_distance

    def _route_distance_to_point(self, route_points: List[Tuple[float, float]],
                                 point_index: int) -> float:
        """Estimate distance along the route from the start to a route point."""
        if point_index <= 0:
            return 0.0

        distance = 0.0
        for i in range(point_index):
            lat1, lng1 = route_points[i]
            lat2, lng2 = route_points[i + 1]
            distance += self.haversine_distance(lat1, lng1, lat2, lng2)

        return distance


stations_service = StationsService()
