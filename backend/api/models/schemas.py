"""公共 Pydantic 响应模型"""
from typing import Any, Dict, Optional
from pydantic import BaseModel


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "ok"


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    error: str


class SuccessResponse(BaseModel):
    """成功消息响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Dict[str, Any]] = None