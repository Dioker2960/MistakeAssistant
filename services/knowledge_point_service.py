import logging
from datetime import datetime
from core.exceptions import BusinessError
from uuid import uuid4
from repositories import knowledge_point_repo, wrong_question_repo
from schemas.knowledge_point import KnowledgePointCreate

logger = logging.getLogger(__name__)


def create(data: KnowledgePointCreate) -> dict:
    """创建知识点。同名报错。"""
    existing = knowledge_point_repo.get_by_name(data.name)
    if existing is not None:
        raise BusinessError("知识点已存在")
    now = datetime.now()
    # 生成 id、时间戳、保存
    kp = {
        "id": uuid4().hex,
        "name": data.name,
        "parent_id": data.parent_id,
        "description": data.description,
        "created_at": now,
        "updated_at": now,
    }
    result = knowledge_point_repo.save(kp)
    logger.info("创建知识点: id=%s, name=%s", result["id"], result["name"])
    return result


def list_all() -> list[dict]:
    return knowledge_point_repo.list_all()


def get_questions_by_kp(kp_id: str, user_id: str) -> list[dict]:
    """查某知识点下当前用户的错题。"""
    kp = knowledge_point_repo.get_by_id(kp_id)
    if kp is None:
        raise BusinessError("知识点不存在")
    # 2. 拿到所有关联的 question_id
    question_ids = knowledge_point_repo.list_question_ids_for_kp(kp_id)
    # 用 qids 过滤该用户的错题
    result = []
    for question_id in question_ids:
        question = wrong_question_repo.get_by_id(question_id)
        if question is not None and question["user_id"] == user_id:
            result.append(question)
    return result


def get_kps_by_question(question_id: str) -> list[dict]:
    """查某题关联的所有知识点详情。"""
    kp_ids = knowledge_point_repo.list_kp_ids_for_question(question_id)
    result = []
    for kp_id in kp_ids:
        kp = knowledge_point_repo.get_by_id(kp_id)
        if kp is not None:
            result.append(kp)
    return result


def tag_question(question_id: str, kp_ids: list[str], user_id: str) -> None:
    """给题目打知识点。先校验，再执行。"""
    # 1. 校验题目属于该用户
    question = wrong_question_repo.get_by_id(question_id)
    if question is None:
        raise BusinessError("错题不存在")
    if question["user_id"] != user_id:
        raise BusinessError("无权操作")

    # 2. 先校验所有 kp_id 都存在（不做任何修改）
    for kp_id in kp_ids:
        if knowledge_point_repo.get_by_id(kp_id) is None:
            raise BusinessError(f"知识点不存在: {kp_id}")

    # 3. 校验通过后，才删旧加新
    knowledge_point_repo.remove_all_for_question(question_id)

    now = datetime.now()
    for kp_id in kp_ids:
        knowledge_point_repo.add_question_knowledge({
            "id": uuid4().hex,
            "question_id": question_id,
            "knowledge_point_id": kp_id,
            "created_at": now,
        })

    logger.info("打知识点: question_id=%s, kp_ids=%s", question_id, kp_ids)
