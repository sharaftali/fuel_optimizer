from django.shortcuts import render

# Create your views here.
"""
API views for route and fuel optimization.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services.geocoding import GeocodingService
from .services.routing import RoutingService
from .services.stations import stations_service
from .services.optimizer import FuelOptimizer
from .serializers import (
    RouteRequestSerializer,
    FuelOptimizeRequestSerializer,
    RouteResponseSerializer,
    FuelOptimizeResponseSerializer,
    ErrorResponseSerializer
)

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """Health check endpoint for monitoring."""
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'version': '1.0.0',
            'stations_loaded': stations_service.is_loaded(),
            'stations_count': stations_service.get_count()
        })


class RouteOptimizeView(APIView):
    """
    GET /api/v1/route/optimize/
    
    Returns route information between two US locations including distance,
    polyline, and coordinates.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.geocoder = GeocodingService()
        self.router = RoutingService()
    
    def get(self, request):
        """Calculate route between start and finish locations."""
        serializer = RouteRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(
                {'status': 'error', 'error': 'Invalid parameters', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        start = serializer.validated_data['start']
        finish = serializer.validated_data['finish']
        
        try:
            # Geocode start location
            start_lat, start_lng, start_addr = self.geocoder.geocode(start)
            if not start_lat:
                return Response(
                    {
                        'status': 'error',
                        'error': f'Could not find location: "{start}"',
                        'code': 'START_LOCATION_NOT_FOUND'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Geocode finish location
            finish_lat, finish_lng, finish_addr = self.geocoder.geocode(finish)
            if not finish_lat:
                return Response(
                    {
                        'status': 'error',
                        'error': f'Could not find location: "{finish}"',
                        'code': 'FINISH_LOCATION_NOT_FOUND'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Calculate route
            route = self.router.get_route(start_lat, start_lng, finish_lat, finish_lng)
            if not route:
                return Response(
                    {
                        'status': 'error',
                        'error': 'Could not calculate route between these locations',
                        'code': 'ROUTE_NOT_FOUND'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Build response
            response_data = {
                'start_location': {
                    'address': start_addr,
                    'coordinates': [start_lng, start_lat]
                },
                'finish_location': {
                    'address': finish_addr,
                    'coordinates': [finish_lng, finish_lat]
                },
                'total_distance_miles': route['distance_miles'],
                'polyline': route['polyline'],
                'cached': route.get('cached', False)
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception(f"Unexpected error processing route request: {e}")
            return Response(
                {'status': 'error', 'error': 'Internal server error', 'code': 'INTERNAL_ERROR'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FuelOptimizeView(APIView):
    """
    GET /api/v1/fuel/optimize/
    
    Returns optimal fuel stops along a route based on fuel prices.
    Vehicle: 500 mile range, 10 MPG.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.geocoder = GeocodingService()
        self.router = RoutingService()
        self.optimizer = FuelOptimizer()
    
    def get(self, request):
        """Calculate optimal fuel stops between start and finish."""
        serializer = FuelOptimizeRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(
                {'status': 'error', 'error': 'Invalid parameters', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        start = serializer.validated_data['start']
        finish = serializer.validated_data['finish']
        buffer_miles = serializer.validated_data.get('buffer_miles', 10)
        
        try:
            # Geocode start location
            start_lat, start_lng, start_addr = self.geocoder.geocode(start)
            if not start_lat:
                return Response(
                    {
                        'status': 'error',
                        'error': f'Could not find location: "{start}"',
                        'code': 'START_LOCATION_NOT_FOUND'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Geocode finish location
            finish_lat, finish_lng, finish_addr = self.geocoder.geocode(finish)
            if not finish_lat:
                return Response(
                    {
                        'status': 'error',
                        'error': f'Could not find location: "{finish}"',
                        'code': 'FINISH_LOCATION_NOT_FOUND'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Calculate route
            route = self.router.get_route(start_lat, start_lng, finish_lat, finish_lng)
            if not route:
                return Response(
                    {
                        'status': 'error',
                        'error': 'Could not calculate route between these locations',
                        'code': 'ROUTE_NOT_FOUND'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get stations near route
            stations = stations_service.get_stations_near_route(
                start_lat, start_lng,
                finish_lat, finish_lng,
                buffer_miles=buffer_miles
            )
            
            if not stations:
                return Response(
                    {
                        'status': 'error',
                        'error': 'No fuel stations found near this route',
                        'code': 'NO_STATIONS_FOUND'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Calculate optimal fuel stops
            fuel_plan = self.optimizer.calculate_optimal_stops(
                total_distance=route['distance_miles'],
                stations=stations
            )
            
            if not fuel_plan['journey_completable']:
                return Response(
                    {
                        'status': 'error',
                        'error': 'Cannot complete journey with available fuel stations',
                        'code': 'JOURNEY_NOT_COMPLETABLE'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Build response
            response_data = {
                'status': 'success',
                'route': {
                    'start_location': {
                        'address': start_addr,
                        'coordinates': [start_lng, start_lat]
                    },
                    'finish_location': {
                        'address': finish_addr,
                        'coordinates': [finish_lng, finish_lat]
                    },
                    'total_distance_miles': route['distance_miles'],
                    'polyline': route['polyline'],
                    'cached': route.get('cached', False)
                },
                'fuel_plan': fuel_plan,
                'summary': {
                    'average_price_per_gallon': round(fuel_plan['total_cost'] / fuel_plan['total_gallons'], 2) if fuel_plan['total_gallons'] > 0 else 0,
                    'cost_per_mile': round(fuel_plan['total_cost'] / route['distance_miles'], 2) if route['distance_miles'] > 0 else 0,
                    'number_of_stops': len(fuel_plan['stops'])
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception(f"Unexpected error processing fuel optimization request: {e}")
            return Response(
                {'status': 'error', 'error': 'Internal server error', 'code': 'INTERNAL_ERROR'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
