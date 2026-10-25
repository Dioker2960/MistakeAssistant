import os
from datetime import datetime, timedelta
from uuid import uuid4

import jwt
from dotenv import load_dotenv

load_dotenv()

_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dioker2960")
_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 1440))

# token 有效期（秒），供 Redis 白名单等使用
TOKEN_TTL_SECONDS = _EXPIRE_MINUTES * 60

def create_token(user_id: str, username: str) -> tuple[str, str]:
    """生成 JWT token，返回 (token, jti)。"""
    jti = uuid4().hex
    payload = {
        "user_id": user_id,
        "username": username,
        "jti": jti,
        "exp": datetime.utcnow() + timedelta(minutes=_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)
    return token, jti


def decode_token(token: str) -> dict | None:
    """
    解析 token。成功返回 payload，失败返回 None。
    失败包括：签名错误、过期、格式错误。
    """
    try:
        return jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
    except jwt.PyJWTError:
        return None