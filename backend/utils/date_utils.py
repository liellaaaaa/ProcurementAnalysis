"""日期工具函数"""
from datetime import date, timedelta
from typing import Optional, Tuple


def format_date(dt):
    """统一日期格式为 yyyy/mm/dd"""
    if isinstance(dt, str):
        try:
            dt = date.fromisoformat(dt[:10])
        except (ValueError, TypeError):
            return dt
    if hasattr(dt, 'strftime'):
        return dt.strftime('%Y/%m/%d')
    return str(dt)


def get_date_range(report_type: str, start_date=None, end_date=None) -> Tuple[date, date]:
    """获取报表日期范围，优先使用传入的自定义范围"""
    if start_date and end_date:
        return start_date, end_date

    today = date.today()
    if report_type == "weekly":
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        return week_start, week_end
    elif report_type == "monthly":
        month_start = date(today.year, today.month, 1)
        if today.month == 12:
            month_end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        return month_start, month_end
    return today - timedelta(days=7), today


def get_previous_period_range(report_type: str, start_date: date, end_date: date) -> Tuple[date, date]:
    """获取上一个周期的日期范围（用于环比）"""
    period_length = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_length - 1)
    return prev_start, prev_end


def parse_date(s: Optional[str]) -> Optional[date]:
    """解析日期字符串，支持 yyyy/mm/dd 和 yyyy-mm-dd 格式"""
    if not s:
        return None
    try:
        return date.fromisoformat(s.replace('/', '-'))
    except (ValueError, TypeError):
        return None