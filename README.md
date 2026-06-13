# ⛽ Fuel Optimizer API

A production-ready Django REST API that calculates optimal fuel stops along US routes based on real fuel prices.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.1-green.svg)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.15-red.svg)](https://www.django-rest-framework.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Overview

This API solves the **fuel stop optimization problem** for long-distance travel across the United States. Given a start and finish location, it:

1. Calculates the optimal driving route using OSRM (Open Source Routing Machine)
2. Finds fuel stations within 10 miles of the route (configurable)
3. Uses a **greedy algorithm** to select the cheapest fuel stops
4. Returns the route, fuel stops, and total cost

**Vehicle Specifications:**
- ⛽ **Range:** 500 miles per full tank
- 🚗 **Efficiency:** 10 miles per gallon
- 💰 **Strategy:** Always fill at the cheapest station within remaining range

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🌐 **Route Calculation** | OSRM integration for accurate driving routes |
| 📍 **Geocoding** | Nominatim (OpenStreetMap) with permanent caching |
| 🗺️ **Route-Aware Filtering** | Stations filtered by actual driving path, not straight line |
| 🔄 **Caching** | 24-hour route cache, permanent geocoding cache |
| ⛽ **Fuel Stations** | 7,200+ geocoded truck stops with real prices |
| 📊 **Greedy Algorithm** | Optimal fuel stop selection |
| 🐳 **Docker Support** | Containerized deployment ready |
| 📚 **API Documentation** | Swagger/OpenAPI UI included |
| ✅ **Testing** | 16+ unit and integration tests |

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/sharaftali/fuel_optimizer.git
cd fuel_optimizer

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start the development server
python manage.py runserver
