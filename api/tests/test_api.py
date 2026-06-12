"""
Integration tests for API endpoints.
"""
import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch, Mock


class APITestCase(TestCase):
    
    def setUp(self):
        self.client = APIClient()
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get('/api/v1/health/')
        assert response.status_code == 200
        assert 'status' in response.json()
    
    def test_route_optimize_success(self):
        """Test route optimization with valid locations."""
        response = self.client.get(
            '/api/v1/route/optimize/',
            {'start': 'Los Angeles, CA', 'finish': 'Las Vegas, NV'}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'total_distance_miles' in data
        assert 'polyline' in data
    
    def test_route_optimize_invalid_start(self):
        """Test route optimization with invalid start location."""
        response = self.client.get(
            '/api/v1/route/optimize/',
            {'start': 'InvalidCityXYZ', 'finish': 'Las Vegas, NV'}
        )
        assert response.status_code == 404
        assert 'error' in response.json()
    
    def test_route_optimize_missing_params(self):
        """Test route optimization with missing parameters."""
        response = self.client.get('/api/v1/route/optimize/')
        assert response.status_code == 400