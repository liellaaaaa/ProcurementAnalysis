"""
产品初始化脚本 - 从 category_urls.json 导入产品数据

运行方式:
  python -m backend.scripts.init_products
  python -m backend.scripts.init_products --dry-run
"""
import re
import sys
import json
import argparse
import os
import hashlib
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.models.database import get_session, Product


def generate_product_code(name: str) -> str:
    """根据产品名称生成唯一的产品编码"""
    hash_str = hashlib.md5(f"{name}|shengyishe".encode()).hexdigest()
    return hash_str[:12].upper()


def load_urls_from_json(json_path: str) -> list:
    """从 JSON 文件加载 URL 列表"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('categories', [])


def init_products_from_json(json_path: str, dry_run: bool = False) -> tuple:
    """从 category_urls.json 初始化产品"""
    items = load_urls_from_json(json_path)
    print(f"从 {json_path} 加载了 {len(items)} 个产品")

    session = get_session()
    created = 0
    updated = 0
    skipped = 0

    try:
        for item in items:
            name = item.get('name', '').strip()
            category = item.get('category', '化工')  # 行业：化工/有色/农副/能源
            detail_url = item.get('url', '')  # detail 页 URL

            if not name or not detail_url:
                print(f"  [skip] 缺少 name 或 url: {item}")
                skipped += 1
                continue

            # 检查是否已存在（根据 product_name + source 查重）
            existing = session.query(Product).filter(
                Product.product_name == name,
                Product.source == 'shengyishe'
            ).first()

            if existing:
                # 更新 source_url（如果有变化）
                if existing.source_url != detail_url:
                    existing.source_url = detail_url
                existing.updated_at = datetime.now()
                updated += 1
                if not dry_run:
                    print(f"  [update] {name}: source_url 更新")
            else:
                product_code = generate_product_code(name)
                product = Product(
                    product_code=product_code,
                    product_name=name,
                    industry=category,
                    category='',
                    unit='元/吨',
                    source='shengyishe',
                    source_url=detail_url,
                    plist_url=None,  # plist_url 后续从 category_urls_mprice.json 更新
                    is_active=True,
                )
                session.add(product)
                created += 1
                if not dry_run:
                    print(f"  [create] {name}: {detail_url}")

        if not dry_run:
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"操作失败: {e}")
        raise
    finally:
        session.close()

    return created, updated, skipped


def update_plist_urls_from_json(json_path: str, dry_run: bool = False) -> int:
    """从 category_urls_mprice.json 更新产品的 plist_url"""
    if not os.path.exists(json_path):
        print(f"文件不存在: {json_path}")
        return 0

    items = load_urls_from_json(json_path)
    print(f"从 {json_path} 加载了 {len(items)} 个产品的 plist URL")

    session = get_session()
    updated = 0

    try:
        for item in items:
            name = item.get('name', '').strip()
            plist_url = item.get('url', '')

            if not name or not plist_url:
                continue

            product = session.query(Product).filter(
                Product.product_name == name,
                Product.source == 'shengyishe'
            ).first()

            if product and not product.plist_url:
                product.plist_url = plist_url
                product.updated_at = datetime.now()
                updated += 1
                if not dry_run:
                    print(f"  [update] {name}: plist_url = {plist_url}")

        if not dry_run:
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"更新 plist_url 失败: {e}")
        raise
    finally:
        session.close()

    return updated


def main():
    parser = argparse.ArgumentParser(description="产品初始化脚本")
    parser.add_argument('--dry-run', action='store_true', help='仅模拟，不写入数据库')
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # 步骤1: 从 category_urls.json 导入产品（包含 detail URL）
    json_path = os.path.join(project_root, 'category_urls.json')
    print(f"\n{'='*50}")
    print(f"步骤1: 从 category_urls.json 导入产品")
    print(f"{'='*50}")
    created, updated, skipped = init_products_from_json(json_path, dry_run=args.dry_run)
    print(f"创建: {created}, 更新: {updated}, 跳过: {skipped}")

    # 步骤2: 从 category_urls_mprice.json 更新 plist_url
    mprice_json_path = os.path.join(project_root, 'category_urls_mprice.json')
    print(f"\n{'='*50}")
    print(f"步骤2: 从 category_urls_mprice.json 更新 plist_url")
    print(f"{'='*50}")
    updated_plist = update_plist_urls_from_json(mprice_json_path, dry_run=args.dry_run)
    print(f"更新 plist_url: {updated_plist} 个产品")

    print(f"\n{'='*50}")
    print(f"产品初始化完成！")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()