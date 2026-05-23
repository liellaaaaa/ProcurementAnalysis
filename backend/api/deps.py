from fastapi import Depends
from sqlalchemy.orm import Session
from backend.models.database import get_session as _get_session


def get_db() -> Session:
    """统一数据库会话依赖注入"""
    session = _get_session()
    try:
        yield session
    finally:
        session.close()