from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import asyncio
import statistics
import numpy
from backend.models.database import Product, PriceRecord, Category, ProductCategory, BenchmarkPrice, DetailedQuote
from backend.services.alert_service import check_and_trigger_alerts
from backend.services.operation_logger import OperationLogger
from backend.services.price_metrics import calculate_yoy_mom, calculate_day_change
from backend.api.deps import get_db
from backend.utils.date_utils import format_date

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
    unit: Optional[str] = None
    price_type: Optional[str] = None
    record_date: str  # yyyy/mm/dd 格式
    extra_data: Optional[dict] = None  # 行业差异化字段

    @staticmethod
    def from_record(pr, product_name=None, product_code=None, extra_data=None):
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
            unit=pr.unit,
            price_type=pr.price_type,
            record_date=formatted_date,
            extra_data=extra_data or pr.extra_data
        )

    class Config:
        from_attributes = True

@router.get("", response_model=List[PriceRecordResponse])
async def get_prices(
    product_id: Optional[int] = None,
    source: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    industry: Optional[str] = None,
    limit: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取价格数据列表（从 benchmark_prices + price_records）"""
    results = []

    # 从 benchmark_prices 读取
    bp_query = db.query(BenchmarkPrice, Product.product_name, Product.product_code).join(Product, BenchmarkPrice.product_id == Product.id)
    if start_date:
        bp_query = bp_query.filter(BenchmarkPrice.record_date >= start_date)
    if product_id:
        bp_query = bp_query.filter(BenchmarkPrice.product_id == product_id)
    if source and source != '__all__':
        bp_query = bp_query.filter(BenchmarkPrice.source == source)
    if end_date:
        bp_query = bp_query.filter(BenchmarkPrice.record_date <= end_date)
    if industry:
        bp_query = bp_query.filter(Product.industry == industry)

    bp_query = bp_query.order_by(BenchmarkPrice.record_date.desc())
    if limit:
        bp_query = bp_query.limit(limit)
    bp_results = bp_query.all()
    for bp, product_name, product_code in bp_results:
        results.append({
            "id": bp.id,
            "product_id": bp.product_id,
            "product_name": product_name,
            "product_code": product_code,
            "price": bp.price,
            "trend": None,
            "change_percent": None,
            "source": bp.source or source or "shengyishe",
            "region": "",
            "supplier": "",
            "brand": bp.brand or "",
            "specification": bp.spec or "",
            "unit": bp.unit or "元/吨",
            "price_type": "基准价",
            "record_date": bp.record_date.strftime('%Y/%m/%d') if bp.record_date else "",
            "extra_data": {}
        })

    # 从 price_records 读取（如果 source='__all__' 或未指定，也读 price_records）
    if not source or source == '__all__':
        pr_query = db.query(PriceRecord, Product.product_name, Product.product_code).join(Product)
        if product_id:
            pr_query = pr_query.filter(PriceRecord.product_id == product_id)
        if start_date:
            pr_query = pr_query.filter(PriceRecord.record_date >= start_date)
        if end_date:
            pr_query = pr_query.filter(PriceRecord.record_date <= end_date)
        if industry:
            pr_query = pr_query.filter(Product.industry == industry)

        pr_query = pr_query.order_by(PriceRecord.record_date.desc())
        if limit:
            pr_query = pr_query.limit(limit)
        pr_results = pr_query.all()
        for pr, product_name, product_code in pr_results:
            results.append(PriceRecordResponse.from_record(pr, product_name, product_code, pr.extra_data))

    # 记录查询日志
    OperationLogger.log_price_query(
        product_ids=[product_id] if product_id else [],
        date_range={"start": start_date, "end": end_date},
        count=len(results)
    )
    return results

@router.get("/latest", response_model=dict)
async def get_latest_prices(
    source: Optional[str] = None,
    industry: Optional[str] = None,
    category_id: Optional[int] = None,
    subcategory_id: Optional[List[int]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取产品列表（按产品名称聚合，每个产品名称只显示一行）
    优先从 benchmark_prices 读取，fallback 到 price_records
    """

    # 先从 benchmark_prices 获取最新基准价
    bp_query = db.query(
        BenchmarkPrice.product_id,
        Product.product_name,
        Product.product_code,
        Product.industry,
        BenchmarkPrice.record_date,
        BenchmarkPrice.price,
        BenchmarkPrice.unit,
        BenchmarkPrice.price_original,
        BenchmarkPrice.spec,
        BenchmarkPrice.brand,
        BenchmarkPrice.market
    ).join(Product, BenchmarkPrice.product_id == Product.id)

    if source and source != '__all__':
        bp_query = bp_query.filter(BenchmarkPrice.source == source)

    if industry:
        bp_query = bp_query.filter(Product.industry == industry)

    if start_date:
        bp_query = bp_query.filter(BenchmarkPrice.record_date >= start_date)
    if end_date:
        bp_query = bp_query.filter(BenchmarkPrice.record_date <= end_date)

    bp_results = bp_query.all()

    # 按 product_id 聚合，只取最新日期
    product_map = {}
    for bp_id, product_name, product_code, industry, record_date, price, unit, price_original, spec, brand, market in bp_results:
        pid = bp_id
        if pid not in product_map:
            product_map[pid] = {
                "product_id": pid,
                "product_name": product_name,
                "product_code": product_code,
                "industry": industry,
                "latest_date": record_date,
                "price": price,
                "min_price": price,
                "max_price": price,
                "change_percent": None,
                "trend": None,
                "source": source or "shengyishe",
                "specification": spec or "",
                "brand": brand or "",
                "region": market or "",
                "supplier": "",
                "price_type": "基准价",
                "unit": unit or "元/吨",
                "extra_data": {"详细报价": []}
            }
        else:
            if price < product_map[pid]["min_price"]:
                product_map[pid]["min_price"] = price
            if price > product_map[pid]["max_price"]:
                product_map[pid]["max_price"] = price
            if record_date > product_map[pid]["latest_date"]:
                product_map[pid]["latest_date"] = record_date
                product_map[pid]["price"] = price

    # 批量查询 detailed_quotes（修复 N+1：一次查询替代循环）
    # 限制：只查询最近30天的报价，每个产品最多返回5条，避免数据量过大导致超时
    MAX_QUOTES_PER_PRODUCT = 5
    all_pids = list(product_map.keys())
    if all_pids:
        # 只查询最近30天的报价
        recent_date = (date.today() - timedelta(days=30)).isoformat()
        all_dqs = db.query(DetailedQuote).filter(
            DetailedQuote.product_id.in_(all_pids),
            DetailedQuote.publish_date >= recent_date
        ).order_by(DetailedQuote.product_id, DetailedQuote.publish_date.desc()).all()
        # 按 product_id 分组，每个产品只取最新的 MAX_QUOTES_PER_PRODUCT 条
        dq_by_pid = {}
        for dq in all_dqs:
            if dq.product_id not in dq_by_pid:
                dq_by_pid[dq.product_id] = []
            if len(dq_by_pid[dq.product_id]) < MAX_QUOTES_PER_PRODUCT:
                dq_by_pid[dq.product_id].append({
                    "supplier": dq.supplier,
                    "brand": dq.brand,
                    "spec_raw": dq.spec,
                    "region": dq.region,
                    "price": dq.price,
                    "price_str": f"{dq.price}",
                    "price_type": dq.price_type,
                    "unit": dq.unit or "元/吨",
                    "publish_date": dq.publish_date.strftime('%Y/%m/%d') if dq.publish_date else ''
                })
        for pid, dqs in dq_by_pid.items():
            product_map[pid]["extra_data"]["详细报价"] = dqs

        # 批量查询昨日基准价用于计算涨跌（修复 N+1）
        yesterday_map = {}  # {product_id: yesterday_price}
        for p in product_map.values():
            if p["latest_date"]:
                prev_date = p["latest_date"] - timedelta(days=1)
                yesterday_map[(p["product_id"], prev_date)] = p["product_id"]
        if yesterday_map:
            prev_date_list = list(set(d[1] for d in yesterday_map.keys()))
            yesterday_bps = db.query(BenchmarkPrice.product_id, BenchmarkPrice.record_date, BenchmarkPrice.price).filter(
                BenchmarkPrice.product_id.in_(all_pids),
                BenchmarkPrice.record_date.in_(prev_date_list)
            ).all()
            # 构建 {(pid, date): price}
            yb_lookup = {(bp.product_id, bp.record_date): bp.price for bp in yesterday_bps}
            for pid, p in product_map.items():
                if p["latest_date"]:
                    prev_date = p["latest_date"] - timedelta(days=1)
                    prev_price = yb_lookup.get((pid, prev_date))
                    if prev_price and prev_price > 0:
                        change_pct = round(((p["price"] - prev_price) / prev_price) * 100, 2)
                        p["change_percent"] = change_pct
                        p["trend"] = "涨" if change_pct > 0 else "跌" if change_pct < 0 else "平"
                    elif p["price"] > 0:
                        p["change_percent"] = 0.0
                        p["trend"] = "平"

    # 如果 benchmark_prices 没有数据，fallback 到 price_records
    if not product_map:
        pr_query = db.query(
            PriceRecord.product_id,
            Product.product_name,
            Product.product_code,
            Product.industry,
            PriceRecord.record_date,
            PriceRecord.price,
            PriceRecord.change_percent,
            PriceRecord.trend,
            PriceRecord.source,
            PriceRecord.specification,
            PriceRecord.brand,
            PriceRecord.region,
            PriceRecord.supplier,
            PriceRecord.price_type,
            PriceRecord.unit,
            PriceRecord.extra_data
        ).join(Product)

        if source and source != '__all__':
            pr_query = pr_query.filter(PriceRecord.source == source)
        if industry:
            pr_query = pr_query.filter(Product.industry == industry)
        if start_date:
            pr_query = pr_query.filter(PriceRecord.record_date >= start_date)
        if end_date:
            pr_query = pr_query.filter(PriceRecord.record_date <= end_date)

        pr_results = pr_query.order_by(Product.product_name, PriceRecord.record_date.desc()).all()

        for pr_id, product_name, product_code, industry, record_date, price, change_percent, trend, pr_source, specification, brand, region, supplier, price_type, unit, extra_data in pr_results:
            pid = pr_id
            if pid not in product_map:
                product_map[pid] = {
                    "product_id": pid,
                    "product_name": product_name,
                    "product_code": product_code,
                    "industry": industry,
                    "latest_date": record_date,
                    "price": price,
                    "min_price": price,
                    "max_price": price,
                    "change_percent": change_percent,
                    "trend": trend,
                    "source": pr_source,
                    "specification": specification or "",
                    "brand": brand or "",
                    "region": region or "",
                    "supplier": supplier or "",
                    "price_type": price_type or "",
                    "unit": unit or "元/吨",
                    "extra_data": extra_data or {}
                }
            else:
                if price < product_map[pid]["min_price"]:
                    product_map[pid]["min_price"] = price
                if price > product_map[pid]["max_price"]:
                    product_map[pid]["max_price"] = price

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
        p["specification"] = p["specification"] or ""
        p["brand"] = p["brand"] or ""
        p["region"] = p["region"] or ""
        p["supplier"] = p["supplier"] or ""
        p["price_type"] = p["price_type"] or ""
        p["unit"] = p["unit"] or "元/吨"

    total = len(products)
    return {
        "total": total,
        "data": products
    }


@router.get("/history/{product_id}", response_model=List[PriceRecordResponse])
async def get_price_history(
    product_id: int,
    days: int = Query(30, ge=1, le=365),
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取产品历史价格趋势"""
    start_date = (date.today() - timedelta(days=days)).isoformat()

    query = db.query(PriceRecord, Product.product_name, Product.product_code).join(
        Product
    ).filter(
        PriceRecord.product_id == product_id,
        PriceRecord.record_date >= start_date
    )

    if source and source != '__all__':
        query = query.filter(PriceRecord.source == source)

    results = query.order_by(PriceRecord.record_date.desc()).all()

    response = []
    for pr, product_name, product_code in results:
        response.append(PriceRecordResponse.from_record(pr, product_name, product_code, pr.extra_data))

    # 记录查询日志
    OperationLogger.log_price_query(
        product_ids=[product_id],
        date_range={"start": start_date, "days": days},
        count=len(response)
    )
    return response


@router.get("/benchmark/history/{product_id}", response_model=List[dict])
async def get_benchmark_history(
    product_id: int,
    days: int = Query(30, ge=1, le=365),
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取产品基准价历史趋势（从 benchmark_prices 读取）"""
    start_date = (date.today() - timedelta(days=days)).isoformat()

    query = db.query(BenchmarkPrice, Product.product_name).join(
        Product, BenchmarkPrice.product_id == Product.id
    ).filter(
        BenchmarkPrice.product_id == product_id,
        BenchmarkPrice.record_date >= start_date
    )

    if source and source != '__all__':
        query = query.filter(BenchmarkPrice.source == source)

    results = query.order_by(BenchmarkPrice.record_date.asc()).all()

    return [
        {
            "product_id": bp.product_id,
            "product_name": product_name,
            "price": bp.price,
            "unit": bp.unit or "元/吨",
            "record_date": bp.record_date.strftime('%Y/%m/%d') if bp.record_date else "",
            "brand": bp.brand or "",
            "spec": bp.spec or "",
            "market": bp.market or ""
        }
        for bp, product_name in results
    ]


@router.get("/benchmark/history", response_model=dict)
async def get_benchmark_history_multi(
    product_ids: Optional[str] = Query(None, description="逗号分隔的产品ID"),
    days: int = Query(30, ge=1, le=365),
    category_id: Optional[int] = None,
    subcategory_id: Optional[List[int]] = Query(None),
    source: Optional[str] = None,
    industry: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取多个产品基准价历史对比（折线图用）"""
    start_date = (date.today() - timedelta(days=days)).isoformat()

    results = []
    id_list = []
    if product_ids and product_ids.strip():
        id_list = [int(pid.strip()) for pid in product_ids.split(",") if pid.strip().isdigit()]

    if id_list:
        query = db.query(BenchmarkPrice, Product.product_name).join(
            Product, BenchmarkPrice.product_id == Product.id
        ).filter(
            BenchmarkPrice.product_id.in_(id_list),
            BenchmarkPrice.record_date >= start_date
        )
        if source and source != '__all__':
            query = query.filter(BenchmarkPrice.source == source)
        results = query.order_by(BenchmarkPrice.record_date.asc()).all()
    else:
        # 按分类获取产品
        query = db.query(Product).filter(Product.is_active == True)
        if industry:
            query = query.filter(Product.industry == industry)

        # 如果 ProductCategory 为空，则忽略 subcategory_id 过滤（返回该行业所有产品）
        pc_count = db.query(ProductCategory).count()
        if subcategory_id and pc_count > 0:
            pc_query = db.query(ProductCategory.product_id).filter(
                ProductCategory.category_id.in_(subcategory_id)
            )
            query = query.filter(Product.id.in_(pc_query))
        elif subcategory_id and pc_count == 0:
            pass  # ProductCategory 为空，忽略 subcategory_id
        elif category_id:
            subcat_ids = [c.id for c in db.query(Category).filter(Category.parent_id == category_id).all()]
            pc_query = db.query(ProductCategory.product_id).filter(
                ProductCategory.category_id.in_(subcat_ids + [category_id])
            )
            query = query.filter(Product.id.in_(pc_query))

        products = query.limit(10).all()
        if products:
            pids = [p.id for p in products]
            bp_query = db.query(BenchmarkPrice, Product.product_name).join(
                Product, BenchmarkPrice.product_id == Product.id
            ).filter(
                BenchmarkPrice.product_id.in_(pids),
                BenchmarkPrice.record_date >= start_date
            )
            if source and source != '__all__':
                bp_query = bp_query.filter(BenchmarkPrice.source == source)
            results = bp_query.order_by(BenchmarkPrice.record_date.asc()).all()

    # 按产品分组
    product_data = {}
    for bp, pname in results:
        if bp.product_id not in product_data:
            product_data[bp.product_id] = {"name": pname, "data": []}
        product_data[bp.product_id]["data"].append(bp.price)

    all_dates = sorted(set(bp.record_date.strftime('%Y/%m/%d') for bp, _ in results))

    return {"dates": all_dates, "series": list(product_data.values())}


@router.get("/stats/summary")
async def get_stats_summary(db: Session = Depends(get_db)):
    """获取统计摘要"""
    total_products = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar()

    # 从 benchmark_prices 获取记录数（优先）和 price_records（fallback）
    benchmark_count = db.query(func.count(BenchmarkPrice.id)).scalar()
    price_record_count = db.query(func.count(PriceRecord.id)).scalar()
    total_records = benchmark_count + price_record_count

    # 平均价格（最新价格）从 benchmark_prices
    subquery = db.query(
        BenchmarkPrice.product_id,
        func.max(BenchmarkPrice.record_date).label('max_date')
    ).group_by(BenchmarkPrice.product_id).subquery()

    avg_price_result = db.query(func.avg(BenchmarkPrice.price)).join(
        subquery,
        (BenchmarkPrice.product_id == subquery.c.product_id) &
        (BenchmarkPrice.record_date == subquery.c.max_date)
    ).scalar()

    avg_price = round(avg_price_result, 2) if avg_price_result else 0

    # 今日更新记录数（benchmark + price_records）
    today_benchmark = db.query(func.count(BenchmarkPrice.id)).filter(BenchmarkPrice.record_date == date.today()).scalar()
    today_pr = db.query(func.count(PriceRecord.id)).filter(PriceRecord.record_date == date.today()).scalar()
    today_count = today_benchmark + today_pr

    return {
        "total_products": total_products or 0,
        "total_records": total_records or 0,
        "avg_price": avg_price,
        "today_records": today_count or 0
    }

@router.post("", response_model=PriceRecordResponse)
async def create_price_record(record: PriceRecordCreate, db: Session = Depends(get_db)):
    """手动添加价格记录"""
    # 验证产品存在
    product = db.query(Product).filter(Product.id == record.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    # 检查重复记录
    existing = db.query(PriceRecord).filter(
        PriceRecord.product_id == record.product_id,
        PriceRecord.record_date == datetime.strptime(record.record_date, "%Y-%m-%d").date(),
        PriceRecord.source == record.source
    ).first()
    if existing:
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
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    # 检查预警触发
    check_and_trigger_alerts(db, new_record.product_id, new_record.price)

    return PriceRecordResponse.from_record(new_record, product.product_name, product.product_code)

@router.put("/{record_id}", response_model=PriceRecordResponse)
async def update_price_record(record_id: int, record: PriceRecordCreate, db: Session = Depends(get_db)):
    """更新价格记录"""
    db_record = db.query(PriceRecord).filter(PriceRecord.id == record_id).first()

    if not db_record:
        raise HTTPException(status_code=404, detail="价格记录不存在")

    update_data = record.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == 'record_date':
            setattr(db_record, field, datetime.strptime(value, "%Y-%m-%d").date())
        else:
            setattr(db_record, field, value)

    db.commit()
    db.refresh(db_record)

    product = db.query(Product).filter(Product.id == db_record.product_id).first()

    return PriceRecordResponse.from_record(db_record, product.product_name if product else None, product.product_code if product else None)

@router.delete("/{record_id}")
async def delete_price_record(record_id: int, db: Session = Depends(get_db)):
    """删除价格记录"""
    record = db.query(PriceRecord).filter(PriceRecord.id == record_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="价格记录不存在")

    db.delete(record)
    db.commit()

    return {"message": "价格记录已删除"}


# ============== Dashboard API ==============

@router.get("/dashboard/distribution")
async def get_dashboard_distribution(
    days: int = Query(30, ge=1, le=365),
    industry: Optional[str] = None,
    category_id: Optional[int] = None,
    subcategory_id: Optional[List[int]] = Query(None),
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取各产品/分类价格占比（饼图数据）"""
    start_date = (date.today() - timedelta(days=days)).isoformat()

    # 优先从 benchmark_prices 读取
    query = db.query(
        Product.product_name,
        func.avg(BenchmarkPrice.price).label('avg_price')
    ).join(Product, BenchmarkPrice.product_id == Product.id).filter(
        BenchmarkPrice.record_date >= start_date
    )

    if source and source != '__all__':
        query = query.filter(BenchmarkPrice.source == source)

    if industry:
        query = query.filter(Product.industry == industry)

    results = query.group_by(Product.id, Product.product_name).order_by(func.avg(BenchmarkPrice.price).desc()).limit(10).all()

    # 如果 benchmark_prices 没有数据，fallback 到 price_records
    if not results:
        query = db.query(
            Product.product_name,
            func.avg(PriceRecord.price).label('avg_price')
        ).join(PriceRecord).filter(
            PriceRecord.record_date >= start_date
        )
        if source and source != '__all__':
            query = query.filter(PriceRecord.source == source)
        if industry:
            query = query.filter(Product.industry == industry)
        results = query.group_by(Product.id, Product.product_name).order_by(func.avg(PriceRecord.price).desc()).limit(10).all()

    labels = [r.product_name[:15] for r in results]
    sizes = [round(r.avg_price, 2) for r in results]

    return {"labels": labels, "sizes": sizes}


@router.get("/dashboard/ranking")
async def get_dashboard_ranking(
    limit: int = Query(10, ge=5, le=30),
    days: int = Query(7, ge=1, le=90),
    industry: Optional[str] = None,
    category_id: Optional[int] = None,
    subcategory_id: Optional[List[int]] = Query(None),
    source: Optional[str] = None,
    period_type: Optional[str] = Query(None, regex="^(yoy|qoq)$", description="yoy=同比, qoq=环比"),
    db: Session = Depends(get_db)
):
    """获取涨跌排行（柱状图数据）"""
    # 如果指定了 period_type，使用同比/环比计算
    if period_type:
        result = calculate_yoy_mom(
            session=db,
            period_type=period_type,
            source=source,
            industry=industry,
            category_id=category_id,
            subcategory_id=subcategory_id,
            top_n=limit
        )
        items = result["items"]
        rising = [item for item in items if item["trend"] == "rise"]
        falling = [item for item in items if item["trend"] == "fall"]
        # 转换字段名以兼容前端
        rising = [{
            "product_id": i["product_id"],
            "product_name": i["product_name"],
            "latest_price": i.get("latest_price", 0),
            "change_percent": i["change_percent"],
            "avg_price": i["current_avg"]
        } for i in rising]
        falling = [{
            "product_id": i["product_id"],
            "product_name": i["product_name"],
            "latest_price": i.get("latest_price", 0),
            "change_percent": i["change_percent"],
            "avg_price": i["current_avg"]
        } for i in falling]
        return {"rising": rising, "falling": falling}

    # 从 BenchmarkPrice 计算日变化涨跌幅
    today_date = date.today()
    start_date = (today_date - timedelta(days=days)).isoformat()

    # 获取每个产品的最新基准价
    latest_subquery = db.query(
        BenchmarkPrice.product_id,
        func.max(BenchmarkPrice.record_date).label('max_date')
    ).group_by(BenchmarkPrice.product_id).subquery()

    latest_prices_query = db.query(
        BenchmarkPrice.product_id,
        BenchmarkPrice.price,
        BenchmarkPrice.record_date
    ).filter(
        BenchmarkPrice.product_id == latest_subquery.c.product_id,
        BenchmarkPrice.record_date == latest_subquery.c.max_date
    )

    if source and source != '__all__':
        latest_prices_query = latest_prices_query.filter(BenchmarkPrice.source == source)

    if industry:
        product_ids_query = db.query(Product.id).filter(Product.industry == industry)
        latest_prices_query = latest_prices_query.filter(BenchmarkPrice.product_id.in_(product_ids_query))

    if category_id:
        subcat_ids = [c.id for c in db.query(Category).filter(Category.parent_id == category_id).all()]
        pc_query = db.query(ProductCategory.product_id).filter(ProductCategory.category_id.in_(subcat_ids + [category_id]))
        latest_prices_query = latest_prices_query.filter(BenchmarkPrice.product_id.in_(pc_query))

    if subcategory_id:
        matched_products = db.query(Product.id).join(
            ProductCategory, Product.id == ProductCategory.product_id
        ).filter(ProductCategory.category_id.in_(subcategory_id)).distinct().all()
        pc_ids = [p[0] for p in matched_products]
        if pc_ids:
            latest_prices_query = latest_prices_query.filter(BenchmarkPrice.product_id.in_(pc_ids))

    latest_prices = latest_prices_query.all()

    product_ids = [lp.product_id for lp in latest_prices]
    products = {p.id: p.product_name for p in db.query(Product).filter(Product.id.in_(product_ids)).all()}

    # 获取最新基准价对应日期，以及对比日期（最新日期 - days）
    latest_dates = {lp.product_id: lp.record_date for lp in latest_prices}
    actual_latest_date = max(latest_dates.values()) if latest_dates else today_date
    compare_date = actual_latest_date - timedelta(days=days)

    compare_prices_query = db.query(
        BenchmarkPrice.product_id,
        BenchmarkPrice.price
    ).filter(BenchmarkPrice.record_date == compare_date)

    compare_prices = {bp.product_id: bp.price for bp in compare_prices_query.all()}

    ranking = []
    for lp in latest_prices:
        # 计算历史平均价格
        hist_query = db.query(func.avg(BenchmarkPrice.price)).filter(
            BenchmarkPrice.product_id == lp.product_id,
            BenchmarkPrice.record_date >= start_date
        )
        if source and source != '__all__':
            hist_query = hist_query.filter(BenchmarkPrice.source == source)
        hist = hist_query.scalar() or 0

        # 计算涨跌幅：对比日期价格 vs 最新价格
        base_price = compare_prices.get(lp.product_id)
        if base_price and base_price != 0:
            change_percent = round((lp.price - base_price) / base_price * 100, 2)
        else:
            # 没有对比日期数据时跳过该产品，不设置虚假的0%涨跌幅
            continue

        ranking.append({
            "product_id": lp.product_id,
            "product_name": products.get(lp.product_id, "未知"),
            "latest_price": lp.price,
            "change_percent": change_percent,
            "avg_price": round(hist, 2)
        })

    # 按涨跌排序：返回所有产品，0% 产品排在 rising 末尾/ falling 开头
    sorted_ranking = sorted(ranking, key=lambda x: x["change_percent"], reverse=True)
    rising = sorted_ranking[:limit]
    falling = sorted_ranking[-limit:][::-1] if len(sorted_ranking) > limit else sorted_ranking[::-1]

    return {"rising": rising, "falling": falling}


@router.get("/dashboard/history/compare")
async def get_dashboard_history_compare(
    product_ids: Optional[str] = Query(None, description="逗号分隔的产品ID，留空则返回分类下所有产品"),
    days: int = Query(30, ge=1, le=365),
    industry: Optional[str] = None,
    category_id: Optional[int] = Query(None),
    subcategory_id: Optional[List[int]] = Query(None),
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取多产品历史价格对比（折线图数据）"""
    start_date = (date.today() - timedelta(days=days)).isoformat()

    def base_filter(q):
        q = q.filter(PriceRecord.record_date >= start_date)
        if source and source != '__all__':
            q = q.filter(PriceRecord.source == source)
        return q

    results = []
    if product_ids and product_ids.strip():
        # 指定了产品ID
        id_list = [int(pid.strip()) for pid in product_ids.split(",") if pid.strip().isdigit()]
        q = db.query(PriceRecord, Product.product_name).join(Product).filter(
            PriceRecord.product_id.in_(id_list),
            PriceRecord.record_date >= start_date
        )
        if source and source != '__all__':
            q = q.filter(PriceRecord.source == source)
        results = q.order_by(PriceRecord.record_date.asc()).all()
    else:
        # 未指定产品ID，按分类获取
        query = db.query(Product).distinct()
        if industry:
            query = query.filter(Product.industry == industry)

        # 如果 ProductCategory 为空，则忽略 subcategory_id 过滤（返回该行业所有产品）
        pc_count = db.query(ProductCategory).count()
        if subcategory_id and pc_count > 0:
            pc_query = db.query(ProductCategory.product_id).filter(
                ProductCategory.category_id.in_(subcategory_id)
            )
            query = query.filter(Product.id.in_(pc_query))
        elif subcategory_id and pc_count == 0:
            # ProductCategory 为空，直接用 category_id 过滤（忽略 subcategory_id）
            pass
        elif category_id:
            subcat_ids = [c.id for c in db.query(Category).filter(Category.parent_id == category_id).all()]
            pc_query = db.query(ProductCategory.product_id).filter(
                ProductCategory.category_id.in_(subcat_ids + [category_id])
            )
            query = query.filter(Product.id.in_(pc_query))

        products = query.limit(10).all()
        if products:
            product_ids_list = [p.id for p in products]
            q = db.query(PriceRecord, Product.product_name).join(Product).filter(
                PriceRecord.product_id.in_(product_ids_list),
                PriceRecord.record_date >= start_date
            )
            if source and source != '__all__':
                q = q.filter(PriceRecord.source == source)
            results = q.order_by(PriceRecord.record_date.asc()).all()
            # 如果有 source 过滤但结果为空，说明随意取的产品没有该 source 数据
            # 改为只取有该 source 数据的产品
            if not results and source and source != '__all__':
                source_product_ids = db.query(PriceRecord.product_id).filter(
                    PriceRecord.source == source,
                    PriceRecord.record_date >= start_date
                ).distinct().limit(10).all()
                if source_product_ids:
                    q = db.query(PriceRecord, Product.product_name).join(Product).filter(
                        PriceRecord.product_id.in_([p[0] for p in source_product_ids]),
                        PriceRecord.record_date >= start_date,
                        PriceRecord.source == source
                    )
                    results = q.order_by(PriceRecord.record_date.asc()).all()

    # 按产品分组
    product_data = {}
    for pr, pname in results:
        if pr.product_id not in product_data:
            product_data[pr.product_id] = {"name": pname, "data": []}
        product_data[pr.product_id]["data"].append(pr.price)

    # 收集所有日期
    all_dates = sorted(set(pr.record_date.isoformat() for pr, _ in results))

    return {"dates": all_dates, "series": list(product_data.values())}


@router.get("/dashboard/volatility")
async def get_dashboard_volatility(
    days: int = Query(7, ge=1, le=30),
    industry: Optional[str] = None,
    category_id: Optional[int] = None,
    subcategory_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取价格波动幅度统计（仪表盘数据）"""
    start_date = (date.today() - timedelta(days=days)).isoformat()

    base_query = db.query(
        func.avg(func.abs(PriceRecord.change_percent)).label('avg_volatility'),
        func.max(func.abs(PriceRecord.change_percent)).label('max_volatility'),
        func.count(func.distinct(PriceRecord.product_id)).label('active_products')
    ).join(Product).filter(
        PriceRecord.record_date >= start_date
    )

    if industry:
        base_query = base_query.filter(Product.industry == industry)

    # Filter by category
    if category_id:
        subcat_ids = [c.id for c in db.query(Category).filter(Category.parent_id == category_id).all()]
        pc_query = db.query(ProductCategory.product_id).filter(ProductCategory.category_id.in_(subcat_ids + [category_id]))
        base_query = base_query.filter(PriceRecord.product_id.in_(pc_query))

    if subcategory_id:
        pc_ids = db.query(ProductCategory.product_id).filter(
            ProductCategory.category_id.in_(subcategory_id)
        ).all()
        pc_ids = [p[0] for p in pc_ids]
        if pc_ids:
            base_query = base_query.filter(PriceRecord.product_id.in_(pc_ids))

    stats = base_query.first()

    # 获取今日最新价格产品数
    today_count_query = db.query(func.count(func.distinct(PriceRecord.product_id))).filter(
        PriceRecord.record_date >= date.today().isoformat()
    )

    if category_id:
        subcat_ids = [c.id for c in db.query(Category).filter(Category.parent_id == category_id).all()]
        pc_query = db.query(ProductCategory.product_id).filter(ProductCategory.category_id.in_(subcat_ids + [category_id]))
        today_count_query = today_count_query.filter(PriceRecord.product_id.in_(pc_query))

    if subcategory_id:
        pc_ids = db.query(ProductCategory.product_id).filter(
            ProductCategory.category_id.in_(subcategory_id)
        ).all()
        pc_ids = [p[0] for p in pc_ids]
        if pc_ids:
            today_count_query = today_count_query.filter(PriceRecord.product_id.in_(pc_ids))

    today_count = today_count_query.scalar() or 0

    return {
        "avg_volatility": round(stats.avg_volatility or 0, 2),
        "max_volatility": round(stats.max_volatility or 0, 2),
        "active_products": stats.active_products or 0,
        "today_updated": today_count
    }


@router.get("/supplier-comparison")
async def get_supplier_comparison(
    product_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    source: Optional[str] = None,
    industry: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取供应商对比数据，从 DetailedQuote 表聚合"""
    start_date = (date.today() - timedelta(days=days)).isoformat()

    base_filter = [
        DetailedQuote.publish_date >= start_date,
        Product.is_active == True,
    ]
    if product_id:
        base_filter.append(DetailedQuote.product_id == product_id)
    if source and source != '__all__':
        base_filter.append(DetailedQuote.source == source)
    if industry:
        base_filter.append(Product.industry == industry)

    # 获取所有产品的最新基准价（一次性）
    benchmark_map = {}
    benchmark_subquery = db.query(
        BenchmarkPrice.product_id,
        func.max(BenchmarkPrice.record_date).label('max_date')
    ).group_by(BenchmarkPrice.product_id).subquery()

    benchmark_rows = db.query(BenchmarkPrice).join(
        benchmark_subquery,
        (BenchmarkPrice.product_id == benchmark_subquery.c.product_id) &
        (BenchmarkPrice.record_date == benchmark_subquery.c.max_date)
    ).all()
    for bp in benchmark_rows:
        benchmark_map[bp.product_id] = bp.price

    # 1. supplier_counts: SQL GROUP BY supplier
    supplier_rows = db.query(
        func.coalesce(DetailedQuote.supplier, '未知供应商').label('supplier'),
        func.count(DetailedQuote.id).label('count'),
        func.count(func.distinct(DetailedQuote.product_id)).label('product_count'),
        func.sum(DetailedQuote.price).label('price_sum'),
        func.max(DetailedQuote.publish_date).label('max_date'),
        func.min(DetailedQuote.publish_date).label('min_date'),
    ).join(Product, DetailedQuote.product_id == Product.id).filter(
        *base_filter
    ).group_by(func.coalesce(DetailedQuote.supplier, '未知供应商')).all()

    # 批量获取每个供应商的价格列表（用于波动率计算）和偏离度
    supplier_names = [row.supplier for row in supplier_rows]
    all_prices_by_supplier = {}
    all_devs_by_supplier = {}
    if supplier_names:
        # 只查有基准价的产品的报价，减少数据量
        pids_with_benchmark = [pid for pid, p in benchmark_map.items() if p and p > 0]
        if pids_with_benchmark:
            raw_rows = db.query(
                func.coalesce(DetailedQuote.supplier, '未知供应商').label('supplier'),
                DetailedQuote.price,
                DetailedQuote.product_id,
            ).join(Product, DetailedQuote.product_id == Product.id).filter(
                *base_filter,
                func.coalesce(DetailedQuote.supplier, '未知供应商').in_(supplier_names),
                DetailedQuote.product_id.in_(pids_with_benchmark),
            ).all()
            for r in raw_rows:
                s = r.supplier
                all_prices_by_supplier.setdefault(s, []).append(r.price)
                bp = benchmark_map.get(r.product_id)
                if bp and bp > 0:
                    all_devs_by_supplier.setdefault(s, []).append((r.price - bp) / bp)

    supplier_counts = []
    for row in supplier_rows:
        supplier = row.supplier
        count = row.count
        prices = all_prices_by_supplier.get(supplier, [])
        deviations = all_devs_by_supplier.get(supplier, [])

        avg_dev = sum(deviations) / len(deviations) if deviations else 0
        max_dev = max(deviations) if deviations else 0

        if avg_dev <= -0.15:
            status_label = "优"
        elif avg_dev >= 0.15:
            status_label = "风险"
        else:
            status_label = "正常"

        avg_price = round(row.price_sum / count, 2) if count else 0

        active_days = 1
        if row.min_date and row.max_date:
            try:
                d1 = datetime.strptime(str(row.min_date)[:10], '%Y-%m-%d').date()
                d2 = datetime.strptime(str(row.max_date)[:10], '%Y-%m-%d').date()
                active_days = (d2 - d1).days + 1
            except (ValueError, TypeError):
                active_days = 1

        price_volatility = 0.0
        if len(prices) > 1:
            mean_price = sum(prices) / len(prices)
            if mean_price > 0:
                price_volatility = round(statistics.stdev(prices) / mean_price, 4)
        price_range = round(max(prices), 2) if prices else 0

        supplier_counts.append({
            "supplier": supplier,
            "count": count,
            "product_count": row.product_count,
            "avg_price": avg_price,
            "avg_deviation": round(avg_dev, 4),
            "max_deviation": round(max_dev, 4),
            "status_label": status_label,
            "active_days": active_days,
            "price_volatility": price_volatility,
            "price_range": price_range
        })

    # 2. product_supplier_prices: SQL GROUP BY product_id + supplier，取最新报价
    ps_rows = db.query(
        DetailedQuote.product_id,
        Product.product_name,
        func.coalesce(DetailedQuote.supplier, '未知供应商').label('supplier'),
        func.max(DetailedQuote.publish_date).label('latest_date'),
        func.count(DetailedQuote.id).label('quote_count'),
    ).join(Product, DetailedQuote.product_id == Product.id).filter(
        *base_filter
    ).group_by(
        DetailedQuote.product_id, Product.product_name, func.coalesce(DetailedQuote.supplier, '未知供应商')
    ).all()

    # 批量获取最新报价价格（避免 N+1）
    latest_price_subquery = db.query(
        DetailedQuote.product_id,
        func.coalesce(DetailedQuote.supplier, '未知供应商').label('supplier'),
        func.max(DetailedQuote.publish_date).label('latest_date'),
    ).join(Product, DetailedQuote.product_id == Product.id).filter(
        *base_filter
    ).group_by(
        DetailedQuote.product_id, func.coalesce(DetailedQuote.supplier, '未知供应商')
    ).subquery()

    latest_prices_rows = db.query(
        latest_price_subquery.c.product_id,
        latest_price_subquery.c.supplier,
        latest_price_subquery.c.latest_date,
        DetailedQuote.price,
    ).join(
        DetailedQuote,
        (DetailedQuote.product_id == latest_price_subquery.c.product_id) &
        (func.coalesce(DetailedQuote.supplier, '未知供应商') == latest_price_subquery.c.supplier) &
        (DetailedQuote.publish_date == latest_price_subquery.c.latest_date)
    ).all()

    latest_price_map = {}
    for lp in latest_prices_rows:
        latest_price_map[(lp.product_id, lp.supplier)] = lp.price

    product_supplier_prices = []
    for row in ps_rows:
        price = latest_price_map.get((row.product_id, row.supplier), 0)

        benchmark_price = benchmark_map.get(row.product_id)
        deviation = round((price - benchmark_price) / benchmark_price, 4) if benchmark_price and benchmark_price > 0 else 0
        product_supplier_prices.append({
            "product_id": row.product_id,
            "product": row.product_name,
            "supplier": row.supplier,
            "price": price,
            "quote_count": row.quote_count,
            "benchmark_price": benchmark_price or 0,
            "deviation": deviation
        })

    # 3. supplier_products: SQL GROUP BY supplier + product_id
    sp_rows = db.query(
        func.coalesce(DetailedQuote.supplier, '未知供应商').label('supplier'),
        DetailedQuote.product_id,
        Product.product_name,
        func.max(DetailedQuote.publish_date).label('latest_date'),
        func.count(DetailedQuote.id).label('count'),
    ).join(Product, DetailedQuote.product_id == Product.id).filter(
        *base_filter
    ).group_by(
        func.coalesce(DetailedQuote.supplier, '未知供应商'),
        DetailedQuote.product_id,
        Product.product_name,
    ).all()

    supplier_products_map = {}
    for row in sp_rows:
        supplier = row.supplier
        if supplier not in supplier_products_map:
            supplier_products_map[supplier] = []

        price = latest_price_map.get((row.product_id, row.supplier), 0)

        bp = benchmark_map.get(row.product_id)
        dev = round((price - bp) / bp, 4) if bp and bp > 0 else 0
        supplier_products_map[supplier].append({
            "product_id": row.product_id,
            "product": row.product_name,
            "price": price,
            "count": row.count,
            "benchmark_price": bp or 0,
            "deviation": dev
        })

    supplier_products = [
        {"supplier": supplier, "products": products}
        for supplier, products in supplier_products_map.items()
    ]

    return {
        "supplier_counts": supplier_counts,
        "product_supplier_prices": product_supplier_prices,
        "supplier_products": supplier_products
    }


@router.get("/dashboard/indicator-cards")
async def get_dashboard_indicator_cards(
    period_type: str = Query(..., regex="^(yoy|qoq|d7|d30)$", description="yoy=同比, qoq=环比, d7=7日涨跌, d30=30日涨跌"),
    industry: Optional[str] = None,
    category_id: Optional[int] = None,
    subcategory_id: Optional[List[int]] = Query(None),
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取指标卡片数据（同比/环比/7日涨跌/30日涨跌）"""
    if period_type in ("yoy", "qoq"):
        result = calculate_yoy_mom(
            session=db,
            period_type=period_type,
            source=source,
            industry=industry,
            category_id=category_id,
            subcategory_id=subcategory_id,
            top_n=10
        )
    else:
        days = int(period_type[1:])
        result = calculate_day_change(
            session=db,
            days=days,
            source=source,
            industry=industry,
            category_id=category_id,
            subcategory_id=subcategory_id,
            top_n=10
        )
    return result