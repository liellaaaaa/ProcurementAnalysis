from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL

Base = declarative_base()

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


class ProductCategory(Base):
    __tablename__ = "product_categories"

    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.now)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_code = Column(String(50), unique=True, nullable=False)
    product_name = Column(String(100), nullable=False)
    industry = Column(String(20))  # 行业：化工/能源/农副/有色
    category = Column(String(50))
    unit = Column(String(20), default="元/吨")
    source = Column(String(50))
    source_url = Column(String(500))     # detail 页 URL（基准价）
    plist_url = Column(String(500))      # plist 页 URL（详细报价，可为空）
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class PriceRecord(Base):
    __tablename__ = "price_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(Float)
    currency = Column(String(10), default="CNY")
    unit = Column(String(20))  # 单位：元/吨、元/克、元/立方米
    price_original = Column(String(100))  # 原始报价文本，如"2750元/吨"
    price_category = Column(String(20))  # 价格类别：现货/期货
    price_type = Column(String(20))
    trend = Column(String(10))  # 涨/跌/平
    change_percent = Column(Float)
    source = Column(String(50))
    region = Column(String(50))      # 地区/产地
    supplier = Column(String(100))   # 供应商
    brand = Column(String(100))      # 品牌
    specification = Column(String(200))  # 规格
    extra_data = Column(JSON)  # 行业差异化字段
    record_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("product_id", "record_date", "source", "region", "supplier", name="uq_price_date_source_region_supplier"),
    )


class BenchmarkPrice(Base):
    """基准价表 - 每个产品每天一条记录（从 detail-xxx.html 解析）"""
    __tablename__ = "benchmark_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(100)) # 产品名称（冗余存储，冗余但便于查询）
    spec = Column(String(200))       # 基准规格
    brand = Column(String(100))      # 品牌
    market = Column(String(50))      # 市场
    price = Column(Float)
    unit = Column(String(20), default="元/吨")
    price_original = Column(String(100))  # 原始报价文本
    trend = Column(String(10))        # 涨/跌/平
    change_percent = Column(Float)    # 涨跌幅 %
    change_reason = Column(String(200))  # 涨跌原因
    source = Column(String(50))
    record_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("product_id", "record_date", name="uq_benchmark_product_date"),
    )


class DetailedQuote(Base):
    """详细报价表 - 每个产品每天多条记录（从 plist-xxx.html 解析）"""
    __tablename__ = "detailed_quotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(100), nullable=False)
    spec = Column(String(200))       # 规格
    brand = Column(String(100))      # 品牌/产地
    price = Column(Float)
    unit = Column(String(20), default="元/吨")
    price_original = Column(String(100))  # 原始报价文本
    price_type = Column(String(20))  # 报价类型（现货/期货/市场价）
    price_category = Column(String(20))  # 价格分类（现货/期货/锁价）
    region = Column(String(50))      # 交货地/区域
    supplier = Column(String(100))   # 供应商/交易商
    source = Column(String(50))
    publish_date = Column(Date, nullable=False)
    extra_data = Column(JSON)        # 行业差异化字段
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("product_id", "publish_date", "region", "supplier", "price_type",
                         name="uq_detailed_quote_key"),
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

class OperationLog(Base):
    """操作日志（文件日志为主，此表用于方便查询）"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now)
    level = Column(String(10))  # INFO/WARNING/ERROR
    module = Column(String(20))  # PRODUCT/PRICE/ALERT/REPORT/SCRAPER/CATEGORY/SYSTEM
    action = Column(String(20))  # CREATE/UPDATE/DELETE/QUERY/EXPORT/SCRAPE
    details = Column(String(1000))  # JSON格式的详情
    result = Column(String(20))  # SUCCESS/FAILURE/WARNING
    operator = Column(String(50), default="system")  # 操作人标识

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