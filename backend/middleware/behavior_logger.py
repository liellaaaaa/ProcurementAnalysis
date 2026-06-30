"""
行为日志中间件
捕获所有 API 请求的访问信息，用于分析用户行为
"""
import time
import json
import base64
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Path-to-module mapping for API routes
API_MODULE_MAP = {
    "/products": "PRODUCT",
    "/prices": "PRICE",
    "/alerts": "ALERT",
    "/reports": "REPORT",
    "/scrapers": "SCRAPER",
    "/categories": "CATEGORY",
    "/feedback": "FEEDBACK",
    "/operation-logs": "OPERATION_LOG",
    "/analytics": "ANALYTICS",
    "/auth": "AUTH",
    "/behavior": "BEHAVIOR",
}

# Paths to skip (static assets, health checks)
SKIP_PATHS = {"/", "/health", "/favicon.ico"}


def extract_module_from_path(path: str) -> str:
    """从请求路径提取模块名"""
    if path.startswith("/api"):
        path = path[4:]  # Strip /api prefix
    for prefix, module in API_MODULE_MAP.items():
        if path.startswith(prefix):
            return module
    return "UNKNOWN"


def soft_extract_jwt(request: Request) -> tuple:
    """
    软提取 JWT - 不验证签名，只解析 payload
    失败时返回 (None, None)
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, None
    token = auth_header[7:]
    try:
        # JWT payload is base64url encoded, second segment
        payload_b64 = token.split(".")[1]
        # Add padding if needed
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload_json = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_json)
        return payload.get("user_id"), payload.get("username")
    except Exception:
        return None, None


def get_client_ip(request: Request) -> str:
    """提取客户端 IP（优先 X-Forwarded-For，支持代理）"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host or "unknown"
    return "unknown"


class BehaviorLoggerMiddleware(BaseHTTPMiddleware):
    """
    中间件：记录所有 API 请求到 operation_logs 表
    - 软提取 JWT（失败不阻断）
    - 记录：path, method, ip, user_agent, user_id, username
    - 采样策略：失败请求 + 慢请求(>阈值) + 成功请求采样 %
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip certain paths
        if path in SKIP_PATHS or path.startswith("/static"):
            return await call_next(request)

        # Only log API calls
        if not path.startswith("/api"):
            return await call_next(request)

        # Import config here to avoid circular imports
        try:
            from backend.config import BEHAVIOR_SLOW_REQUEST_THRESHOLD_MS, BEHAVIOR_SAMPLE_RATE
            slow_threshold = BEHAVIOR_SLOW_REQUEST_THRESHOLD_MS
            sample_rate = BEHAVIOR_SAMPLE_RATE
        except ImportError:
            slow_threshold = 2000
            sample_rate = 10

        start_time = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)

        # Extract user info (soft - won't fail on bad JWT)
        user_id, username = soft_extract_jwt(request)
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")[:500]
        session_id = request.headers.get("x-session-id", "")[:100] or None
        module = extract_module_from_path(path)

        # Decide whether to log this request
        # Log if: failed, slow, or sampled (10% of successful requests)
        should_log = (
            response.status_code >= 400
            or duration_ms > slow_threshold
            or (response.status_code == 200 and hash(f"{user_id or 'anon'}:{session_id or path}") % 100 < sample_rate)
        )

        if should_log:
            try:
                from backend.services.operation_logger import OperationLogger
                OperationLogger.log_frontend_behavior(
                    module=module,
                    action=request.method,
                    details={
                        "path": path,
                        "method": request.method,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms
                    },
                    user_id=user_id,
                    username=username,
                    page=path,
                    referrer=request.headers.get("referer", ""),
                    session_id=session_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    result="FAILURE" if response.status_code >= 400 else "SUCCESS"
                )
            except Exception:
                pass  # Never fail due to logging

        return response
