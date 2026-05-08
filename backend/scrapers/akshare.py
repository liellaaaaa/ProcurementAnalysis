import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import akshare as ak

from backend.scrapers.base import BaseScraper, ScrapedItem
from backend.models.database import get_session, Product, PriceRecord, ScraperLog
from backend.services.alert_service import check_and_trigger_alerts


# AKshare symbol → 数据库 product_name 映射表
AKSHARE_SYMBOL_MAP = {
    "PX": "PX",
    "EB": "苯乙烯",
    "EG": "乙二醇",
    "MA": "甲醇",
    "TA": "PTA",
    "PP": "PP(拉丝)",
    "V": "PVC树脂SG5",
    "L": "线性聚乙烯",
    "UR": "尿素",
    "PG": "液化石油气",
}


class AkshareScraper(BaseScraper):
    """AKshare 化工期货现货价格爬虫"""

    SOURCE_KEY = "akshare"
    SOURCE_URL = "https://www.100ppi.com"
    # 默认回溯天数
    BACKWARD_DAYS = 7

    def __init__(self, name: str = "akshare", backward_days: int = None):
        super().__init__(name)
        self.backward_days = backward_days or self.BACKWARD_DAYS

    def get_entry_urls(self) -> List[str]:
        return []

    def _generate_code(self, name: str, specification: str = None) -> str:
        """生成产品编码（与生意社爬虫保持一致）"""
        import hashlib
        raw = f"{name}|{specification or ''}"
        return hashlib.md5(raw.encode()).hexdigest()[:12].upper()

    def _call_akshare(self, date_str: str) -> List[Dict]:
        """调用 AKshare futures_spot_price 获取指定日期数据"""
        try:
            df = ak.futures_spot_price(date=date_str)
            if df is None or df.empty:
                return []
            # 重命名列（AKshare 列名可能含中文编码问题，按位置映射）
            df = df.rename(columns={
                "date": "date",
                "symbol": "symbol",
                "spot_price": "spot_price",
                "near_contract": "near_contract",
                "near_contract_price": "near_contract_price",
                "dominant_contract": "dominant_contract",
                "dominant_contract_price": "dominant_contract_price",
                "near_month": "near_month",
                "dominant_month": "dominant_month",
                "near_basis": "near_basis",
                "dom_basis": "dom_basis",
                "near_basis_rate": "near_basis_rate",
                "dom_basis_rate": "dom_basis_rate",
            })
            return df.to_dict("records")
        except Exception as e:
            print(f"  [AKshare] {date_str} 获取失败: {e}")
            return []

    def _record_to_scraped_item(self, record: Dict, record_date: str) -> Optional[ScrapedItem]:
        """将 AKshare 单条记录转为 ScrapedItem"""
        symbol = record.get("symbol", "")
        if symbol not in AKSHARE_SYMBOL_MAP:
            return None

        product_name = AKSHARE_SYMBOL_MAP[symbol]
        spot_price = record.get("spot_price")
        if spot_price is None or spot_price <= 0:
            return None

        # 基差率 → 涨跌幅（取绝对值，方向由基差正负决定）
        near_basis_rate = record.get("near_basis_rate") or 0
        dom_basis_rate = record.get("dom_basis_rate") or 0
        change_percent = round(abs(dom_basis_rate) * 100, 2) if dom_basis_rate else 0.0

        # 基差率为正 → 现货高于期货 → 趋势涨；负 → 跌
        if dom_basis_rate > 0:
            trend = "涨"
            change_percent = abs(change_percent)
        elif dom_basis_rate < 0:
            trend = "跌"
            change_percent = -abs(change_percent)
        else:
            trend = "平"
            change_percent = 0.0

        return ScrapedItem(
            product_code=self._generate_code(product_name),
            product_name=product_name,
            price=float(spot_price),
            price_type="市场价",
            trend=trend,
            change_percent=change_percent,
            record_date=record_date,
            raw_data={
                "supplier": self.SOURCE_KEY,
                "source_url": self.SOURCE_URL,
                "specification": None,
                "region": None,
                "near_contract": record.get("near_contract"),
                "near_contract_price": record.get("near_contract_price"),
                "dominant_contract": record.get("dominant_contract"),
                "dominant_contract_price": record.get("dominant_contract_price"),
                "near_basis_rate": near_basis_rate,
                "dom_basis_rate": dom_basis_rate,
            }
        )

    def run(self) -> List[ScrapedItem]:
        """回溯最近 backward_days 天，每天调用 futures_spot_price"""
        all_items = []
        seen = set()

        today = datetime.now().date()
        for i in range(self.backward_days):
            target_date = today - timedelta(days=i)
            date_str = target_date.strftime("%Y%m%d")
            print(f"  正在抓取 {date_str} ...")

            records = self._call_akshare(date_str)
            print(f"    获取到 {len(records)} 条记录")

            for record in records:
                item = self._record_to_scraped_item(record, target_date.strftime("%Y-%m-%d"))
                if item is None:
                    continue
                key = f"{item.product_name}|{item.record_date}"
                if key not in seen:
                    seen.add(key)
                    all_items.append(item)

        print(f"\nAKshare 爬取完成，共获取 {len(all_items)} 条去重后数据")
        return all_items

    def parse_product_list(self, html: str) -> List[str]:
        return []

    def parse_product_detail(self, html: str, url: str) -> Optional[ScrapedItem]:
        return None

    def save_to_db(self, items: List[ScrapedItem]) -> int:
        """保存到数据库（与生意社爬虫逻辑一致）"""
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
                        source_url=item.raw_data.get("source_url")
                    )
                    session.add(product)
                    session.flush()

                record_date = datetime.strptime(item.record_date, "%Y-%m-%d").date()
                region_val = item.raw_data.get("region")
                supplier_val = item.raw_data.get("supplier")

                # 检查是否已存在相同 product_id + record_date + source + region + supplier 的记录
                existing = session.query(PriceRecord).filter(
                    PriceRecord.product_id == product.id,
                    PriceRecord.record_date == record_date,
                    PriceRecord.source == self.name,
                    PriceRecord.region == region_val,
                    PriceRecord.supplier == supplier_val
                ).first()

                if existing:
                    existing.price = item.price
                    existing.price_type = item.price_type or "市场价"
                    existing.trend = item.trend
                    existing.change_percent = item.change_percent
                else:
                    record = PriceRecord(
                        product_id=product.id,
                        price=item.price,
                        price_type=item.price_type or "市场价",
                        trend=item.trend,
                        change_percent=item.change_percent,
                        source=self.name,
                        region=region_val,
                        supplier=supplier_val,
                        specification=item.raw_data.get("specification"),
                        record_date=record_date
                    )
                    session.add(record)
                saved_count += 1

            except Exception as e:
                print(f"Error saving item: {e}")
                session.rollback()

        session.commit()

        # 预警触发检查
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
    """运行爬虫（作为独立脚本入口）"""
    scraper = AkshareScraper()
    scraper.log_scraper_run("running", 0)

    try:
        items = scraper.run()
        saved = scraper.save_to_db(items)
        scraper.log_scraper_run("success", saved)
        print(f"Scraped {len(items)} items, saved {saved} to database.")
    except Exception as e:
        scraper.log_scraper_run("failed", 0, str(e))
        print(f"Scraper failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_scraper()
