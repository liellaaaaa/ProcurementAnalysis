"""
更新产品 URL（detail 页 + plist 页）
运行方式: python backend/scripts/update_product_urls.py
"""
import sys
import os
import json

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.models.database import get_session, Product


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_product_urls():
    benchmark_path = os.path.join(project_root, 'category_urls.json')
    mprice_path = os.path.join(project_root, 'category_urls_mprice.json')

    benchmark_data = load_json(benchmark_path)
    mprice_data = load_json(mprice_path)

    detail_urls = {item['name']: item['url'] for item in benchmark_data['categories']}
    plist_urls = {item['name']: item['url'] for item in mprice_data['categories']}

    benchmark_names = set(detail_urls.keys())
    mprice_names = set(plist_urls.keys())
    missing_plist = benchmark_names - mprice_names

    session = get_session()
    updated = 0

    try:
        products = session.query(Product).filter(Product.source == 'shengyishe').all()
        for p in products:
            name = p.product_name.strip()
            if name in detail_urls:
                p.source_url = detail_urls[name]
                p.plist_url = plist_urls.get(name, None)  # 可为 None
                updated += 1

        session.commit()
        print(f"共更新 {updated} 个产品的 URL")

        if missing_plist:
            print(f"\n[!] 缺失 plist 页的产品（共 {len(missing_plist)} 个）:")
            for name in sorted(missing_plist):
                print(f"  - {name}")

        extra_in_mprice = mprice_names - benchmark_names
        if extra_in_mprice:
            print(f"\n[!] mprice 中有但 benchmark 中没有的产品（共 {len(extra_in_mprice)} 个）:")

        return list(missing_plist)

    except Exception as e:
        session.rollback()
        print(f"更新失败: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 50)
    print("开始更新产品 URL...")
    print("=" * 50)
    update_product_urls()
    print("=" * 50)