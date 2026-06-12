"""
Unit tests for routing service.
"""
import pytest
from unittest.mock import patch, Mock
from api.services.routing import RoutingService


class TestRoutingService:
    
    def setup_method(self):
        self.service = RoutingService()
    
    @patch('api.services.routing.requests.get')
    def test_get_route_success(self, mock_get):
        """Test successful route calculation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 'Ok',
            'routes': [{'distance': 451000, 'duration': 14400, 'geometry': 'polyline'}]
        }
        mock_get.return_value = mock_response
        
        result = self.service.get_route(34.05, -118.24, 36.17, -115.14)
        
        assert result is not None
        assert 'distance_miles' in result
        assert result['cached'] is False
    
    def test_meters_to_miles_conversion(self):
        """Test meter to mile conversion."""
        assert self.service._meters_to_miles(1609.34) == 1.0
        assert self.service._meters_to_miles(0) == 0.0
