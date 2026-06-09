"""
生意社 detail 页爬虫 - 从 detail 页抓取基准价数据

运行方式:
  python -m backend.scrapers.detail_scraper
  python -m backend.scrapers.detail_scraper --dry-run
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
from backend.models.database import get_session, Product, BenchmarkPrice, ScraperLog

class DetailScraper:
    """生意社 detail 页爬虫"""

    SOURCE_KEY = "shengyishe"
    BASE_URL = "https://www.100ppi.com"

    # 涨跌状态映射（根据CSS类名或文本）
    TREND_UP = "涨"
    TREND_DOWN = "跌"
    TREND_FLAT = "平"

    def __init__(self):
        self._product_map: Dict[str, Product] = {}  # source_url -> Product

    # ------------------------------------------------------------------
    # 加载产品数据
    # ------------------------------------------------------------------
    def load_products(self) -> Dict[str, Product]:
        """从数据库加载产品，构建 source_url -> Product 映射"""
        session = get_session()
        try:
            products = session.query(Product).filter(
                Product.source_url.isnot(None),
                Product.is_active == True
            ).all()
            for p in products:
                self._product_map[p.source_url] = p
            print(f"从数据库加载了 {len(products)} 个产品")
            return self._product_map
        finally:
            session.close()

    def load_urls_from_json(self, json_path: str) -> List[Dict]:
        """从 category_urls.json 加载 URL 列表"""
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

    def parse_change_percent(self, text: str) -> Optional[float]:
        """从涨跌文本提取涨跌幅百分比"""
        if not text:
            return None
        # 匹配 "+2.5%" 或 "-1.2%" 或 "2.5%" 等
        match = re.search(r'([+-]?\d+\.?\d*)%', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def determine_trend(self, text: str) -> str:
        """根据文本判断涨跌状态"""
        if not text:
            return self.TREND_FLAT
        text = text.lower()
        if '涨' in text or 'up' in text or 'rise' in text or '+' in text:
            return self.TREND_UP
        elif '跌' in text or 'down' in text or 'fall' in text or '-' in text:
            return self.TREND_DOWN
        return self.TREND_FLAT

    # ------------------------------------------------------------------
    # 页面解析
    # ------------------------------------------------------------------
    def scrape_detail_page(self, product: Product) -> Optional[Dict]:
        """爬取单个产品的 detail 页"""
        url = product.source_url
        if not url:
            return None

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

                    data = self._parse_benchmark_page(page, product)
                    return data
                finally:
                    browser.close()
        except Exception as e:
            print(f"    [FAIL] loading: {e}")
            return None

    def _parse_benchmark_page(self, page, product: Product) -> Optional[Dict]:
        """解析 detail 页，提取基准价数据"""
        try:
            # 价格元素
            price_el = page.query_selector('.price-fb01_1')
            price_str = price_el.inner_text() if price_el else ""
            price = self.parse_price(price_str)
            if price is None or price <= 0:
                print(f"    [FAIL] price parse: {price_str}")
                return None

            # 涨跌状态和涨跌幅
            trend = self.TREND_FLAT
            change_percent = None
            change_reason = ""

            # 尝试从价格元素附近的兄弟元素或父元素获取涨跌信息
            body_text = page.evaluate('document.body.innerText')

            if price_el:
                parent = price_el.evaluate_handle('el => el.parentElement')
                if parent:
                    parent_text = parent.inner_text() if parent else ""
                    if '↑' in parent_text or '▲' in parent_text:
                        trend = self.TREND_UP
                    elif '↓' in parent_text or '▼' in parent_text:
                        trend = self.TREND_DOWN

                change_el = page.query_selector('.change-percent, .price-change, .trend')
                if change_el:
                    change_text = change_el.inner_text()
                    change_percent = self.parse_change_percent(change_text)

            # 如果没找到change_percent，尝试从页面其他位置获取
            if change_percent is None:
                body_text = page.evaluate('document.body.innerText')
                match = re.search(r'涨跌幅[：:]\s*([+-]?\d+\.?\d*)%', body_text)
                if match:
                    change_percent = float(match.group(1))
                else:
                    match = re.search(r'([+-]?\d+\.?\d*)%\s*$', body_text.split('\n')[0])
                    if match:
                        change_percent = float(match.group(1))

            # 涨跌原因
            reason_el = page.query_selector('.change-reason, .price-reason, .trend-reason')
            if reason_el:
                change_reason = reason_el.inner_text().strip()
            else:
                reason_match = re.search(r'原因[：:]\s*([^\n]+)', body_text)
                if reason_match:
                    change_reason = reason_match.group(1).strip()

            # 日期
            date_el = page.query_selector('.post_date_li')
            date_text = date_el.inner_text() if date_el else ""
            date_match = re.search(r'(\d{2})-(\d{2})\s+(\d{2}):(\d{2})', date_text)
            if date_match:
                record_date = date(date.today().year, int(date_match.group(1)), int(date_match.group(2)))
            else:
                # 解析失败时使用当天日期
                record_date = date.today()

            # 产品名固定使用数据库的产品名
            name = product.product_name

            # 从价格表格提取规格/品牌/市场
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
                        if '商品名称' in cell_texts[0] or '规格' in cell_texts[1] if len(cell_texts) > 1 else False:
                            continue
                        if len(cell_texts) >= 5:
                            # 只从表格提取规格、品牌、市场，不覆盖产品名
                            spec = cell_texts[1] if len(cell_texts) > 1 else ''
                            brand = cell_texts[2] if len(cell_texts) > 2 else ''
                            market = cell_texts[3] if len(cell_texts) > 3 else ''

            # 产品名固定使用数据库的产品名，不从页面提取
            name = product.product_name

            result = {
                'product_id': product.id,
                'product_name': name,
                'spec': spec,
                'brand': brand,
                'market': market,
                'price': price,
                'unit': '元/吨',
                'price_original': price_str,
                'trend': trend,
                'change_percent': change_percent,
                'change_reason': change_reason,
                'source': self.SOURCE_KEY,
                'record_date': record_date,
            }

            print(f"    → price={price} trend={trend} change={change_percent}%")
            return result

        except Exception as e:
            print(f"    [FAIL] parse error: {e}")
            return None

    # ------------------------------------------------------------------
    # 数据库操作
    # ------------------------------------------------------------------
    def save_benchmark(self, data: Dict) -> int:
        """保存基准价到数据库（增量：已存在则跳过）"""
        session = get_session()
        try:
            product_id = data['product_id']
            record_date = data['record_date']

            existing = session.query(BenchmarkPrice).filter(
                BenchmarkPrice.product_id == product_id,
                BenchmarkPrice.record_date == record_date
            ).first()
            if existing:
                print(f"    [skip] benchmark {data['product_name']} {record_date} 已存在")
                return 0

            bp = BenchmarkPrice(
                product_id=product_id,
                spec=data.get('spec', ''),
                brand=data.get('brand', ''),
                market=data.get('market', ''),
                price=data['price'],
                unit=data.get('unit', '元/吨'),
                price_original=data.get('price_original', ''),
                trend=data.get('trend', '平'),
                change_percent=data.get('change_percent'),
                change_reason=data.get('change_reason', ''),
                source=data.get('source', self.SOURCE_KEY),
                record_date=record_date,
            )
            session.add(bp)
            session.commit()
            return 1
        except Exception as e:
            session.rollback()
            print(f"    保存失败: {e}")
            return 0
        finally:
            session.close()

    def log_run(self, status: str, items_scraped: int, error_message: str = None):
        session = get_session()
        try:
            log = ScraperLog(
                scraper_name=f"{self.SOURCE_KEY}_benchmark",
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
                '..', 'category_urls.json'
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
            industry = item.get('category', '化工')

            product = self._product_map.get(url)
            if not product:
                print(f"  [skip] {name} 未在数据库中找到对应产品")
                continue

            data = self.scrape_detail_page(product)
            if data:
                if not dry_run:
                    n = self.save_benchmark(data)
                    total_saved += n
                else:
                    print(f"    [dry-run] would save benchmark for {name}")
            else:
                total_failed += 1

            time.sleep(0.5)

        print(f"\n{'='*50}")
        print(f"基准价爬取完成！成功: {total_saved}, 失败: {total_failed}")
        print(f"{'='*50}")

        self.log_run("success" if total_failed == 0 else "partial",
                    total_saved,
                    f"failed: {total_failed}" if total_failed > 0 else None)


def main():
    parser = argparse.ArgumentParser(description="生意社 detail 页爬虫")
    parser.add_argument('--json-path', help='category_urls.json 路径')
    parser.add_argument('--dry-run', action='store_true', help='仅模拟，不写入数据库')
    args = parser.parse_args()

    scraper = DetailScraper()
    scraper.log_run("running", 0)

    try:
        scraper.run(json_path=args.json_path, dry_run=args.dry_run)
    except Exception as e:
        scraper.log_run("failed", 0, str(e))
        print(f"爬虫失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()