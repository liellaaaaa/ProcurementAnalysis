from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import random
import time

@dataclass
class ScrapedItem:
    product_code: str
    product_name: str
    price: float
    price_type: str
    trend: str
    change_percent: float
    record_date: str
    raw_data: Dict

class BaseScraper(ABC):
    def __init__(self, name: str):
        self.name = name
        self.session = requests.Session()
        self._setup_headers()

    def _setup_headers(self):
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })

    @abstractmethod
    def get_entry_urls(self) -> List[str]:
        """获取入口URL列表"""
        pass

    @abstractmethod
    def parse_product_list(self, html: str) -> List[str]:
        """解析产品列表页，获取产品详情页URL"""
        pass

    @abstractmethod
    def parse_product_detail(self, html: str, url: str) -> Optional[ScrapedItem]:
        """解析产品详情页，提取价格数据"""
        pass

    def validate_data(self, item: ScrapedItem) -> bool:
        """数据验证"""
        if not item.product_name or not item.price:
            return False
        if item.price <= 0:
            return False
        return True

    def random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """随机延时"""
        time.sleep(random.uniform(min_sec, max_sec))

    def fetch_page(self, url: str, timeout: int = 30) -> Optional[str]:
        """获取页面内容"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def run(self) -> List[ScrapedItem]:
        """执行爬取流程"""
        results = []
        for url in self.get_entry_urls():
            self.random_delay()
            html = self.fetch_page(url)
            if html:
                detail_urls = self.parse_product_list(html)
                for detail_url in detail_urls:
                    self.random_delay()
                    detail_html = self.fetch_page(detail_url)
                    if detail_html:
                        item = self.parse_product_detail(detail_html, detail_url)
                        if item and self.validate_data(item):
                            results.append(item)
        return results