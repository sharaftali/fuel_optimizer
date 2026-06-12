"""
API serializers for request/response validation.
"""
from rest_framework import serializers


class RouteRequestSerializer(serializers.Serializer):
    """Validate request query parameters for route endpoint."""
    start = serializers.CharField(
        max_length=500,
        required=True,
        help_text="Starting location (address, city/state, or ZIP code)"
    )
    finish = serializers.CharField(
        max_length=500,
        required=True,
        help_text="Destination location (address, city/state, or ZIP code)"
    )
    
    def validate_start(self, value):
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Start location must be at least 2 characters")
        return value.strip()
    
    def validate_finish(self, value):
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Finish location must be at least 2 characters")
        return value.strip()


class FuelOptimizeRequestSerializer(serializers.Serializer):
    """Validate request query parameters for fuel optimization endpoint."""
    start = serializers.CharField(
        max_length=500,
        required=True,
        help_text="Starting location (address, city/state, or ZIP code)"
    )
    finish = serializers.CharField(
        max_length=500,
        required=True,
        help_text="Destination location (address, city/state, or ZIP code)"
    )
    buffer_miles = serializers.IntegerField(
        required=False,
        default=10,
        min_value=1,
        max_value=50,
        help_text="Search radius in miles around route for fuel stations"
    )


class LocationSerializer(serializers.Serializer):
    """Location response serializer."""
    address = serializers.CharField(help_text="Formatted address")
    coordinates = serializers.ListField(
        child=serializers.FloatField(),
        help_text="[longitude, latitude] coordinates"
    )


class RouteResponseSerializer(serializers.Serializer):
    """Route response serializer."""
    start_location = LocationSerializer()
    finish_location = LocationSerializer()
    total_distance_miles = serializers.FloatField(help_text="Distance in miles")
    polyline = serializers.CharField(help_text="Encoded polyline for route visualization")
    cached = serializers.BooleanField(help_text="Whether response came from cache")


class FuelStopSerializer(serializers.Serializer):
    """Fuel stop response serializer."""
    name = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    price = serializers.FloatField()
    gallons = serializers.FloatField()
    cost = serializers.FloatField()
    miles_from_start = serializers.FloatField()
    miles_from_previous = serializers.FloatField()


class FuelPlanSerializer(serializers.Serializer):
    """Fuel plan response serializer."""
    stops = FuelStopSerializer(many=True)
    total_gallons = serializers.FloatField()
    total_cost = serializers.FloatField()
    total_miles = serializers.FloatField()


class FuelOptimizeResponseSerializer(serializers.Serializer):
    """Complete fuel optimization response serializer."""
    status = serializers.CharField()
    route = RouteResponseSerializer()
    fuel_plan = FuelPlanSerializer()
    summary = serializers.DictField()


class ErrorResponseSerializer(serializers.Serializer):
    """Error response serializer."""
    status = serializers.CharField(default='error')
    error = serializers.CharField()
    code = serializers.CharField(required=False)
    details = serializers.DictField(required=False)