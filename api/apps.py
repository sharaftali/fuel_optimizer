from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'Fuel Optimizer API'
    
    def ready(self):
        """Preload stations data when Django starts."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            from api.services.stations import stations_service
            # Trigger station loading
            _ = stations_service.get_all_stations()
            logger.info("Stations data preloaded successfully")
        except Exception as e:
            logger.warning(f"Could not preload stations: {e}")