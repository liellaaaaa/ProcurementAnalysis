from fastapi import APIRouter, HTTPException
from typing import List

from backend.scrapers import ScraperRegistry

router = APIRouter(prefix="/api/v1", tags=["scrapers"])


@router.get("/sources", response_model=List[str])
async def get_sources():
    """返回已注册的数据源列表"""
    return ScraperRegistry.list_sources()


@router.post("/scrapers/{source}/run")
async def run_scraper(source: str):
    """触发指定数据源的爬取"""
    try:
        scraper = ScraperRegistry.get(source)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        items = scraper.run()
        saved = scraper.save_to_db(items)
        return {"status": "success", "scraped": len(items), "saved": saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraper failed: {str(e)}")