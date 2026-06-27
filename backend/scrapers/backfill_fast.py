"""
生意社历史数据快速回填脚本
- 使用 Playwright 绕过 Cloudflare 反爬
- 支持两种页面格式：
  1. 详细报价页面 (rawmex/detail-*.html) - 基准价
  2. mprice/plist-*.html - 多产品详细报价

用法:
  python -m backend.scrapers.backfill_fast --mode detail --urls-file category_urls.json
  python -m backend.scrapers.backfill_fast --mode mprice --urls-file category_urls_mprice.json
  python -m backend.scrapers.backfill_fast --mode both
"""
import re
import sys
import argparse
import time
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional

from playwright.sync_api import sync_playwright

from backend.scrapers.base import (
    parse_price, parse_date, new_page, make_playwright_context,
    save_benchmark_records_batch, save_detailed_quotes_batch,
)
from backend.scrapers.shengyishe import _parse_plist_table
from backend.models.database import get_session, Product


SOURCE_KEY = "shengyishe"


# ---------------------------------------------------------------------------
# 图表 iframe 历史数据提取
# ---------------------------------------------------------------------------

def parse_benchmark_history_from_chart(page) -> List[Dict]:
    """从图表 iframe 页面提取历史基准价数据"""
    try:
        chart_option = page.evaluate("""
            () => {
                if (window.myChart && typeof window.myChart.getOption === 'function') {
                    return window.myChart.getOption();
                }
                const container = document.querySelector('#container');
                if (container && container.__echarts__) {
                    return container.__echarts__.getOption();
                }
                for (let key in window) {
                    const val = window[key];
                    if (val && typeof val.getOption === 'function' && key.includes('Chart')) {
                        return val.getOption();
                    }
                }
                return null;
            }
        """)

        if not chart_option:
            return []

        x_axis_data = chart_option.get('xAxis', [{}])[0].get('data', [])
        series_data = chart_option.get('series', [{}])[0].get('data', [])

        if not x_axis_data or not series_data:
            return []

        results = []
        for date_str, price in zip(x_axis_data, series_data):
            if date_str and price is not None:
                try:
                    parsed_date = datetime.strptime(str(date_str), '%Y-%m-%d').date()
                    results.append({
                        'date': parsed_date,
                        'price': float(price),
                    })
                except (ValueError, TypeError):
                    continue

        return results
    except Exception as e:
        print(f"    解析图表数据失败: {e}")
        return []


# ---------------------------------------------------------------------------
# 解析 detail 页（基准价）
# ---------------------------------------------------------------------------

def parse_detail_page(page, product_name: str, industry: str) -> List[Dict]:
    """解析 detail 页，提取基准价历史数据"""
    results = []

    try:
        price_el = page.query_selector('.price-fb01_1')
        price = None
        if price_el:
            price_str = price_el.inner_text()
            price = parse_price(price_str)

        date_el = page.query_selector('.post_date_li')
        record_date = date.today()
        if date_el:
            date_text = date_el.inner_text()
            date_match = re.search(r'(\d{2})-(\d{2})\s+(\d{2}):(\d{2})', date_text)
            if date_match:
                record_date = date(date.today().year, int(date_match.group(1)), int(date_match.group(2)))

        table = page.query_selector('.price-newp table') or page.query_selector('table.price-newp, table.rmbpj')
        spec, brand, market = '', '', ''
        if table:
            rows = table.query_selector_all('tr')
            for row in rows:
                cells = row.query_selector_all('td')
                if len(cells) >= 5:
                    cell_texts = [c.text_content().strip() for c in cells]
                    if '商品名称' in cell_texts[0]:
                        continue
                    if len(cell_texts) >= 5 and cell_texts[0]:
                        spec = cell_texts[1] if len(cell_texts) > 1 else ''
                        brand = cell_texts[2] if len(cell_texts) > 2 else ''
                        market = cell_texts[3] if len(cell_texts) > 3 else ''
                        break

        if price and price > 0:
            results.append({
                'date': record_date,
                'price': price,
                'price_str': f"{price}元/吨",
                'price_type': '基准价',
                'industry': industry,
                'product_name': product_name,
                'spec': spec,
                'brand': brand,
                'market': market,
            })

    except Exception as e:
        print(f"    解析 detail 页失败: {e}")

    return results


# ---------------------------------------------------------------------------
# URL 构建
# ---------------------------------------------------------------------------

def build_chart_iframe_url(detail_url: str) -> str:
    """从 detail 页 URL 构建图表 iframe URL"""
    match = re.search(r'detail-(\d+)\.html', detail_url)
    if match:
        ppid = match.group(1)
        return f"https://www.100ppi.com/graph/cindex.php?f=graph_ppid_ave&ppid={ppid}"
    return None


# ---------------------------------------------------------------------------
# 爬取基准价（detail 页 + 图表历史）
# ---------------------------------------------------------------------------

def scrape_benchmark_page(url: str, product_name: str, industry: str, browser=None) -> List[Dict]:
    """使用 Playwright 抓取 detail 页及历史图表数据"""
    results = []
    own_browser = browser is None
    if own_browser:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
    try:
        context = make_playwright_context(browser)
        page = context.new_page()
        try:
            page.goto(url, timeout=30000, wait_until='networkidle')
            page.wait_for_timeout(1500)
            results = parse_detail_page(page, product_name, industry)

            chart_url = build_chart_iframe_url(url)
            if chart_url:
                chart_page = context.new_page()
                try:
                    chart_page.goto(chart_url, timeout=30000, wait_until='networkidle')
                    chart_page.wait_for_timeout(2000)
                    history_records = parse_benchmark_history_from_chart(chart_page)
                    if history_records:
                        print(f"      历史图表数据: {len(history_records)} 条")
                        for record in history_records:
                            record['product_name'] = product_name
                            record['industry'] = industry
                            record['price_str'] = f"{record['price']}元/吨"
                            record['price_type'] = '基准价'
                        results.extend(history_records)
                except Exception as e:
                    print(f"      图表页面加载失败: {e}")
                finally:
                    chart_page.close()
        finally:
            page.close()
            if own_browser:
                browser.close()
    except Exception as e:
        print(f"    Playwright 失败: {e}")
    return results


# ---------------------------------------------------------------------------
# 爬取详细报价（plist 页 + 多页）
# ---------------------------------------------------------------------------

def scrape_plist_pages(base_url: str, product_name: str, industry: str, max_pages: int = 10, browser=None) -> List[Dict]:
    """使用 Playwright 抓取 plist 页（多页历史）"""
    all_rows = []
    own_browser = browser is None

    page_urls = [base_url]
    match = re.search(r'(plist-\d+-\d+-)(\d+)(\.html)', base_url)
    if match:
        for page_num in range(2, max_pages + 1):
            page_urls.append(re.sub(
                r'(plist-\d+-\d+-)(\d+)(\.html)',
                lambda m: f"{m.group(1)}{page_num}{m.group(3)}",
                base_url
            ))

    if own_browser:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
    try:
        context = make_playwright_context(browser)
        page = context.new_page()

        for idx, page_url in enumerate(page_urls):
            try:
                page.goto(page_url, timeout=30000, wait_until='networkidle')
                page.wait_for_timeout(1000)
                rows = _parse_plist_table(page)
                all_rows.extend(rows)
                print(f"      第 {idx + 1} 页: {len(rows)} 条")
            except Exception as e:
                print(f"      页面 {page_url} 失败: {e}")
                continue

        page.close()
        if own_browser:
            browser.close()
    except Exception as e:
        print(f"    Playwright plist 失败: {e}")

    return all_rows


# ---------------------------------------------------------------------------
# 获取或创建产品
# ---------------------------------------------------------------------------

def get_or_create_product(product_name: str, industry: str, source_url: str, plist_url: str = None) -> Optional[int]:
    """返回 product_id，不返回 detached 对象"""
    session = get_session()
    try:
        product = session.query(Product).filter(
            Product.product_name == product_name,
            Product.source == SOURCE_KEY,
        ).first()

        if not product:
            product = Product(
                product_name=product_name,
                industry=industry,
                source=SOURCE_KEY,
                source_url=source_url,
                plist_url=plist_url,
                unit='元/吨',
                is_active=True,
            )
            session.add(product)
            session.commit()
            pid = product.id
        else:
            if source_url:
                product.source_url = source_url
            if plist_url:
                product.plist_url = plist_url
            session.commit()
            pid = product.id

        return pid
    except Exception as e:
        session.rollback()
        return None
    finally:
        session.close()


# ---------------------------------------------------------------------------
# 主爬虫类
# ---------------------------------------------------------------------------

class FastBackfillScraper:
    """快速历史回填爬虫 - Playwright 驱动"""

    def __init__(self, headless: bool = True):
        self.headless = headless

    def run_detail(self, urls_file: str, dry_run: bool = False) -> tuple:
        """回填基准价（detail 页）"""
        try:
            with open(urls_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"读取 URLs 文件失败: {e}")
            return 0, 0

        categories = data.get('categories', [])
        if not categories:
            print("未找到 categories")
            return 0, 0

        print(f"\n{'='*60}")
        print(f"基准价模式回填（rawmex/detail 页面）")
        print(f"{'='*60}")
        print(f"产品数: {len(categories)}")

        total_saved, total_failed, done = 0, 0, 0
        start_time = time.time()

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)

            for cat in categories:
                done += 1
                name = cat['name']
                industry = cat.get('category', '化工')
                url = cat['url']

                print(f"\n[{done}/{len(categories)}] {name} ({industry})")
                print(f"  URL: {url}")

                product_id = get_or_create_product(name, industry, url, None)
                if not product_id:
                    print(f"  -> 产品创建失败")
                    total_failed += 1
                    continue

                records = scrape_benchmark_page(url, name, industry, browser=browser)

                if not records:
                    print(f"  -> 无数据")
                    continue

                print(f"  -> 获取到 {len(records)} 条基准价")

                if not dry_run:
                    saved = save_benchmark_records_batch(product_id, records, SOURCE_KEY)
                    print(f"  -> 已保存 {saved} 条")
                    total_saved += saved

                time.sleep(0.5)

            browser.close()

        elapsed = time.time() - start_time
        print(f"\n基准价模式完成: 耗时 {elapsed:.1f}s, 总记录 {total_saved} 条, 失败 {total_failed} 个")
        return total_saved, total_failed

    def run_mprice(self, urls_file: str, dry_run: bool = False, max_pages: int = 10) -> tuple:
        """回填详细报价（mprice/plist 页）"""
        try:
            with open(urls_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"读取 URLs 文件失败: {e}")
            return 0, 0

        categories = data.get('categories', [])
        if not categories:
            print("未找到 categories")
            return 0, 0

        print(f"\n{'='*60}")
        print(f"详细报价模式回填（mprice/plist 页面）")
        print(f"{'='*60}")
        print(f"产品数: {len(categories)}, 每产品翻 {max_pages} 页")

        total_saved, total_failed, done = 0, 0, 0
        start_time = time.time()

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)

            for cat in categories:
                done += 1
                name = cat['name']
                industry = cat.get('category', '化工')
                url = cat['url']

                print(f"\n[{done}/{len(categories)}] {name} ({industry})")
                print(f"  URL: {url}")

                product_id = get_or_create_product(name, industry, url, url)
                if not product_id:
                    print(f"  -> 产品创建失败")
                    total_failed += 1
                    continue

                all_rows = scrape_plist_pages(url, name, industry, max_pages, browser=browser)

                if not all_rows:
                    print(f"  -> 无数据")
                    continue

                print(f"  -> 共获取 {len(all_rows)} 条报价")

                if not dry_run:
                    saved = save_detailed_quotes_batch(product_id, name, all_rows, SOURCE_KEY)
                    print(f"  -> 已保存 {saved} 条")
                    total_saved += saved

                time.sleep(0.5)

            browser.close()

        elapsed = time.time() - start_time
        print(f"\n详细报价模式完成: 耗时 {elapsed:.1f}s, 总记录 {total_saved} 条, 失败 {total_failed} 个")
        return total_saved, total_failed

    def run(self, mode: str = 'both', urls_file_detail: str = 'category_urls.json',
            urls_file_mprice: str = 'category_urls_mprice.json',
            dry_run: bool = False, max_pages: int = 10):
        """主入口"""
        print(f"\n{'='*60}")
        print(f"生意社历史数据快速回填")
        print(f"{'='*60}")
        print(f"模式: {mode}")
        print(f"详细报价文件: {urls_file_mprice}")
        print(f"基准价文件: {urls_file_detail}")
        print(f"模式: {'模拟运行' if dry_run else '实际回填'}")
        print(f"{'='*60}")

        total_saved, total_failed = 0, 0

        if mode in ('detail', 'both'):
            saved, failed = self.run_detail(urls_file_detail, dry_run)
            total_saved += saved
            total_failed += failed

        if mode in ('mprice', 'both'):
            saved, failed = self.run_mprice(urls_file_mprice, dry_run, max_pages)
            total_saved += saved
            total_failed += failed

        print(f"\n{'='*60}")
        print(f"全部完成!")
        print(f"总记录: {total_saved} 条, 失败: {total_failed} 个")
        print(f"{'='*60}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="生意社历史数据快速回填")
    parser.add_argument('--mode', type=str, choices=['detail', 'mprice', 'both'],
                        default='both', help='回填模式')
    parser.add_argument('--urls-file-detail', type=str, default='category_urls.json',
                        help='基准价 URLs 文件（rawmex/detail）')
    parser.add_argument('--urls-file-mprice', type=str, default='category_urls_mprice.json',
                        help='详细报价 URLs 文件（mprice/plist）')
    parser.add_argument('--dry-run', action='store_true', help='仅模拟不写入')
    parser.add_argument('--max-pages', type=int, default=10, help='每产品最大翻页数')
    args = parser.parse_args()

    scraper = FastBackfillScraper()
    scraper.run(
        mode=args.mode,
        urls_file_detail=args.urls_file_detail,
        urls_file_mprice=args.urls_file_mprice,
        dry_run=args.dry_run,
        max_pages=args.max_pages,
    )


if __name__ == "__main__":
    main()
