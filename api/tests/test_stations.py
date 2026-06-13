"""
Unit tests for station route filtering.
"""

from api.services.stations import StationsService


class TestStationsService:

    def setup_method(self):
        self.service = StationsService()
        self.service._loaded = True
        self.service._stations = [
            type('Station', (), {
                'id': '1',
                'name': 'Route Stop',
                'address': '100 Route Rd',
                'city': 'Test',
                'state': 'TX',
                'price': 3.50,
                'latitude': 34.05,
                'longitude': -118.25,
                'to_dict': lambda self=None: {
                    'id': '1',
                    'name': 'Route Stop',
                    'address': '100 Route Rd',
                    'city': 'Test',
                    'state': 'TX',
                    'price': 3.50,
                    'latitude': 34.05,
                    'longitude': -118.25,
                }
            })(),
            type('Station', (), {
                'id': '2',
                'name': 'Far Stop',
                'address': '500 Far St',
                'city': 'Test',
                'state': 'TX',
                'price': 2.50,
                'latitude': 35.00,
                'longitude': -119.00,
                'to_dict': lambda self=None: {
                    'id': '2',
                    'name': 'Far Stop',
                    'address': '500 Far St',
                    'city': 'Test',
                    'state': 'TX',
                    'price': 2.50,
                    'latitude': 35.00,
                    'longitude': -119.00,
                }
            })(),
        ]

    def test_get_stations_near_route(self):
        route_points = [
            (34.00, -118.30),
            (34.10, -118.20),
        ]

        result = self.service.get_stations_near_route(route_points, buffer_miles=10)

        assert len(result) == 1
        assert result[0]['name'] == 'Route Stop'
        assert result[0]['distance_to_route'] <= 10
