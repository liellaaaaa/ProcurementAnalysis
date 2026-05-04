from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.database import get_session, Product, PriceRecord

router = APIRouter(prefix="/api/v1/prices", tags=["价格数据"])

class PriceRecordResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    price: float
    trend: Optional[str] = None
    change_percent: Optional[float] = None
    source: Optional[str] = None
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

@router.get("/latest", response_model=List[PriceRecordResponse])
async def get_latest_prices(source: Optional[str] = None):
    """获取各产品最新价格"""
    session = get_session()

    # 子查询获取每个产品的最新日期
    subquery = session.query(
        PriceRecord.product_id,
        func.max(PriceRecord.record_date).label('max_date')
    )
    if source:
        subquery = subquery.filter(PriceRecord.source == source)
    subquery = subquery.group_by(PriceRecord.product_id).subquery()

    query = session.query(PriceRecord, Product.product_name, Product.product_code).join(
        Product
    ).join(
        subquery,
        (PriceRecord.product_id == subquery.c.product_id) &
        (PriceRecord.record_date == subquery.c.max_date)
    )

    if source:
        query = query.filter(PriceRecord.source == source)

    results = query.all()

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