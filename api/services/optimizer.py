"""
Fuel stop optimization algorithm.
"""
import logging
from typing import List, Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class FuelOptimizer:
    """
    Greedy algorithm for optimal fuel stops.
    
    Vehicle specifications:
    - Range: 500 miles per full tank
    - Efficiency: 10 miles per gallon
    """
    
    RANGE_MILES = getattr(settings, 'VEHICLE_RANGE_MILES', 500)
    MPG = getattr(settings, 'VEHICLE_MPG', 10)
    
    def calculate_optimal_stops(self, total_distance: float,
                                stations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate optimal fuel stops using greedy algorithm.
        """
        if not stations:
            return {
                'stops': [],
                'total_gallons': 0,
                'total_cost': 0,
                'journey_completable': total_distance <= self.RANGE_MILES
            }
        
        # Ensure all stations have distance_from_start
        valid_stations = []
        for s in stations:
            distance = s.get('distance_from_start')
            if distance is not None and distance <= total_distance:
                valid_stations.append(s)
        
        if not valid_stations:
            if total_distance <= self.RANGE_MILES:
                return {
                    'stops': [],
                    'total_gallons': 0,
                    'total_cost': 0,
                    'journey_completable': True
                }
            return {
                'stops': [],
                'total_gallons': 0,
                'total_cost': 0,
                'journey_completable': False
            }
        
        stops = []
        current_position = 0
        remaining_range = self.RANGE_MILES
        total_gallons = 0
        total_cost = 0
        
        while current_position < total_distance:
            # Find stations within remaining range
            reachable = [
                s for s in valid_stations
                if s['distance_from_start'] > current_position + 0.1
                and s['distance_from_start'] <= current_position + remaining_range
            ]
            
            if not reachable:
                if total_distance - current_position <= remaining_range:
                    break
                else:
                    return {
                        'stops': stops,
                        'total_gallons': total_gallons,
                        'total_cost': total_cost,
                        'journey_completable': False
                    }
            
            # Choose cheapest station
            best = min(reachable, key=lambda x: x['price'])
            
            distance_to_station = best['distance_from_start'] - current_position
            gallons_purchased = self.RANGE_MILES / self.MPG
            cost = gallons_purchased * best['price']
            
            stops.append({
                'name': best.get('name', ''),
                'address': best.get('address', ''),
                'city': best.get('city', ''),
                'state': best.get('state', ''),
                'price': round(best.get('price', 0), 4),
                'gallons': round(gallons_purchased, 2),
                'cost': round(cost, 2),
                'miles_from_start': round(best['distance_from_start'], 2),
                'miles_from_previous': round(distance_to_station, 2)
            })
            
            total_gallons += gallons_purchased
            total_cost += cost
            current_position = best['distance_from_start']
            remaining_range = self.RANGE_MILES
        
        return {
            'stops': stops,
            'total_gallons': round(total_gallons, 2),
            'total_cost': round(total_cost, 2),
            'journey_completable': True
        }
