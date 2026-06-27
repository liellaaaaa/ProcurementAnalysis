"""
操作日志查询API
优先从数据库查询，文件作为 fallback
"""
from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
import re
from pathlib import Path
from backend.api.deps import get_db
from backend.models.database import OperationLog

router = APIRouter(prefix="/api/v1/operation-logs", tags=["操作日志"])

# 日志文件路径 (fallback)
LOG_DIR = Path(__file__).parent.parent.parent.parent / "log"
LOG_FILE = LOG_DIR / "operations.log"

# 允许的 operator 字符：字母、数字、下划线、汉字
OPERATOR_PATTERN = re.compile(r'^[\w\u4e00-\u9fff]{1,50}$')


def sanitize_operator(value: str) -> str:
    """清理 operator 字段，防止注入和信息泄露"""
    if not value or not isinstance(value, str):
        return "system"
    cleaned = value.strip()[:50]
    if OPERATOR_PATTERN.match(cleaned):
        return cleaned
    return "system"


class OperationLogResponse(BaseModel):
    timestamp: str
    level: str
    module: str
    action: str
    details: dict
    result: str
    operator: Optional[str] = "system"


def read_logs_from_file(lines: int = 100, keyword: str = None, module: str = None) -> List[dict]:
    """从日志文件读取 (fallback)"""
    if not LOG_FILE.exists():
        return []

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    logs = []
    for line in reversed(all_lines[-lines*2:]):
        try:
            log = json.loads(line.strip())
            if module and log.get("module") != module:
                continue
            if keyword:
                log_str = json.dumps(log, ensure_ascii=False).lower()
                if keyword.lower() not in log_str:
                    continue
            logs.append(log)
            if len(logs) >= lines:
                break
        except (json.JSONDecodeError, KeyError, TypeError):
            continue

    return list(reversed(logs))


@router.get("", response_model=List[OperationLogResponse])
async def get_operation_logs(
    limit: int = Query(100, le=500),
    keyword: Optional[str] = None,
    module: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取操作日志列表（优先从数据库查询）
    """
    # 尝试从数据库查询
    try:
        query = db.query(OperationLog)

        if module:
            query = query.filter(OperationLog.module == module)
        if level:
            query = query.filter(OperationLog.level == level)
        if start_date:
            query = query.filter(OperationLog.timestamp >= start_date)
        if end_date:
            query = query.filter(OperationLog.timestamp <= end_date + " 23:59:59")
        if keyword:
            query = query.filter(OperationLog.details.contains(keyword))

        db_logs = query.order_by(OperationLog.timestamp.desc()).limit(limit).all()

        if db_logs:
            return [OperationLogResponse(
                timestamp=log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
                level=log.level or "INFO",
                module=log.module or "",
                action=log.action or "",
                details=json.loads(log.details) if log.details and log.details.startswith("{") else {"raw": log.details} if log.details else {},
                result=log.result or "SUCCESS",
                operator=sanitize_operator(log.operator or "system")
            ) for log in db_logs]
    except Exception:
        pass

    # Fallback: 从文件读取
    logs = read_logs_from_file(lines=1000, keyword=keyword, module=module)

    if start_date:
        logs = [l for l in logs if l.get("timestamp", "") >= start_date]
    if end_date:
        logs = [l for l in logs if l.get("timestamp", "")[:10] <= end_date]
    if level:
        logs = [l for l in logs if l.get("level") == level]

    logs = logs[:limit]

    return [OperationLogResponse(
        timestamp=log.get("timestamp", ""),
        level=log.get("level", "INFO"),
        module=log.get("module", ""),
        action=log.get("action", ""),
        details=log.get("details", {}),
        result=log.get("result", "SUCCESS"),
        operator=sanitize_operator(
            log.get("details", {}).get("operator", "system") if isinstance(log.get("details"), dict) else "system"
        )
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
            {"value": "FEEDBACK", "label": "采购反馈"},
            {"value": "SYSTEM", "label": "系统"}
        ]
    }


@router.get("/summary")
async def get_log_summary(db: Session = Depends(get_db)):
    """获取日志统计摘要"""
    # 尝试从数据库聚合
    try:
        total = db.query(func.count(OperationLog.id)).scalar() or 0
        if total > 0:
            by_module = dict(db.query(OperationLog.module, func.count(OperationLog.id)).group_by(OperationLog.module).all())
            by_level = dict(db.query(OperationLog.level, func.count(OperationLog.id)).group_by(OperationLog.level).all())
            by_result = dict(db.query(OperationLog.result, func.count(OperationLog.id)).group_by(OperationLog.result).all())
            return {"total": total, "by_module": by_module, "by_level": by_level, "by_result": by_result}
    except Exception:
        pass

    # Fallback: 从文件聚合
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
