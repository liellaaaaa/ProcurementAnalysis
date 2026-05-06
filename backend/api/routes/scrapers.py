from fastapi import APIRouter, HTTPException, Query
from typing import List
import subprocess
import sys
import os
from datetime import date

from backend.scrapers import ScraperRegistry
from backend.models.database import get_session, PriceRecord, ScraperLog

router = APIRouter(prefix="/api/v1", tags=["scrapers"])

SCRAPER_SCRIPTS = {
    "shengyishe": "backend/scrapers/shengyishe.py"
}


@router.get("/sources", response_model=List[str])
async def get_sources():
    """返回已注册的数据源列表"""
    return ScraperRegistry.list_sources()


@router.get("/check-freshness")
async def check_data_freshness():
    """检查各数据源数据的最新日期，提醒是否需要更新"""
    session = get_session()
    today = date.today()

    # 查询每个数据源的最新记录日期
    from sqlalchemy import func
    results = session.query(
        PriceRecord.source,
        func.max(PriceRecord.record_date).label('latest_date')
    ).group_by(PriceRecord.source).all()

    source_status = []
    for source, latest_date in results:
        if source == 'manual':
            continue
        if latest_date:
            days_diff = (today - latest_date).days
            needs_update = days_diff > 0
            source_status.append({
                "source": source,
                "latest_date": latest_date.isoformat(),
                "days_ago": days_diff,
                "needs_update": needs_update,
                "message": f"最新数据来自 {days_diff} 天前" if needs_update else f"数据已是最新（{latest_date}）"
            })
        else:
            source_status.append({
                "source": source,
                "latest_date": None,
                "days_ago": None,
                "needs_update": True,
                "message": "暂无数据，请抓取"
            })

    # 检查是否有完全没数据的源（排除 manual）
    registered_sources = ScraperRegistry.list_sources()
    for src in registered_sources:
        if src == 'manual':
            continue
        if not any(s['source'] == src for s in source_status):
            source_status.append({
                "source": src,
                "latest_date": None,
                "days_ago": None,
                "needs_update": True,
                "message": "暂无数据，请抓取"
            })

    session.close()
    return {
        "today": today.isoformat(),
        "sources": source_status,
        "any_needs_update": any(s['needs_update'] for s in source_status)
    }


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