from typing import Dict, Type, List

from backend.scrapers.base import BaseScraper


class ScraperRegistry:
    """爬虫注册中心，管理所有数据源爬虫"""

    _scrapers: Dict[str, Type[BaseScraper]] = {}

    @classmethod
    def register(cls, name: str, scraper_class: Type[BaseScraper]):
        """注册一个爬虫类"""
        cls._scrapers[name] = scraper_class

    @classmethod
    def get(cls, name: str) -> BaseScraper:
        """获取指定名称的爬虫实例"""
        if name not in cls._scrapers:
            raise ValueError(f"Unknown scraper: {name}")
        return cls._scrapers[name]()

    @classmethod
    def list_sources(cls) -> List[str]:
        """列出所有已注册的数据源名称"""
        return list(cls._scrapers.keys())

    @classmethod
    def register_all(cls):
        """注册所有爬虫（自动调用）"""
        from backend.scrapers.shengyishe import ShengyisheScraper
        cls.register("shengyishe", ShengyisheScraper)