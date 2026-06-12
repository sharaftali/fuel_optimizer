# Fuel Optimizer API

A production-ready Django REST API that calculates optimal fuel stops along US routes based on real fuel prices.

## Features

- Route calculation between any two US locations
- Fuel stop optimization for vehicles with 500-mile range and 10 MPG
- Real fuel price data from 8,000+ truck stops
- Caching for geocoding and route results
- OpenAPI/Swagger documentation
- Docker support

## Quick Start

```bash
# Clone repository
git clone <repo-url>
cd fuel_optimizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver

# Run the geocoding script (this will take ~30-40 minutes)
python scripts/geocode_initial.py

# Or for testing with limit
python scripts/geocode_initial.py --limit 100