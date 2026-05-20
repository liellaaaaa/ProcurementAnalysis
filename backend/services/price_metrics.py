"""
同比/环比/日变化计算服务 - 价格变化分析
"""
from datetime import date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from backend.models.database import PriceRecord, Product, Category, ProductCategory


def get_period_bounds(year: int, month: int) -> Tuple[date, date]:
    """返回某年某月的起止日期"""
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    return start, end


def get_previous_period_bounds(period_type: str, curr_start: date, curr_end: date) -> Tuple[date, date]:
    """根据当前周期获取上一个周期的日期范围"""
    if period_type == "yoy":
        prev_start = curr_start.replace(year=curr_start.year - 1)
        prev_end = curr_end.replace(year=curr_end.year - 1)
    else:
        period_length = (curr_end - curr_start).days + 1
        prev_end = curr_start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=period_length - 1)
    return prev_start, prev_end


def _get_product_ids_by_industry(session: Session, industry: str):
    """获取指定行业的产品ID列表"""
    return [p[0] for p in session.query(Product.id).filter(Product.industry == industry).all()]


def _get_product_ids_by_category(session: Session, category_id: int):
    """获取指定分类及其子分类的产品ID列表"""
    subcat_ids = [c.id for c in session.query(Category).filter(Category.parent_id == category_id).all()]
    return [p[0] for p in session.query(ProductCategory.product_id).filter(
        ProductCategory.category_id.in_(subcat_ids + [category_id])
    ).distinct().all()]


def _get_product_ids_by_subcategory(session: Session, subcategory_ids: List[int]):
    """获取指定子分类的产品ID列表"""
    return [p[0] for p in session.query(Product.id).join(
        ProductCategory, Product.id == ProductCategory.product_id
    ).filter(ProductCategory.category_id.in_(subcategory_ids)).distinct().all()]


def calculate_yoy_mom(
    session: Session,
    period_type: str,
    source: Optional[str] = None,
    industry: Optional[str] = None,
    category_id: Optional[int] = None,
    subcategory_id: Optional[List[int]] = None,
    top_n: int = 10
) -> Dict[str, Any]:
    """计算同比/环比价格变化"""
    today = date.today()
    curr_start, curr_end = get_period_bounds(today.year, today.month)
    prev_start, prev_end = get_previous_period_bounds(period_type, curr_start, curr_end)

    # 确定要筛选的产品ID
    product_filter = None
    if industry:
        product_filter = _get_product_ids_by_industry(session, industry)
    if category_id:
        product_filter = _get_product_ids_by_category(session, category_id)
    if subcategory_id:
        product_filter = _get_product_ids_by_subcategory(session, subcategory_id)

    # 当前周期均价
    curr_query = session.query(
        PriceRecord.product_id,
        Product.product_name,
        func.avg(PriceRecord.price).label('avg_price')
    ).join(Product).filter(
        PriceRecord.record_date >= curr_start,
        PriceRecord.record_date <= curr_end
    )
    if source and source != '__all__':
        curr_query = curr_query.filter(PriceRecord.source == source)
    if product_filter:
        curr_query = curr_query.filter(PriceRecord.product_id.in_(product_filter))
    curr_query = curr_query.group_by(PriceRecord.product_id, Product.product_name)
    curr_results = {r.product_id: {'name': r.product_name, 'avg': r.avg_price} for r in curr_query.all()}

    # 上一周期均价
    prev_query = session.query(
        PriceRecord.product_id,
        func.avg(PriceRecord.price).label('avg_price')
    ).filter(
        PriceRecord.record_date >= prev_start,
        PriceRecord.record_date <= prev_end
    )
    if source and source != '__all__':
        prev_query = prev_query.filter(PriceRecord.source == source)
    if product_filter:
        prev_query = prev_query.filter(PriceRecord.product_id.in_(product_filter))
    prev_query = prev_query.group_by(PriceRecord.product_id)
    prev_results = {r.product_id: r.avg_price for r in prev_query.all()}

    # 最新价格
    latest_query = session.query(
        PriceRecord.product_id,
        func.max(PriceRecord.record_date).label('max_date')
    ).group_by(PriceRecord.product_id).subquery()
    latest_prices = session.query(
        PriceRecord.product_id,
        PriceRecord.price
    ).join(
        latest_query,
        (PriceRecord.product_id == latest_query.c.product_id) &
        (PriceRecord.record_date == latest_query.c.max_date)
    ).all()
    latest_price_map = {r.product_id: r.price for r in latest_prices}

    # 计算变化率
    items = []
    for product_id, curr_data in curr_results.items():
        prev_avg = prev_results.get(product_id)
        if prev_avg is None or prev_avg == 0:
            continue
        curr_avg = curr_data['avg']
        change_pct = ((curr_avg - prev_avg) / prev_avg) * 100
        items.append({
            "product_id": product_id,
            "product_name": curr_data['name'],
            "current_avg": round(curr_avg, 2),
            "previous_avg": round(prev_avg, 2),
            "change_percent": round(change_pct, 2),
            "trend": "rise" if change_pct >= 0 else "fall",
            "latest_price": latest_price_map.get(product_id, 0)
        })

    items.sort(key=lambda x: abs(x['change_percent']), reverse=True)
    return {
        "period_type": period_type,
        "current_period": {"start": curr_start.isoformat(), "end": curr_end.isoformat()},
        "previous_period": {"start": prev_start.isoformat(), "end": prev_end.isoformat()},
        "items": items[:top_n]
    }


def calculate_day_change(
    session: Session,
    days: int,
    source: Optional[str] = None,
    industry: Optional[str] = None,
    category_id: Optional[int] = None,
    subcategory_id: Optional[List[int]] = None,
    top_n: int = 10
) -> Dict[str, Any]:
    """计算N日涨跌"""
    today = date.today()
    curr_end = today
    curr_start = date.today() - timedelta(days=days)
    prev_end = curr_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days)

    # 确定要筛选的产品ID
    product_filter = None
    if industry:
        product_filter = _get_product_ids_by_industry(session, industry)
    if category_id:
        product_filter = _get_product_ids_by_category(session, category_id)
    if subcategory_id:
        product_filter = _get_product_ids_by_subcategory(session, subcategory_id)

    # 当前周期均价
    curr_query = session.query(
        PriceRecord.product_id,
        Product.product_name,
        func.avg(PriceRecord.price).label('avg_price')
    ).join(Product).filter(
        PriceRecord.record_date >= curr_start.isoformat(),
        PriceRecord.record_date <= curr_end.isoformat()
    )
    if source and source != '__all__':
        curr_query = curr_query.filter(PriceRecord.source == source)
    if product_filter:
        curr_query = curr_query.filter(PriceRecord.product_id.in_(product_filter))
    curr_query = curr_query.group_by(PriceRecord.product_id, Product.product_name)
    curr_results = {r.product_id: {'name': r.product_name, 'avg': r.avg_price} for r in curr_query.all()}

    # 上一周期均价
    prev_query = session.query(
        PriceRecord.product_id,
        func.avg(PriceRecord.price).label('avg_price')
    ).filter(
        PriceRecord.record_date >= prev_start.isoformat(),
        PriceRecord.record_date <= prev_end.isoformat()
    )
    if source and source != '__all__':
        prev_query = prev_query.filter(PriceRecord.source == source)
    if product_filter:
        prev_query = prev_query.filter(PriceRecord.product_id.in_(product_filter))
    prev_query = prev_query.group_by(PriceRecord.product_id)
    prev_results = {r.product_id: r.avg_price for r in prev_query.all()}

    # 最新价格
    latest_query = session.query(
        PriceRecord.product_id,
        func.max(PriceRecord.record_date).label('max_date')
    ).group_by(PriceRecord.product_id).subquery()
    latest_prices = session.query(
        PriceRecord.product_id,
        PriceRecord.price
    ).join(
        latest_query,
        (PriceRecord.product_id == latest_query.c.product_id) &
        (PriceRecord.record_date == latest_query.c.max_date)
    ).all()
    latest_price_map = {r.product_id: r.price for r in latest_prices}

    # 计算变化率
    items = []
    for product_id, curr_data in curr_results.items():
        prev_avg = prev_results.get(product_id)
        if prev_avg is None or prev_avg == 0:
            continue
        curr_avg = curr_data['avg']
        change_pct = ((curr_avg - prev_avg) / prev_avg) * 100
        items.append({
            "product_id": product_id,
            "product_name": curr_data['name'],
            "current_avg": round(curr_avg, 2),
            "previous_avg": round(prev_avg, 2),
            "change_percent": round(change_pct, 2),
            "trend": "rise" if change_pct >= 0 else "fall",
            "latest_price": latest_price_map.get(product_id, 0)
        })

    items.sort(key=lambda x: abs(x['change_percent']), reverse=True)
    return {
        "period_type": f"d{days}",
        "current_period": {"start": curr_start.isoformat(), "end": curr_end.isoformat()},
        "previous_period": {"start": prev_start.isoformat(), "end": prev_end.isoformat()},
        "items": items[:top_n]
    }