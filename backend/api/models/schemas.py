"""公共 Pydantic 响应模型"""
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar('T')


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "ok"


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    error: str


class ListResponse(BaseModel, Generic[T]):
    """列表响应模型"""
    items: List[T]
    total: Optional[int] = None


class PageResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    items: List[T]
    total: int
    page: int = 1
    page_size: int = 20


class SuccessResponse(BaseModel):
    """成功消息响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Dict[str, Any]] = None