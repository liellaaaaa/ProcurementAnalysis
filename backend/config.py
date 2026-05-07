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

# 数据源新鲜度配置 (max_delay_days: 最大允许延迟天数)
SOURCE_FRESHNESS_CONFIG = {
    "shengyishe": {"max_delay_days": 1, "description": "T+1延迟数据源"},
    "manual": {"max_delay_days": 0, "description": "实时数据源"},
}

# 爬虫抓取间隔控制 (秒)
SCRAPER_MIN_INTERVAL = 1800  # 30分钟

# Logging
LOG_DIR = BASE_DIR / "logs"
LOG_LEVEL = "INFO"