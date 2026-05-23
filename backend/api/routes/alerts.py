from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
from backend.api.deps import get_db
from backend.models.database import AlertConfig, AlertRecord, Product, Category
from backend.services.operation_logger import OperationLogger

router = APIRouter(prefix="/api/v1/alerts", tags=["预警管理"])


# ============ Pydantic Models ============

class AlertConfigCreate(BaseModel):
    product_id: int
    alert_type: str  # threshold / change_rate / trend
    threshold_value: Optional[float] = None
    change_percent: Optional[float] = None
    is_active: bool = True


class AlertConfigUpdate(BaseModel):
    alert_type: Optional[str] = None
    threshold_value: Optional[float] = None
    change_percent: Optional[float] = None
    is_active: Optional[bool] = None


class AlertConfigResponse(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    industry: Optional[str] = None
    category_id: Optional[int] = None
    alert_type: str
    threshold_value: Optional[float] = None
    change_percent: Optional[float] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AlertRecordResponse(BaseModel):
    id: int
    alert_config_id: Optional[int]
    product_id: int
    product_name: Optional[str] = None
    alert_type: Optional[str] = None
    alert_message: str
    triggered_price: float
    triggered_at: datetime
    is_read: bool

    class Config:
        from_attributes = True


# ============ Alert Config CRUD ============

@router.get("/configs", response_model=List[AlertConfigResponse])
async def get_alert_configs(
    product_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    industry: Optional[str] = None,
    source: Optional[str] = None,
    category_id: Optional[int] = None,
    subcategory_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取预警配置列表"""
    query = db.query(AlertConfig)

    if product_id:
        query = query.filter(AlertConfig.product_id == product_id)
    if is_active is not None:
        query = query.filter(AlertConfig.is_active == is_active)

    results = query.order_by(AlertConfig.created_at.desc()).all()
    product_ids = [r.product_id for r in results]

    # Build product query with filters
    product_query = db.query(Product)
    if industry:
        product_query = product_query.filter(Product.industry == industry)
    if source:
        product_query = product_query.filter(Product.source == source)
    if category_id:
        from backend.models.database import ProductCategory, Category
        subcat_ids = [c.id for c in db.query(Category).filter(Category.parent_id == category_id).all()]
        pc_query = db.query(ProductCategory.product_id).filter(ProductCategory.category_id.in_(subcat_ids + [category_id]))
        product_query = product_query.filter(Product.id.in_(pc_query))
    if subcategory_id:
        from backend.models.database import ProductCategory
        pc_query = db.query(ProductCategory.product_id).filter(ProductCategory.category_id == subcategory_id)
        product_query = product_query.filter(Product.id.in_(pc_query))

    filtered_products = {p.id: p for p in product_query.all()}
    product_names = {p.id: p.product_name for p in db.query(Product).filter(Product.id.in_(product_ids)).all()}

    # Get product industry and category info
    from backend.models.database import ProductCategory
    product_industries = {p.id: p.industry for p in db.query(Product).filter(Product.id.in_(product_ids)).all()}
    product_categories = {}
    for pc in db.query(ProductCategory).filter(ProductCategory.product_id.in_(product_ids)).all():
        if pc.product_id not in product_categories:
            product_categories[pc.product_id] = pc.category_id

    response = []
    for config in results:
        if config.product_id in filtered_products:
            response.append(AlertConfigResponse(
                id=config.id,
                product_id=config.product_id,
                product_name=product_names.get(config.product_id),
                industry=product_industries.get(config.product_id),
                category_id=product_categories.get(config.product_id),
                alert_type=config.alert_type,
                threshold_value=config.threshold_value,
                change_percent=config.change_percent,
                is_active=config.is_active,
                created_at=config.created_at
            ))
    return response


@router.post("/configs", response_model=AlertConfigResponse)
async def create_alert_config(config: AlertConfigCreate, db: Session = Depends(get_db)):
    """创建预警配置"""

    # 验证产品存在
    product = db.query(Product).filter(Product.id == config.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    product_name = product.product_name

    new_config = AlertConfig(
        product_id=config.product_id,
        alert_type=config.alert_type,
        threshold_value=config.threshold_value,
        change_percent=config.change_percent,
        is_active=config.is_active
    )
    db.add(new_config)
    db.commit()
    db.refresh(new_config)

    # 记录操作日志
    OperationLogger.log_alert_create(
        alert_config_id=new_config.id,
        product_name=product_name,
        alert_type=config.alert_type
    )

    return AlertConfigResponse(
        id=new_config.id,
        product_id=new_config.product_id,
        product_name=product_name,
        alert_type=new_config.alert_type,
        threshold_value=new_config.threshold_value,
        change_percent=new_config.change_percent,
        is_active=new_config.is_active,
        created_at=new_config.created_at
    )


@router.put("/configs/{config_id}", response_model=AlertConfigResponse)
async def update_alert_config(config_id: int, config: AlertConfigUpdate, db: Session = Depends(get_db)):
    """更新预警配置"""
    db_config = db.query(AlertConfig).filter(AlertConfig.id == config_id).first()

    if not db_config:
        raise HTTPException(status_code=404, detail="预警配置不存在")

    update_data = config.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_config, field, value)

    db.commit()
    db.refresh(db_config)

    product = db.query(Product).filter(Product.id == db_config.product_id).first()
    product_name = product.product_name if product else None

    # 记录操作日志
    OperationLogger.log_alert_update(config_id, update_data)

    return AlertConfigResponse(
        id=db_config.id,
        product_id=db_config.product_id,
        product_name=product_name,
        alert_type=db_config.alert_type,
        threshold_value=db_config.threshold_value,
        change_percent=db_config.change_percent,
        is_active=db_config.is_active,
        created_at=db_config.created_at
    )


@router.delete("/configs/{config_id}")
async def delete_alert_config(config_id: int, db: Session = Depends(get_db)):
    """删除预警配置"""
    config = db.query(AlertConfig).filter(AlertConfig.id == config_id).first()

    if not config:
        raise HTTPException(status_code=404, detail="预警配置不存在")

    db.delete(config)
    db.commit()

    # 记录操作日志
    OperationLogger.log_alert_delete(config_id)
    return {"message": "预警配置已删除"}


# ============ Alert Record APIs ============

@router.get("", response_model=List[AlertRecordResponse])
async def get_alert_records(
    product_id: Optional[int] = None,
    is_read: Optional[bool] = None,
    industry: Optional[str] = None,
    source: Optional[str] = None,
    category_id: Optional[int] = None,
    subcategory_id: Optional[int] = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db)
):
    """获取预警记录列表"""

    # Build product filter base
    product_query = db.query(Product)
    if industry:
        product_query = product_query.filter(Product.industry == industry)
    if source:
        product_query = product_query.filter(Product.source == source)
    if category_id:
        from backend.models.database import ProductCategory, Category
        subcat_ids = [c.id for c in db.query(Category).filter(Category.parent_id == category_id).all()]
        pc_query = db.query(ProductCategory.product_id).filter(ProductCategory.category_id.in_(subcat_ids + [category_id]))
        product_query = product_query.filter(Product.id.in_(pc_query))
    if subcategory_id:
        from backend.models.database import ProductCategory
        pc_query = db.query(ProductCategory.product_id).filter(ProductCategory.category_id == subcategory_id)
        product_query = product_query.filter(Product.id.in_(pc_query))

    filtered_product_ids = [p.id for p in product_query.all()]

    query = db.query(AlertRecord, Product.product_name, AlertConfig.alert_type).join(
        Product, AlertRecord.product_id == Product.id
    ).join(AlertConfig, AlertRecord.alert_config_id == AlertConfig.id)

    if product_id:
        query = query.filter(AlertRecord.product_id == product_id)
    if is_read is not None:
        query = query.filter(AlertRecord.is_read == is_read)
    if filtered_product_ids:
        query = query.filter(AlertRecord.product_id.in_(filtered_product_ids))
    else:
        # No products match the filter, return empty
        return []

    results = query.order_by(AlertRecord.triggered_at.desc()).limit(limit).all()
    response = []
    for record, product_name, alert_type in results:
        response.append(AlertRecordResponse(
            id=record.id,
            alert_config_id=record.alert_config_id,
            product_id=record.product_id,
            product_name=product_name,
            alert_type=alert_type,
            alert_message=record.alert_message,
            triggered_price=record.triggered_price,
            triggered_at=record.triggered_at,
            is_read=record.is_read
        ))
    return response


@router.put("/{record_id}/read")
async def mark_alert_as_read(record_id: int, db: Session = Depends(get_db)):
    """标记预警为已读"""
    record = db.query(AlertRecord).filter(AlertRecord.id == record_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="预警记录不存在")

    record.is_read = True
    db.commit()
    return {"message": "已标记为已读"}


@router.put("/read-all")
async def mark_all_alerts_as_read(db: Session = Depends(get_db)):
    """标记所有预警为已读"""
    db.query(AlertRecord).filter(AlertRecord.is_read == False).update({"is_read": True})
    db.commit()
    return {"message": "已标记全部已读"}


@router.delete("/{record_id}")
async def delete_alert_record(record_id: int, db: Session = Depends(get_db)):
    """删除预警记录"""
    record = db.query(AlertRecord).filter(AlertRecord.id == record_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="预警记录不存在")

    db.delete(record)
    db.commit()
    return {"message": "预警记录已删除"}