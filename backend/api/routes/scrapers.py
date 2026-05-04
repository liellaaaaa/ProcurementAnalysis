from fastapi import APIRouter, HTTPException
from typing import List
import subprocess
import sys
import os

from backend.scrapers import ScraperRegistry

router = APIRouter(prefix="/api/v1", tags=["scrapers"])

SCRAPER_SCRIPTS = {
    "shengyishe": "backend/scrapers/shengyishe.py"
}


@router.get("/sources", response_model=List[str])
async def get_sources():
    """返回已注册的数据源列表"""
    return ScraperRegistry.list_sources()


@router.post("/scrapers/{source}/run")
async def run_scraper(source: str):
    """触发指定数据源的爬取（在独立进程中运行爬虫脚本）"""
    if source not in SCRAPER_SCRIPTS:
        raise HTTPException(status_code=404, detail=f"Unknown source: {source}")

    # 项目根目录（往上退3层：routes -> api -> backend -> 项目根目录）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))  # backend/api/routes -> backend/api -> backend -> 项目根

    try:
        env = os.environ.copy()
        # 设置 PYTHONPATH 让子进程能找到 backend 模块
        env['PYTHONPATH'] = base_dir

        # 直接用 python -m 运行模块
        result = subprocess.run(
            [sys.executable, '-m', 'backend.scrapers.shengyishe'],
            capture_output=True,
            text=True,
            cwd=base_dir,
            env=env,
            timeout=300
        )

        if result.returncode != 0:
            print(f"Scraper stderr: {result.stderr}")
            print(f"Scraper stdout: {result.stdout}")
            raise HTTPException(status_code=500, detail=f"Scraper failed: {result.stderr[:200] if result.stderr else result.stdout[:200]}")

        return {"status": "success", "message": "爬取完成，数据已更新"}

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="爬取超时（超过5分钟）")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraper error: {str(e)}")