"""
操作日志查询API
优先从数据库查询，文件作为 fallback
支持行为日志分析：漏斗、热力图、留存
"""
from fastapi import APIRouter, Query, Depends, Request, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
import re
from pathlib import Path
from collections import defaultdict

from backend.api.deps import get_db
from backend.models.database import OperationLog

router = APIRouter(prefix="/api/v1/operation-logs", tags=["操作日志"])

# 日志文件路径 (fallback)
LOG_DIR = Path(__file__).parent.parent.parent.parent / "log"
LOG_FILE = LOG_DIR / "operations.log"

# 允许的 operator 字符：字母、数字、下划线、汉字
OPERATOR_PATTERN = re.compile(r'^[\w一-鿿]{1,50}$')

# 简单的内存缓存（生产环境建议用 Redis）
_cache = {}
_cache_ttl = {
    "summary": 300,      # 5 分钟
    "funnel": 300,       # 5 分钟
    "heatmap": 300,       # 5 分钟
    "retention": 600,    # 10 分钟
}


def sanitize_operator(value: str) -> str:
    """清理 operator 字段，防止注入和信息泄露"""
    if not value or not isinstance(value, str):
        return "system"
    cleaned = value.strip()[:50]
    if OPERATOR_PATTERN.match(cleaned):
        return cleaned
    return "system"


def get_cache(key: str) -> Optional[dict]:
    """获取缓存"""
    if key in _cache:
        entry = _cache[key]
        if datetime.now().timestamp() - entry["ts"] < _cache_ttl.get(key.split(":")[0], 300):
            return entry["data"]
    return None


def set_cache(key: str, data: dict):
    """设置缓存"""
    _cache[key] = {"data": data, "ts": datetime.now().timestamp()}


class OperationLogResponse(BaseModel):
    timestamp: str
    level: str
    module: str
    action: str
    details: dict
    result: str
    operator: Optional[str] = "system"
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    page: Optional[str] = None
    referrer: Optional[str] = None


class BehaviorEvent(BaseModel):
    """单个前端行为事件"""
    module: str = Field(..., description="模块: NAV/UI/BEHAVIOR/PRICE/etc.")
    action: str = Field(..., description="动作: PAGE_VIEW/CLICK/FILTER_CHANGE/etc.")
    details: dict = Field(default_factory=dict, description="详细信息")
    page: str = Field(..., description="当前页面路由")
    referrer: Optional[str] = Field(None, description="来源页面")
    session_id: str = Field(..., description="会话ID")
    timestamp: Optional[str] = Field(None, description="事件时间戳 ISO格式")
    result: str = Field(default="SUCCESS", description="结果: SUCCESS/FAILURE")


class BehaviorEventBatch(BaseModel):
    """批量前端行为事件"""
    events: List[BehaviorEvent] = Field(..., description="事件列表")


class FunnelStep(BaseModel):
    step: str
    module: str
    action: str
    count: int


class FunnelResponse(BaseModel):
    start_date: str
    end_date: str
    total_users: int
    steps: List[FunnelStep]


class HeatmapEntry(BaseModel):
    page: str
    action: str
    element_id: Optional[str]
    count: int
    avg_dwell_ms: Optional[float] = None


class HeatmapResponse(BaseModel):
    start_date: str
    end_date: str
    data: List[HeatmapEntry]


class RetentionCohort(BaseModel):
    cohort_date: str
    cohort_size: int
    retention_by_week: List[float]


class RetentionResponse(BaseModel):
    start_date: str
    end_date: str
    cohorts: List[RetentionCohort]


class PagePopularity(BaseModel):
    page: str
    view_count: int
    unique_users: int
    avg_dwell_ms: float = 0


class ActionDistribution(BaseModel):
    action: str
    module: str
    count: int


class UserActivitySummary(BaseModel):
    total_events: int
    unique_users: int
    unique_sessions: int
    page_popularity: List[PagePopularity]
    action_distribution: List[ActionDistribution]


# 频率限制：同一 session_id 每分钟最多 10 批
_rate_limit = defaultdict(list)


def check_rate_limit(session_id: str) -> bool:
    """检查频率限制，返回 True 表示超限"""
    now = datetime.now().timestamp()
    # 清理 1 分钟前的记录
    _rate_limit[session_id] = [t for t in _rate_limit[session_id] if now - t < 60]
    if len(_rate_limit[session_id]) >= 10:
        return True
    _rate_limit[session_id].append(now)
    return False


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
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    page: Optional[str] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取操作日志列表（优先从数据库查询）
    """
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
        if user_id is not None:
            query = query.filter(OperationLog.user_id == user_id)
        if session_id:
            query = query.filter(OperationLog.session_id == session_id)
        if page:
            query = query.filter(OperationLog.page == page)
        if action:
            query = query.filter(OperationLog.action == action)

        db_logs = query.order_by(OperationLog.timestamp.desc()).limit(limit).all()

        if db_logs:
            return [OperationLogResponse(
                timestamp=log.timestamp.strftime("%Y-%m-%d %H:%M:%S") if log.timestamp else "",
                level=log.level or "INFO",
                module=log.module or "",
                action=log.action or "",
                details=json.loads(log.details) if log.details and log.details.startswith("{") else {"raw": log.details} if log.details else {},
                result=log.result or "SUCCESS",
                operator=sanitize_operator(log.operator or "system"),
                user_id=log.user_id,
                username=None,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                session_id=log.session_id,
                page=log.page,
                referrer=log.referrer
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
        ),
        user_id=log.get("user_id"),
        username=log.get("username"),
        ip_address=log.get("ip_address"),
        user_agent=log.get("user_agent"),
        session_id=log.get("session_id"),
        page=log.get("page"),
        referrer=log.get("referrer")
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
            {"value": "SYSTEM", "label": "系统"},
            {"value": "NAV", "label": "导航"},
            {"value": "UI", "label": "界面交互"},
            {"value": "BEHAVIOR", "label": "行为分析"}
        ]
    }


@router.get("/summary")
async def get_log_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取日志统计摘要（含用户行为分析）"""
    cache_key = f"summary:{start_date}:{end_date}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    try:
        total = db.query(func.count(OperationLog.id)).scalar() or 0
        if total > 0:
            by_module = dict(db.query(OperationLog.module, func.count(OperationLog.id)).group_by(OperationLog.module).all())
            by_level = dict(db.query(OperationLog.level, func.count(OperationLog.id)).group_by(OperationLog.level).all())
            by_result = dict(db.query(OperationLog.result, func.count(OperationLog.id)).group_by(OperationLog.result).all())

            # User activity summary (行为日志统计)
            behavior_query = db.query(OperationLog).filter(
                OperationLog.module.in_(["NAV", "UI", "BEHAVIOR"])
            )
            if start_date:
                behavior_query = behavior_query.filter(OperationLog.timestamp >= start_date)
            if end_date:
                behavior_query = behavior_query.filter(OperationLog.timestamp <= end_date + " 23:59:59")

            total_events = behavior_query.count()
            unique_users = behavior_query.filter(OperationLog.user_id.isnot(None)).distinct(OperationLog.user_id).count()
            unique_sessions = behavior_query.filter(OperationLog.session_id.isnot(None)).distinct(OperationLog.session_id).count()

            # Page popularity (top pages by PAGE_VIEW count)
            page_pop = db.query(
                OperationLog.page,
                func.count(OperationLog.id).label("view_count"),
                func.count(func.distinct(OperationLog.user_id)).label("unique_users")
            ).filter(
                OperationLog.module == "NAV",
                OperationLog.action == "PAGE_VIEW"
            )
            if start_date:
                page_pop = page_pop.filter(OperationLog.timestamp >= start_date)
            if end_date:
                page_pop = page_pop.filter(OperationLog.timestamp <= end_date + " 23:59:59")
            page_pop = page_pop.group_by(OperationLog.page).order_by(func.count(OperationLog.id).desc()).limit(10).all()

            # Action distribution
            action_dist = db.query(
                OperationLog.action,
                OperationLog.module,
                func.count(OperationLog.id).label("count")
            ).filter(
                OperationLog.module.in_(["NAV", "UI", "BEHAVIOR"])
            )
            if start_date:
                action_dist = action_dist.filter(OperationLog.timestamp >= start_date)
            if end_date:
                action_dist = action_dist.filter(OperationLog.timestamp <= end_date + " 23:59:59")
            action_dist = action_dist.group_by(OperationLog.action, OperationLog.module).all()

            result = {
                "total": total,
                "by_module": by_module,
                "by_level": by_level,
                "by_result": by_result,
                "user_activity_summary": {
                    "total_events": total_events,
                    "unique_users": unique_users,
                    "unique_sessions": unique_sessions,
                    "page_popularity": [
                        {"page": p.page or "", "view_count": p.view_count, "unique_users": p.unique_users, "avg_dwell_ms": 0}
                        for p in page_pop
                    ],
                    "action_distribution": [
                        {"action": a.action or "", "module": a.module or "", "count": a.count}
                        for a in action_dist
                    ]
                }
            }
            set_cache(cache_key, result)
            return result
    except Exception:
        pass

    # Fallback: 从文件聚合
    if not LOG_FILE.exists():
        return {"total": 0, "by_module": {}, "by_level": {}, "by_result": {}, "user_activity_summary": None}

    logs = read_logs_from_file(lines=10000)

    by_module = {}
    by_level = {}
    by_result = {}

    for log in logs:
        module = log.get("module", "UNKNOWN")
        level = log.get("level", "INFO")
        result_val = log.get("result", "SUCCESS")

        by_module[module] = by_module.get(module, 0) + 1
        by_level[level] = by_level.get(level, 0) + 1
        by_result[result_val] = by_result.get(result_val, 0) + 1

    return {
        "total": len(logs),
        "by_module": by_module,
        "by_level": by_level,
        "by_result": by_result,
        "user_activity_summary": None
    }


@router.post("/behavior")
async def post_behavior_events(
    batch: BehaviorEventBatch,
    request: Request,
    db: Session = Depends(get_db)
):
    """批量接收前端行为事件"""
    # 限流检查：取第一个事件的 session_id
    session_id = batch.events[0].session_id if batch.events else "unknown"
    if check_rate_limit(session_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded: max 10 batches per minute per session")

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:500]

    # Soft JWT extract
    auth_header = request.headers.get("authorization", "")
    user_id, username = None, None
    if auth_header.startswith("Bearer "):
        try:
            import base64 as b64
            token = auth_header[7:]
            payload_b64 = token.split(".")[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += "=" * padding
            payload = json.loads(b64.urlsafe_b64decode(payload_b64))
            user_id = payload.get("user_id")
            username = payload.get("username")
        except Exception:
            pass

    logged_count = 0
    max_events = 100  # 单批次最多 100 条

    for i, event in enumerate(batch.events[:max_events]):
        if i >= max_events:
            break
        try:
            op_log = OperationLog(
                timestamp=datetime.fromisoformat(event.timestamp) if event.timestamp else datetime.now(),
                level="INFO",
                module=event.module,
                action=event.action,
                details=json.dumps(event.details, ensure_ascii=False)[:1000] if event.details else "",
                result=event.result,
                operator=username or "anonymous",
                user_id=user_id,
                page=event.page[:200] if event.page else None,
                referrer=event.referrer[:200] if event.referrer else None,
                session_id=event.session_id[:100] if event.session_id else None,
                ip_address=ip_address[:50] if ip_address else None,
                user_agent=user_agent
            )
            db.add(op_log)
            logged_count += 1
        except Exception:
            continue

    try:
        db.commit()
    except Exception:
        db.rollback()

    return {
        "logged": logged_count,
        "received": len(batch.events),
        "truncated": len(batch.events) > max_events
    }


@router.get("/funnel", response_model=FunnelResponse)
async def get_funnel_analysis(
    start_date: str = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """漏斗分析"""
    cache_key = f"funnel:{start_date}:{end_date}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    # 定义漏斗步骤
    funnel_steps = [
        {"step": "page_view", "module": "NAV", "action": "PAGE_VIEW"},
        {"step": "filter_change", "module": "UI", "action": "FILTER_CHANGE"},
        {"step": "search_or_pagination", "module": "UI", "action": "SEARCH"},
        {"step": "download_export", "module": "UI", "action": "DOWNLOAD"},
    ]

    result_steps = []
    query_base = db.query(OperationLog).filter(
        OperationLog.timestamp >= start_date,
        OperationLog.timestamp <= end_date + " 23:59:59",
        OperationLog.module.in_(["NAV", "UI", "BEHAVIOR"])
    )

    for step_def in funnel_steps:
        step_query = query_base.filter(
            OperationLog.module == step_def["module"],
            OperationLog.action == step_def["action"]
        )
        count = step_query.count()
        result_steps.append(FunnelStep(
            step=step_def["step"],
            module=step_def["module"],
            action=step_def["action"],
            count=count
        ))

    # Total unique users in period
    total_users = query_base.filter(
        OperationLog.user_id.isnot(None)
    ).distinct(OperationLog.user_id).count()

    result = FunnelResponse(
        start_date=start_date,
        end_date=end_date,
        total_users=total_users,
        steps=result_steps
    )
    set_cache(cache_key, result.model_dump())
    return result


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap_data(
    start_date: str = Query(..., description="开始日期"),
    end_date: str = Query(..., description="结束日期"),
    page: Optional[str] = Query(None, description="页面过滤"),
    db: Session = Depends(get_db)
):
    """获取热力图数据：每个页面的元素点击分布"""
    cache_key = f"heatmap:{start_date}:{end_date}:{page}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    query = db.query(
        OperationLog.page,
        OperationLog.action,
        OperationLog.details,
        func.count(OperationLog.id).label("count")
    ).filter(
        OperationLog.timestamp >= start_date,
        OperationLog.timestamp <= end_date + " 23:59:59",
        OperationLog.module == "UI",
        OperationLog.action.in_(["CLICK", "FILTER_CHANGE", "PAGINATE", "EXPAND"])
    )

    if page:
        query = query.filter(OperationLog.page == page)

    results = query.group_by(
        OperationLog.page, OperationLog.action, OperationLog.details
    ).order_by(func.count(OperationLog.id).desc()).all()

    data = []
    for r in results:
        details = {}
        try:
            if r.details and r.details.startswith("{"):
                details = json.loads(r.details)
        except Exception:
            pass
        element_id = details.get("element_id")
        data.append(HeatmapEntry(
            page=r.page or "",
            action=r.action or "",
            element_id=element_id,
            count=r.count,
            avg_dwell_ms=None
        ))

    result = HeatmapResponse(start_date=start_date, end_date=end_date, data=data)
    set_cache(cache_key, result.model_dump())
    return result


@router.get("/retention", response_model=RetentionResponse)
async def get_retention_stats(
    start_date: str = Query(..., description="开始日期"),
    end_date: str = Query(..., description="结束日期"),
    db: Session = Depends(get_db)
):
    """用户留存分析，按周统计新用户在后续周的留存率"""
    cache_key = f"retention:{start_date}:{end_date}"
    cached = get_cache(cache_key)
    if cached:
        return cached

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format")

    # Generate weekly cohorts
    cohort_weeks = []
    current = start
    while current < end:
        week_end = current + timedelta(days=7)
        cohort_weeks.append((current, min(week_end, end)))
        current = week_end

    cohorts = []
    for cohort_start, cohort_end in cohort_weeks[:8]:
        # Users who first appeared in this cohort week
        first_seen_subq = db.query(
            OperationLog.user_id,
            func.min(OperationLog.timestamp).label("first_seen")
        ).filter(
            OperationLog.user_id.isnot(None),
            OperationLog.timestamp >= cohort_start,
            OperationLog.timestamp < cohort_end
        ).group_by(OperationLog.user_id).subquery()

        cohort_size = db.query(func.count(func.distinct(first_seen_subq.c.user_id))).scalar() or 0

        if cohort_size == 0:
            cohorts.append(RetentionCohort(
                cohort_date=cohort_start.strftime("%Y-%m-%d"),
                cohort_size=0,
                retention_by_week=[0.0] * min(8, len(cohort_weeks))
            ))
            continue

        retention_by_week = []
        for week_offset in range(min(8, len(cohort_weeks))):
            retention_week_start = cohort_start + timedelta(weeks=week_offset)
            retention_week_end = retention_week_start + timedelta(weeks=1)

            returned = db.query(func.count(func.distinct(OperationLog.user_id))).filter(
                OperationLog.user_id.in_(
                    db.query(first_seen_subq.c.user_id)
                ),
                OperationLog.timestamp >= retention_week_start,
                OperationLog.timestamp < retention_week_end
            ).scalar() or 0

            retention_by_week.append(round(returned / cohort_size, 3))

        cohorts.append(RetentionCohort(
            cohort_date=cohort_start.strftime("%Y-%m-%d"),
            cohort_size=cohort_size,
            retention_by_week=retention_by_week
        ))

    result = RetentionResponse(start_date=start_date, end_date=end_date, cohorts=cohorts)
    set_cache(cache_key, result.model_dump())
    return result
