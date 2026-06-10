"""
生意社价格爬虫 - 增量爬取最新一天数据
- detail-xxx.html → benchmark_prices 表（1条/产品/天）
- plist-xxx.html  → detailed_quotes 表（多条/产品/天）

运行方式:
  python -m backend.scrapers.shengyishe
  python -m backend.scrapers.shengyishe --dry-run
"""
import re
import sys
import argparse
import time
from datetime import datetime, date
from collections import defaultdict
from typing import List, Dict, Optional, Tuple

from playwright.sync_api import sync_playwright

from backend.scrapers.base import BaseScraper, ScrapedItem
from backend.models.database import get_session, Product, ScraperLog, ProductCategory, BenchmarkPrice, DetailedQuote, PriceRecord


class ShengyisheScraper:
    """生意社化工价格爬虫 - 使用 Playwright 绕过反爬"""

    BASE_URL = "https://www.100ppi.com"
    SOURCE_KEY = "shengyishe"

    def __init__(self):
        self._product_map: Dict[str, Product] = {}  # url -> Product

    # ------------------------------------------------------------------
    # 入口：获取所有产品（含 detail_url 和 plist_url）
    # ------------------------------------------------------------------
    def get_all_products(self) -> List[Product]:
        session = get_session()
        try:
            products = session.query(Product).filter(
                Product.source_url.isnot(None),
                Product.is_active == True
            ).all()
            for p in products:
                self._product_map[p.source_url] = p
            print(f"从数据库获取到 {len(products)} 个产品")
            return products
        finally:
            session.close()

    # ------------------------------------------------------------------
    # 解析工具
    # ------------------------------------------------------------------
    def parse_price(self, price_str: str) -> Optional[float]:
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
        """解析日期字符串，返回 date 对象"""
        if not date_str:
            return None
        date_str = date_str.strip()
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m/%d", "%m-%d"]:
            try:
                dt = datetime.strptime(date_str, fmt)
                # 如果是 %m/%d 或 %m-%d（year=1900），补全年份为今年
                if dt.year == 1900:
                    dt = dt.replace(year=date.today().year)
                return dt.date()
            except:
                continue
        return None

    # ------------------------------------------------------------------
    # 爬取 detail 页 → benchmark_prices
    # ------------------------------------------------------------------
    def scrape_benchmark(self, product: Product) -> Optional[Dict]:
        """爬取单个产品的 detail 页，提取基准价"""
        url = product.source_url
        industry = product.industry or "化工"
        print(f"  [基准价] {product.product_name}: {url}")

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

                    data = self._parse_benchmark_page(page, product.product_name, url)
                    if data:
                        data['product_id'] = product.id
                        data['record_date'] = date.today()
                        print(f"    → price={data.get('price')} date={data.get('record_date')}")
                    return data
                finally:
                    browser.close()
        except Exception as e:
            print(f"    ✗ 加载失败: {e}")
            return None

    def _parse_benchmark_page(self, page, product_name: str, url: str) -> Optional[Dict]:
        """解析 detail 页，提取基准价（含 spec/brand/market）"""
        try:
            # 价格元素
            price_el = page.query_selector('.price-fb01_1')
            price_str = price_el.inner_text() if price_el else ""
            price = self.parse_price(price_str)
            if price is None or price <= 0:
                return None

            # 日期元素
            date_el = page.query_selector('.post_date_li')
            date_text = date_el.inner_text() if date_el else ""
            date_match = re.search(r'(\d{2})-(\d{2})\s+(\d{2}):(\d{2})', date_text)
            if date_match:
                record_date = date(2026, int(date_match.group(1)), int(date_match.group(2)))
            else:
                record_date = date.today()

            # 产品名（从页面标题或元素）
            name_el = page.query_selector('.pricename a')
            if name_el:
                name = name_el.inner_text().strip()
            else:
                name_el2 = page.query_selector('.pricename')
                name = name_el2.inner_text().strip().split('\n')[0] if name_el2 else product_name

            # 从价格表格中提取 spec / brand / market
            spec = ''
            brand = ''
            market = ''
            table = page.query_selector('.price-newp table')
            if not table:
                table = page.query_selector('table.price-newp, table.rmbpj')
            if table:
                rows = table.query_selector_all('tr')
                for row in rows:
                    cells = row.query_selector_all('td')
                    if len(cells) >= 5:
                        cell_texts = [c.text_content().strip() for c in cells]
                        # 表头行跳过
                        if '商品名称' in cell_texts[0] or '规格' in cell_texts[1] if len(cell_texts) > 1 else False:
                            continue
                        # 数据行: 商品名称 | 基准规格 | 品牌 | 市场 | 价格 | 时间
                        if len(cell_texts) >= 5:
                            if cell_texts[0] and cell_texts[0] != product_name:
                                name = cell_texts[0]
                            spec = cell_texts[1] if len(cell_texts) > 1 else ''
                            brand = cell_texts[2] if len(cell_texts) > 2 else ''
                            market = cell_texts[3] if len(cell_texts) > 3 else ''

            # 智能分离 name 中的品牌和市场（部分页面把品牌/市场合并在名称列）
            # 常见格式: "产品名 品牌 市场" 或 "产品名 市场"（2-3个词）
            # 当 brand 和 market 已有值时不处理；只有 market 没有 brand 时，取倒数第二个
            if brand and market:
                pass  # 已有独立列，保持不变
            elif market and not brand:
                # 只有 market，尝试从 name 中提取 brand（name 可能是 "产品名 品牌"）
                name_parts = name.split()
                if len(name_parts) >= 2:
                    # 用 market 名称的最后2个字（去"省"/"市"后缀）与 name 最后一部分模糊匹配
                    market_stripped = market[:-1] if market.endswith(('省', '市')) else market
                    last_part = name_parts[-1]
                    last_stripped = last_part[:-1] if last_part.endswith(('省', '市')) else last_part
                    if market_stripped and (last_stripped in market or market in last_stripped or last_part == market_stripped):
                        brand = name_parts[-2] if len(name_parts) >= 2 else ''
                        name = ' '.join(name_parts[:-2]) if len(name_parts) > 2 else (name_parts[0] if name_parts else name)
                    elif len(name_parts) >= 2 and name_parts[-1] == market:
                        brand = name_parts[-2] if len(name_parts) >= 2 else ''
                        name = ' '.join(name_parts[:-2]) if len(name_parts) > 2 else (name_parts[0] if name_parts else name)
            elif brand and not market:
                # 只有 brand，尝试从 name 中提取 market（name 可能是 "产品名 市场"）
                name_parts = name.split()
                if len(name_parts) >= 2:
                    market = name_parts[-1]
                    name = ' '.join(name_parts[:-1])
            else:
                # 两项都为空，尝试从 name 中提取（格式: "产品名 品牌 市场" 或 "产品名 市场"）
                name_parts = name.split()
                if len(name_parts) >= 3:
                    market = name_parts[-1]
                    brand = name_parts[-2]
                    name = ' '.join(name_parts[:-2])
                elif len(name_parts) == 2:
                    # "产品名 市场"：后缀是省/市级别的认为是市场
                    if name_parts[1] in ('华东', '华北', '华南', '华中', '西南', '西北', '东北') or name_parts[1].endswith('省') or name_parts[1].endswith('市'):
                        market = name_parts[1]
                    else:
                        brand = name_parts[1]
                    name = name_parts[0]

            return {
                'product_name': name,
                'spec': spec,
                'brand': brand,
                'market': market,
                'price': price,
                'price_original': price_str,
                'record_date': record_date,
                'unit': '元/吨'
            }
        except Exception as e:
            print(f"    解析失败: {e}")
            return None

    # ------------------------------------------------------------------
    # 爬取 plist 页 → detailed_quotes
    # ------------------------------------------------------------------
    def scrape_plist(self, product: Product) -> List[Dict]:
        """爬取单个产品的 plist 页，提取所有报价行（最新一天）"""
        url = product.plist_url
        if not url:
            return []

        industry = product.industry or "化工"
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
            print(f"    ✗ 加载失败: {e}")
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

                parsed_date = self.parse_date(publish_date_str)
                if not parsed_date:
                    continue

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
    # 保存到数据库
    # ------------------------------------------------------------------
    def save_benchmark(self, data: Dict) -> int:
        """保存基准价到 benchmark_prices 表，同时写入 price_records 供 Dashboard 使用"""
        session = get_session()
        try:
            product_id = data['product_id']
            record_date = data['record_date']

            # 增量：已存在则跳过
            existing = session.query(BenchmarkPrice).filter(
                BenchmarkPrice.product_id == product_id,
                BenchmarkPrice.record_date == record_date
            ).first()
            if existing:
                print(f"    [skip] benchmark {data['product_name']} {record_date} 已存在")
                return 0

            bp = BenchmarkPrice(
                product_id=product_id,
                product_name=data.get('product_name', ''),
                spec=data.get('spec', ''),
                brand=data.get('brand', ''),
                market=data.get('market', ''),
                price=data['price'],
                unit=data.get('unit', '元/吨'),
                price_original=data.get('price_original', ''),
                source=self.SOURCE_KEY,
                record_date=record_date,
            )
            session.add(bp)

            # 同步写入 price_records 表，供 Dashboard 涨跌排行/历史走势使用
            existing_pr = session.query(PriceRecord).filter(
                PriceRecord.product_id == product_id,
                PriceRecord.record_date == record_date,
                PriceRecord.source == self.SOURCE_KEY
            ).first()
            if not existing_pr:
                pr = PriceRecord(
                    product_id=product_id,
                    price=data['price'],
                    unit=data.get('unit', '元/吨'),
                    currency='CNY',
                    price_type='基准价',
                    trend='平',
                    change_percent=0.0,
                    source=self.SOURCE_KEY,
                    region=data.get('market', ''),
                    brand=data.get('brand', ''),
                    specification=data.get('spec', ''),
                    extra_data={
                        'spec': data.get('spec', ''),
                        'brand': data.get('brand', ''),
                        'market': data.get('market', ''),
                    },
                    record_date=record_date,
                )
                session.add(pr)

            session.commit()
            return 1
        except Exception as e:
            session.rollback()
            print(f"    保存 benchmark 失败: {e}")
            return 0
        finally:
            session.close()

    def save_detailed_quotes(self, product_id: int, product_name: str, rows: List[Dict]) -> int:
        """保存详细报价到 detailed_quotes 表"""
        session = get_session()
        saved = 0
        try:
            for row in rows:
                # 增量：已存在则跳过
                existing = session.query(DetailedQuote).filter(
                    DetailedQuote.product_id == product_id,
                    DetailedQuote.publish_date == row['publish_date'],
                    DetailedQuote.region == row['region'],
                    DetailedQuote.supplier == row['supplier'],
                    DetailedQuote.price_type == row['price_type']
                ).first()
                if existing:
                    continue

                dq = DetailedQuote(
                    product_id=product_id,
                    product_name=row['product_name'],
                    spec=row['spec'],
                    brand=row['brand'],
                    price=row['price'],
                    unit='元/吨',
                    price_type=row['price_type'],
                    region=row['region'],
                    supplier=row['supplier'],
                    source=self.SOURCE_KEY,
                    publish_date=row['publish_date'],
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

    # ------------------------------------------------------------------
    # 主运行流程
    # ------------------------------------------------------------------
    def run(self, dry_run: bool = False):
        """增量爬取所有产品的最新一天数据"""
        products = self.get_all_products()
        if not products:
            print("没有找到产品，退出")
            return

        benchmark_total = 0
        quotes_total = 0

        # 第一步：爬取所有 detail 页 → benchmark_prices
        print(f"\n{'='*50}")
        print(f"第一步：爬取基准价（{len(products)} 个产品）")
        print(f"{'='*50}")
        for product in products:
            data = self.scrape_benchmark(product)
            if data and not dry_run:
                n = self.save_benchmark(data)
                benchmark_total += n
            elif dry_run:
                print(f"    [dry-run] would save benchmark for {product.product_name}")
            time.sleep(0.5)

        # 第二步：爬取所有 plist 页 → detailed_quotes
        print(f"\n{'='*50}")
        print(f"第二步：爬取详细报价（{len(products)} 个产品）")
        print(f"{'='*50}")
        for product in products:
            if not product.plist_url:
                print(f"  [skip] {product.product_name} 无 plist 页")
                continue
            rows = self.scrape_plist(product)
            if rows and not dry_run:
                n = self.save_detailed_quotes(product.id, product.product_name, rows)
                quotes_total += n
            elif dry_run:
                print(f"    [dry-run] would save {len(rows)} detailed quotes for {product.product_name}")
            time.sleep(0.5)

        print(f"\n{'='*50}")
        print(f"爬取完成！benchmark: {benchmark_total} 条, detailed_quotes: {quotes_total} 条")
        print(f"{'='*50}")

        self.log_run("success", benchmark_total + quotes_total)

    def log_run(self, status: str, items_scraped: int, error_message: str = None):
        session = get_session()
        try:
            log = ScraperLog(
                scraper_name=self.SOURCE_KEY,
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

    def run_historical(self, product_id: int, max_pages: int = 5, dry_run: bool = False):
        """历史数据回填（单独使用，后续写独立脚本）"""
        pass


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="生意社价格爬虫")
    parser.add_argument('--dry-run', action='store_true', help='仅模拟，不写入数据库')
    parser.add_argument('--historical', action='store_true', help='回填历史数据')
    parser.add_argument('--product-ids', type=int, nargs='+', help='指定产品ID')
    args = parser.parse_args()

    scraper = ShengyisheScraper()
    scraper.log_run("running", 0)

    try:
        if args.historical:
            print("历史数据回填请使用独立脚本（待开发）")
        else:
            scraper.run(dry_run=args.dry_run)
    except Exception as e:
        scraper.log_run("failed", 0, str(e))
        print(f"爬虫失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()