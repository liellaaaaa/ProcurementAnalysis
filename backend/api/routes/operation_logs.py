"""
操作日志查询API
"""
from fastapi import APIRouter, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import json
from pathlib import Path

router = APIRouter(prefix="/api/v1/operation-logs", tags=["操作日志"])

# 日志文件路径
LOG_DIR = Path(__file__).parent.parent.parent.parent / "log"
LOG_FILE = LOG_DIR / "operations.log"


class OperationLogResponse(BaseModel):
    timestamp: str
    level: str
    module: str
    action: str
    details: dict
    result: str
    operator: Optional[str] = "system"


def read_logs_from_file(lines: int = 100, keyword: str = None, module: str = None) -> List[dict]:
    """从日志文件读取"""
    if not LOG_FILE.exists():
        return []

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    logs = []
    for line in reversed(all_lines[-lines*2:]):  # 多读一些用于过滤
        try:
            log = json.loads(line.strip())
            # 过滤
            if module and log.get("module") != module:
                continue
            if keyword:
                log_str = json.dumps(log, ensure_ascii=False).lower()
                if keyword.lower() not in log_str:
                    continue
            logs.append(log)
            if len(logs) >= lines:
                break
        except:
            continue

    return list(reversed(logs))


@router.get("", response_model=List[OperationLogResponse])
async def get_operation_logs(
    limit: int = Query(100, le=500),
    keyword: Optional[str] = None,
    module: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    level: Optional[str] = None
):
    """
    获取操作日志列表

    - **limit**: 返回条数，默认100，最大500
    - **keyword**: 关键词搜索
    - **module**: 模块筛选 (PRODUCT/PRICE/ALERT/REPORT/SCRAPER/CATEGORY)
    - **start_date**: 开始日期 (yyyy-mm-dd)
    - **end_date**: 结束日期 (yyyy-mm-dd)
    - **level**: 级别筛选 (INFO/WARNING/ERROR)
    """
    logs = read_logs_from_file(lines=1000, keyword=keyword, module=module)

    # 日期过滤
    if start_date:
        logs = [l for l in logs if l.get("timestamp", "") >= start_date]
    if end_date:
        logs = [l for l in logs if l.get("timestamp", "")[:10] <= end_date]

    # 级别过滤
    if level:
        logs = [l for l in logs if l.get("level") == level]

    # 限制返回数量
    logs = logs[:limit]

    return [OperationLogResponse(
        timestamp=log.get("timestamp", ""),
        level=log.get("level", "INFO"),
        module=log.get("module", ""),
        action=log.get("action", ""),
        details=log.get("details", {}),
        result=log.get("result", "SUCCESS"),
        operator=log.get("details", {}).get("operator", "system") if isinstance(log.get("details"), dict) else "system"
    ) for log in logs]


@router.get("/modules")
async def get_modules():
    """获取所有模块分类"""
    return {
        "modules": [
            {"value": "PRODUCT", "label": "产品管理"},
            {"value": "PRICE", "label": "价格查询"},
            {"value": "ALERT", "label": "预警管理"},
            {"value": "REPORT", "label": "报表生成"},
            {"value": "SCRAPER", "label": "爬虫运行"},
            {"value": "CATEGORY", "label": "分类管理"},
            {"value": "SYSTEM", "label": "系统"}
        ]
    }


@router.get("/summary")
async def get_log_summary():
    """获取日志统计摘要"""
    if not LOG_FILE.exists():
        return {"total": 0, "by_module": {}, "by_level": {}, "by_result": {}}

    logs = read_logs_from_file(lines=10000)

    by_module = {}
    by_level = {}
    by_result = {}

    for log in logs:
        module = log.get("module", "UNKNOWN")
        level = log.get("level", "INFO")
        result = log.get("result", "SUCCESS")

        by_module[module] = by_module.get(module, 0) + 1
        by_level[level] = by_level.get(level, 0) + 1
        by_result[result] = by_result.get(result, 0) + 1

    return {
        "total": len(logs),
        "by_module": by_module,
        "by_level": by_level,
        "by_result": by_result
    }
