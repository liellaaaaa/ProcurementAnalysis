"""
精确品类产品数据初始化
只包含用户指定的 58 个强相关产品
运行方式: python backend/scripts/seed_exact_products.py
"""
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.models.database import get_session, Product
from datetime import datetime
import hashlib


# 用户指定的 58 个强相关产品
EXACT_PRODUCTS = [
    # 化工 (53个)
    ("AES 脂肪醇聚氧乙烯醚硫酸钠", "化工"),
    ("DMF", "化工"),
    ("EGDA", "化工"),
    ("TDI", "化工"),
    ("苯酚", "化工"),
    ("丙二醇甲醚醋酸酯", "化工"),
    ("丙酮", "化工"),
    ("丙烯", "化工"),
    ("丙烯酸", "化工"),
    ("丙烯酰胺", "化工"),
    ("纯苯", "化工"),
    ("醋酸", "化工"),
    ("电石", "化工"),
    ("丁酮肟", "化工"),
    ("二丙二醇", "化工"),
    ("二甘醇", "化工"),
    ("二甲胺水溶液", "化工"),
    ("二乙醇胺", "化工"),
    ("富马酸", "化工"),
    ("过硫酸铵", "化工"),
    ("过硫酸钾", "化工"),
    ("过硫酸钠", "化工"),
    ("环氧丙烷", "化工"),
    ("环氧氯丙烷", "化工"),
    ("环氧树脂", "化工"),
    ("环氧乙烷", "化工"),
    ("黄磷", "化工"),
    ("甲醇", "化工"),
    ("甲醛", "化工"),
    ("焦亚硫酸钠", "化工"),
    ("聚丙烯酰胺", "化工"),
    ("聚合MDI", "化工"),
    ("磷酸", "化工"),
    ("硫磺", "化工"),
    ("硫脲", "化工"),
    ("硫酸", "化工"),
    ("硫酸二甲酯", "化工"),
    ("硫酸二乙酯", "化工"),
    ("尿素", "化工"),
    ("轻质纯碱", "化工"),
    ("三乙醇胺", "化工"),
    ("双氰胺", "化工"),
    ("双氧水", "化工"),
    ("顺酐", "化工"),
    ("盐酸", "化工"),
    ("一水柠檬酸", "化工"),
    ("衣康酸", "化工"),
    ("乙二醇丁醚", "化工"),
    ("异丙醇", "化工"),
    ("异辛醇", "化工"),
    ("油酸", "化工"),
    ("有机硅DMC", "化工"),
    ("元明粉", "化工"),
    ("精萘", "化工"),
    # 能源 (3个)
    ("液化天然气", "能源"),
    ("Brent原油", "能源"),
    ("WTI原油", "能源"),
    # 农副 (2个)
    ("玉米", "农副"),
    ("棕榈油", "农副"),
    # 有色 (2个)
    ("金属硅", "有色"),
    ("黄金", "有色"),
]


def generate_product_code(name: str) -> str:
    """生成产品编码"""
    raw = f"{name}|exact"
    return hashlib.md5(raw.encode()).hexdigest()[:12].upper()


def seed_exact_products():
    """初始化精确产品数据"""
    session = get_session()

    try:
        # 检查是否已有产品数据
        existing_count = session.query(Product).filter(Product.source == "shengyishe").count()
        if existing_count > 0:
            print(f"数据库中已有 {existing_count} 个生意社产品，正在清理...")
            session.query(Product).filter(Product.source == "shengyishe").delete()
            session.commit()

        added_count = 0
        for product_name, industry in EXACT_PRODUCTS:
            product_code = generate_product_code(product_name)

            # 构造生意社 URL（根据产品名生成搜索 URL）
            # 生意社产品页面格式: https://www.100ppi.com/detail-{id}.html
            # 由于我们没有具体 ID，使用搜索页作为入口
            search_url = f"https://www.100ppi.com/sou/?kwd={product_name}"
            # plist 页用于详细报价
            plist_url = f"https://www.100ppi.com/plist-0-1.html?kw={product_name}"

            product = Product(
                product_code=product_code,
                product_name=product_name,
                industry=industry,
                category="",
                unit="元/吨",
                source="shengyishe",
                source_url=plist_url,  # 使用 plist 页作为主入口（包含详细报价）
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(product)
            added_count += 1
            print(f"  添加产品: {product_name} ({industry})")

        session.commit()
        print(f"\n成功添加 {added_count} 个精确产品！")
        return added_count

    except Exception as e:
        session.rollback()
        print(f"初始化失败: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 50)
    print("开始初始化精确产品数据...")
    print("=" * 50)
    seed_exact_products()
    print("=" * 50)
    print("初始化完成！")
    print("=" * 50)