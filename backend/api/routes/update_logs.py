from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import json
import os

from backend.config import BASE_DIR

router = APIRouter(prefix="/api/v1/update-logs", tags=["更新日志"])

UPDATE_LOG_FILE = BASE_DIR / "data" / "update_log.json"


class UpdateLogItem(BaseModel):
    date: str
    content: str


class UpdateLogResponse(BaseModel):
    logs: List[UpdateLogItem]


def read_update_logs() -> List[UpdateLogItem]:
    """读取更新日志 JSON 文件"""
    if not UPDATE_LOG_FILE.exists():
        return []
    try:
        with open(UPDATE_LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [UpdateLogItem(**item) for item in data]
    except Exception:
        return []


@router.get("", response_model=UpdateLogResponse)
def get_update_logs():
    """获取更新日志列表（按时间倒序）"""
    logs = read_update_logs()
    # 按时间倒序
    logs.sort(key=lambda x: x.date, reverse=True)
    return UpdateLogResponse(logs=logs)
