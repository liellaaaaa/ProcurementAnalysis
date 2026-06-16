"""Feedback JSON 文件存储"""
import json
import os
from datetime import datetime
from typing import List, Optional

FEEDBACK_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "database",
    "feedback.json"
)

def _load() -> List[dict]:
    """加载反馈数据"""
    if not os.path.exists(FEEDBACK_FILE):
        return []
    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(data: List[dict]):
    """保存反馈数据"""
    os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_all(is_resolved: Optional[bool] = None) -> List[dict]:
    """获取所有反馈"""
    feedbacks = _load()
    if is_resolved is not None:
        feedbacks = [f for f in feedbacks if f.get("is_resolved") == is_resolved]
    return sorted(feedbacks, key=lambda x: x.get("feedback_date", ""), reverse=True)

def get_by_id(feedback_id: int) -> Optional[dict]:
    """根据ID获取反馈"""
    feedbacks = _load()
    for f in feedbacks:
        if f.get("id") == feedback_id:
            return f
    return None

def create(feedback_date: str, current_status: str, expected_result: str,
           is_resolved: bool = False, resolved_at: Optional[str] = None,
           rating: Optional[int] = None) -> dict:
    """创建反馈"""
    feedbacks = _load()
    max_id = max([f.get("id", 0) for f in feedbacks], default=0)

    new_feedback = {
        "id": max_id + 1,
        "feedback_date": feedback_date,
        "current_status": current_status,
        "expected_result": expected_result,
        "is_resolved": is_resolved,
        "resolved_at": resolved_at,
        "rating": rating,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    feedbacks.append(new_feedback)
    _save(feedbacks)
    return new_feedback

def update(feedback_id: int, **kwargs) -> Optional[dict]:
    """更新反馈"""
    feedbacks = _load()
    for i, f in enumerate(feedbacks):
        if f.get("id") == feedback_id:
            for key, value in kwargs.items():
                if value is not None:
                    f[key] = value
            f["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            feedbacks[i] = f
            _save(feedbacks)
            return f
    return None

def delete(feedback_id: int) -> bool:
    """删除反馈"""
    feedbacks = _load()
    original_len = len(feedbacks)
    feedbacks = [f for f in feedbacks if f.get("id") != feedback_id]
    if len(feedbacks) < original_len:
        _save(feedbacks)
        return True
    return False