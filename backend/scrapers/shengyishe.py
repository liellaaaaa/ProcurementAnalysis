import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup
from backend.scrapers.base import BaseScraper, ScrapedItem
from backend.models.database import get_session, Product, PriceRecord, ScraperLog

class ShengyisheScraper(BaseScraper):
    """生意社爬虫 - www.100ppi.com"""

    BASE_URL = "https://www.100ppi.com"
    SOURCE_KEY = "shengyishe"
    CATEGORY_URLS = [
        "https://www.100ppi.com/chemical/",  # 化工类
    ]

    def __init__(self):
        super().__init__("shengyishe")
        self.session.headers.update({
            'Referer': self.BASE_URL,
        })

    def get_entry_urls(self) -> List[str]:
        return self.CATEGORY_URLS

    def parse_product_list(self, html: str) -> List[str]:
        """从分类页面解析产品链接"""
        soup = BeautifulSoup(html, 'lxml')
        product_urls = []

        # 根据实际页面结构调整选择器
        links = soup.select('.product-list a, .chem-list a, .item a, a[href*="/price/"]')
        for a in links:
            href = a.get('href', '')
            if href and '/price/' in href:
                if href.startswith('/'):
                    product_urls.append(self.BASE_URL + href)
                elif href.startswith('http'):
                    product_urls.append(href)

        return list(set(product_urls))[:50]  # 限制数量

    def parse_product_detail(self, html: str, url: str) -> Optional[ScrapedItem]:
        """解析产品详情页"""
        soup = BeautifulSoup(html, 'lxml')

        # 产品名称
        name_elem = soup.select_one('h1.title, .product-name, h1')
        product_name = name_elem.text.strip() if name_elem else ""

        # 价格
        price_elem = soup.select_one('.price-value, .current-price, #price')
        price_text = price_elem.text.strip() if price_elem else ""
        price = self._parse_price(price_text)

        # 趋势和涨跌幅
        trend = "平"
        change_percent = 0.0

        trend_elem = soup.select_one('.trend-up, .trend-down, .trend, .change')
        if trend_elem:
            trend_text = trend_elem.text.strip()
            if '涨' in trend_text or '↑' in trend_text:
                trend = "涨"
            elif '跌' in trend_text or '↓' in trend_text:
                trend = "跌"

            # 解析涨跌幅百分比
            import re
            match = re.search(r'([+-]?\d+\.?\d*)%', trend_text)
            if match:
                change_percent = float(match.group(1))

        return ScrapedItem(
            product_code=self._generate_code(product_name),
            product_name=product_name,
            price=price,
            price_type="市场价",
            trend=trend,
            change_percent=change_percent,
            record_date=datetime.now().strftime("%Y-%m-%d"),
            raw_data={'url': url}
        )

    def _parse_price(self, price_text: str) -> float:
        """从文本中提取价格"""
        import re
        match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if match:
            return float(match.group())
        return 0.0

    def _generate_code(self, name: str) -> str:
        """生成产品编码"""
        import hashlib
        return hashlib.md5(name.encode()).hexdigest()[:12].upper()

    def save_to_db(self, items: List[ScrapedItem]) -> int:
        """保存到数据库"""
        session = get_session()
        saved_count = 0

        for item in items:
            try:
                # 查找或创建产品
                product = session.query(Product).filter_by(product_code=item.product_code).first()
                if not product:
                    product = Product(
                        product_code=item.product_code,
                        product_name=item.product_name,
                        category="化工",
                        source=self.name,
                        source_url=item.raw_data.get('url')
                    )
                    session.add(product)
                    session.flush()

                # 创建价格记录
                from datetime import datetime as dt
                record = PriceRecord(
                    product_id=product.id,
                    price=item.price,
                    trend=item.trend,
                    change_percent=item.change_percent,
                    source=self.name,
                    record_date=dt.strptime(item.record_date, "%Y-%m-%d").date()
                )
                session.add(record)
                saved_count += 1
            except Exception as e:
                print(f"Error saving item: {e}")
                session.rollback()

        session.commit()
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