"""
Fuel stations data service - loads CSV and provides filtering.
"""
import logging
import csv
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
            'price': self.price,
            'latitude': self.latitude,
            'longitude': self.longitude,
        }


class StationsService:
    """Service for managing fuel stations data."""
    
    def __init__(self):
        self._stations: List[FuelStation] = []
        self._loaded = False
    
    def load_stations(self, csv_path: Optional[Path] = None) -> None:
        """Load fuel stations from CSV file."""
        if csv_path is None:
            csv_path = settings.FUEL_STATIONS_CSV
        
        if not csv_path.exists():
            logger.warning(f"Stations CSV not found: {csv_path}")
            return
        
        self._stations = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    lat = float(row.get('latitude', '')) if row.get('latitude') else None
                    lng = float(row.get('longitude', '')) if row.get('longitude') else None
                    
                    if lat and lng:
                        station = FuelStation(
                            id=row['OPIS Truckstop ID'],
                            name=row['Truckstop Name'],
                            address=row['Address'],
                            city=row['City'],
                            state=row['State'],
                            price=float(row['Retail Price']),
                            latitude=lat,
                            longitude=lng,
                        )
                        self._stations.append(station)
                except (KeyError, ValueError) as e:
                    logger.debug(f"Skipping row: {e}")
                    continue
        
        self._loaded = True
        logger.info(f"Loaded {len(self._stations)} fuel stations")
    
    def is_loaded(self) -> bool:
        """Check if stations are loaded."""
        return self._loaded
    
    def get_count(self) -> int:
        """Get number of loaded stations."""
        return len(self._stations)
    
    def get_all_stations(self) -> List[FuelStation]:
        """Get all loaded stations."""
        if not self._loaded:
            self.load_stations()
        return self._stations
    
    def haversine_distance(self, lat1: float, lng1: float, 
                           lat2: float, lng2: float) -> float:
        """Calculate distance between two points in miles using Haversine formula."""
        R = 3959.87433  # Earth's radius in miles
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * \
            math.sin(delta_lng / 2) ** 2
        c = 2 * math.asin(min(1, math.sqrt(a)))
        
        return R * c
    
    def point_to_line_distance(self, lat: float, lng: float,
                               lat1: float, lng1: float,
                               lat2: float, lng2: float) -> float:
        """
        Calculate minimum distance from a point to a line segment.
        Returns distance in miles.
        """
        # Cross-track distance formula
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        lat_rad = math.radians(lat)
        lng_rad = math.radians(lng)
        
        # Calculate angular distance between start and point
        delta_lng = lng_rad - lng1_rad
        x = math.cos(lat_rad) * math.sin(delta_lng)
        y = math.cos(lat1_rad) * math.sin(lat_rad) - \
            math.sin(lat1_rad) * math.cos(lat_rad) * math.cos(delta_lng)
        angular_distance = math.asin(min(1, math.sqrt(x*x + y*y)))
        
        # Calculate bearing
        theta = math.atan2(
            math.sin(delta_lng) * math.cos(lat_rad),
            math.cos(lat1_rad) * math.sin(lat_rad) -
            math.sin(lat1_rad) * math.cos(lat_rad) * math.cos(delta_lng)
        )
        
        # Angular distance of projection along route
        delta = math.asin(min(1, math.sin(angular_distance) * math.sin(theta)))
        
        # Distance from point to line
        R = 3959.87433
        distance = R * abs(delta)
        
        return abs(distance)
    
    def get_stations_near_route(self, start_lat: float, start_lng: float,
                                finish_lat: float, finish_lng: float,
                                buffer_miles: int = 10) -> List[Dict[str, Any]]:
        """
        Get all fuel stations within buffer_miles of the route.
        Returns stations sorted by distance from start.
        """
        if not self._loaded:
            self.load_stations()
        
        # Calculate bounding box for quick filtering
        min_lat = min(start_lat, finish_lat) - (buffer_miles / 69)
        max_lat = max(start_lat, finish_lat) + (buffer_miles / 69)
        min_lng = min(start_lng, finish_lng) - (buffer_miles / 69)
        max_lng = max(start_lng, finish_lng) + (buffer_miles / 69)
        
        # Quick bounding box filter
        candidate_stations = []
        for station in self._stations:
            if (min_lat <= station.latitude <= max_lat and
                min_lng <= station.longitude <= max_lng):
                candidate_stations.append(station)
        
        # Calculate precise distance to route
        stations_with_distance = []
        total_distance = self.haversine_distance(start_lat, start_lng, finish_lat, finish_lng)
        
        for station in candidate_stations:
            dist_to_route = self.point_to_line_distance(
                station.latitude, station.longitude,
                start_lat, start_lng,
                finish_lat, finish_lng
            )
            
            if dist_to_route <= buffer_miles:
                # Calculate approximate distance along route
                dist_from_start = self.haversine_distance(
                    start_lat, start_lng,
                    station.latitude, station.longitude
                )
                
                stations_with_distance.append({
                    **station.to_dict(),
                    'distance_from_start': dist_from_start,
                    'distance_to_route': dist_to_route
                })
        
        # Sort by distance from start
        stations_with_distance.sort(key=lambda x: x['distance_from_start'])
        
        logger.info(f"Found {len(stations_with_distance)} stations near route")
        return stations_with_distance


# Singleton instance
stations_service = StationsService()