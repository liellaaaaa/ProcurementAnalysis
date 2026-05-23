"""
生意社历史数据快速回填脚本
- 使用 asyncio + aiohttp 并发请求（静态页面不需要 Playwright）
- 静态列表页：直接请求 HTML 解析，不需要 JS 渲染
- 全量并发，90天数据一次性回填
"""
import asyncio
import aiohttp
import re
import sys
import argparse
import time
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin

import lxml.html
from backend.models.database import get_session, Product, PriceRecord, ScraperLog
import sqlalchemy as sa


BASE_URL = "https://www.100ppi.com"
SOURCE_KEY = "shengyishe"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}
TIMEOUT = aiohttp.ClientTimeout(total=30)


def parse_price(price_str: str) -> Optional[float]:
    if not price_str:
        return None
    match = re.search(r'([\d,]+\.?\d*)', price_str.replace(',', ''))
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def parse_historical_date(date_str: str) -> Optional[str]:
    """解析历史价格日期字符串，返回 YYYY-MM-DD"""
    if not date_str:
        return None
    date_str = date_str.strip()
    # YYYY-MM-DD
    m = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
    if m:
        return f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
    # YYYY/MM/DD
    m = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', date_str)
    if m:
        return f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
    # MM-DD（补充当前年份）
    m = re.search(r'(\d{1,2})-(\d{1,2})', date_str)
    if m:
        year = datetime.now().year
        return f"{year}-{m.group(1).zfill(2)}-{m.group(2).zfill(2)}"
    return None


def parse_list_page(html: str, industry: str) -> List[Dict]:
    """解析列表页 HTML，返回所有报价行"""
    results = []
    try:
        tree = lxml.html.fromstring(html)
        table = tree.cssselect('table.lp-table.mb15')
        if not table:
            table = tree.cssselect('table.lp-table')
        if not table:
            return results

        rows = table[0].cssselect('tr')
        for row in rows:
            cells = row.cssselect('td')
            if len(cells) < 8:
                continue

            product_name = (cells[0].text_content() or '').strip()
            if not product_name or product_name == '商品名称':
                continue

            spec_text = (cells[1].text_content() or '').strip()
            brand = (cells[2].text_content() or '').strip()
            price_str = (cells[3].text_content() or '').strip()
            price_type = (cells[4].text_content() or '').strip()
            region = (cells[5].text_content() or '').strip()
            supplier = (cells[6].text_content() or '').strip()
            publish_date = (cells[7].text_content() or '').strip()

            price = parse_price(price_str)
            if price is None or price <= 0:
                continue

            results.append({
                'product_name': product_name,
                'spec_raw': spec_text,
                'brand': brand,
                'price': price,
                'price_str': price_str,
                'price_type': price_type,
                'region': region,
                'supplier': supplier,
                'publish_date': publish_date,
                'industry': industry,
            })
    except Exception as e:
        print(f"    解析页面失败: {e}")
    return results


def group_by_date_and_calculate_benchmark(rows: List[Dict]) -> List[Dict]:
    """按日期分组，计算每日的基准价（按产品分组）"""
    by_date = defaultdict(list)
    for row in rows:
        by_date[row['publish_date']].append(row)

    results = []
    for date, day_rows in by_date.items():
        by_product = defaultdict(list)
        for row in day_rows:
            by_product[row['product_name']].append(row)

        for product_name, product_rows in by_product.items():
            prices = [r['price'] for r in product_rows]
            benchmark = sum(prices) / len(prices) if prices else 0

            results.append({
                'date': date,
                'product_name': product_name,
                'benchmark': round(benchmark, 2),
                'quote_count': len(product_rows),
                'details': product_rows,
                'price_type': product_rows[0]['price_type'],
            })
    return results


class FastBackfillScraper:
    """快速历史回填爬虫 - asyncio 并发"""

    def __init__(self, max_concurrency: int = 20):
        self.max_concurrency = max_concurrency
        self.semaphore = None
        self.session = None
        self._product_industry_map = {}

    async def fetch_page(self, url: str, industry: str) -> Tuple[str, str, List[Dict]]:
        """并发抓取单个页面，返回 (url, industry, rows)"""
        async with self.semaphore:
            try:
                async with self.session.get(url, headers=HEADERS, timeout=TIMEOUT) as resp:
                    if resp.status != 200:
                        return (url, industry, [])
                    html = await resp.text()
                    rows = parse_list_page(html, industry)
                    return (url, industry, rows)
            except Exception as e:
                return (url, industry, [])

    async def scrape_product_pages(self, product: Product, max_pages: int) -> List[Dict]:
        """并发抓取单个产品的所有历史页面"""
        base_url = product.source_url
        industry = product.industry or "化工"

        # 构建所有页面 URL
        page_urls = [base_url]
        match = re.search(r'(plist-\d+-\d+-)(\d+)(\.html)', base_url)
        if match:
            for page_num in range(2, max_pages + 1):
                page_url = re.sub(
                    r'(plist-\d+-\d+-)(\d+)(\.html)',
                    lambda m: f"{m.group(1)}{page_num}{m.group(3)}",
                    base_url
                )
                page_urls.append(page_url)

        # 并发抓取所有页面
        tasks = [self.fetch_page(url, industry) for url in page_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_rows = []
        for result in results:
            if isinstance(result, Exception):
                continue
            url, ind, rows = result
            all_rows.extend(rows)

        if not all_rows:
            return []

        # 按日期+产品分组计算基准价
        grouped = group_by_date_and_calculate_benchmark(all_rows)

        items = []
        unit = '元/吨' if industry in ['化工', '农副'] else ('元/立方米' if industry == '能源' else '元/克')
        for g in grouped:
            items.append({
                'date': g['date'],
                'product_name': g['product_name'],
                'price': g['benchmark'],
                'price_str': f"{g['benchmark']}元/吨",
                'price_type': g['price_type'],
                'industry': industry,
                'unit': unit,
                'source_url': base_url,
            })
        return items

    def save_records(self, product_id: int, records: List[Dict]) -> int:
        """批量保存历史记录"""
        if not records:
            return 0

        session = get_session()
        saved_count = 0

        try:
            for record in records:
                date_str = record.get('date', '')
                if not date_str:
                    continue

                record_date = None
                for fmt in ["%Y-%m-%d", "%m/%d", "%Y/%m/%d"]:
                    try:
                        record_date = datetime.strptime(date_str, fmt).date()
                        break
                    except:
                        continue

                if not record_date:
                    continue

                # 检查是否已存在
                existing = session.query(PriceRecord).filter(
                    PriceRecord.product_id == product_id,
                    PriceRecord.record_date == record_date,
                    PriceRecord.source == SOURCE_KEY
                ).first()

                if existing:
                    existing.price = record['price']
                    # 计算涨跌幅
                    prev_record = session.query(PriceRecord).filter(
                        PriceRecord.product_id == product_id,
                        PriceRecord.record_date < record_date,
                        PriceRecord.source == SOURCE_KEY
                    ).order_by(PriceRecord.record_date.desc()).first()
                    if prev_record and prev_record.price > 0:
                        change_pct = round(((record['price'] - prev_record.price) / prev_record.price) * 100, 2)
                        existing.change_percent = change_pct
                        existing.trend = "涨" if change_pct > 0 else "跌" if change_pct < 0 else "平"
                else:
                    # 查上一条计算涨跌幅
                    prev_record = session.query(PriceRecord).filter(
                        PriceRecord.product_id == product_id,
                        PriceRecord.record_date < record_date,
                        PriceRecord.source == SOURCE_KEY
                    ).order_by(PriceRecord.record_date.desc()).first()

                    if prev_record and prev_record.price > 0:
                        change_pct = round(((record['price'] - prev_record.price) / prev_record.price) * 100, 2)
                        trend = "涨" if change_pct > 0 else "跌" if change_pct < 0 else "平"
                    else:
                        change_pct = 0.0
                        trend = "平"

                    price_record = PriceRecord(
                        product_id=product_id,
                        price=record['price'],
                        unit=record.get('unit', '元/吨'),
                        price_original=record.get('price_str', ''),
                        price_category='现货',
                        price_type=record.get('price_type', '市场价'),
                        trend=trend,
                        change_percent=change_pct,
                        source=SOURCE_KEY,
                        region='',
                        supplier='',
                        brand='',
                        specification='',
                        extra_data={'报价类型': record.get('price_type', '市场价')},
                        record_date=record_date
                    )
                    session.add(price_record)
                saved_count += 1

            session.commit()
        except Exception as e:
            print(f"    数据库保存失败: {e}")
            session.rollback()
        finally:
            session.close()

        return saved_count

    async def run(self, product_ids: List[int] = None, days: int = 90, dry_run: bool = False):
        """主入口"""
        session = get_session()
        try:
            if product_ids:
                products = session.query(Product).filter(
                    Product.id.in_(product_ids),
                    Product.is_active == True,
                    Product.source_url.isnot(None)
                ).all()
            else:
                products = session.query(Product).filter(
                    Product.source == SOURCE_KEY,
                    Product.is_active == True,
                    Product.source_url.isnot(None)
                ).all()
        finally:
            session.close()

        if not products:
            print("没有找到待回填的产品")
            return

        max_pages = max(1, days // 2)
        print(f"\n{'='*60}")
        print(f"快速历史数据回填（asyncio 并发）")
        print(f"{'='*60}")
        print(f"产品数: {len(products)}")
        print(f"回填天数: {days}（翻 {max_pages} 页）")
        print(f"并发数: {self.max_concurrency}")
        print(f"模式: {'模拟运行' if dry_run else '实际回填'}")
        print(f"{'='*60}\n")

        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        self.session = aiohttp.ClientSession(headers=HEADERS)

        total_saved = 0
        total_failed = 0
        done = 0

        start_time = time.time()

        for product in products:
            done += 1
            elapsed = time.time() - start_time
            speed = done / elapsed if elapsed > 0 else 0
            eta = (len(products) - done) / speed if speed > 0 else 0

            print(f"[{done}/{len(products)}] {product.product_name} ({product.industry}) ", end='', flush=True)

            try:
                items = await self.scrape_product_pages(product, max_pages=max_pages)

                if not items:
                    print("无数据")
                    continue

                if dry_run:
                    print(f"模拟: 可保存 {len(items)} 条")
                    total_saved += len(items)
                else:
                    saved = self.save_records(product.id, items)
                    print(f"已保存 {saved} 条")
                    total_saved += saved

            except Exception as e:
                print(f"失败: {e}")
                total_failed += 1

            # 小延迟避免对服务器压力太大
            await asyncio.sleep(0.2)

        await self.session.close()

        elapsed = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"回填完成")
        print(f"{'='*60}")
        print(f"耗时: {elapsed:.1f}s")
        print(f"总记录: {total_saved} 条")
        print(f"失败产品: {total_failed} 个")
        print(f"平均速度: {total_saved / elapsed:.1f} 条/秒")


async def main():
    parser = argparse.ArgumentParser(description="生意社历史数据快速回填")
    parser.add_argument('--days', type=int, default=90, help='回填天数')
    parser.add_argument('--product-ids', type=int, nargs='+', help='指定产品ID')
    parser.add_argument('--dry-run', action='store_true', help='仅模拟不写入')
    parser.add_argument('--concurrency', type=int, default=20, help='并发数')
    parser.add_argument('--industry', type=str, choices=['化工', '农副', '能源'], help='只回填指定行业')
    args = parser.parse_args()

    scraper = FastBackfillScraper(max_concurrency=args.concurrency)

    await scraper.run(
        product_ids=args.product_ids,
        days=args.days,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    asyncio.run(main())