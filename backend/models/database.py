from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_code = Column(String(50), unique=True, nullable=False)
    product_name = Column(String(100), nullable=False)
    category = Column(String(50))
    unit = Column(String(20), default="元/吨")
    source = Column(String(50))
    source_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class PriceRecord(Base):
    __tablename__ = "price_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(Float)
    currency = Column(String(10), default="CNY")
    price_type = Column(String(20))
    trend = Column(String(10))  # 涨/跌/平
    change_percent = Column(Float)
    source = Column(String(50))
    record_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("product_id", "record_date", "source", name="uq_price_date_source"),
    )

class AlertConfig(Base):
    __tablename__ = "alert_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    alert_type = Column(String(20))  # threshold/change_rate/trend
    threshold_value = Column(Float)
    change_percent = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

class AlertRecord(Base):
    __tablename__ = "alert_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_config_id = Column(Integer, ForeignKey("alert_configs.id"))
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    alert_message = Column(String(500))
    triggered_price = Column(Float)
    triggered_at = Column(DateTime, default=datetime.now)
    is_read = Column(Boolean, default=False)

class ScraperLog(Base):
    __tablename__ = "scraper_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scraper_name = Column(String(50))
    status = Column(String(20))  # running/success/failed
    items_scraped = Column(Integer, default=0)
    error_message = Column(String(500))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

def init_db():
    engine = create_engine(DATABASE_URL, echo=True)
    Base.metadata.create_all(engine)
    return engine

def get_session():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()

if __name__ == "__main__":
    os.makedirs(os.path.dirname(__file__).replace("models", "") + "/data/database", exist_ok=True)
    init_db()
    print("Database initialized.")