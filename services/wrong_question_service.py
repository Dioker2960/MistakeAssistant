from datetime import datetime

from ai.embedding_service import build_question_text
from repositories import wrong_question_repo, knowledge_point_repo
from schemas.knowledge_point import KnowledgePointCreate
from schemas.wrong_question import WrongQuestionUpdate, WrongQuestionCreate
from uuid import uuid4
import logging
import random
import threading
import time

from core import redis_client
from services import knowledge_point_service, answer_record_service

logger = logging.getLogger(__name__)

# 逻辑过期时间（秒）：数据在缓存里"逻辑上"多久算新鲜
_QUESTION_LOGICAL_TTL = 600 * 2
# 物理 TTL（秒）：兜底淘汰，防止 key 永久占内存；不是过期依据
_QUESTION_PHYSICAL_TTL = 86400
# 空值缓存 TTL（秒）
_QUESTION_NULL_TTL = 60
# 空值标记
_DATETIME_FIELDS = ("last_wrong_time", "created_at", "updated_at")

# 异步重建去重
# 注意：_rebuilding 是进程内去重，多进程部署时同一 key 可能被多个进程同时重建。
# 单进程无碍；多进程如需严格去重，改用 Redis 分布式锁。
_rebuild_lock = threading.Lock()
_rebuilding: set[str] = set()


def _serialize_question(q: dict) -> dict:
    """缓存用：datetime 转 ISO 字符串。"""
    data = dict(q)
    for f in _DATETIME_FIELDS:
        if data.get(f):
            data[f] = data[f].isoformat()
    return data


def _deserialize_question(data: dict) -> dict:
    """缓存读回：ISO 字符串转回 datetime。"""
    result = dict(data)
    for f in _DATETIME_FIELDS:
        if result.get(f):
            result[f] = datetime.fromisoformat(result[f])
    return result


def _question_key(user_id: str, question_id: str) -> str:
    return f"cache:question:{user_id}:{question_id}"


def _async_rebuild(cache_key: str, question_id: str, user_id: str) -> None:
    """逻辑过期后异步重建缓存，同一 key 只允许一个线程重建。"""
    with _rebuild_lock:
        if cache_key in _rebuilding:
            return
        _rebuilding.add(cache_key)

    def _do():
        try:
            question = wrong_question_repo.get_by_id(question_id)
            if question is not None and question["user_id"] == user_id:
                redis_client.set_json(cache_key, {
                    "data": _serialize_question(question),
                    "expire_time": time.time() + _QUESTION_LOGICAL_TTL,
                }, ttl=_QUESTION_PHYSICAL_TTL)
        except Exception as e:
            logger.warning("异步重建题目缓存失败: %s", e)
        finally:
            with _rebuild_lock:
                _rebuilding.discard(cache_key)

    threading.Thread(target=_do, daemon=True).start()


def create(data: WrongQuestionCreate, user_id: str) -> dict:
    """
    业务逻辑：
    1. 生成 id（用 uuid4().hex）
    2. user_id 由 API 层从 token 解析后传入
    3. 设置 mastery_status = "薄弱"
    4. 设置 wrong_count = 1
    5. 设置 last_wrong_time / created_at / updated_at = 当前时间
    6. 调用 repo.save()
    """
    # 1. 过滤掉空字符串和重复项
    kp_names = []
    for name in data.knowledge_point_names:
        name = name.strip()
        if name and name not in kp_names:
            kp_names.append(name)
    # 2. 先"查或创建"所有知识点，拿到 id（避免创建了题但打标签失败）
    kp_ids = []
    for name in kp_names:
        kp = knowledge_point_repo.get_by_name(name)
        if kp is None:
            kp = knowledge_point_service.create(KnowledgePointCreate(name=name))
        kp_ids.append(kp["id"])
    # 3. 创建错题
    now = datetime.now()
    question = {
        "id": uuid4().hex,
        "user_id": user_id,
        **data.model_dump(exclude={"knowledge_point_names"}),
        "mastery_status": "薄弱",
        "wrong_count": 1,
        "last_wrong_time": now,
        "created_at": now,
        "updated_at": now,
    }
    result = wrong_question_repo.save(question)
    # 4. 给错题增加知识点标签
    if kp_ids:
        knowledge_point_service.tag_question(result["id"], kp_ids, user_id)
    answer_record_service.record_answer(
        user_id=user_id,
        question_id=result["id"],
        user_answer=data.user_answer,
        is_correct=False,       # 录错题 = 答错
        source_type="INITIAL",
    )
    # ← 新增：增量更新 FAISS 索引
    try:
        from ai import langchain_store
        text = build_question_text(result)
        langchain_store.add_document(
            question_id=result["id"],
            user_id=user_id,
            text=text,
        )
    except Exception as e:
        logger.error("索引增量更新失败: %s", e, exc_info=True)
    logger.info("创建错题: id=%s, 题目=%s", result["id"], data.question_content[:30])
    return result


def get_one(question_id: str, user_id: str) -> dict | None:
    cache_key = _question_key(user_id, question_id)

    # 1. 读缓存
    try:
        raw = redis_client.get_json(cache_key)
    except Exception as e:
        logger.warning("读取题目缓存失败，降级查库: %s", e)
        raw = None

    # 2. 命中空值标记 → 直接返回 None（防穿透）
    if isinstance(raw, dict) and raw.get("__null__"):
        return None

    # 3. 命中正常缓存
    if isinstance(raw, dict) and "data" in raw:
        if raw.get("expire_time", 0) < time.time():
            _async_rebuild(cache_key, question_id, user_id)
        return _deserialize_question(raw["data"])

    # 4. 未命中 → 查库
    question = wrong_question_repo.get_by_id(question_id)
    if question is None or question["user_id"] != user_id:
        try:
            redis_client.set_json(cache_key, {"__null__": True}, ttl=_QUESTION_NULL_TTL)
        except Exception as e:
            logger.warning("写入空值缓存失败: %s", e)
        if question is None:
            logger.debug("查询错题不存在: id=%s", question_id)
        else:
            logger.warning("无权访问: id=%s", question_id)
        return None

    # 5. 回填缓存（逻辑过期）
    try:
        redis_client.set_json(cache_key, {
            "data": _serialize_question(question),
            "expire_time": time.time() + _QUESTION_LOGICAL_TTL,
        }, ttl=_QUESTION_PHYSICAL_TTL)
    except Exception as e:
        logger.warning("写入题目缓存失败: %s", e)

    return question


def get_list(
        user_id: str,
        page: int = 1,
        size: int = 10,
        difficulty_min: int | None = None,
        difficulty_max: int | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
) -> dict:
    """分页查询某用户的错题。"""
    total = wrong_question_repo.count_by_user(
        user_id, difficulty_min, difficulty_max, created_after, created_before
    )
    offset = (page - 1) * size
    items = wrong_question_repo.list_paged(
        user_id, offset, size,
        difficulty_min, difficulty_max, created_after, created_before,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    }


def update_one(question_id: str, data: WrongQuestionUpdate, user_id: str) -> dict | None:
    """
    1. 先查是否存在，不存在返回 None
    2. 只更新 data 中不为 None 的字段
    3. 更新 updated_at
    4. 调 repo.update
    """
    question = wrong_question_repo.get_by_id(question_id)
    if not question:
        logger.warning("更新失败，错题不存在: id=%s", question_id)
        return None
    if question["user_id"] != user_id:   # ← 权限校验
        return None
    fields = data.model_dump(exclude_unset=True)
    result = wrong_question_repo.update(question_id, fields)
    try:
        redis_client.delete(_question_key(user_id, question_id))
    except Exception as e:
        logger.warning("删除题目缓存失败: %s", e)
    logger.info("更新错题: id=%s, 字段=%s", question_id, list(fields.keys()))
    return result


def delete_one(question_id: str, user_id: str) -> bool:
    """调用 repo.delete"""
    question = wrong_question_repo.get_by_id(question_id)
    if not question:
        logger.warning("删除失败，错题不存在: id=%s", question_id)
        return False
    if question["user_id"] != user_id:   # ← 权限校验
        return False
    result = wrong_question_repo.delete(question_id)
    logger.info("删除错题: id=%s", question_id)
    try:
        redis_client.delete(_question_key(user_id, question_id))
    except Exception as e:
        logger.warning("删除题目缓存失败: %s", e)
    logger.info("删除错题: id=%s", question_id)
    return result


def stats_by_error_type(user_id: str) -> list[dict]:
    """按错误类型统计。"""
    return wrong_question_repo.stats_by_error_type(user_id)


def stats_by_knowledge_point(user_id: str) -> list[dict]:
    """按知识点统计。"""
    return wrong_question_repo.stats_by_knowledge_point(user_id)
