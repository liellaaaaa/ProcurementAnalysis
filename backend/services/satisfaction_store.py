"""Satisfaction Score JSON 文件存储 (1-10分制)"""
import json
import os
from datetime import datetime
from typing import List, Optional

SATISFACTION_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "database",
    "satisfaction.json"
)

def _load() -> List[dict]:
    """加载满意度数据"""
    if not os.path.exists(SATISFACTION_FILE):
        return []
    with open(SATISFACTION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(data: List[dict]):
    """保存满意度数据"""
    os.makedirs(os.path.dirname(SATISFACTION_FILE), exist_ok=True)
    with open(SATISFACTION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_all() -> List[dict]:
    """获取所有满意度记录"""
    feedbacks = _load()
    return sorted(feedbacks, key=lambda x: x.get("created_at", ""), reverse=True)

def get_by_id(record_id: int) -> Optional[dict]:
    """根据ID获取满意度记录"""
    feedbacks = _load()
    for f in feedbacks:
        if f.get("id") == record_id:
            return f
    return None

def create(score: int, complaint: str) -> dict:
    """创建满意度记录"""
    feedbacks = _load()
    max_id = max([f.get("id", 0) for f in feedbacks], default=0)

    new_record = {
        "id": max_id + 1,
        "score": score,
        "complaint": complaint,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    feedbacks.append(new_record)
    _save(feedbacks)
    return new_record

def update(record_id: int, **kwargs) -> Optional[dict]:
    """更新满意度记录"""
    feedbacks = _load()
    for i, f in enumerate(feedbacks):
        if f.get("id") == record_id:
            for key, value in kwargs.items():
                if value is not None:
                    f[key] = value
            f["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            feedbacks[i] = f
            _save(feedbacks)
            return f
    return None

def delete(record_id: int) -> bool:
    """删除满意度记录"""
    feedbacks = _load()
    original_len = len(feedbacks)
    feedbacks = [f for f in feedbacks if f.get("id") != record_id]
    if len(feedbacks) < original_len:
        _save(feedbacks)
        return True
    return False
