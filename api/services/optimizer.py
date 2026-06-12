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
    
    RANGE_MILES = settings.VEHICLE_RANGE_MILES
    MPG = settings.VEHICLE_MPG
    
    def calculate_optimal_stops(self, total_distance: float,
                                stations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate optimal fuel stops using greedy algorithm.
        
        Strategy:
        1. Start with full tank at origin
        2. At each segment, look ahead within remaining range
        3. Choose cheapest station within that window
        4. Fill full tank at each stop
        5. Continue until destination
        
        Returns:
            Dict with 'stops', 'total_gallons', 'total_cost', 'journey_completable'
        """
        if not stations:
            return {
                'stops': [],
                'total_gallons': 0,
                'total_cost': 0,
                'journey_completable': False
            }
        
        # Add destination as a virtual station at distance = total_distance
        # This helps with the final leg calculation
        
        stops = []
        current_position = 0
        remaining_range = self.RANGE_MILES
        total_gallons = 0
        total_cost = 0
        
        # Filter stations that are within route distance
        valid_stations = [s for s in stations if s['distance_from_start'] <= total_distance]
        
        if not valid_stations:
            # Check if destination is within range
            if total_distance <= self.RANGE_MILES:
                gallons_needed = total_distance / self.MPG
                total_cost = 0  # No fuel purchased if starting with full tank?
                # Actually, cost is $0 because we assume starting with full tank
                return {
                    'stops': [],
                    'total_gallons': 0,
                    'total_cost': 0,
                    'journey_completable': True
                }
            else:
                return {
                    'stops': [],
                    'total_gallons': 0,
                    'total_cost': 0,
                    'journey_completable': False
                }
        
        current_index = 0
        last_stop_distance = 0
        
        while current_position < total_distance:
            # Find stations within remaining range from current position
            reachable_stations = [
                s for s in valid_stations
                if s['distance_from_start'] > current_position + 0.1  # Must be ahead
                and s['distance_from_start'] <= current_position + remaining_range
            ]
            
            if not reachable_stations:
                # Check if destination is within remaining range
                if total_distance - current_position <= remaining_range:
                    # Can reach destination without stopping
                    break
                else:
                    # Cannot reach destination or any station
                    logger.warning(f"Cannot reach destination or any station from {current_position}")
                    return {
                        'stops': stops,
                        'total_gallons': total_gallons,
                        'total_cost': total_cost,
                        'journey_completable': False
                    }
            
            # Find cheapest station in reachable set
            best_station = min(reachable_stations, key=lambda x: x['price'])
            
            # Calculate distance to this station
            distance_to_station = best_station['distance_from_start'] - current_position
            
            # Gallons consumed to reach station
            gallons_to_reach = distance_to_station / self.MPG
            
            # At station, fill full tank
            gallons_purchased = self.RANGE_MILES / self.MPG
            cost = gallons_purchased * best_station['price']
            
            stops.append({
                'name': best_station['name'],
                'address': best_station['address'],
                'city': best_station['city'],
                'state': best_station['state'],
                'price': best_station['price'],
                'gallons': round(gallons_purchased, 2),
                'cost': round(cost, 2),
                'miles_from_start': round(best_station['distance_from_start'], 2),
                'miles_from_previous': round(distance_to_station, 2)
            })
            
            total_gallons += gallons_purchased
            total_cost += cost
            
            # Update position and remaining range
            current_position = best_station['distance_from_start']
            remaining_range = self.RANGE_MILES  # Full tank after fill-up
            current_index = valid_stations.index(best_station) if best_station in valid_stations else current_index
        
        # Final leg: no additional fuel purchase (already accounted in last stop)
        if stops and total_distance - stops[-1]['miles_from_start'] > 0:
            final_leg = total_distance - stops[-1]['miles_from_start']
            # No additional purchase because we filled at last stop
        
        return {
            'stops': stops,
            'total_gallons': round(total_gallons, 2),
            'total_cost': round(total_cost, 2),
            'journey_completable': True
        }
