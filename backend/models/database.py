from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, UniqueConstraint, JSON, Index
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime
import os

from backend.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


class ProductCategory(Base):
    __tablename__ = "product_categories"

    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=datetime.now)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_code = Column(String(50), unique=True, nullable=False)
    product_name = Column(String(100), nullable=False)
    industry = Column(String(20))
    category = Column(String(50))
    unit = Column(String(20), default="元/吨")
    source = Column(String(50))
    source_url = Column(String(500))
    plist_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class PriceRecord(Base):
    __tablename__ = "price_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    price = Column(Float)
    currency = Column(String(10), default="CNY")
    unit = Column(String(20))
    price_original = Column(String(100))
    price_category = Column(String(20))
    price_type = Column(String(20))
    trend = Column(String(10))
    change_percent = Column(Float)
    source = Column(String(50))
    region = Column(String(50))
    supplier = Column(String(100))
    brand = Column(String(100))
    specification = Column(String(200))
    extra_data = Column(JSON)
    record_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("product_id", "record_date", "source", "region", "supplier", name="uq_price_date_source_region_supplier"),
        Index("ix_price_product_date", "product_id", "record_date"),
    )


class BenchmarkPrice(Base):
    """基准价表 - 每个产品每天一条记录（从 detail-xxx.html 解析）"""
    __tablename__ = "benchmark_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String(100))
    spec = Column(String(200))
    brand = Column(String(100))
    market = Column(String(50))
    price = Column(Float)
    unit = Column(String(20), default="元/吨")
    price_original = Column(String(100))
    trend = Column(String(10))
    change_percent = Column(Float)
    change_reason = Column(String(200))
    source = Column(String(50))
    record_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("product_id", "record_date", name="uq_benchmark_product_date"),
        Index("ix_benchmark_product_date", "product_id", "record_date"),
    )


class DetailedQuote(Base):
    """详细报价表 - 每个产品每天多条记录（从 plist-xxx.html 解析）"""
    __tablename__ = "detailed_quotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String(100), nullable=False)
    spec = Column(String(200))
    brand = Column(String(100))
    price = Column(Float)
    unit = Column(String(20), default="元/吨")
    price_original = Column(String(100))
    price_type = Column(String(20))
    price_category = Column(String(20))
    region = Column(String(50))
    supplier = Column(String(100))
    source = Column(String(50))
    publish_date = Column(Date, nullable=False)
    extra_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("product_id", "publish_date", "region", "supplier", "price_type",
                         name="uq_detailed_quote_key"),
        Index("ix_detailed_product_date", "product_id", "publish_date"),
    )

class AlertConfig(Base):
    __tablename__ = "alert_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(20))
    threshold_value = Column(Float)
    change_percent = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("ix_alert_config_product", "product_id"),
    )

class AlertRecord(Base):
    __tablename__ = "alert_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_config_id = Column(Integer, ForeignKey("alert_configs.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    alert_message = Column(String(500))
    triggered_price = Column(Float)
    triggered_at = Column(DateTime, default=datetime.now)
    is_read = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_alert_record_product", "product_id"),
    )

class Feedback(Base):
    """反馈记录表"""
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    feedback_date = Column(String(20), nullable=False)
    current_status = Column(String(500), nullable=False)
    expected_result = Column(String(500), nullable=False)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(String(30))
    rating = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Satisfaction(Base):
    """满意度记录表"""
    __tablename__ = "satisfactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    score = Column(Integer, nullable=False)
    complaint = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ScraperLog(Base):
    __tablename__ = "scraper_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scraper_name = Column(String(50))
    status = Column(String(20))
    items_scraped = Column(Integer, default=0)
    error_message = Column(String(500))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class OperationLog(Base):
    """操作日志（文件日志为主，此表用于方便查询）"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now)
    level = Column(String(10))
    module = Column(String(20))
    action = Column(String(20))
    details = Column(String(1000))
    result = Column(String(20))
    operator = Column(String(50), default="system")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)


def init_db(echo=False):
    init_engine = create_engine(DATABASE_URL, echo=echo)
    Base.metadata.create_all(init_engine)
    init_engine.dispose()
    return init_engine


def get_session():
    return SessionLocal()


if __name__ == "__main__":
    os.makedirs(os.path.dirname(__file__).replace("models", "") + "/data/database", exist_ok=True)
    init_db()
    print("Database initialized.")
