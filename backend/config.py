import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "database" / "prices.db"

# Database
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# API
API_HOST = "0.0.0.0"
API_PORT = 8000

# Scraper settings
SCRAPER_REQUEST_TIMEOUT = 30
SCRAPER_RETRY_TIMES = 3
SCRAPER_MIN_DELAY = 2  # seconds

# Logging
LOG_DIR = BASE_DIR / "logs"
LOG_LEVEL = "INFO"