from backend.scrapers.registry import ScraperRegistry

ScraperRegistry.register_all()

__all__ = ['ScraperRegistry', 'BaseScraper', 'ScrapedItem']