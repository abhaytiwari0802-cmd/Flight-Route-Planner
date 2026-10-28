"""Configuration and path resolutions for the web application."""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = PROJECT_DIR / "data"

AIRPORTS_CSV = DATA_DIR / "airports.csv"
ROUTES_CSV = DATA_DIR / "routes.csv"

STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Host & Port
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
