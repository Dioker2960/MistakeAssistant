from datetime import datetime
from uuid import uuid4

from core.database import SessionLocal
from sqlalchemy import select, delete

from models import QuestionKnowledge, KnowledgePoint


def _to_dict(obj: KnowledgePoint) -> dict:
    return {
        "id": obj.id,
        "name": obj.name,
        "parent_id": obj.parent_id,
        "description": obj.description,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
    }


def save(kp: dict) -> dict:
    obj = KnowledgePoint(**kp)
    with SessionLocal() as session:
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return _to_dict(obj)


def get_by_id(kp_id: str) -> dict | None:
    with SessionLocal() as session:
        obj = session.get(KnowledgePoint, kp_id)
        if obj is None:
            return None
        return _to_dict(obj)


def get_by_name(name: str) -> dict | None:    # 按名字查（去重）
    with SessionLocal() as session:
        stmt = select(KnowledgePoint).where(KnowledgePoint.name == name)
        obj = session.scalars(stmt).first()
        if obj is None:
            return None
        return _to_dict(obj)


def list_all() -> list[dict]:                 # 所有知识点
    with SessionLocal() as session:
        stmt = select(KnowledgePoint)
        objs = session.scalars(stmt).all()
        return [_to_dict(obj) for obj in objs]


# # 关联表相关
def add_question_knowledge(question_knowledge: dict) -> None:
    obj = QuestionKnowledge(**question_knowledge)
    with SessionLocal() as session:
        session.add(obj)
        session.commit()


def remove_all_for_question(question_id: str) -> None:    # 删除题目的所有关联
    with SessionLocal() as session:
        stmt = delete(QuestionKnowledge).where(QuestionKnowledge.question_id == question_id)
        session.execute(stmt)
        session.commit()


def list_kp_ids_for_question(question_id: str) -> list[str]:    # 查某题的所有知识点
    with SessionLocal() as session:
        stmt = select(QuestionKnowledge.knowledge_point_id).where(QuestionKnowledge.question_id == question_id)
        objs = session.scalars(stmt).all()
        return list(objs)


def list_question_ids_for_kp(kp_id: str) -> list[str]:    # 查某知识点下的所有题
    with SessionLocal() as session:
        stmt = select(QuestionKnowledge.question_id).where(QuestionKnowledge.knowledge_point_id == kp_id)
        objs = session.scalars(stmt).all()
        return list(objs)


def get_descendant_ids(kp_id: str) -> list[str]:
    """
    递归获取某知识点及其所有子孙知识点的 ID（含自己）。
    用于"数据结构"包含"二叉树"、"栈"等场景。
    """
    with SessionLocal() as session:
        # 一次性拿所有知识点，在内存里递归（数据量小，够用）
        stmt = select(KnowledgePoint)
        all_kps = session.scalars(stmt).all()

    # 构建 parent_id -> [children] 的映射
    children_map: dict[str | None, list[str]] = {}
    for kp in all_kps:
        children_map.setdefault(kp.parent_id, []).append(kp.id)

    # BFS 收集所有子孙
    result = []
    queue = [kp_id]
    visited = set()
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        result.append(current)
        queue.extend(children_map.get(current, []))

    return result
