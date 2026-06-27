"""
将 feedback.json 和 satisfaction.json 数据迁移到数据库
幂等：已存在则跳过
"""
import json
import os
import sys
from datetime import datetime

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.models.database import Feedback, Satisfaction, SessionLocal, init_db


def parse_datetime(value):
    """将字符串解析为 datetime 对象"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None


def migrate_feedback(session):
    """迁移反馈数据"""
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "database", "feedback.json")
    if not os.path.exists(json_path):
        print("feedback.json not found, skipping")
        return 0

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print("feedback.json is empty, skipping")
        return 0

    existing_count = session.query(Feedback).count()
    if existing_count > 0:
        print(f"Feedback table already has {existing_count} records, skipping")
        return 0

    imported = 0
    for item in data:
        feedback = Feedback(
            id=item.get("id"),
            feedback_date=item.get("feedback_date", ""),
            current_status=item.get("current_status", ""),
            expected_result=item.get("expected_result", ""),
            is_resolved=item.get("is_resolved", False),
            resolved_at=item.get("resolved_at"),
            rating=item.get("rating"),
            created_at=parse_datetime(item.get("created_at")),
            updated_at=parse_datetime(item.get("updated_at"))
        )
        session.add(feedback)
        imported += 1

    session.commit()
    print(f"Imported {imported} feedback records")
    return imported


def migrate_satisfaction(session):
    """迁移满意度数据"""
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "database", "satisfaction.json")
    if not os.path.exists(json_path):
        print("satisfaction.json not found, skipping")
        return 0

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print("satisfaction.json is empty, skipping")
        return 0

    existing_count = session.query(Satisfaction).count()
    if existing_count > 0:
        print(f"Satisfaction table already has {existing_count} records, skipping")
        return 0

    imported = 0
    for item in data:
        sat = Satisfaction(
            id=item.get("id"),
            score=item.get("score", 5),
            complaint=item.get("complaint", ""),
            created_at=parse_datetime(item.get("created_at")),
            updated_at=parse_datetime(item.get("updated_at"))
        )
        session.add(sat)
        imported += 1

    session.commit()
    print(f"Imported {imported} satisfaction records")
    return imported


if __name__ == "__main__":
    print("Initializing database...")
    init_db()

    session = SessionLocal()
    try:
        print("\n--- Migrating feedback ---")
        migrate_feedback(session)

        print("\n--- Migrating satisfaction ---")
        migrate_satisfaction(session)

        print("\nMigration complete!")
    finally:
        session.close()
