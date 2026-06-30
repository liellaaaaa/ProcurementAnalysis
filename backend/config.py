import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "database" / "prices.db"

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")

# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Scraper settings
SCRAPER_REQUEST_TIMEOUT = int(os.getenv("SCRAPER_REQUEST_TIMEOUT", "30"))
SCRAPER_RETRY_TIMES = int(os.getenv("SCRAPER_RETRY_TIMES", "3"))
SCRAPER_MIN_DELAY = int(os.getenv("SCRAPER_MIN_DELAY", "2"))

# 数据源新鲜度配置 (max_delay_days: 最大允许延迟天数)
SOURCE_FRESHNESS_CONFIG = {
    "shengyishe": {"max_delay_days": 1, "description": "T+1延迟数据源"},
    "manual": {"max_delay_days": 0, "description": "实时数据源"},
}

# 爬虫抓取间隔控制 (秒)
SCRAPER_MIN_INTERVAL = int(os.getenv("SCRAPER_MIN_INTERVAL", "1800"))

# Logging
LOG_DIR = BASE_DIR / "logs"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "procurement-analysis-secret-key-2024")
ALGORITHM = "HS256"

# 行为日志配置
BEHAVIOR_SLOW_REQUEST_THRESHOLD_MS = int(os.getenv("BEHAVIOR_SLOW_REQUEST_THRESHOLD_MS", "2000"))
BEHAVIOR_SAMPLE_RATE = int(os.getenv("BEHAVIOR_SAMPLE_RATE", "10"))  # 成功请求采样率 %
BEHAVIOR_DATA_RETENTION_DAYS = 90  # GDPR 合规：数据保留天数
