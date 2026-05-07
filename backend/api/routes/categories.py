from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.database import get_session, Category, ProductCategory, Product
from backend.services.operation_logger import OperationLogger

router = APIRouter(prefix="/api/v1/categories", tags=["品类管理"])


class CategoryCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None
    sort_order: Optional[int] = 0


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    sort_order: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CategoryWithSubResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    sort_order: int
    subcategories: List[CategoryResponse] = []

    class Config:
        from_attributes = True


@router.get("", response_model=List[CategoryWithSubResponse])
async def get_all_categories():
    """获取所有品类（树形结构）"""
    session = get_session()
    all_categories = session.query(Category).order_by(Category.sort_order, Category.id).all()

    # Build tree structure
    result = []
    for cat in all_categories:
        if cat.parent_id is None:
            subcats = [c for c in all_categories if c.parent_id == cat.id]
            result.append({
                "id": cat.id,
                "name": cat.name,
                "parent_id": cat.parent_id,
                "sort_order": cat.sort_order,
                "subcategories": [{
                    "id": s.id,
                    "name": s.name,
                    "parent_id": s.parent_id,
                    "sort_order": s.sort_order,
                    "created_at": s.created_at
                } for s in subcats]
            })

    session.close()
    return result


@router.get("/level-one", response_model=List[CategoryResponse])
async def get_level_one_categories():
    """获取所有一级目录"""
    session = get_session()
    categories = session.query(Category).filter(
        Category.parent_id.is_(None)
    ).order_by(Category.sort_order, Category.id).all()
    session.close()
    return categories


@router.get("/level-two/{parent_id}", response_model=List[CategoryResponse])
async def get_level_two_categories(parent_id: int):
    """获取指定一级目录下的二级目录"""
    session = get_session()
    categories = session.query(Category).filter(
        Category.parent_id == parent_id
    ).order_by(Category.sort_order, Category.id).all()
    session.close()
    return categories


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int):
    """获取单个品类"""
    session = get_session()
    category = session.query(Category).filter(Category.id == category_id).first()
    session.close()

    if not category:
        raise HTTPException(status_code=404, detail="品类不存在")
    return category


@router.post("", response_model=CategoryResponse)
async def create_category(category: CategoryCreate):
    """创建品类"""
    session = get_session()

    # Validate parent exists if parent_id is provided
    if category.parent_id is not None:
        parent = session.query(Category).filter(Category.id == category.parent_id).first()
        if not parent:
            session.close()
            raise HTTPException(status_code=400, detail="父级品类不存在")
        if parent.parent_id is not None:
            session.close()
            raise HTTPException(status_code=400, detail="只能创建一级或二级品类")

    new_category = Category(**category.model_dump())
    session.add(new_category)
    session.commit()
    session.refresh(new_category)
    session.close()

    # 记录操作日志
    OperationLogger.log_category_create(new_category.name, new_category.id)

    return new_category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: int, category: CategoryUpdate):
    """更新品类"""
    session = get_session()
    db_category = session.query(Category).filter(Category.id == category_id).first()

    if not db_category:
        session.close()
        raise HTTPException(status_code=404, detail="品类不存在")

    update_data = category.model_dump(exclude_unset=True)

    # Validate parent if being updated
    if "parent_id" in update_data and update_data["parent_id"] is not None:
        parent = session.query(Category).filter(Category.id == update_data["parent_id"]).first()
        if not parent:
            session.close()
            raise HTTPException(status_code=400, detail="父级品类不存在")
        if parent.parent_id is not None:
            session.close()
            raise HTTPException(status_code=400, detail="父级品类必须是一级品类")

    for field, value in update_data.items():
        setattr(db_category, field, value)

    session.commit()
    session.refresh(db_category)
    session.close()

    # 记录操作日志
    OperationLogger.log_category_update(category_id, update_data)

    return db_category


@router.delete("/{category_id}")
async def delete_category(category_id: int):
    """删除品类（同时删除子品类和关联）"""
    session = get_session()
    category = session.query(Category).filter(Category.id == category_id).first()

    if not category:
        session.close()
        raise HTTPException(status_code=404, detail="品类不存在")

    # Delete child categories first
    session.query(Category).filter(Category.parent_id == category_id).delete()

    # Delete product associations
    session.query(ProductCategory).filter(ProductCategory.category_id == category_id).delete()

    # Delete the category itself
    session.delete(category)
    session.commit()
    session.close()

    # 记录操作日志
    OperationLogger.log_category_delete(category_id)

    return {"message": "品类已删除"}


# Product-Category association endpoints

class ProductCategoryRequest(BaseModel):
    category_ids: List[int]


@router.get("/product/{product_id}", response_model=List[CategoryResponse])
async def get_product_categories(product_id: int):
    """获取产品关联的所有品类"""
    session = get_session()

    product = session.query(Product).filter(Product.id == product_id).first()
    if not product:
        session.close()
        raise HTTPException(status_code=404, detail="产品不存在")

    associations = session.query(ProductCategory).filter(
        ProductCategory.product_id == product_id
    ).all()

    category_ids = [a.category_id for a in associations]
    categories = session.query(Category).filter(Category.id.in_(category_ids)).all()

    session.close()
    return categories


@router.post("/product/{product_id}")
async def set_product_categories(product_id: int, request: ProductCategoryRequest):
    """设置产品关联的品类"""
    session = get_session()

    product = session.query(Product).filter(Product.id == product_id).first()
    if not product:
        session.close()
        raise HTTPException(status_code=404, detail="产品不存在")

    # Validate all category_ids exist
    if request.category_ids:
        existing_cats = session.query(Category.id).filter(
            Category.id.in_(request.category_ids)
        ).all()
        existing_ids = {c.id for c in existing_cats}
        invalid_ids = set(request.category_ids) - existing_ids
        if invalid_ids:
            session.close()
            raise HTTPException(status_code=400, detail=f"品类不存在: {invalid_ids}")

    # Remove existing associations
    session.query(ProductCategory).filter(ProductCategory.product_id == product_id).delete()

    # Add new associations
    for cat_id in request.category_ids:
        assoc = ProductCategory(product_id=product_id, category_id=cat_id)
        session.add(assoc)

    session.commit()
    session.close()

    return {"message": "产品品类已更新"}
