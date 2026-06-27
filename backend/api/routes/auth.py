from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt

from backend.models.database import get_session, User
from backend.config import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])

# 固定密码（不存数据库）
FIXED_PASSWORD = "123456"

# Token 过期时间
TOKEN_EXPIRE_DAYS = 7


class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    id: int
    username: str


class LoginResponse(BaseModel):
    token: str
    user: UserInfo


def create_token(user_id: int, username: str) -> str:
    """创建 JWT token"""
    expire = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """验证 token，返回 payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的 Token")


def extract_token(authorization: str = Header(None)) -> str | None:
    """从 Authorization header 提取 token"""
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    return parts[1]


def get_current_user(token: str = Depends(extract_token)) -> UserInfo:
    """从 token 获取当前用户（依赖注入）"""
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    payload = verify_token(token)
    return UserInfo(id=payload["user_id"], username=payload["username"])


def get_current_user_optional(token: str = Depends(extract_token)) -> UserInfo | None:
    """可选的当前用户（未登录返回 None）"""
    if not token:
        return None
    try:
        payload = verify_token(token)
        return UserInfo(id=payload["user_id"], username=payload["username"])
    except:
        return None


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_session)):
    """登录"""
    # 密码验证
    if req.password != FIXED_PASSWORD:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 查找用户，不存在则创建
    user = db.query(User).filter(User.username == req.username).first()
    if not user:
        user = User(username=req.username)
        db.add(user)
        db.commit()
        db.refresh(user)

    # 记录登录日志
    from backend.services.operation_logger import OperationLogger
    OperationLogger.log_success(
        module=OperationLogger.MODULE_SYSTEM,
        action=OperationLogger.OP_LOGIN,
        details={"username": user.username},
        user_id=user.id,
        username=user.username
    )

    token = create_token(user.id, user.username)
    return LoginResponse(token=token, user=UserInfo(id=user.id, username=user.username))


@router.post("/logout")
def logout(token: str = Depends(extract_token)):
    """登出（前端删除 token 即可）"""
    if token:
        try:
            payload = verify_token(token)
            from backend.services.operation_logger import OperationLogger
            OperationLogger.log_success(
                module=OperationLogger.MODULE_SYSTEM,
                action=OperationLogger.OP_LOGOUT,
                details={"username": payload.get("username")},
                user_id=payload.get("user_id"),
                username=payload.get("username")
            )
        except:
            pass
    return {"message": "已退出登录"}


@router.get("/me", response_model=UserInfo)
def get_me(token: str = Depends(extract_token), db: Session = Depends(get_session)):
    """获取当前用户信息"""
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    payload = verify_token(token)
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserInfo(id=user.id, username=user.username)
