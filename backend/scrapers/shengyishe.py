import re
from datetime import datetime
from typing import List, Dict, Optional

from playwright.sync_api import sync_playwright

from backend.scrapers.base import BaseScraper, ScrapedItem
from backend.models.database import get_session, Product, PriceRecord, ScraperLog
from backend.services.alert_service import check_and_trigger_alerts


class ShengyisheScraper(BaseScraper):
    """生意社化工价格爬虫 - 使用 Playwright 绕过反爬"""

    BASE_URL = "https://www.100ppi.com"
    LIST_URL = "https://www.100ppi.com/mprice/mlist-1-14-{}.html"
    SOURCE_KEY = "shengyishe"
    PAGES_TO_SCRAPE = 10

    def __init__(self, name: str = "shengyishe"):
        super().__init__(name)

    def get_entry_urls(self) -> List[str]:
        return [self.LIST_URL.format(i) for i in range(1, self.PAGES_TO_SCRAPE + 1)]

    def parse_price(self, price_str: str) -> Optional[float]:
        """解析价格字符串，提取数值"""
        if not price_str:
            return None
        match = re.search(r'([\d,]+\.?\d*)', price_str.replace(',', ''))
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def _generate_code(self, name: str, specification: str = None) -> str:
        """生成产品编码"""
        import hashlib
        raw = f"{name}|{specification or ''}"
        return hashlib.md5(raw.encode()).hexdigest()[:12].upper()

    def scrape_page(self, page_num: int = 1) -> List[Dict]:
        """同步爬取单页数据"""
        url = self.LIST_URL.format(page_num)
        print(f"  正在爬取: {url}")

        results = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()

            try:
                page.goto(url, timeout=60000, wait_until='networkidle')
                page.wait_for_timeout(1000)

                rows = page.query_selector_all('table tr')

                for row in rows:
                    try:
                        cells = row.query_selector_all('td')
                        if len(cells) < 5:
                            continue

                        name_cell = cells[0]
                        name = name_cell.text_content()
                        name = name.strip() if name else None

                        if not name or name == '商品名称':
                            continue

                        link = name_cell.query_selector('a')
                        href = link.get_attribute('href') if link else None
                        detail_url = self.BASE_URL + href if href else None

                        spec_cell = cells[1] if len(cells) > 1 else None
                        specification = spec_cell.text_content() if spec_cell else None
                        specification = specification.strip() if specification else None

                        brand_cell = cells[2] if len(cells) > 2 else None
                        brand = brand_cell.text_content() if brand_cell else None
                        brand = brand.strip() if brand else None

                        price_cell = cells[3] if len(cells) > 3 else None
                        price_str = price_cell.text_content() if price_cell else None
                        price = self.parse_price(price_str)

                        if price is None or price <= 0:
                            continue

                        type_cell = cells[4] if len(cells) > 4 else None
                        price_type = type_cell.text_content() if type_cell else None
                        price_type = price_type.strip() if price_type else '市场价'

                        region_cell = cells[5] if len(cells) > 5 else None
                        region = region_cell.text_content() if region_cell else None
                        region = region.strip() if region else None

                        supplier_cell = cells[6] if len(cells) > 6 else None
                        supplier = supplier_cell.text_content() if supplier_cell else None
                        supplier = supplier.strip() if supplier else None

                        date_cell = cells[7] if len(cells) > 7 else None
                        date_str = date_cell.text_content() if date_cell else None
                        date_str = date_str.strip() if date_str else None

                        results.append({
                            'name': name,
                            'specification': specification,
                            'brand': brand,
                            'price': price,
                            'price_type': price_type,
                            'region': region,
                            'supplier': supplier,
                            'date': date_str,
                            'source_url': detail_url
                        })

                    except Exception as e:
                        continue

            except Exception as e:
                print(f"  页面加载失败: {e}")
            finally:
                browser.close()

        print(f"  获取到 {len(results)} 条数据")
        return results

    def run(self) -> List[ScrapedItem]:
        """执行爬取流程"""
        all_results = []
        seen = set()

        for page in range(1, self.PAGES_TO_SCRAPE + 1):
            items = self.scrape_page(page)
            for item in items:
                key = f"{item['name']}|{item['specification']}|{item['supplier']}|{item['date']}"
                if key not in seen:
                    seen.add(key)
                    all_results.append(self._dict_to_scraped_item(item))

        print(f"\n生意社爬取完成，共获取 {len(all_results)} 条去重后数据")
        return all_results

    def _dict_to_scraped_item(self, data: Dict) -> ScrapedItem:
        """将字典转换为 ScrapedItem"""
        name = data['name']
        specification = data.get('specification', '')
        code = self._generate_code(name, specification)

        return ScrapedItem(
            product_code=code,
            product_name=name,
            price=data['price'],
            price_type=data.get('price_type', '市场价'),
            trend="平",
            change_percent=0.0,
            record_date=data['date'] or datetime.now().strftime("%Y-%m-%d"),
            raw_data=data
        )

    def parse_product_list(self, html: str) -> List[str]:
        return self.get_entry_urls()

    def parse_product_detail(self, html: str, url: str) -> Optional[ScrapedItem]:
        return None

    def save_to_db(self, items: List[ScrapedItem]) -> int:
        """保存到数据库（支持同产品同日期不同地区/供应商的重复数据）"""
        session = get_session()
        saved_count = 0

        for item in items:
            try:
                product = session.query(Product).filter_by(product_code=item.product_code).first()
                if not product:
                    product = Product(
                        product_code=item.product_code,
                        product_name=item.product_name,
                        category="化工",
                        unit="元/吨",
                        source=self.name,
                        source_url=item.raw_data.get('source_url')
                    )
                    session.add(product)
                    session.flush()

                from datetime import datetime as dt
                record_date = dt.strptime(item.record_date, "%Y-%m-%d").date()

                # 计算涨跌幅：对比该产品昨日收盘价
                prev_record = session.query(PriceRecord).filter(
                    PriceRecord.product_id == product.id,
                    PriceRecord.record_date < record_date
                ).order_by(PriceRecord.record_date.desc()).first()

                if prev_record and prev_record.price > 0:
                    change_percent = round(((item.price - prev_record.price) / prev_record.price) * 100, 2)
                    trend = "涨" if change_percent > 0 else "跌" if change_percent < 0 else "平"
                else:
                    change_percent = 0.0
                    trend = "平"

                # 检查是否已存在相同 product_id + record_date + source + region + supplier 的记录
                region_val = item.raw_data.get('region')
                supplier_val = item.raw_data.get('supplier')
                existing = session.query(PriceRecord).filter(
                    PriceRecord.product_id == product.id,
                    PriceRecord.record_date == record_date,
                    PriceRecord.source == self.name,
                    PriceRecord.region == region_val,
                    PriceRecord.supplier == supplier_val
                ).first()

                if existing:
                    # 更新已有记录
                    existing.price = item.price
                    existing.price_type = item.price_type or "市场价"
                    existing.trend = trend
                    existing.change_percent = change_percent
                    existing.brand = item.raw_data.get('brand')
                    existing.specification = item.raw_data.get('specification')
                else:
                    record = PriceRecord(
                        product_id=product.id,
                        price=item.price,
                        price_type=item.price_type or "市场价",
                        trend=trend,
                        change_percent=change_percent,
                        source=self.name,
                        region=region_val,
                        supplier=supplier_val,
                        brand=item.raw_data.get('brand'),
                        specification=item.raw_data.get('specification'),
                        record_date=record_date
                    )
                    session.add(record)
                saved_count += 1
            except Exception as e:
                print(f"Error saving item: {e}")
                session.rollback()

        session.commit()

        # 检查预警触发（针对每个保存的产品）
        for item in items:
            product = session.query(Product).filter_by(product_code=item.product_code).first()
            if product:
                check_and_trigger_alerts(session, product.id, item.price)

        session.close()
        return saved_count

    def log_scraper_run(self, status: str, items_scraped: int, error_message: str = None):
        """记录爬虫运行日志"""
        session = get_session()
        log = ScraperLog(
            scraper_name=self.name,
            status=status,
            items_scraped=items_scraped,
            error_message=error_message,
            started_at=datetime.now(),
            completed_at=datetime.now()
        )
        session.add(log)
        session.commit()
        session.close()


def run_scraper():
    """运行爬虫"""
    scraper = ShengyisheScraper()
    scraper.log_scraper_run("running", 0)

    try:
        items = scraper.run()
        saved = scraper.save_to_db(items)
        scraper.log_scraper_run("success", saved)
        print(f"Scraped {len(items)} items, saved {saved} to database.")
    except Exception as e:
        scraper.log_scraper_run("failed", 0, str(e))
        print(f"Scraper failed: {e}")


if __name__ == "__main__":
    run_scraper()