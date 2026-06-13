"""
Unit tests for geocoding service.
"""
import pytest
from unittest.mock import patch, Mock
from django.core.cache import cache
from api.services.geocoding import GeocodingService


class TestGeocodingService:
    
    def setup_method(self):
        cache.clear()
        self.service = GeocodingService()
    
    @patch('api.services.geocoding.requests.get')
    def test_geocode_success(self, mock_get):
        """Test successful geocoding of valid address."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'lat': '34.052235', 'lon': '-118.243683', 'display_name': 'Los Angeles, CA, USA'}
        ]
        mock_get.return_value = mock_response
        
        lat, lng, addr = self.service.geocode("Los Angeles, CA")
        
        assert lat == 34.052235
        assert lng == -118.243683
        assert "Los Angeles" in addr
    
    @patch('api.services.geocoding.requests.get')
    def test_geocode_not_found(self, mock_get):
        """Test geocoding of invalid address returns None."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        lat, lng, addr = self.service.geocode("InvalidPlaceXYZ123")
        
        assert lat is None
        assert lng is None
    
    def test_clean_address_removes_highway_exits(self):
        """Test address cleaning removes highway exit patterns."""
        dirty = "I-44, EXIT 283 & US-69, Big Cabin"
        cleaned = self.service._clean_address(dirty)
        assert "EXIT" not in cleaned.upper()