from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.api.deps import get_db
from backend.models.database import Product, ProductCategory
from backend.services.operation_logger import OperationLogger

router = APIRouter(prefix="/api/v1/products", tags=["产品管理"])

class ProductCreate(BaseModel):
    product_code: str
    product_name: str
    industry: Optional[str] = "化工"
    category: Optional[str] = "化工"
    unit: Optional[str] = "元/吨"
    source: Optional[str] = None
    source_url: Optional[str] = None
    category_ids: Optional[List[int]] = None

class ProductResponse(BaseModel):
    id: int
    product_code: str
    product_name: str
    industry: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    source: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True

@router.get("", response_model=List[ProductResponse])
async def get_products(
    db: Session = Depends(get_db),
    industry: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = True,
    limit: int = Query(100, le=500)
):
    """获取产品列表（支持行业筛选）"""
    query = db.query(Product)

    if industry:
        query = query.filter(Product.industry == industry)
    if category:
        query = query.filter(Product.category == category)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    products = query.limit(limit).all()

    # 记录查询日志
    OperationLogger.log_product_query(
        filters={"category": category, "is_active": is_active},
        count=len(products)
    )
    return products

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """获取产品详情"""
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    return product

@router.post("", response_model=ProductResponse)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """创建产品"""

    existing = db.query(Product).filter(Product.product_code == product.product_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="产品编码已存在")

    # Extract category_ids before creating product
    category_ids = product.category_ids
    product_data = product.model_dump(exclude={"category_ids"})

    new_product = Product(**product_data)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    # Add category associations
    if category_ids:
        for cat_id in category_ids:
            assoc = ProductCategory(product_id=new_product.id, category_id=cat_id)
            db.add(assoc)
        db.commit()
        db.refresh(new_product)

    # 记录操作日志
    OperationLogger.log_product_create(
        product_code=product.product_code,
        product_name=product.product_name
    )
    return new_product

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    industry: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    is_active: Optional[bool] = None
    category_ids: Optional[List[int]] = None

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    """更新产品"""
    db_product = db.query(Product).filter(Product.id == product_id).first()

    if not db_product:
        raise HTTPException(status_code=404, detail="产品不存在")

    update_data = product.model_dump(exclude_unset=True)

    # Handle category_ids separately
    if "category_ids" in update_data:
        category_ids = update_data.pop("category_ids")
        # Remove existing associations
        db.query(ProductCategory).filter(ProductCategory.product_id == product_id).delete()
        # Add new associations
        if category_ids:
            for cat_id in category_ids:
                assoc = ProductCategory(product_id=product_id, category_id=cat_id)
                db.add(assoc)

    for field, value in update_data.items():
        setattr(db_product, field, value)

    from datetime import datetime
    db_product.updated_at = datetime.now()
    db.commit()
    db.refresh(db_product)

    # 记录操作日志
    OperationLogger.log_product_update(
        product_id=product_id,
        product_name=db_product.product_name,
        changes=update_data
    )
    return db_product

@router.delete("/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """删除产品（软删除）"""
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")

    product.is_active = False
    db.commit()

    # 记录操作日志
    OperationLogger.log_product_delete(
        product_id=product_id,
        product_name=product.product_name
    )
    return {"message": "产品已删除"}


class BatchProductItem(BaseModel):
    product_name: str
    industry: str
    category: Optional[str] = "化工"
    unit: Optional[str] = "元/吨"
    source: Optional[str] = "shengyishe"
    source_url: Optional[str] = None


class BatchProductRequest(BaseModel):
    products: List[BatchProductItem]


class BatchProductResponse(BaseModel):
    total: int
    created: int
    skipped: int
    results: List[dict]


@router.post("/batch", response_model=BatchProductResponse)
async def batch_import_products(batch: BatchProductRequest, db: Session = Depends(get_db)):
    """批量导入产品（支持按 product_name + source_url 查重，已存在则跳过）"""
    import hashlib
    created_count = 0
    skipped_count = 0
    results = []

    for item in batch.products:
        # 按 product_name + source_url 查重
        existing = db.query(Product).filter(
            Product.product_name == item.product_name,
            Product.source_url == item.source_url
        ).first()

        if existing:
            skipped_count += 1
            results.append({
                "product_name": item.product_name,
                "status": "skipped",
                "reason": "已存在"
            })
            continue

        # 生成产品编码
        raw = f"{item.product_name}|{item.source_url or ''}"
        product_code = hashlib.md5(raw.encode()).hexdigest()[:12].upper()

        new_product = Product(
            product_code=product_code,
            product_name=item.product_name,
            industry=item.industry,
            category=item.category,
            unit=item.unit,
            source=item.source,
            source_url=item.source_url
        )
        db.add(new_product)
        created_count += 1
        results.append({
            "product_name": item.product_name,
            "status": "created",
            "product_code": product_code
        })

    db.commit()

    return BatchProductResponse(
        total=len(batch.products),
        created=created_count,
        skipped=skipped_count,
        results=results
    )