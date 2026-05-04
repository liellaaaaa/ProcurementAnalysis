from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import date
from sqlalchemy.orm import Session
from backend.models.database import get_session, Product

router = APIRouter(prefix="/api/v1/products", tags=["产品管理"])

class ProductCreate(BaseModel):
    product_code: str
    product_name: str
    category: Optional[str] = "化工"
    unit: Optional[str] = "元/吨"
    source: Optional[str] = None
    source_url: Optional[str] = None

class ProductResponse(BaseModel):
    id: int
    product_code: str
    product_name: str
    category: Optional[str]
    unit: str
    source: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True

@router.get("", response_model=List[ProductResponse])
async def get_products(
    category: Optional[str] = None,
    is_active: Optional[bool] = True,
    limit: int = Query(100, le=500)
):
    """获取产品列表"""
    session = get_session()
    query = session.query(Product)

    if category:
        query = query.filter(Product.category == category)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    products = query.limit(limit).all()
    session.close()
    return products

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int):
    """获取产品详情"""
    session = get_session()
    product = session.query(Product).filter(Product.id == product_id).first()
    session.close()

    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    return product

@router.post("", response_model=ProductResponse)
async def create_product(product: ProductCreate):
    """创建产品"""
    session = get_session()

    existing = session.query(Product).filter(Product.product_code == product.product_code).first()
    if existing:
        session.close()
        raise HTTPException(status_code=400, detail="产品编码已存在")

    new_product = Product(**product.model_dump())
    session.add(new_product)
    session.commit()
    session.refresh(new_product)
    session.close()

    return new_product

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    is_active: Optional[bool] = None

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, product: ProductUpdate):
    """更新产品"""
    session = get_session()
    db_product = session.query(Product).filter(Product.id == product_id).first()

    if not db_product:
        session.close()
        raise HTTPException(status_code=404, detail="产品不存在")

    update_data = product.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)

    from datetime import datetime
    db_product.updated_at = datetime.now()
    session.commit()
    session.refresh(db_product)
    session.close()

    return db_product

@router.delete("/{product_id}")
async def delete_product(product_id: int):
    """删除产品（软删除）"""
    session = get_session()
    product = session.query(Product).filter(Product.id == product_id).first()

    if not product:
        session.close()
        raise HTTPException(status_code=404, detail="产品不存在")

    product.is_active = False
    session.commit()
    session.close()

    return {"message": "产品已删除"}