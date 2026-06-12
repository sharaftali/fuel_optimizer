#!/usr/bin/env python
"""
Geocode fuel stations from CSV using Nominatim (OpenStreetMap).
Output: CSV with latitude and longitude columns added.

Usage:
    python scripts/geocode_initial.py
    python scripts/geocode_initial.py --input data/fuel-prices-for-be-assessment.csv --output data/fuel_prices_with_coords.csv
    python scripts/geocode_initial.py --resume  # Resume from last successful
"""

import csv
import time
import logging
import argparse
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass, asdict

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('geocoding.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Station:
    """Fuel station data structure."""
    opis_truckstop_id: str
    truckstop_name: str
    address: str
    city: str
    state: str
    rack_id: str
    retail_price: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Geocoder:
    """Handles geocoding with rate limiting and retries."""
    
    BASE_URL = "https://nominatim.openstreetmap.org/search"
    REQUEST_DELAY_SECONDS = 1.0  # Respect Nominatim usage policy
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 10
    
    def __init__(self):
        self.session = self._create_session()
        self.last_request_time = 0
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy."""
        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=1,  # 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def _rate_limit(self) -> None:
        """Ensure we don't exceed 1 request per second."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.REQUEST_DELAY_SECONDS:
            time.sleep(self.REQUEST_DELAY_SECONDS - elapsed)
        self.last_request_time = time.time()
    
    def _clean_address(self, address: str, city: str, state: str) -> str:
        """
        Clean and simplify address for better geocoding results.
        Highway exit formats don't work well with Nominatim.
        """
        # Remove highway exit details (I-44, EXIT 283 & US-69)
        import re
        
        # Remove "I-XX, EXIT XXX" patterns
        cleaned = re.sub(r'I-\d+,?\s*EXIT\s*[\d\w&]+\s*', '', address, flags=re.IGNORECASE)
        cleaned = re.sub(r'EXIT\s*[\d\w&]+\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'&?\s*US-\d+\s*', '', cleaned)
        cleaned = re.sub(r'&?\s*SR-\d+\s*', '', cleaned)
        cleaned = re.sub(r'&?\s*CR-\d+\s*', '', cleaned)
        
        # Remove extra commas and spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip().rstrip(',')
        
        # If cleaned address is empty or too short, use just city + state
        if len(cleaned) < 5:
            return f"{city}, {state}, USA"
        
        return f"{cleaned}, {city}, {state}, USA"


    def geocode(self, address: str, city: str, state: str) -> Tuple[Optional[float], Optional[float]]:
        """Geocode with address cleaning."""
        # Try cleaned address first
        cleaned_address = self._clean_address(address, city, state)
        
        for attempt in range(self.MAX_RETRIES):
            try:
                self._rate_limit()
                
                params = {
                    "q": cleaned_address,
                    "format": "json",
                    "limit": 1,
                }
                headers = {
                    "User-Agent": "FuelOptimizer/1.0 (sharafatali.work@gmail.com)"
                }
                
                response = self.session.get(
                    self.BASE_URL,
                    params=params,
                    headers=headers,
                    timeout=self.TIMEOUT_SECONDS
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        lat = float(data[0]["lat"])
                        lon = float(data[0]["lon"])
                        logger.debug(f"Geocoded: {cleaned_address} -> ({lat}, {lon})")
                        return lat, lon
                
                # If cleaned address fails, fallback to city+state only
                if attempt == 0:
                    fallback_address = f"{city}, {state}, USA"
                    logger.info(f"Retrying with fallback: {fallback_address}")
                    params["q"] = fallback_address
                    continue
                        
            except Exception as e:
                logger.warning(f"Error (attempt {attempt + 1}): {e}")
            
            if attempt < self.MAX_RETRIES - 1:
                backoff = 2 ** attempt
                time.sleep(backoff)
        
        logger.warning(f"Failed after {self.MAX_RETRIES} attempts: {cleaned_address}")
        return None, None

def read_stations(input_path: Path) -> list[Station]:
    """Read CSV and return list of Station objects."""
    stations = []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                station = Station(
                    opis_truckstop_id=row['OPIS Truckstop ID'],
                    truckstop_name=row['Truckstop Name'],
                    address=row['Address'],
                    city=row['City'],
                    state=row['State'],
                    rack_id=row['Rack ID'],
                    retail_price=float(row['Retail Price']),
                )
                stations.append(station)
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping row due to error: {e}")
                continue
    
    logger.info(f"Loaded {len(stations)} stations from {input_path}")
    return stations


def write_stations(output_path: Path, stations: list[Station]) -> None:
    """Write stations to CSV with lat/lng columns."""
    if not stations:
        logger.warning("No stations to write")
        return
    
    fieldnames = [
        'OPIS Truckstop ID',
        'Truckstop Name',
        'Address',
        'City',
        'State',
        'Rack ID',
        'Retail Price',
        'latitude',
        'longitude'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for station in stations:
            row = {
                'OPIS Truckstop ID': station.opis_truckstop_id,
                'Truckstop Name': station.truckstop_name,
                'Address': station.address,
                'City': station.city,
                'State': station.state,
                'Rack ID': station.rack_id,
                'Retail Price': f"{station.retail_price:.8f}",
                'latitude': station.latitude if station.latitude else '',
                'longitude': station.longitude if station.longitude else '',
            }
            writer.writerow(row)
    
    logger.info(f"Wrote {len(stations)} stations to {output_path}")


def save_checkpoint(checkpoint_path: Path, stations: list[Station], index: int) -> None:
    """Save progress checkpoint for resume capability."""
    checkpoint = {
        'index': index,
        'stations': [asdict(s) for s in stations[:index] if s.latitude is not None]
    }
    # Simplified: just log the index, full checkpoint is complex
    logger.info(f"Checkpoint: {index}/{len(stations)} stations processed")


def main():
    parser = argparse.ArgumentParser(description='Geocode fuel stations CSV')
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('data/fuel-prices-for-be-assessment.csv'),
        help='Input CSV file path'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/fuel_prices_with_coords.csv'),
        help='Output CSV file path'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from last successful (not fully implemented, just continues)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of stations to process (for testing)'
    )
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    # Create output directory if needed
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Read stations
    stations = read_stations(args.input)
    
    if args.limit:
        stations = stations[:args.limit]
        logger.info(f"Limited to {args.limit} stations for testing")
    
    # Geocode
    geocoder = Geocoder()
    success_count = 0
    
    logger.info(f"Starting geocoding of {len(stations)} stations...")
    logger.info("This will take approximately {:.1f} hours".format(
        len(stations) * geocoder.REQUEST_DELAY_SECONDS / 3600
    ))
    
    for i, station in enumerate(stations):
        logger.info(f"Processing {i+1}/{len(stations)}: {station.truckstop_name} - {station.city}, {station.state}")
        
        lat, lng = geocoder.geocode(station.address, station.city, station.state)
        
        if lat is not None and lng is not None:
            station.latitude = lat
            station.longitude = lng
            success_count += 1
        else:
            station.latitude = None
            station.longitude = None
        
        # Save checkpoint every 50 stations
        if (i + 1) % 50 == 0:
            write_stations(args.output, stations[:i+1])
            logger.info(f"Checkpoint saved at {i+1} stations. Success rate: {success_count}/{i+1} ({success_count*100/(i+1):.1f}%)")
    
    # Write final output
    write_stations(args.output, stations)
    
    # Summary
    logger.info("=" * 50)
    logger.info("GEOCODING COMPLETE")
    logger.info(f"Total stations: {len(stations)}")
    logger.info(f"Successfully geocoded: {success_count}")
    logger.info(f"Failed: {len(stations) - success_count}")
    logger.info(f"Success rate: {success_count * 100 / len(stations):.1f}%")
    logger.info(f"Output saved to: {args.output}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()