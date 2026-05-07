"""
品类数据初始化脚本
运行方式: python backend/scripts/seed_categories.py
"""
import sys
import os

# 动态计算项目根目录并添加到 sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.models.database import get_session, Category, ProductCategory, Product
from datetime import datetime

# 定义 18 个一级品类及其二级品类
CATEGORIES_DATA = [
    {"name": "烯烃", "subs": ["石脑油", "丙烯", "丁二烯"]},
    {"name": "芳烃", "subs": ["纯苯", "甲苯", "混二甲苯", "PX", "苯乙烯", "环己烷", "环己酮", "己内酰胺", "苯胺"]},
    {"name": "醇类", "subs": ["乙二醇", "二甘醇", "异辛醇", "正丁醇(工业级)", "正丙醇", "乙醇", "丙二醇", "异丙醇"]},
    {"name": "氟化工", "subs": ["萤石", "氢氟酸", "氢氟酸(出口)", "R22", "R134a", "冰晶石", "氟化铝", "二氯甲烷", "三氯甲烷"]},
    {"name": "磷化工", "subs": ["黄磷", "磷酸", "磷酸(湿法)", "磷酸一铵"]},
    {"name": "溴化工", "subs": ["溴素", "硫磺", "硫酸", "烧碱", "轻质纯碱", "重质纯碱"]},
    {"name": "丙烯产业", "subs": ["异丙醇", "苯酚", "丙酮", "PP(拉丝)", "丙烯", "环氧氯丙烷", "石脑油", "环氧丙烷", "丙烯酸", "异辛醇", "正丁醇(工业级)", "丙烯腈"]},
    {"name": "苯乙烯产业", "subs": ["纯苯", "苯乙烯", "丁苯橡胶", "ABS", "PS"]},
    {"name": "醋酸产业", "subs": ["醋酸", "醋酐", "醋酸乙酯", "醋酸丁酯", "PTA", "甲醇"]},
    {"name": "酚酮产业", "subs": ["纯苯", "丁酮", "环己酮", "丙酮", "异丙醇", "丙烯", "双酚A", "苯酚", "环氧树脂", "MIBK"]},
    {"name": "化肥板块", "subs": ["尿素", "液氨", "硫酸钾", "氯化钾(进口)", "硫酸铵", "硝酸铵", "磷酸一铵"]},
    {"name": "甲醇产业", "subs": ["甲醇", "甲醛", "二甲醚", "DMF", "MTBE", "醋酸", "三氯甲烷"]},
    {"name": "聚氨酯板块", "subs": ["TDI", "聚合MDI", "1,4-丁二醇", "DMF", "EVA", "苯胺", "环氧丙烷", "己二酸", "苯酐"]},
    {"name": "氯碱产业", "subs": ["电石", "片碱", "烧碱", "小苏打", "轻质纯碱", "重质纯碱", "盐酸"]},
    {"name": "锂电产业", "subs": ["镍", "钴", "碳酸锂", "电池级碳酸锂", "氢氧化锂"]},
    {"name": "乙二醇产业", "subs": ["乙二醇", "PET", "涤纶短纤", "涤纶DTY", "涤纶FDY", "涤纶POY", "环氧乙烷"]},
    {"name": "增塑剂板块", "subs": ["DBP", "DOP", "PTA", "PVC树脂SG5", "苯酐", "异辛醇", "正丁醇(工业级)"]},
    {"name": "其他", "subs": []}
]


def seed_categories():
    """初始化品类数据"""
    session = get_session()

    try:
        # 检查是否已有品类数据
        existing_count = session.query(Category).count()
        if existing_count > 0:
            print(f"数据库中已有 {existing_count} 个品类，跳过初始化。")
            return

        category_id_map = {}  # 用于存储二级品类的名称到ID的映射

        for cat_data in CATEGORIES_DATA:
            # 创建一级品类
            parent_cat = Category(
                name=cat_data["name"],
                parent_id=None,
                sort_order=CATEGORIES_DATA.index(cat_data)
            )
            session.add(parent_cat)
            session.commit()
            session.refresh(parent_cat)
            print(f"创建一级品类: {cat_data['name']} (ID: {parent_cat.id})")

            # 创建二级品类
            for sub_name in cat_data["subs"]:
                sub_cat = Category(
                    name=sub_name,
                    parent_id=parent_cat.id,
                    sort_order=cat_data["subs"].index(sub_name)
                )
                session.add(sub_cat)
                session.commit()
                session.refresh(sub_cat)
                category_id_map[sub_name] = sub_cat.id
                print(f"  创建二级品类: {sub_name} (ID: {sub_cat.id})")

        print("\n品类数据初始化完成！")
        return category_id_map

    except Exception as e:
        session.rollback()
        print(f"初始化失败: {e}")
        raise
    finally:
        session.close()


def auto_match_products():
    """自动匹配现有产品到品类"""
    session = get_session()

    try:
        # 获取所有产品
        products = session.query(Product).filter(Product.is_active == True).all()
        print(f"\n开始匹配 {len(products)} 个产品...")

        matched_count = 0
        for product in products:
            product_name = product.product_name.strip()
            matched = False

            # 遍历所有二级品类，查找名称匹配的产品
            subcategories = session.query(Category).filter(Category.parent_id.isnot(None)).all()
            for sub_cat in subcategories:
                if sub_cat.name in product_name or product_name in sub_cat.name:
                    # 检查是否已有关联
                    existing = session.query(ProductCategory).filter(
                        ProductCategory.product_id == product.id,
                        ProductCategory.category_id == sub_cat.id
                    ).first()

                    if not existing:
                        assoc = ProductCategory(product_id=product.id, category_id=sub_cat.id)
                        session.add(assoc)
                        matched = True

            if matched:
                matched_count += 1
                print(f"  匹配产品: {product_name}")

        session.commit()
        print(f"\n匹配完成！共匹配 {matched_count} 个产品。")

    except Exception as e:
        session.rollback()
        print(f"匹配失败: {e}")
        raise
    finally:
        session.close()


def main():
    print("=" * 50)
    print("开始初始化品类数据...")
    print("=" * 50)

    # 初始化品类
    seed_categories()

    # 自动匹配产品
    auto_match_products()

    print("\n" + "=" * 50)
    print("所有任务完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
