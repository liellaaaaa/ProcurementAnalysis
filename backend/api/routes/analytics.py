from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from datetime import date, timedelta, datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.api.deps import get_db
from backend.utils.date_utils import format_date
from backend.models.database import Product, PriceRecord

router = APIRouter(prefix="/api/v1/prices", tags=["价格分析"])


def simple_linear_regression(values: List[float]) -> tuple:
    """简单线性回归，返回斜率和预测值"""
    if len(values) < 2:
        return 0, values[-1] if values else 0

    n = len(values)
    x_mean = sum(range(n)) / n
    y_mean = sum(values) / n

    numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return 0, values[-1]

    slope = numerator / denominator
    next_pred = values[-1] + slope
    return slope, next_pred


@router.get("/stats/weekly")
async def get_weekly_stats(db: Session = Depends(get_db)):
    """本周价格统计"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    results = db.query(
        PriceRecord.product_id,
        Product.product_name,
        func.max(PriceRecord.price).label('max_price'),
        func.min(PriceRecord.price).label('min_price'),
        func.avg(PriceRecord.price).label('avg_price'),
        func.count(PriceRecord.id).label('record_count')
    ).join(Product).filter(
        PriceRecord.record_date >= week_start,
        PriceRecord.record_date <= week_end
    ).group_by(PriceRecord.product_id).all()

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "products": [
            {
                "product_id": r.product_id,
                "product_name": r.product_name,
                "max_price": round(r.max_price, 2),
                "min_price": round(r.min_price, 2),
                "avg_price": round(r.avg_price, 2),
                "record_count": r.record_count
            }
            for r in results
        ]
    }


@router.get("/stats/monthly")
async def get_monthly_stats(month: Optional[str] = None, db: Session = Depends(get_db)):
    """本月价格统计"""
    today = date.today()
    if month:
        year, month_num = map(int, month.split('-'))
        month_start = date(year, month_num, 1)
        if month_num == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month_num + 1, 1) - timedelta(days=1)
    else:
        month_start = date(today.year, today.month, 1)
        if today.month == 12:
            month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)

    results = db.query(
        PriceRecord.product_id,
        Product.product_name,
        func.max(PriceRecord.price).label('max_price'),
        func.min(PriceRecord.price).label('min_price'),
        func.avg(PriceRecord.price).label('avg_price'),
        func.count(PriceRecord.id).label('record_count')
    ).join(Product).filter(
        PriceRecord.record_date >= month_start,
        PriceRecord.record_date <= month_end
    ).group_by(PriceRecord.product_id).all()

    return {
        "month_start": month_start.isoformat(),
        "month_end": month_end.isoformat(),
        "products": [
            {
                "product_id": r.product_id,
                "product_name": r.product_name,
                "max_price": round(r.max_price, 2),
                "min_price": round(r.min_price, 2),
                "avg_price": round(r.avg_price, 2),
                "record_count": r.record_count
            }
            for r in results
        ]
    }


@router.get("/stats/ranking")
async def get_price_ranking(limit: int = Query(10, le=50), days: int = Query(7, le=90), db: Session = Depends(get_db)):
    """价格涨跌排行榜"""
    start_date = date.today() - timedelta(days=days)

    subquery = db.query(
        PriceRecord.product_id,
        func.max(PriceRecord.record_date).label('latest_date')
    ).filter(PriceRecord.record_date >= start_date).group_by(PriceRecord.product_id).subquery()

    latest_records = db.query(PriceRecord).join(
        subquery,
        (PriceRecord.product_id == subquery.c.product_id) &
        (PriceRecord.record_date == subquery.c.latest_date)
    ).all()

    product_ids = [r.product_id for r in latest_records]
    products_map = {p.id: p.product_name for p in db.query(Product).filter(Product.id.in_(product_ids)).all()}

    change_data = []
    for record in latest_records:
        old_date = record.record_date - timedelta(days=days)
        old_record = db.query(PriceRecord).filter(
            PriceRecord.product_id == record.product_id,
            PriceRecord.record_date <= old_date,
            PriceRecord.source == record.source
        ).order_by(PriceRecord.record_date.desc()).first()

        if old_record and old_record.price > 0:
            change_pct = ((record.price - old_record.price) / old_record.price) * 100
            change_data.append({
                "product_id": record.product_id,
                "product_name": products_map.get(record.product_id, ""),
                "latest_price": record.price,
                "old_price": old_record.price,
                "change_percent": round(change_pct, 2),
                "source": record.source
            })

    rising = sorted([x for x in change_data if x['change_percent'] > 0], key=lambda x: x['change_percent'], reverse=True)[:limit]
    falling = sorted([x for x in change_data if x['change_percent'] < 0], key=lambda x: x['change_percent'])[:limit]

    return {
        "rising": rising,
        "falling": falling
    }


@router.get("/forecast/{product_id}")
async def get_price_forecast(product_id: int, days: int = Query(30, le=90), db: Session = Depends(get_db)):
    """价格预测（基于移动平均和线性回归）"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "产品不存在"}

    records = db.query(PriceRecord).filter(
        PriceRecord.product_id == product_id
    ).order_by(PriceRecord.record_date.asc()).limit(days).all()

    if len(records) < 3:
        return {"error": "数据不足，无法预测", "record_count": len(records)}

    prices = [r.price for r in records]
    dates = [r.record_date for r in records]

    ma7 = sum(prices[-7:]) / min(7, len(prices)) if len(prices) >= 7 else sum(prices) / len(prices)
    ma30 = sum(prices) / len(prices) if len(prices) <= 30 else sum(prices[-30:]) / 30

    slope, next_pred = simple_linear_regression(prices)

    trend_direction = "上涨" if slope > 0.5 else ("下跌" if slope < -0.5 else "平稳")

    return {
        "product_id": product_id,
        "product_name": product.product_name,
        "current_price": prices[-1],
        "ma7": round(ma7, 2),
        "ma30": round(ma30, 2),
        "trend_slope": round(slope, 4),
        "trend_direction": trend_direction,
        "forecast_next": round(max(next_pred, 0), 2),
        "record_count": len(records),
        "data_range": {
            "start": dates[0].isoformat(),
            "end": dates[-1].isoformat()
        }
    }


@router.get("/compare")
async def compare_products(product_ids: str = Query(..., description="产品ID列表，逗号分隔"), db: Session = Depends(get_db)):
    """多产品横向对比"""
    ids = [int(x.strip()) for x in product_ids.split(',')]

    results = []
    for pid in ids:
        product = db.query(Product).filter(Product.id == pid).first()
        if not product:
            continue

        latest_record = db.query(PriceRecord).filter(
            PriceRecord.product_id == pid
        ).order_by(PriceRecord.record_date.desc()).first()

        records_30 = db.query(PriceRecord).filter(
            PriceRecord.product_id == pid,
            PriceRecord.record_date >= date.today() - timedelta(days=30)
        ).all()

        prices = [r.price for r in records_30] if records_30 else [latest_record.price] if latest_record else []

        results.append({
            "product_id": pid,
            "product_name": product.product_name,
            "industry": product.industry,
            "category": product.category,
            "unit": product.unit,
            "latest_price": latest_record.price if latest_record else None,
            "latest_date": format_date(latest_record.record_date) if latest_record else None,
            "avg_price_30d": round(sum(prices) / len(prices), 2) if prices else None,
            "max_price_30d": max(prices) if prices else None,
            "min_price_30d": min(prices) if prices else None,
            "record_count_30d": len(records_30)
        })

    return {"products": results}