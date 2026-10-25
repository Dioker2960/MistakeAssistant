import json
import os

import redis
from dotenv import load_dotenv

import logging
logger = logging.getLogger(__name__)

from core.jwt_utils import TOKEN_TTL_SECONDS

load_dotenv()

# 统一 key 前缀，避免和其他应用共用同一 DB 时冲突
KEY_PREFIX = os.getenv("REDIS_KEY_PREFIX", "app:")

# 用户对象缓存 TTL
USER_CACHE_TTL_SECONDS = int(os.getenv("USER_CACHE_TTL_SECONDS", 1800))


_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "127.0.0.1"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    decode_responses=True,
    socket_connect_timeout=0.5,
    socket_timeout=0.5,
    retry_on_timeout=False,  # 超时不重试
    health_check_interval=0,  # 不做后台健康检查（避免额外连接）
)


def get_client() -> redis.Redis:
    return _client


def _key(key: str) -> str:
    """给 key 加上统一前缀。"""
    return f"{KEY_PREFIX}{key}"


def set_json(key: str, value, ttl: int | None = None) -> None:
    """存 JSON 值。ttl 单位秒，None 表示不过期。"""
    data = json.dumps(value, ensure_ascii=False, default=str)
    if ttl is None:
        _client.set(_key(key), data)
    else:
        _client.setex(_key(key), ttl, data)


def get_json(key: str):
    """取 JSON 值，不存在返回 None。"""
    raw = _client.get(_key(key))
    if raw is None:
        return None
    return json.loads(raw)


def delete(key: str) -> None:
    """删除单个 key。"""
    _client.delete(_key(key))


def set_str(key: str, value: str, ttl: int | None = None) -> None:
    if ttl is None:
        _client.set(_key(key), value)
    else:
        _client.setex(_key(key), ttl, value)


def get_str(key: str) -> str | None:
    try:
        value = _client.get(_key(key))
        logger.debug("get_str 返回: key=%s value=%r", key, value)
        return value
    except Exception as e:
        logger.warning("get_str 异常: key=%s err=%r", key, e)
        raise
