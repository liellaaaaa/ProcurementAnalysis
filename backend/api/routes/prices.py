from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import asyncio
import numpy
from backend.models.database import get_session, Product, PriceRecord, Category, ProductCategory
from backend.services.alert_service import check_and_trigger_alerts
from backend.services.operation_logger import OperationLogger

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
    record_date: str  # yyyy/mm/dd 格式

    @staticmethod
    def from_record(pr, product_name=None, product_code=None):
        """从 PriceRecord 创建响应对象"""
        record_date = pr.record_date
        if hasattr(record_date, 'strftime'):
            formatted_date = record_date.strftime('%Y/%m/%d')
        else:
            formatted_date = str(record_date)
        return PriceRecordResponse(
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
            record_date=formatted_date
        )

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
        response.append(PriceRecordResponse.from_record(pr, product_name, product_code))

    session.close()

    # 记录查询日志
    OperationLogger.log_price_query(
        product_ids=[product_id] if product_id else [],
        date_range={"start": start_date, "end": end_date},
        count=len(response)
    )
    return response

@router.get("/latest", response_model=dict)
async def get_latest_prices(
    source: Optional[str] = None,
    category_id: Optional[int] = None,
    subcategory_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """获取产品列表（按产品名称聚合，每个产品名称只显示一行）"""
    session = get_session()

    # 先查出所有符合条件的产品名称及其最新日期
    base_query = session.query(
        PriceRecord.product_id,
        Product.product_name,
        Product.product_code,
        PriceRecord.record_date,
        PriceRecord.price,
        PriceRecord.change_percent,
        PriceRecord.trend,
        PriceRecord.source
    ).join(Product)

    if source:
        base_query = base_query.filter(PriceRecord.source == source)

    if category_id:
        subcat_ids = [c.id for c in session.query(Category).filter(Category.parent_id == category_id).all()]
        pc_query = session.query(ProductCategory.product_id).filter(ProductCategory.category_id.in_(subcat_ids + [category_id]))
        base_query = base_query.filter(PriceRecord.product_id.in_(pc_query))

    if subcategory_id:
        pc_query = session.query(ProductCategory.product_id).filter(ProductCategory.category_id == subcategory_id)
        base_query = base_query.filter(PriceRecord.product_id.in_(pc_query))

    if start_date:
        base_query = base_query.filter(PriceRecord.record_date >= start_date)
    if end_date:
        base_query = base_query.filter(PriceRecord.record_date <= end_date)

    all_records = base_query.order_by(Product.product_name, PriceRecord.record_date.desc()).all()

    # 按产品名称聚合，每个名称只取最新日期的那条
    product_map = {}
    for r in all_records:
        name = r.product_name
        if name not in product_map:
            product_map[name] = {
                "product_id": r.product_id,
                "product_name": name,
                "product_code": r.product_code,
                "latest_date": r.record_date,
                "price": r.price,
                "min_price": r.price,
                "max_price": r.price,
                "change_percent": r.change_percent,
                "trend": r.trend,
                "source": r.source
            }
        else:
            # 更新价格区间
            if r.price < product_map[name]["min_price"]:
                product_map[name]["min_price"] = r.price
            if r.price > product_map[name]["max_price"]:
                product_map[name]["max_price"] = r.price

    # 转为列表并排序
    products = list(product_map.values())
    products.sort(key=lambda x: x["latest_date"] or "", reverse=True)

    # 格式化日期
    for p in products:
        if p["latest_date"]:
            p["latest_date"] = p["latest_date"].strftime('%Y/%m/%d')
        p["price"] = p["price"] or 0
        p["min_price"] = p["min_price"] or 0
        p["max_price"] = p["max_price"] or 0

    total = len(products)

    session.close()
    return {
        "total": total,
        "data": products
    }

    session.close()
    return {
        "total": total,
        "data": products
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
        response.append(PriceRecordResponse.from_record(pr, product_name, product_code))

    session.close()

    # 记录查询日志
    OperationLogger.log_price_query(
        product_ids=[product_id],
        date_range={"start": start_date, "days": days},
        count=len(response)
    )
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

    # 今日更新记录数
    today_count = session.query(func.count(PriceRecord.id)).filter(PriceRecord.record_date == date.today()).scalar()

    session.close()

    return {
        "total_products": total_products or 0,
        "total_records": total_records or 0,
        "avg_price": avg_price,
        "today_records": today_count or 0
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

    return PriceRecordResponse.from_record(new_record, product.product_name, product.product_code)

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

    return PriceRecordResponse.from_record(db_record, product.product_name if product else None, product.product_code if product else None)

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


# ============== Dashboard API ==============

@router.get("/dashboard/distribution")
async def get_dashboard_distribution(
    days: int = Query(30, ge=7, le=365),
    category_id: Optional[int] = None,
    subcategory_id: Optional[int] = None
):
    """获取各产品/分类价格占比（饼图数据）"""
    session = get_session()
    start_date = (date.today() - timedelta(days=days)).isoformat()

    query = session.query(
        Product.product_name,
        func.avg(PriceRecord.price).label('avg_price')
    ).join(PriceRecord).filter(
        PriceRecord.record_date >= start_date
    )

    # Filter by category
    if category_id:
        subcat_ids = [c.id for c in session.query(Category).filter(Category.parent_id == category_id).all()]
        pc_query = session.query(ProductCategory.product_id).filter(ProductCategory.category_id.in_(subcat_ids + [category_id]))
        query = query.filter(PriceRecord.product_id.in_(pc_query))

    if subcategory_id:
        pc_query = session.query(ProductCategory.product_id).filter(ProductCategory.category_id == subcategory_id)
        query = query.filter(PriceRecord.product_id.in_(pc_query))

    results = query.group_by(Product.id).order_by(func.avg(PriceRecord.price).desc()).limit(10).all()

    session.close()

    labels = [r.product_name[:15] for r in results]
    sizes = [round(r.avg_price, 2) for r in results]

    return {"labels": labels, "sizes": sizes}


@router.get("/dashboard/ranking")
async def get_dashboard_ranking(
    limit: int = Query(10, ge=5, le=30),
    days: int = Query(7, ge=1, le=90),
    category_id: Optional[int] = None,
    subcategory_id: Optional[int] = None
):
    """获取涨跌排行（柱状图数据）"""
    session = get_session()
    start_date = (date.today() - timedelta(days=days)).isoformat()

    # 获取每个产品的最新价格和变化率
    subquery = session.query(
        PriceRecord.product_id,
        func.max(PriceRecord.record_date).label('max_date')
    ).group_by(PriceRecord.product_id).subquery()

    query = session.query(
        PriceRecord.product_id,
        PriceRecord.price,
        PriceRecord.change_percent,
        PriceRecord.record_date
    ).join(
        subquery,
        (PriceRecord.product_id == subquery.c.product_id) &
        (PriceRecord.record_date == subquery.c.max_date)
    )

    # Filter by category
    if category_id:
        subcat_ids = [c.id for c in session.query(Category).filter(Category.parent_id == category_id).all()]
        pc_query = session.query(ProductCategory.product_id).filter(ProductCategory.category_id.in_(subcat_ids + [category_id]))
        query = query.filter(PriceRecord.product_id.in_(pc_query))

    if subcategory_id:
        pc_query = session.query(ProductCategory.product_id).filter(ProductCategory.category_id == subcategory_id)
        query = query.filter(PriceRecord.product_id.in_(pc_query))

    latest_prices = query.all()

    product_ids = [lp.product_id for lp in latest_prices]
    products = {p.id: p.product_name for p in session.query(Product).filter(Product.id.in_(product_ids)).all()}

    ranking = []
    for lp in latest_prices:
        ranking.append({
            "product_id": lp.product_id,
            "product_name": products.get(lp.product_id, "未知"),
            "latest_price": lp.price,
            "change_percent": lp.change_percent or 0
        })

    # 按涨跌排序
    ranking.sort(key=lambda x: x["change_percent"], reverse=True)
    rising = ranking[:limit]
    falling = ranking[-limit:][::-1]

    session.close()
    return {"rising": rising, "falling": falling}


@router.get("/dashboard/history/compare")
async def get_dashboard_history_compare(
    product_ids: Optional[str] = Query(None, description="逗号分隔的产品ID，留空则返回分类下所有产品"),
    days: int = Query(30, ge=7, le=365),
    category_id: Optional[int] = Query(None),
    subcategory_id: Optional[int] = Query(None)
):
    """获取多产品历史价格对比（折线图数据）"""
    session = get_session()
    start_date = (date.today() - timedelta(days=days)).isoformat()

    results = []
    if product_ids and product_ids.strip():
        # 指定了产品ID
        id_list = [int(pid.strip()) for pid in product_ids.split(",") if pid.strip().isdigit()]
        results = session.query(PriceRecord, Product.product_name).join(Product).filter(
            PriceRecord.product_id.in_(id_list),
            PriceRecord.record_date >= start_date
        ).order_by(PriceRecord.record_date.asc()).all()
    else:
        # 未指定产品ID，按分类获取
        query = session.query(Product).distinct()
        if subcategory_id:
            pc_query = session.query(ProductCategory.product_id).filter(ProductCategory.category_id == subcategory_id)
            query = query.filter(Product.id.in_(pc_query))
        elif category_id:
            subcat_ids = [c.id for c in session.query(Category).filter(Category.parent_id == category_id).all()]
            pc_query = session.query(ProductCategory.product_id).filter(ProductCategory.category_id.in_(subcat_ids + [category_id]))
            query = query.filter(Product.id.in_(pc_query))

        products = query.limit(10).all()
        if products:
            product_ids_list = [p.id for p in products]
            results = session.query(PriceRecord, Product.product_name).join(Product).filter(
                PriceRecord.product_id.in_(product_ids_list),
                PriceRecord.record_date >= start_date
            ).order_by(PriceRecord.record_date.asc()).all()

    # 按产品分组
    product_data = {}
    for pr, pname in results:
        if pr.product_id not in product_data:
            product_data[pr.product_id] = {"name": pname, "data": []}
        product_data[pr.product_id]["data"].append(pr.price)

    # 收集所有日期
    all_dates = sorted(set(pr.record_date.isoformat() for pr, _ in results))

    session.close()
    return {"dates": all_dates, "series": list(product_data.values())}


@router.get("/dashboard/heatmap")
async def get_dashboard_heatmap(
    days: int = Query(30, ge=7, le=90),
    region: Optional[str] = None,
    category_id: Optional[int] = None,
    subcategory_id: Optional[int] = None
):
    """获取产品-地区价格矩阵热力图"""
    session = get_session()
    start_date = (date.today() - timedelta(days=days)).isoformat()

    # 获取每个产品-地区组合的最新记录
    subquery = session.query(
        PriceRecord.product_id,
        PriceRecord.region,
        func.max(PriceRecord.record_date).label('max_date')
    ).group_by(
        PriceRecord.product_id,
        PriceRecord.region
    ).subquery()

    query = session.query(
        PriceRecord,
        Product.product_name
    ).join(
        Product
    ).join(
        subquery,
        (PriceRecord.product_id == subquery.c.product_id) &
        (PriceRecord.region == subquery.c.region) &
        (PriceRecord.record_date == subquery.c.max_date)
    ).filter(
        PriceRecord.record_date >= start_date
    )

    # Filter by category
    if category_id:
        subcat_ids = [c.id for c in session.query(Category).filter(Category.parent_id == category_id).all()]
        pc_query = session.query(ProductCategory.product_id).filter(ProductCategory.category_id.in_(subcat_ids + [category_id]))
        query = query.filter(PriceRecord.product_id.in_(pc_query))

    if subcategory_id:
        pc_query = session.query(ProductCategory.product_id).filter(ProductCategory.category_id == subcategory_id)
        query = query.filter(PriceRecord.product_id.in_(pc_query))

    results = query.all()

    if not results:
        session.close()
        return {"products": [], "regions": [], "data": []}

    # 收集所有产品和地区
    product_map = {}  # product_id -> product_name
    region_set = set()
    matrix = {}  # (product_id, region) -> price

    for pr, pname in results:
        product_map[pr.product_id] = pname
        if pr.region:
            region_set.add(pr.region)
        matrix[(pr.product_id, pr.region)] = pr.price

    # 排序产品（按名称）和地区
    sorted_products = sorted(product_map.items(), key=lambda x: x[1])
    sorted_regions = sorted(region_set)

    # 构建热力图数据
    heatmap_data = []
    for pid, pname in sorted_products:
        for ridx, region in enumerate(sorted_regions):
            price = matrix.get((pid, region))
            if price is not None:
                heatmap_data.append({
                    "product_id": pid,
                    "product_name": pname,
                    "region": region,
                    "price": price
                })

    session.close()
    return {
        "products": [{"id": p[0], "name": p[1]} for p in sorted_products],
        "regions": sorted_regions,
        "data": heatmap_data
    }


@router.get("/dashboard/calendar")
async def get_dashboard_calendar(
    days: int = Query(30, ge=7, le=90),
    category_id: Optional[int] = None,
    subcategory_id: Optional[int] = None
):
    """获取价格日历热力图数据（过去N天每日平均价格）"""
    session = get_session()
    start_date = (date.today() - timedelta(days=days)).isoformat()

    # 查询每日平均价格
    query = session.query(
        PriceRecord.record_date,
        func.avg(PriceRecord.price).label('avg_price')
    ).filter(
        PriceRecord.record_date >= start_date
    ).group_by(
        PriceRecord.record_date
    ).order_by(
        PriceRecord.record_date.asc()
    )

    # Filter by category
    if category_id:
        subcat_ids = [c.id for c in session.query(Category).filter(Category.parent_id == category_id).all()]
        pc_query = session.query(ProductCategory.product_id).filter(ProductCategory.category_id.in_(subcat_ids + [category_id]))
        query = query.filter(PriceRecord.product_id.in_(pc_query))

    if subcategory_id:
        pc_query = session.query(ProductCategory.product_id).filter(ProductCategory.category_id == subcategory_id)
        query = query.filter(PriceRecord.product_id.in_(pc_query))

    results = query.all()
    session.close()

    return [{"date": r.record_date.isoformat(), "price": round(r.avg_price, 2)} for r in results]


@router.get("/dashboard/volatility")
async def get_dashboard_volatility(days: int = Query(7, ge=1, le=30)):
    """获取价格波动幅度统计（仪表盘数据）"""
    session = get_session()
    start_date = (date.today() - timedelta(days=days)).isoformat()

    stats = session.query(
        func.avg(func.abs(PriceRecord.change_percent)).label('avg_volatility'),
        func.max(func.abs(PriceRecord.change_percent)).label('max_volatility'),
        func.count(func.distinct(PriceRecord.product_id)).label('active_products')
    ).filter(
        PriceRecord.record_date >= start_date
    ).first()

    # 获取今日最新价格产品数
    today_count = session.query(func.count(func.distinct(PriceRecord.product_id))).filter(
        PriceRecord.record_date >= date.today().isoformat()
    ).scalar() or 0

    session.close()

    return {
        "avg_volatility": round(stats.avg_volatility or 0, 2),
        "max_volatility": round(stats.max_volatility or 0, 2),
        "active_products": stats.active_products or 0,
        "today_updated": today_count
    }