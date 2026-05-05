from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import asyncio
from backend.models.database import get_session, Product, PriceRecord
from backend.services.alert_service import check_and_trigger_alerts

router = APIRouter(prefix="/api/v1/prices", tags=["价格数据"])

class PriceRecordCreate(BaseModel):
    product_id: int
    price: float
    currency: Optional[str] = "CNY"
    price_type: Optional[str] = "市场价"
    trend: Optional[str] = "平"
    change_percent: Optional[float] = 0.0
    source: Optional[str] = "manual"
    record_date: str  # YYYY-MM-DD format

class PriceRecordResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    price: float
    trend: Optional[str] = None
    change_percent: Optional[float] = None
    source: Optional[str] = None
    region: Optional[str] = None
    supplier: Optional[str] = None
    brand: Optional[str] = None
    specification: Optional[str] = None
    record_date: date

    class Config:
        from_attributes = True

@router.get("", response_model=List[PriceRecordResponse])
async def get_prices(
    product_id: Optional[int] = None,
    source: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """获取价格数据列表"""
    session = get_session()
    query = session.query(PriceRecord, Product.product_name, Product.product_code).join(Product)

    if product_id:
        query = query.filter(PriceRecord.product_id == product_id)
    if source:
        query = query.filter(PriceRecord.source == source)
    if start_date:
        query = query.filter(PriceRecord.record_date >= start_date)
    if end_date:
        query = query.filter(PriceRecord.record_date <= end_date)

    results = query.order_by(PriceRecord.record_date.desc()).limit(limit).all()

    response = []
    for pr, product_name, product_code in results:
        response.append(PriceRecordResponse(
            id=pr.id,
            product_id=pr.product_id,
            product_name=product_name,
            product_code=product_code,
            price=pr.price,
            trend=pr.trend,
            change_percent=pr.change_percent,
            source=pr.source,
            record_date=pr.record_date
        ))

    session.close()
    return response

@router.get("/latest", response_model=dict)
async def get_latest_prices(
    source: Optional[str] = None,
    product_name: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取各产品最新价格（分页+筛选）"""
    session = get_session()

    # 子查询获取每个产品的最新日期
    subquery = session.query(
        PriceRecord.product_id,
        func.max(PriceRecord.record_date).label('max_date')
    ).group_by(PriceRecord.product_id).subquery()

    query = session.query(PriceRecord, Product.product_name, Product.product_code).join(
        Product
    ).join(
        subquery,
        (PriceRecord.product_id == subquery.c.product_id) &
        (PriceRecord.record_date == subquery.c.max_date)
    )

    if source:
        query = query.filter(PriceRecord.source == source)
    if product_name:
        query = query.filter(Product.product_name.contains(product_name))

    # 总数
    total = query.count()
    # 分页
    results = query.order_by(PriceRecord.record_date.desc()).offset((page - 1) * page_size).limit(page_size).all()

    response = []
    for pr, product_name, product_code in results:
        response.append(PriceRecordResponse(
            id=pr.id,
            product_id=pr.product_id,
            product_name=product_name,
            product_code=product_code,
            price=pr.price,
            trend=pr.trend,
            change_percent=pr.change_percent,
            source=pr.source,
            region=pr.region,
            supplier=pr.supplier,
            brand=pr.brand,
            specification=pr.specification,
            record_date=pr.record_date
        ))

    session.close()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": response
    }

@router.get("/history/{product_id}", response_model=List[PriceRecordResponse])
async def get_price_history(
    product_id: int,
    days: int = Query(30, ge=1, le=365),
    source: Optional[str] = None
):
    """获取产品历史价格趋势"""
    session = get_session()

    start_date = (date.today() - timedelta(days=days)).isoformat()

    query = session.query(PriceRecord, Product.product_name, Product.product_code).join(
        Product
    ).filter(
        PriceRecord.product_id == product_id,
        PriceRecord.record_date >= start_date
    )

    if source:
        query = query.filter(PriceRecord.source == source)

    results = query.order_by(PriceRecord.record_date.asc()).all()

    response = []
    for pr, product_name, product_code in results:
        response.append(PriceRecordResponse(
            id=pr.id,
            product_id=pr.product_id,
            product_name=product_name,
            product_code=product_code,
            price=pr.price,
            trend=pr.trend,
            change_percent=pr.change_percent,
            source=pr.source,
            record_date=pr.record_date
        ))

    session.close()
    return response

@router.get("/stats/summary")
async def get_stats_summary():
    """获取统计摘要"""
    session = get_session()

    total_products = session.query(func.count(Product.id)).filter(Product.is_active == True).scalar()
    total_records = session.query(func.count(PriceRecord.id)).scalar()

    # 平均价格（最新价格）
    subquery = session.query(
        PriceRecord.product_id,
        func.max(PriceRecord.record_date).label('max_date')
    ).group_by(PriceRecord.product_id).subquery()

    avg_price_result = session.query(func.avg(PriceRecord.price)).join(
        subquery,
        (PriceRecord.product_id == subquery.c.product_id) &
        (PriceRecord.record_date == subquery.c.max_date)
    ).scalar()

    avg_price = round(avg_price_result, 2) if avg_price_result else 0

    session.close()

    return {
        "total_products": total_products or 0,
        "total_records": total_records or 0,
        "avg_price": avg_price
    }

@router.post("", response_model=PriceRecordResponse)
async def create_price_record(record: PriceRecordCreate):
    """手动添加价格记录"""
    session = get_session()

    # 验证产品存在
    product = session.query(Product).filter(Product.id == record.product_id).first()
    if not product:
        session.close()
        raise HTTPException(status_code=404, detail="产品不存在")

    # 检查重复记录
    existing = session.query(PriceRecord).filter(
        PriceRecord.product_id == record.product_id,
        PriceRecord.record_date == datetime.strptime(record.record_date, "%Y-%m-%d").date(),
        PriceRecord.source == record.source
    ).first()
    if existing:
        session.close()
        raise HTTPException(status_code=400, detail="该日期价格记录已存在")

    new_record = PriceRecord(
        product_id=record.product_id,
        price=record.price,
        currency=record.currency,
        price_type=record.price_type,
        trend=record.trend,
        change_percent=record.change_percent,
        source=record.source,
        record_date=datetime.strptime(record.record_date, "%Y-%m-%d").date()
    )
    session.add(new_record)
    session.commit()
    session.refresh(new_record)

    # 检查预警触发
    check_and_trigger_alerts(session, new_record.product_id, new_record.price)

    session.close()

    return PriceRecordResponse(
        id=new_record.id,
        product_id=new_record.product_id,
        product_name=product.product_name,
        product_code=product.product_code,
        price=new_record.price,
        trend=new_record.trend,
        change_percent=new_record.change_percent,
        source=new_record.source,
        record_date=new_record.record_date
    )

@router.put("/{record_id}", response_model=PriceRecordResponse)
async def update_price_record(record_id: int, record: PriceRecordCreate):
    """更新价格记录"""
    session = get_session()
    db_record = session.query(PriceRecord).filter(PriceRecord.id == record_id).first()

    if not db_record:
        session.close()
        raise HTTPException(status_code=404, detail="价格记录不存在")

    update_data = record.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == 'record_date':
            setattr(db_record, field, datetime.strptime(value, "%Y-%m-%d").date())
        else:
            setattr(db_record, field, value)

    session.commit()
    session.refresh(db_record)

    product = session.query(Product).filter(Product.id == db_record.product_id).first()
    session.close()

    return PriceRecordResponse(
        id=db_record.id,
        product_id=db_record.product_id,
        product_name=product.product_name if product else None,
        product_code=product.product_code if product else None,
        price=db_record.price,
        trend=db_record.trend,
        change_percent=db_record.change_percent,
        source=db_record.source,
        record_date=db_record.record_date
    )

@router.delete("/{record_id}")
async def delete_price_record(record_id: int):
    """删除价格记录"""
    session = get_session()
    record = session.query(PriceRecord).filter(PriceRecord.id == record_id).first()

    if not record:
        session.close()
        raise HTTPException(status_code=404, detail="价格记录不存在")

    session.delete(record)
    session.commit()
    session.close()

    return {"message": "价格记录已删除"}