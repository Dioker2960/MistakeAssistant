import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends

from core.exceptions import BusinessError
from core.jwt_utils import create_token, decode_token
from schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse, PasswordChange
from services import user_service
import redis
from core import redis_client


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["认证"])

# HTTP Bearer 认证方案
_bearer = HTTPBearer(auto_error=False)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate):
    """注册新用户。"""
    user = user_service.create(data)
    return UserResponse(
        id=user["id"],
        username=user["username"],
        role=user["role"],
        created_at=user["created_at"],
    )


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin):
    """登录，返回 JWT token。"""
    user = user_service.verify_password(data.username, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token, jti = create_token(user["id"], user["username"])
    try:
        redis_client.set_str(f"auth:token:{jti}", user["id"], redis_client.TOKEN_TTL_SECONDS)
    except redis.RedisError as e:
        logger.error("登录写入白名单失败: username=%s err=%s", user["username"], e)
        raise HTTPException(status_code=503, detail="认证服务暂时不可用，请稍后重试")
    logger.info("用户登录: username=%s", user["username"])

    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            role=user["role"],
            created_at=user["created_at"],
        ),
    )


def get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """
    依赖函数：从 Authorization header 解析当前用户。
    未登录、token 无效、或已登出（白名单无记录）时抛 401。
    Redis 不可用时降级为纯 JWT 校验。
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="未登录")

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="token 无效或已过期")

    jti = payload.get("jti")
    if not jti:
        raise HTTPException(status_code=401, detail="token 无效，请重新登录")

    try:
        cached = redis_client.get_str(f"auth:token:{jti}")
    except redis.RedisError as e:
        logger.warning("Redis 不可用，降级为纯 JWT 校验: jti=%s err=%s", jti, e)
        cached = None
        redis_ok = False
    else:
        redis_ok = True

    if redis_ok and cached is None:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")

    user_id = payload.get("user_id")
    user = user_service.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")

    return user


def get_current_jti(
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """轻量依赖：只解析并返回当前 token 的 jti。"""
    if credentials is None:
        raise HTTPException(status_code=401, detail="未登录")
    payload = decode_token(credentials.credentials)
    if payload is None or not payload.get("jti"):
        raise HTTPException(status_code=401, detail="token 无效")
    return payload["jti"]


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    data: PasswordChange,
    user: dict = Depends(get_current_user),
    jti: str = Depends(get_current_jti),
):
    """修改当前用户的密码，并让当前会话立即失效。"""
    user_service.change_password(user["id"], data.old_password, data.new_password)
    try:
        redis_client.delete(f"auth:token:{jti}")
    except redis.RedisError as e:
        logger.warning("改密后删除白名单失败: jti=%s err=%s", jti, e)
    return None


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(jti: str = Depends(get_current_jti)):
    """登出：删除当前 token 的白名单记录。"""
    try:
        redis_client.delete(f"auth:token:{jti}")
    except redis.RedisError as e:
        logger.warning("登出时删除白名单失败: jti=%s err=%s", jti, e)
    return None