"""
Unit tests for fuel stop optimization algorithm.
"""
import pytest
from api.services.optimizer import FuelOptimizer


class TestFuelOptimizer:
    
    def setup_method(self):
        self.optimizer = FuelOptimizer()
    
    def test_no_stations_short_distance(self):
        """Test with no stations but distance within range."""
        result = self.optimizer.calculate_optimal_stops(300, [])
        assert result['journey_completable'] is True
        assert result['stops'] == []
    
    def test_no_stations_long_distance(self):
        """Test with no stations but distance exceeds range."""
        result = self.optimizer.calculate_optimal_stops(600, [])
        assert result['journey_completable'] is False
    
    def test_single_station_within_range(self):
        """Test with one station within range."""
        stations = [{
            'name': 'Test Station',
            'address': '123 Main St',
            'city': 'Test City',
            'state': 'TX',
            'price': 3.50,
            'distance_from_start': 100
        }]
        result = self.optimizer.calculate_optimal_stops(400, stations)
        assert result['journey_completable'] is True
        assert len(result['stops']) == 1
        assert result['stops'][0]['price'] == 3.50
    
    def test_choose_cheapest_station(self):
        """Test algorithm chooses cheapest station within range."""
        stations = [
            {'name': 'Expensive', 'price': 4.50, 'distance_from_start': 100},
            {'name': 'Cheap', 'price': 2.50, 'distance_from_start': 150},
            {'name': 'Medium', 'price': 3.50, 'distance_from_start': 200}
        ]
        result = self.optimizer.calculate_optimal_stops(400, stations)
        assert result['stops'][0]['name'] == 'Cheap'
    
    def test_station_out_of_range_not_selected(self):
        """Test station beyond range is not selected."""
        stations = [{
            'name': 'Too Far',
            'price': 2.50,
            'distance_from_start': 600
        }]
        result = self.optimizer.calculate_optimal_stops(700, stations)
        assert result['journey_completable'] is False
    
    def test_multiple_stops(self):
        """Test journey requiring multiple stops."""
        stations = [
            {'name': 'Stop 1', 'price': 3.00, 'distance_from_start': 450},
            {'name': 'Stop 2', 'price': 3.50, 'distance_from_start': 800},
            {'name': 'Stop 3', 'price': 4.00, 'distance_from_start': 1200}
        ]
        result = self.optimizer.calculate_optimal_stops(1500, stations)
        assert result['journey_completable'] is True
        assert len(result['stops']) >= 2