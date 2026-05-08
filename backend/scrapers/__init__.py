from backend.scrapers.registry import ScraperRegistry

ScraperRegistry.register_all()

from backend.scrapers.akshare import AkshareScraper

ScraperRegistry.register("akshare", AkshareScraper)

__all__ = ['ScraperRegistry', 'BaseScraper', 'ScrapedItem']