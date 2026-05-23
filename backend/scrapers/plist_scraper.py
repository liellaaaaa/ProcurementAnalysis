"""
生意社 plist 页爬虫 - 从 plist 页抓取详细报价数据

运行方式:
  python -m backend.scrapers.plist_scraper
  python -m backend.scrapers.plist_scraper --dry-run
"""
import re
import sys
import json
import argparse
import time
import os
from datetime import date, datetime
from typing import List, Dict, Optional

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.models.database import get_session, Product, DetailedQuote, ScraperLog


# 需要跳过的产品（只有基准价，没有详细报价）
SKIP_PRODUCTS = {"WTI原油", "Brent原油"}


class PlistScraper:
    """生意社 plist 页爬虫"""

    SOURCE_KEY = "shengyishe"
    BASE_URL = "https://www.100ppi.com"

    def __init__(self):
        self._product_map: Dict[str, Product] = {}  # plist_url -> Product

    # ------------------------------------------------------------------
    # 加载产品数据
    # ------------------------------------------------------------------
    def load_products(self) -> Dict[str, Product]:
        """从数据库加载产品，构建 plist_url -> Product 映射"""
        session = get_session()
        try:
            products = session.query(Product).filter(
                Product.plist_url.isnot(None),
                Product.is_active == True
            ).all()
            for p in products:
                self._product_map[p.plist_url] = p
            print(f"从数据库加载了 {len(products)} 个有 plist_url 的产品")
            return self._product_map
        finally:
            session.close()

    def load_urls_from_json(self, json_path: str) -> List[Dict]:
        """从 category_urls_mprice.json 加载 URL 列表"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('categories', [])

    # ------------------------------------------------------------------
    # 解析工具
    # ------------------------------------------------------------------
    def parse_price(self, price_str: str) -> Optional[float]:
        """从价格字符串提取数值"""
        if not price_str:
            return None
        match = re.search(r'([\d,]+\.?\d*)', price_str.replace(',', ''))
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def parse_date(self, date_str: str) -> Optional[date]:
        """解析日期字符串，返回 date 对象或 None"""
        if not date_str:
            return None
        date_str = date_str.strip()
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m/%d", "%m-%d"]:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.year == 1900:
                    dt = dt.replace(year=date.today().year)
                return dt.date()
            except:
                continue
        return None

    def determine_price_category(self, price_type: str, region: str) -> str:
        """根据报价类型和地区判断价格分类"""
        price_type_lower = price_type.lower() if price_type else ""
        region_lower = region.lower() if region else ""

        if '期货' in price_type or 'future' in price_type_lower:
            return "期货"
        elif '锁价' in price_type or 'lock' in price_type_lower:
            return "锁价"
        else:
            return "现货"

    # ------------------------------------------------------------------
    # 页面解析
    # ------------------------------------------------------------------
    def scrape_plist_page(self, product: Product) -> List[Dict]:
        """爬取单个产品的 plist 页，返回所有报价行"""
        url = product.plist_url
        if not url:
            return []

        # 跳过没有详细报价的产品
        if product.product_name in SKIP_PRODUCTS:
            print(f"  [skip] {product.product_name} 无详细报价（需跳过）")
            return []

        print(f"  [详细报价] {product.product_name}: {url}")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()
                try:
                    page.goto(url, timeout=30000, wait_until='networkidle')
                    page.wait_for_timeout(1000)

                    rows = self._parse_plist_table(page)
                    results = self._filter_latest_day(rows)
                    print(f"    → {len(results)} 条报价（最新一天）")
                    return results
                finally:
                    browser.close()
        except Exception as e:
            print(f"    [FAIL] loading: {e}")
            return []

    def _parse_plist_table(self, page) -> List[Dict]:
        """解析 plist 页表格，返回所有行"""
        results = []
        try:
            table = page.query_selector('table.lp-table.mb15')
            if not table:
                table = page.query_selector('table.lp-table')
            if not table:
                return results

            rows = table.query_selector_all('tr')
            for row in rows:
                cells = row.query_selector_all('td')
                if len(cells) < 8:
                    continue

                product_name = cells[0].text_content().strip()
                if not product_name or product_name == '商品名称':
                    continue

                spec_text = cells[1].text_content().strip()
                brand = cells[2].text_content().strip()
                price_str = cells[3].text_content().strip()
                price_type = cells[4].text_content().strip()
                region = cells[5].text_content().strip()
                supplier = cells[6].text_content().strip()
                publish_date_str = cells[7].text_content().strip()

                price = self.parse_price(price_str)
                if price is None or price <= 0:
                    continue

                # 日期解析失败时使用当天日期作为默认值
                parsed_date = self.parse_date(publish_date_str)
                if not parsed_date:
                    parsed_date = date.today()

                results.append({
                    'product_name': product_name,
                    'spec': spec_text,
                    'brand': brand,
                    'price': price,
                    'price_str': price_str,
                    'price_type': price_type,
                    'region': region,
                    'supplier': supplier,
                    'publish_date': parsed_date,
                })
        except Exception as e:
            print(f"    表格解析失败: {e}")
        return results

    def _filter_latest_day(self, rows: List[Dict]) -> List[Dict]:
        """只保留最新一天的数据"""
        if not rows:
            return []
        latest = max(r['publish_date'] for r in rows)
        return [r for r in rows if r['publish_date'] == latest]

    # ------------------------------------------------------------------
    # 数据库操作
    # ------------------------------------------------------------------
    def save_detailed_quotes(self, product_id: int, product_name: str, rows: List[Dict]) -> int:
        """保存详细报价到数据库（增量：已存在则跳过）"""
        session = get_session()
        saved = 0
        try:
            for row in rows:
                # 检查是否已存在
                existing = session.query(DetailedQuote).filter(
                    DetailedQuote.product_id == product_id,
                    DetailedQuote.publish_date == row['publish_date'],
                    DetailedQuote.region == row['region'],
                    DetailedQuote.supplier == row['supplier'],
                    DetailedQuote.price_type == row['price_type']
                ).first()
                if existing:
                    continue

                price_category = self.determine_price_category(
                    row.get('price_type', ''),
                    row.get('region', '')
                )

                dq = DetailedQuote(
                    product_id=product_id,
                    product_name=row['product_name'],
                    spec=row['spec'],
                    brand=row['brand'],
                    price=row['price'],
                    unit='元/吨',
                    price_original=row.get('price_str', ''),
                    price_type=row.get('price_type', ''),
                    price_category=price_category,
                    region=row['region'],
                    supplier=row['supplier'],
                    source=self.SOURCE_KEY,
                    publish_date=row['publish_date'],
                    extra_data={'price_type_original': row.get('price_type', '')},
                )
                session.add(dq)
                saved += 1
            session.commit()
            return saved
        except Exception as e:
            session.rollback()
            print(f"    保存 detailed_quotes 失败: {e}")
            return 0
        finally:
            session.close()

    def log_run(self, status: str, items_scraped: int, error_message: str = None):
        session = get_session()
        try:
            log = ScraperLog(
                scraper_name=f"{self.SOURCE_KEY}_detailed",
                status=status,
                items_scraped=items_scraped,
                error_message=error_message,
                started_at=datetime.now(),
                completed_at=datetime.now()
            )
            session.add(log)
            session.commit()
        finally:
            session.close()

    # ------------------------------------------------------------------
    # 主运行流程
    # ------------------------------------------------------------------
    def run(self, json_path: str = None, dry_run: bool = False):
        """主运行流程"""
        if json_path is None:
            json_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                '..', 'category_urls_mprice.json'
            )

        self.load_products()
        if not self._product_map:
            print("没有找到产品，请先初始化产品数据")
            return

        try:
            url_list = self.load_urls_from_json(json_path)
            print(f"从 {json_path} 加载了 {len(url_list)} 个产品")
        except Exception as e:
            print(f"加载 JSON 文件失败: {e}")
            return

        total_saved = 0
        total_failed = 0

        for item in url_list:
            name = item.get('name')
            url = item.get('url')

            # 跳过没有详细报价的产品
            if name in SKIP_PRODUCTS:
                print(f"  [skip] {name}（无详细报价）")
                continue

            product = self._product_map.get(url)
            if not product:
                print(f"  [skip] {name} 未在数据库中找到对应产品")
                continue

            rows = self.scrape_plist_page(product)
            if rows:
                if not dry_run:
                    n = self.save_detailed_quotes(product.id, name, rows)
                    total_saved += n
                else:
                    print(f"    [dry-run] would save {len(rows)} detailed quotes for {name}")
            else:
                total_failed += 1

            time.sleep(0.5)

        print(f"\n{'='*50}")
        print(f"详细报价爬取完成！成功: {total_saved}, 失败: {total_failed}")
        print(f"{'='*50}")

        self.log_run("success" if total_failed == 0 else "partial",
                    total_saved,
                    f"failed: {total_failed}" if total_failed > 0 else None)


def main():
    parser = argparse.ArgumentParser(description="生意社 plist 页爬虫")
    parser.add_argument('--json-path', help='category_urls_mprice.json 路径')
    parser.add_argument('--dry-run', action='store_true', help='仅模拟，不写入数据库')
    args = parser.parse_args()

    scraper = PlistScraper()
    scraper.log_run("running", 0)

    try:
        scraper.run(json_path=args.json_path, dry_run=args.dry_run)
    except Exception as e:
        scraper.log_run("failed", 0, str(e))
        print(f"爬虫失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()