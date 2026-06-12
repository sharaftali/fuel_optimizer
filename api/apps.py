from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'Fuel Optimizer API'
    
    def ready(self):
        """
        Preload stations data when Django starts.
        This runs once at application startup.
        """
        try:
            from api.services.stations import stations_service
            
            # Try to load stations
            if stations_service.load_stations():
                logger.info(f"Preloaded {stations_service.get_count()} fuel stations on startup")
            else:
                logger.warning(f"Failed to preload stations: {stations_service.get_load_error()}")
                
        except Exception as e:
            logger.error(f"Error preloading stations: {e}")