"""查询工具函数"""
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.models.database import Category, ProductCategory


def build_category_filter(query, model, category_id: int, session: Session):
    """
    构建品类过滤查询，自动包含二级品类

    Args:
        query: SQLAlchemy query 对象
        model: 带有 category_id 或 product_id 字段的模型
        category_id: 品类ID（一级或二级）
        session: 数据库会话
    """
    # 获取二级品类ID列表
    subcat_ids = [c.id for c in session.query(Category).filter(Category.parent_id == category_id).all()]

    # 构建品类过滤条件
    if hasattr(model, 'category_id'):
        # 直接有 category_id 字段（如 AlertConfig）
        cat_ids = subcat_ids + [category_id]
        if hasattr(model, 'product_id'):
            # 需要通过 product_categories 关联表查询
            pc_query = select(ProductCategory.product_id).filter(ProductCategory.category_id.in_(cat_ids))
            query = query.filter(model.product_id.in_(pc_query))
        else:
            query = query.filter(model.category_id.in_(cat_ids))

    return query