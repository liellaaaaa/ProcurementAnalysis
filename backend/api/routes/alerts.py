from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from backend.models.database import get_session, AlertConfig, AlertRecord, Product

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
    is_active: Optional[bool] = None
):
    """获取预警配置列表"""
    session = get_session()
    query = session.query(AlertConfig, Product.product_name).join(Product)

    if product_id:
        query = query.filter(AlertConfig.product_id == product_id)
    if is_active is not None:
        query = query.filter(AlertConfig.is_active == is_active)

    results = query.order_by(AlertConfig.created_at.desc()).all()
    response = []
    for config, product_name in results:
        response.append(AlertConfigResponse(
            id=config.id,
            product_id=config.product_id,
            product_name=product_name,
            alert_type=config.alert_type,
            threshold_value=config.threshold_value,
            change_percent=config.change_percent,
            is_active=config.is_active,
            created_at=config.created_at
        ))
    session.close()
    return response


@router.post("/configs", response_model=AlertConfigResponse)
async def create_alert_config(config: AlertConfigCreate):
    """创建预警配置"""
    session = get_session()

    # 验证产品存在
    product = session.query(Product).filter(Product.id == config.product_id).first()
    if not product:
        session.close()
        raise HTTPException(status_code=404, detail="产品不存在")

    new_config = AlertConfig(
        product_id=config.product_id,
        alert_type=config.alert_type,
        threshold_value=config.threshold_value,
        change_percent=config.change_percent,
        is_active=config.is_active
    )
    session.add(new_config)
    session.commit()
    session.refresh(new_config)
    session.close()

    return AlertConfigResponse(
        id=new_config.id,
        product_id=new_config.product_id,
        product_name=product.product_name,
        alert_type=new_config.alert_type,
        threshold_value=new_config.threshold_value,
        change_percent=new_config.change_percent,
        is_active=new_config.is_active,
        created_at=new_config.created_at
    )


@router.put("/configs/{config_id}", response_model=AlertConfigResponse)
async def update_alert_config(config_id: int, config: AlertConfigUpdate):
    """更新预警配置"""
    session = get_session()
    db_config = session.query(AlertConfig).filter(AlertConfig.id == config_id).first()

    if not db_config:
        session.close()
        raise HTTPException(status_code=404, detail="预警配置不存在")

    update_data = config.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_config, field, value)

    session.commit()
    session.refresh(db_config)

    product = session.query(Product).filter(Product.id == db_config.product_id).first()
    session.close()

    return AlertConfigResponse(
        id=db_config.id,
        product_id=db_config.product_id,
        product_name=product.product_name if product else None,
        alert_type=db_config.alert_type,
        threshold_value=db_config.threshold_value,
        change_percent=db_config.change_percent,
        is_active=db_config.is_active,
        created_at=db_config.created_at
    )


@router.delete("/configs/{config_id}")
async def delete_alert_config(config_id: int):
    """删除预警配置"""
    session = get_session()
    config = session.query(AlertConfig).filter(AlertConfig.id == config_id).first()

    if not config:
        session.close()
        raise HTTPException(status_code=404, detail="预警配置不存在")

    session.delete(config)
    session.commit()
    session.close()
    return {"message": "预警配置已删除"}


# ============ Alert Record APIs ============

@router.get("", response_model=List[AlertRecordResponse])
async def get_alert_records(
    product_id: Optional[int] = None,
    is_read: Optional[bool] = None,
    limit: int = Query(100, le=500)
):
    """获取预警记录列表"""
    session = get_session()
    query = session.query(AlertRecord, Product.product_name).join(Product)

    if product_id:
        query = query.filter(AlertRecord.product_id == product_id)
    if is_read is not None:
        query = query.filter(AlertRecord.is_read == is_read)

    results = query.order_by(AlertRecord.triggered_at.desc()).limit(limit).all()
    response = []
    for record, product_name in results:
        response.append(AlertRecordResponse(
            id=record.id,
            alert_config_id=record.alert_config_id,
            product_id=record.product_id,
            product_name=product_name,
            alert_message=record.alert_message,
            triggered_price=record.triggered_price,
            triggered_at=record.triggered_at,
            is_read=record.is_read
        ))
    session.close()
    return response


@router.put("/{record_id}/read")
async def mark_alert_as_read(record_id: int):
    """标记预警为已读"""
    session = get_session()
    record = session.query(AlertRecord).filter(AlertRecord.id == record_id).first()

    if not record:
        session.close()
        raise HTTPException(status_code=404, detail="预警记录不存在")

    record.is_read = True
    session.commit()
    session.close()
    return {"message": "已标记为已读"}


@router.put("/read-all")
async def mark_all_alerts_as_read():
    """标记所有预警为已读"""
    session = get_session()
    session.query(AlertRecord).filter(AlertRecord.is_read == False).update({"is_read": True})
    session.commit()
    session.close()
    return {"message": "已标记全部已读"}


@router.delete("/{record_id}")
async def delete_alert_record(record_id: int):
    """删除预警记录"""
    session = get_session()
    record = session.query(AlertRecord).filter(AlertRecord.id == record_id).first()

    if not record:
        session.close()
        raise HTTPException(status_code=404, detail="预警记录不存在")

    session.delete(record)
    session.commit()
    session.close()
    return {"message": "预警记录已删除"}