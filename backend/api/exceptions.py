"""统一异常处理"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


class APIException(Exception):
    """API基础异常类"""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class NotFoundError(APIException):
    """资源不存在"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(status_code=404, message=message)


class BadRequestError(APIException):
    """请求无效"""

    def __init__(self, message: str = "请求无效"):
        super().__init__(status_code=400, message=message)


class ConflictError(APIException):
    """资源冲突"""

    def __init__(self, message: str = "资源已存在"):
        super().__init__(status_code=409, message=message)


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """全局API异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message}
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器（保留原有行为）"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )