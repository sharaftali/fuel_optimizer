"""
Django management command to preload fuel stations data.
Usage: python manage.py preload_stations
"""
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from api.services.stations import stations_service

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Preload fuel stations data from CSV into memory'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            help='Path to CSV file (overrides settings)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload even if already loaded'
        )
    
    def handle(self, *args, **options):
        csv_path = options.get('csv-path')
        force = options.get('force', False)
        
        self.stdout.write("=" * 60)
        self.stdout.write("FUEL STATIONS PRELOAD COMMAND")
        self.stdout.write("=" * 60)
        
        if stations_service.is_loaded() and not force:
            self.stdout.write(self.style.WARNING(
                f"Stations already loaded ({stations_service.get_count()} stations)"
            ))
            self.stdout.write("Use --force to reload")
            return
        
        self.stdout.write("Loading fuel stations from CSV...")
        
        if csv_path:
            self.stdout.write(f"Using custom CSV path: {csv_path}")
            success = stations_service.load_stations(csv_path)
        else:
            csv_path = getattr(settings, 'FUEL_STATIONS_CSV', 'data/fuel_prices_with_coords.csv')
            self.stdout.write(f"Using CSV path: {csv_path}")
            success = stations_service.load_stations()
        
        if success:
            self.stdout.write(self.style.SUCCESS(
                f"Successfully loaded {stations_service.get_count()} fuel stations"
            ))
            
            stations = stations_service.get_all_stations()
            if stations:
                self.stdout.write("\nSample stations:")
                for i, station in enumerate(stations[:5]):
                    self.stdout.write(
                        f"  {i+1}. {station.name} - {station.city}, {station.state} "
                        f"(${station.price:.4f})"
                    )
        else:
            error = stations_service.get_load_error()
            self.stdout.write(self.style.ERROR(f"Failed to load stations: {error}"))
        
        self.stdout.write("=" * 60)
