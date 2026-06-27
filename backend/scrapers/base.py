"""
爬虫共享工具模块
- 解析函数: parse_price, parse_date, parse_change_percent, determine_trend
- Playwright 浏览器上下文管理
- 数据库保存辅助函数
"""
import re
import time
import random
from datetime import datetime, date
from typing import List, Dict, Optional

from loguru import logger
from playwright.sync_api import sync_playwright

from backend.config import SCRAPER_RETRY_TIMES, SCRAPER_MIN_DELAY


# ======================================================================
# 解析工具
# ======================================================================

def parse_price(price_str: str) -> Optional[float]:
    """从价格字符串提取数值，支持逗号分隔"""
    if not price_str:
        return None
    match = re.search(r'([\d,]+\.?\d*)', price_str.replace(',', ''))
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def parse_date(date_str: str) -> Optional[date]:
    """解析日期字符串，返回 date 对象。支持多种格式，自动补全年份"""
    if not date_str:
        return None
    date_str = date_str.strip()
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m/%d", "%m-%d"]:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.year == 1900:
                dt = dt.replace(year=date.today().year)
            return dt.date()
        except ValueError:
            continue
    return None


def parse_change_percent(text: str) -> Optional[float]:
    """从涨跌文本提取涨跌幅百分比，如 '+2.5%' → 2.5"""
    if not text:
        return None
    match = re.search(r'([+-]?\d+\.?\d*)%', text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def determine_trend(text: str) -> str:
    """根据文本判断涨跌状态"""
    if not text:
        return "平"
    text = text.lower()
    if '涨' in text or 'up' in text or 'rise' in text or '+' in text:
        return "涨"
    elif '跌' in text or 'down' in text or 'fall' in text or ('-' in text and any(c.isdigit() for c in text)):
        return "跌"
    return "平"


def filter_latest_day(rows: List[Dict], date_key: str = 'publish_date') -> List[Dict]:
    """只保留最新一天的数据"""
    if not rows:
        return []
    latest = max(r[date_key] for r in rows)
    return [r for r in rows if r[date_key] == latest]


# ======================================================================
# Playwright 浏览器上下文管理
# ======================================================================

PLAYWRIGHT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
PLAYWRIGHT_VIEWPORT = {'width': 1920, 'height': 1080}


def make_playwright_context(browser, user_agent=None, viewport=None):
    """创建反反爬浏览器上下文"""
    return browser.new_context(
        user_agent=user_agent or PLAYWRIGHT_USER_AGENT,
        viewport=viewport or PLAYWRIGHT_VIEWPORT,
    )


def new_page(url: str, playwright=None, browser=None, context=None, retries: int = None):
    """
    创建新页面，支持重试。
    返回 (page, browser, context, own_browser)。
    own_browser 标记是否由本函数创建了浏览器（调用方需负责关闭）。
    """
    if retries is None:
        retries = SCRAPER_RETRY_TIMES
    own_browser = browser is None
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            pw = playwright
            if own_browser:
                pw = pw or sync_playwright().start()
                browser = pw.chromium.launch(headless=True)
            if context is None:
                context = make_playwright_context(browser)
            page = context.new_page()
            page.goto(url, timeout=30000, wait_until='networkidle')
            page.wait_for_timeout(1000)
            return page, browser, context, own_browser
        except Exception as e:
            last_error = e
            logger.warning(f"    页面加载失败 (尝试 {attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(SCRAPER_MIN_DELAY * attempt)
            if own_browser and browser:
                try:
                    browser.close()
                except Exception:
                    pass
                browser = None
                context = None
    raise last_error


# ======================================================================
# 数据库保存辅助
# ======================================================================

def save_benchmark_record(product_id: int, data: Dict, source: str = "shengyishe") -> int:
    """
    保存单条基准价到 benchmark_prices + price_records 表（增量：已存在则跳过）。
    返回保存数量（0 或 1）。
    """
    from backend.models.database import get_session, BenchmarkPrice, PriceRecord

    session = get_session()
    try:
        record_date = data['record_date']
        existing = session.query(BenchmarkPrice).filter(
            BenchmarkPrice.product_id == product_id,
            BenchmarkPrice.record_date == record_date,
        ).first()
        if existing:
            logger.debug(f"    [skip] benchmark {data.get('product_name', '')} {record_date} 已存在")
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
            trend=data.get('trend', '平'),
            change_percent=data.get('change_percent'),
            change_reason=data.get('change_reason', ''),
            source=source,
            record_date=record_date,
        )
        session.add(bp)

        # 同步写入 price_records
        existing_pr = session.query(PriceRecord).filter(
            PriceRecord.product_id == product_id,
            PriceRecord.record_date == record_date,
            PriceRecord.source == source,
        ).first()
        if not existing_pr:
            pr = PriceRecord(
                product_id=product_id,
                price=data['price'],
                unit=data.get('unit', '元/吨'),
                currency='CNY',
                price_type='基准价',
                trend=data.get('trend', '平'),
                change_percent=data.get('change_percent', 0.0),
                source=source,
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
        logger.error(f"    保存 benchmark 失败: {e}")
        return 0
    finally:
        session.close()


def save_benchmark_records_batch(product_id: int, records: List[Dict], source: str = "shengyishe") -> int:
    """
    批量保存基准价到 benchmark_prices + price_records（历史回填用）。
    已存在则更新价格，不存在则插入。
    返回保存数量。
    """
    from backend.models.database import get_session, BenchmarkPrice, PriceRecord

    if not records:
        return 0

    session = get_session()
    saved = 0
    try:
        for record in records:
            record_date = record.get('date')
            if isinstance(record_date, str):
                record_date = parse_date(record_date) or date.today()

            existing = session.query(BenchmarkPrice).filter(
                BenchmarkPrice.product_id == product_id,
                BenchmarkPrice.record_date == record_date,
            ).first()

            if existing:
                existing.price = record['price']
                existing.spec = record.get('spec', '')
                existing.brand = record.get('brand', '')
                existing.market = record.get('market', '')
            else:
                bp = BenchmarkPrice(
                    product_id=product_id,
                    product_name=record.get('product_name', ''),
                    spec=record.get('spec', ''),
                    brand=record.get('brand', ''),
                    market=record.get('market', ''),
                    price=record['price'],
                    unit=record.get('unit', '元/吨'),
                    price_original=record.get('price_str', ''),
                    source=source,
                    record_date=record_date,
                )
                session.add(bp)

            existing_pr = session.query(PriceRecord).filter(
                PriceRecord.product_id == product_id,
                PriceRecord.record_date == record_date,
                PriceRecord.source == source,
            ).first()

            if not existing_pr:
                pr = PriceRecord(
                    product_id=product_id,
                    price=record['price'],
                    unit=record.get('unit', '元/吨'),
                    price_type='基准价',
                    trend='平',
                    change_percent=0.0,
                    source=source,
                    region=record.get('market', ''),
                    brand=record.get('brand', ''),
                    specification=record.get('spec', ''),
                    extra_data={
                        'spec': record.get('spec', ''),
                        'brand': record.get('brand', ''),
                        'market': record.get('market', ''),
                    },
                    record_date=record_date,
                )
                session.add(pr)
                saved += 1

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"    批量保存 benchmark 失败: {e}")
    finally:
        session.close()

    return saved


def save_detailed_quotes_batch(product_id: int, product_name: str, rows: List[Dict],
                                source: str = "shengyishe") -> int:
    """
    批量保存详细报价到 detailed_quotes + price_records。
    增量：已存在则跳过。
    返回保存数量。
    """
    from backend.models.database import get_session, DetailedQuote, PriceRecord

    if not rows:
        return 0

    session = get_session()
    saved = 0
    try:
        for row in rows:
            publish_date = row.get('publish_date')
            if isinstance(publish_date, str):
                publish_date = parse_date(publish_date) or date.today()

            existing = session.query(DetailedQuote).filter(
                DetailedQuote.product_id == product_id,
                DetailedQuote.publish_date == publish_date,
                DetailedQuote.region == row.get('region', ''),
                DetailedQuote.supplier == row.get('supplier', ''),
                DetailedQuote.price_type == row.get('price_type', ''),
            ).first()
            if existing:
                continue

            price_category = _determine_price_category(
                row.get('price_type', ''), row.get('region', '')
            )

            dq = DetailedQuote(
                product_id=product_id,
                product_name=row.get('product_name', product_name),
                spec=row.get('spec', ''),
                brand=row.get('brand', ''),
                price=row['price'],
                unit='元/吨',
                price_original=row.get('price_str', ''),
                price_type=row.get('price_type', ''),
                price_category=price_category,
                region=row.get('region', ''),
                supplier=row.get('supplier', ''),
                source=source,
                publish_date=publish_date,
                extra_data={'price_type_original': row.get('price_type', '')},
            )
            session.add(dq)
            saved += 1

        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"    保存 detailed_quotes 失败: {e}")
        return 0
    finally:
        session.close()

    return saved


def _determine_price_category(price_type: str, region: str) -> str:
    """根据报价类型和地区判断价格分类"""
    pt = price_type.lower() if price_type else ""
    if '期货' in price_type or 'future' in pt:
        return "期货"
    elif '锁价' in price_type or 'lock' in pt:
        return "锁价"
    return "现货"


def log_scraper_run(scraper_name: str, status: str, items_scraped: int,
                    error_message: str = None):
    """记录爬虫运行日志"""
    from backend.models.database import get_session, ScraperLog

    session = get_session()
    try:
        log = ScraperLog(
            scraper_name=scraper_name,
            status=status,
            items_scraped=items_scraped,
            error_message=error_message,
            started_at=datetime.now(),
            completed_at=datetime.now(),
        )
        session.add(log)
        session.commit()
    finally:
        session.close()
