from django.urls import path
from .views import RouteOptimizeView, FuelOptimizeView, HealthCheckView

urlpatterns = [
    path('v1/route/optimize/', RouteOptimizeView.as_view(), name='route-optimize'),
    path('v1/fuel/optimize/', FuelOptimizeView.as_view(), name='fuel-optimize'),
    path('v1/health/', HealthCheckView.as_view(), name='health-check'),
]