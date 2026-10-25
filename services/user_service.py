from datetime import datetime
from uuid import uuid4
import logging
from core.security import hash_password, verify_hash
from core.exceptions import BusinessError
from repositories import user_repo
from schemas.user import UserCreate
from core import redis_client


logger = logging.getLogger(__name__)

_USER_CACHE_TTL = redis_client.USER_CACHE_TTL_SECONDS


def _cache_key(user_id: str) -> str:
    return f"auth:user:{user_id}"


def create(data: UserCreate) -> dict:
    """注册新用户。"""
    # TODO 1: 检查用户名是否已存在（调 user_repo.get_by_username）
    #         存在 → 抛 BusinessError("用户名已存在")
    user = user_repo.get_by_username(data.username)
    if user is not None:
        raise BusinessError("用户名已存在")
    # TODO 2: 生成 id（uuid4().hex）
    user_id = uuid4().hex
    now = datetime.now()
    # TODO 3: 密码哈希
    #         password_hash = hash_password(data.password)
    password_hash = hash_password(data.password)
    # TODO 4: 组装 user dict
    user = {
        "id": user_id,
        "username": data.username,
        "password_hash": password_hash,
        "role": "user",
        "created_at": now,
        "updated_at": now,
    }
    # TODO 5: 保存并返回
    result = user_repo.save(user)
    logger.info("创建用户: id=%s", result["id"])
    return result


def _serialize_user(user: dict) -> dict:
    """缓存用：剔除 password_hash，datetime 转 ISO 字符串。"""
    data = {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
        "updated_at": user["updated_at"].isoformat() if user.get("updated_at") else None,
    }
    return data


def _deserialize_user(data: dict) -> dict:
    """从缓存读回：ISO 字符串转回 datetime。"""
    result = dict(data)
    for field in ("created_at", "updated_at"):
        if result.get(field):
            result[field] = datetime.fromisoformat(result[field])
    return result


def _to_public_dict(user: dict) -> dict:
    """对外返回：不含 password_hash，datetime 保留为 datetime。"""
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
    }


def get_by_id(user_id: str) -> dict | None:
    """
    按 id 查用户，返回不含 password_hash 的公开字段。
    优先读缓存，未命中查库并回填；Redis 故障时降级查库。
    """
    cache_key = _cache_key(user_id)

    try:
        cached = redis_client.get_json(cache_key)
    except Exception as e:
        logger.warning("读取用户缓存失败，降级查库: user_id=%s err=%s", user_id, e)
        cached = None
    else:
        if cached is not None:
            return _deserialize_user(cached)

    user = user_repo.get_by_id(user_id)
    if user is None:
        return None

    try:
        redis_client.set_json(cache_key, _serialize_user(user), ttl=_USER_CACHE_TTL)
    except Exception as e:
        logger.warning("写入用户缓存失败: user_id=%s err=%s", user_id, e)

    # 统一契约：查库返回也不含 password_hash
    return _to_public_dict(user)


def verify_password(username: str, password: str) -> dict | None:
    """
    校验用户名密码。
    成功返回用户信息（不含密码），失败返回 None。
    """
    # TODO 1: 按用户名查用户
    user = user_repo.get_by_username(username)
    # TODO 2: 不存在 → return None
    if user is None:
        return None
    # TODO 3: 校验密码 hash
    if not verify_hash(password, user["password_hash"]):
        return None
    # TODO 4: 通过 → 返回用户信息
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
    }


def change_password(user_id: str, old_password: str, new_password: str) -> None:
    """修改密码。旧密码错误或用户不存在时抛 BusinessError。"""
    user = user_repo.get_by_id(user_id)
    if user is None:
        raise BusinessError("用户不存在")

    if not verify_hash(old_password, user["password_hash"]):
        raise BusinessError("旧密码错误")

    new_hash = hash_password(new_password)
    ok = user_repo.update_password(user_id, new_hash)
    if not ok:
        raise BusinessError("密码更新失败")

    logger.info("用户修改密码: user_id=%s", user_id)
    # 让用户缓存失效，下次读取重新查库
    try:
        redis_client.delete(_cache_key(user_id))
    except Exception as e:
        logger.warning("删除用户缓存失败: user_id=%s err=%s", user_id, e)
