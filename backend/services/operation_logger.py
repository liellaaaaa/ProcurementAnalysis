"""
操作日志服务
记录用户关键操作，便于后续审计和问题定位
"""
import os
import json
from datetime import datetime
from typing import Optional, List
from pathlib import Path

# 日志目录
LOG_DIR = Path(__file__).parent.parent.parent / "log"
LOG_FILE = LOG_DIR / "operations.log"


class OperationLogger:
    """操作日志记录器"""

    # 操作类型
    OP_CREATE = "CREATE"
    OP_UPDATE = "UPDATE"
    OP_DELETE = "DELETE"
    OP_QUERY = "QUERY"
    OP_EXPORT = "EXPORT"
    OP_ALERT = "ALERT"
    OP_SCRAPE = "SCRAPE"
    OP_LOGIN = "LOGIN"
    OP_LOGOUT = "LOGOUT"

    # 模块分类
    MODULE_PRODUCT = "PRODUCT"
    MODULE_PRICE = "PRICE"
    MODULE_ALERT = "ALERT"
    MODULE_REPORT = "REPORT"
    MODULE_SCRAPER = "SCRAPER"
    MODULE_CATEGORY = "CATEGORY"
    MODULE_SYSTEM = "SYSTEM"

    @classmethod
    def _ensure_log_dir(cls):
        """确保日志目录存在"""
        LOG_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _write_log(cls, level: str, module: str, action: str, details: dict, result: str = "SUCCESS"):
        """写入日志到文件"""
        cls._ensure_log_dir()
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "module": module,
            "action": action,
            "details": details,
            "result": result
        }
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    @classmethod
    def log(cls, module: str, action: str, details: dict = None, result: str = "SUCCESS"):
        """记录一般操作"""
        cls._write_log("INFO", module, action, details or {}, result)

    @classmethod
    def log_success(cls, module: str, action: str, details: dict = None):
        """记录成功操作"""
        cls._write_log("INFO", module, action, details or {}, "SUCCESS")

    @classmethod
    def log_failure(cls, module: str, action: str, details: dict = None, error: str = ""):
        """记录失败操作"""
        cls._write_log("ERROR", module, action, {**(details or {}), "error": error}, "FAILURE")

    @classmethod
    def log_warning(cls, module: str, action: str, details: dict = None):
        """记录警告操作"""
        cls._write_log("WARNING", module, action, details or {}, "WARNING")

    # ============ 便捷方法 ============

    @classmethod
    def log_product_create(cls, product_code: str, product_name: str, operator: str = "system"):
        """记录产品创建"""
        cls.log_success(cls.MODULE_PRODUCT, cls.OP_CREATE, {
            "product_code": product_code,
            "product_name": product_name,
            "operator": operator
        })

    @classmethod
    def log_product_update(cls, product_id: int, product_name: str, changes: dict, operator: str = "system"):
        """记录产品更新"""
        cls.log_success(cls.MODULE_PRODUCT, cls.OP_UPDATE, {
            "product_id": product_id,
            "product_name": product_name,
            "changes": changes,
            "operator": operator
        })

    @classmethod
    def log_product_delete(cls, product_id: int, product_name: str, operator: str = "system"):
        """记录产品删除"""
        cls.log_success(cls.MODULE_PRODUCT, cls.OP_DELETE, {
            "product_id": product_id,
            "product_name": product_name,
            "operator": operator
        })

    @classmethod
    def log_product_query(cls, filters: dict, count: int):
        """记录产品查询"""
        cls.log(cls.MODULE_PRODUCT, cls.OP_QUERY, {
            "filters": filters,
            "result_count": count
        })

    @classmethod
    def log_price_query(cls, product_ids: List[int], date_range: dict, count: int):
        """记录价格查询"""
        cls.log(cls.MODULE_PRICE, cls.OP_QUERY, {
            "product_ids": product_ids,
            "date_range": date_range,
            "result_count": count
        })

    @classmethod
    def log_alert_create(cls, alert_config_id: int, product_name: str, alert_type: str):
        """记录预警配置创建"""
        cls.log_success(cls.MODULE_ALERT, cls.OP_CREATE, {
            "alert_config_id": alert_config_id,
            "product_name": product_name,
            "alert_type": alert_type
        })

    @classmethod
    def log_alert_update(cls, alert_config_id: int, changes: dict):
        """记录预警配置更新"""
        cls.log_success(cls.MODULE_ALERT, cls.OP_UPDATE, {
            "alert_config_id": alert_config_id,
            "changes": changes
        })

    @classmethod
    def log_alert_delete(cls, alert_config_id: int):
        """记录预警配置删除"""
        cls.log_success(cls.MODULE_ALERT, cls.OP_DELETE, {
            "alert_config_id": alert_config_id
        })

    @classmethod
    def log_alert_triggered(cls, alert_message: str, product_name: str, price: float):
        """记录预警触发"""
        cls.log(cls.MODULE_ALERT, cls.OP_ALERT, {
            "alert_message": alert_message,
            "product_name": product_name,
            "triggered_price": price
        })

    @classmethod
    def log_report_generate(cls, report_type: str, date_range: dict, format: str):
        """记录报表生成"""
        cls.log_success(cls.MODULE_REPORT, cls.OP_EXPORT, {
            "report_type": report_type,
            "date_range": date_range,
            "format": format
        })

    @classmethod
    def log_scraper_run(cls, scraper_name: str, items_scraped: int, status: str, duration: float = None):
        """记录爬虫运行"""
        cls.log_success(cls.MODULE_SCRAPER, cls.OP_SCRAPE, {
            "scraper_name": scraper_name,
            "items_scraped": items_scraped,
            "duration_seconds": duration,
            "status": status
        })

    @classmethod
    def log_category_create(cls, category_name: str, category_id: int):
        """记录分类创建"""
        cls.log_success(cls.MODULE_CATEGORY, cls.OP_CREATE, {
            "category_id": category_id,
            "category_name": category_name
        })

    @classmethod
    def log_category_update(cls, category_id: int, changes: dict):
        """记录分类更新"""
        cls.log_success(cls.MODULE_CATEGORY, cls.OP_UPDATE, {
            "category_id": category_id,
            "changes": changes
        })

    @classmethod
    def log_category_delete(cls, category_id: int):
        """记录分类删除"""
        cls.log_success(cls.MODULE_CATEGORY, cls.OP_DELETE, {
            "category_id": category_id
        })


# 简化的实例方法，方便直接调用
def log_operation(module: str, action: str, details: dict = None, result: str = "SUCCESS"):
    """快捷日志函数"""
    OperationLogger.log(module, action, details, result)


def get_recent_logs(lines: int = 100) -> List[dict]:
    """读取最近的操作日志"""
    if not LOG_FILE.exists():
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
        recent = all_lines[-lines:]
        return [json.loads(line) for line in recent]


def search_logs(keyword: str = None, module: str = None, start_date: str = None, end_date: str = None) -> List[dict]:
    """搜索操作日志"""
    if not LOG_FILE.exists():
        return []
    logs = get_recent_logs(10000)  # 最多读取1万条
    if keyword:
        logs = [l for l in logs if keyword.lower() in json.dumps(l, ensure_ascii=False).lower()]
    if module:
        logs = [l for l in logs if l.get("module") == module]
    if start_date:
        logs = [l for l in logs if l.get("timestamp", "") >= start_date]
    if end_date:
        logs = [l for l in logs if l.get("timestamp", "") <= end_date]
    return logs
