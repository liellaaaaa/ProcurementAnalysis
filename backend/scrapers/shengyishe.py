"""
生意社价格爬虫 - 统一入口
- 基准价（detail 页）→ benchmark_prices 表
- 详细报价（plist 页）→ detailed_quotes 表

运行方式:
  python -m backend.scrapers.shengyishe
  python -m backend.scrapers.shengyishe --dry-run
"""
import re
import sys
import argparse
import time
from datetime import datetime, date
from typing import List, Dict, Optional

from loguru import logger
from playwright.sync_api import sync_playwright

from backend.scrapers.base import (
    parse_price, parse_date, parse_change_percent, determine_trend,
    filter_latest_day, new_page, make_playwright_context,
    save_benchmark_record, save_detailed_quotes_batch, log_scraper_run,
)
from backend.models.database import get_session, Product, ScraperLog


SOURCE_KEY = "shengyishe"


class ShengyisheScraper:
    """生意社化工价格爬虫 - 使用 Playwright 绕过反爬"""

    def __init__(self):
        self._product_map: Dict[str, Product] = {}

    # ------------------------------------------------------------------
    # 产品数据加载
    # ------------------------------------------------------------------
    def get_all_products(self) -> List[Product]:
        session = get_session()
        try:
            products = session.query(Product).filter(
                Product.source_url.isnot(None),
                Product.is_active == True,
            ).all()
            for p in products:
                self._product_map[p.source_url] = p
            logger.info(f"从数据库获取到 {len(products)} 个产品")
            return products
        finally:
            session.close()

    # ------------------------------------------------------------------
    # 基准价爬取（detail 页）
    # ------------------------------------------------------------------
    def scrape_benchmark(self, product: Product, browser=None, context=None) -> Optional[Dict]:
        """爬取单个产品的 detail 页，提取基准价"""
        url = product.source_url
        logger.info(f"  [基准价] {product.product_name}: {url}")

        page, b, ctx, own = new_page(url, browser=browser, context=context)
        try:
            page.goto(url, timeout=30000, wait_until='networkidle')
            page.wait_for_timeout(1000)
            data = self._parse_benchmark_page(page, product)
            if data:
                logger.debug(f"    → price={data.get('price')} date={data.get('record_date')}")
            return data
        except Exception as e:
            logger.warning(f"    ✗ 加载失败: {e}")
            return None
        finally:
            page.close()
            if own:
                b.close()

    def _parse_benchmark_page(self, page, product: Product) -> Optional[Dict]:
        """解析 detail 页，提取基准价（含 spec/brand/market）"""
        try:
            # 价格
            price_el = page.query_selector('.price-fb01_1')
            price_str = price_el.inner_text() if price_el else ""
            price = parse_price(price_str)
            if price is None or price <= 0:
                return None

            # 涨跌
            trend = "平"
            change_percent = None
            change_reason = ""

            if price_el:
                parent = price_el.evaluate_handle('el => el.parentElement')
                if parent:
                    parent_text = parent.inner_text() if parent else ""
                    if '↑' in parent_text or '▲' in parent_text:
                        trend = "涨"
                    elif '↓' in parent_text or '▼' in parent_text:
                        trend = "跌"

                change_el = page.query_selector('.change-percent, .price-change, .trend')
                if change_el:
                    change_percent = parse_change_percent(change_el.inner_text())

            if change_percent is None:
                body_text = page.evaluate('document.body.innerText')
                match = re.search(r'涨跌幅[：:]\s*([+-]?\d+\.?\d*)%', body_text)
                if match:
                    change_percent = float(match.group(1))
                else:
                    match = re.search(r'([+-]?\d+\.?\d*)%\s*$', body_text.split('\n')[0])
                    if match:
                        change_percent = float(match.group(1))

            reason_el = page.query_selector('.change-reason, .price-reason, .trend-reason')
            if reason_el:
                change_reason = reason_el.inner_text().strip()
            else:
                body_text = page.evaluate('document.body.innerText')
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
                record_date = date.today()

            # 产品名（使用数据库名）
            name = product.product_name

            # 从价格表格提取 spec/brand/market
            spec, brand, market = '', '', ''
            table = page.query_selector('.price-newp table')
            if not table:
                table = page.query_selector('table.price-newp, table.rmbpj')
            if table:
                rows = table.query_selector_all('tr')
                for row in rows:
                    cells = row.query_selector_all('td')
                    if len(cells) >= 5:
                        cell_texts = [c.text_content().strip() for c in cells]
                        if '商品名称' in cell_texts[0]:
                            continue
                        if len(cell_texts) >= 5:
                            if cell_texts[0] and cell_texts[0] != product.product_name:
                                name = cell_texts[0]
                            spec = cell_texts[1] if len(cell_texts) > 1 else ''
                            brand = cell_texts[2] if len(cell_texts) > 2 else ''
                            market = cell_texts[3] if len(cell_texts) > 3 else ''

            # 智能分离 name 中的品牌和市场
            name = _separate_brand_market(name, brand, market)

            return {
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
                'source': SOURCE_KEY,
                'record_date': record_date,
            }
        except Exception as e:
            logger.warning(f"    解析失败: {e}")
            return None

    # ------------------------------------------------------------------
    # 详细报价爬取（plist 页）
    # ------------------------------------------------------------------
    def scrape_plist(self, product: Product, browser=None, context=None) -> List[Dict]:
        """爬取单个产品的 plist 页，提取所有报价行（最新一天）"""
        url = product.plist_url
        if not url:
            return []

        logger.info(f"  [详细报价] {product.product_name}: {url}")

        page, b, ctx, own = new_page(url, browser=browser, context=context)
        try:
            page.goto(url, timeout=30000, wait_until='networkidle')
            page.wait_for_timeout(1000)
            rows = _parse_plist_table(page)
            results = filter_latest_day(rows)
            logger.info(f"    → {len(results)} 条报价（最新一天）")
            return results
        except Exception as e:
            logger.warning(f"    ✗ 加载失败: {e}")
            return []
        finally:
            page.close()
            if own:
                b.close()

    # ------------------------------------------------------------------
    # 主运行流程
    # ------------------------------------------------------------------
    def run(self, dry_run: bool = False):
        """增量爬取所有产品的最新一天数据"""
        products = self.get_all_products()
        if not products:
            logger.warning("没有找到产品，退出")
            return

        benchmark_total = 0
        quotes_total = 0

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = make_playwright_context(browser)

            # 第一步：基准价
            logger.info(f"第一步：爬取基准价（{len(products)} 个产品）")
            for product in products:
                data = self.scrape_benchmark(product, browser=browser, context=context)
                if data and not dry_run:
                    n = save_benchmark_record(product.id, data, SOURCE_KEY)
                    benchmark_total += n
                elif dry_run:
                    logger.debug(f"    [dry-run] would save benchmark for {product.product_name}")
                time.sleep(0.5)

            # 第二步：详细报价
            logger.info(f"第二步：爬取详细报价（{len(products)} 个产品）")
            for product in products:
                if not product.plist_url:
                    logger.debug(f"  [skip] {product.product_name} 无 plist 页")
                    continue
                rows = self.scrape_plist(product, browser=browser, context=context)
                if rows and not dry_run:
                    n = save_detailed_quotes_batch(product.id, product.product_name, rows, SOURCE_KEY)
                    quotes_total += n
                elif dry_run:
                    logger.debug(f"    [dry-run] would save {len(rows)} detailed quotes for {product.product_name}")
                time.sleep(0.5)

            context.close()
            browser.close()

        logger.info(f"爬取完成！benchmark: {benchmark_total} 条, detailed_quotes: {quotes_total} 条")

        log_scraper_run(SOURCE_KEY, "success", benchmark_total + quotes_total)


# ======================================================================
# plist 表格解析（独立函数，供 backfill_fast 复用）
# ======================================================================

def _parse_plist_table(page) -> List[Dict]:
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

            price = parse_price(price_str)
            if price is None or price <= 0:
                continue

            parsed_date = parse_date(publish_date_str)
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
        logger.warning(f"    表格解析失败: {e}")
    return results


def _separate_brand_market(name: str, brand: str, market: str) -> str:
    """智能分离 name 中的品牌和市场"""
    if brand and market:
        return name

    name_parts = name.split()
    if market and not brand:
        if len(name_parts) >= 2:
            market_stripped = market[:-1] if market.endswith(('省', '市')) else market
            last_part = name_parts[-1]
            last_stripped = last_part[:-1] if last_part.endswith(('省', '市')) else last_part
            if market_stripped and (last_stripped in market or market in last_stripped or last_part == market_stripped):
                return ' '.join(name_parts[:-2]) if len(name_parts) > 2 else (name_parts[0] if name_parts else name)
            elif len(name_parts) >= 2 and name_parts[-1] == market:
                return ' '.join(name_parts[:-2]) if len(name_parts) > 2 else (name_parts[0] if name_parts else name)
    elif brand and not market:
        if len(name_parts) >= 2:
            return ' '.join(name_parts[:-1])
    else:
        if len(name_parts) >= 3:
            return ' '.join(name_parts[:-2])
        elif len(name_parts) == 2:
            if name_parts[1] in ('华东', '华北', '华南', '华中', '西南', '西北', '东北') or \
               name_parts[1].endswith('省') or name_parts[1].endswith('市'):
                return name_parts[0]
    return name


# ======================================================================
# CLI 入口
# ======================================================================

def main():
    parser = argparse.ArgumentParser(description="生意社价格爬虫")
    parser.add_argument('--dry-run', action='store_true', help='仅模拟，不写入数据库')
    args = parser.parse_args()

    scraper = ShengyisheScraper()
    log_scraper_run(SOURCE_KEY, "running", 0)

    try:
        scraper.run(dry_run=args.dry_run)
    except Exception as e:
        log_scraper_run(SOURCE_KEY, "failed", 0, str(e))
        logger.error(f"爬虫失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
