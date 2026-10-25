from datetime import datetime

from sqlalchemy import select, func

from core.database import SessionLocal
from models.knowledge_point import KnowledgePoint, QuestionKnowledge
from models.wrong_question import WrongQuestion


def _to_dict(obj: WrongQuestion) -> dict:
    """
    把 ORM 对象转成 dict，供 Service 和 Schema 使用。
    提示：直接读 obj.__dict__ 会包含 SQLAlchemy 内部字段，
    推荐手动列出所有字段。
    """
    # TODO: 返回包含所有业务字段的 dict
    return {
        "id": obj.id,
        "user_id": obj.user_id,
        "question_content": obj.question_content,
        "question_type": obj.question_type,
        "options": obj.options,
        "user_answer": obj.user_answer,
        "correct_answer": obj.correct_answer,
        "analysis": obj.analysis,
        "error_type": obj.error_type,
        "difficulty": obj.difficulty,
        "mastery_status": obj.mastery_status,
        "wrong_count": obj.wrong_count,
        "last_wrong_time": obj.last_wrong_time,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
    }


def save(question: dict) -> dict:
    """
    把 dict 转成 ORM 对象，写入数据库，返回包含所有字段的 dict。
    步骤：
    1. 创建 WrongQuestion(**question)
    2. with SessionLocal() as session:
    3.     session.add(obj)
    4.     session.commit()
    5.     session.refresh(obj)   ← 取回数据库生成的值
    6. 返回 _to_dict(obj)
    """
    # TODO
    # 1. 把 dict 转成 ORM 对象
    obj = WrongQuestion(**question)
    # 2. 打开一个 Session   with   as   相当于try catch
    with SessionLocal() as session:
        # 3. 把对象加入 Session 的“待保存队列”
        session.add(obj)
        # 4. 提交事务，真正执行 INSERT
        session.commit()
        # 5. 从数据库重新加载，确保拿到所有字段的最新值
        session.refresh(obj)
        # 6. 转成 dict 返回
        return _to_dict(obj)


def get_by_id(question_id: str) -> dict | None:
    """
    按 id 查询，不存在返回 None。
    提示：session.get(WrongQuestion, question_id) 最方便。
    """
    # TODO
    with SessionLocal() as session:
        obj = session.get(WrongQuestion, question_id)
        if obj is None:
            return None
        return _to_dict(obj)


def list_all(user_id: str | None = None) -> list[dict]:
    """
    返回全部错题，可按 user_id 过滤。
    提示：用 select(WrongQuestion)，配合 .where() 过滤。
    """
    # TODO
    with SessionLocal() as session:
        stmt = select(WrongQuestion)
        if user_id is not None:
            stmt = stmt.where(WrongQuestion.user_id == user_id)
        orms = session.scalars(stmt).all()
        return [_to_dict(orm) for orm in orms]


def update(question_id: str, fields: dict) -> dict | None:
    """
    按 id 更新部分字段，返回更新后的数据；不存在返回 None。
    步骤：
    1. 查出对象，不存在返回 None
    2. 遍历 fields，setattr(obj, key, value)
    3. session.commit()
    4. session.refresh(obj)
    5. 返回 _to_dict(obj)
    """
    # TODO
    with SessionLocal() as session:
        obj = session.get(WrongQuestion, question_id)
        if obj is None:
            return None
        for key, value in fields.items():
            setattr(obj, key, value)
        session.commit()
        session.refresh(obj)
        return _to_dict(obj)


def delete(question_id: str) -> bool:
    """
    按 id 删除，返回是否删除成功。
    提示：查出对象，session.delete(obj)，commit，返回 True；
    不存在返回 False。
    """
    # TODO
    with SessionLocal() as session:
        obj = session.get(WrongQuestion, question_id)
        if obj is None:
            return False
        session.delete(obj)
        session.commit()
        return True


def count_by_user(
        user_id: str,
        difficulty_min: int | None = None,
        difficulty_max: int | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
) -> int:
    """统计某用户的错题总数。"""
    with SessionLocal() as session:
        stmt = select(func.count()).select_from(WrongQuestion).where(
            WrongQuestion.user_id == user_id
        )
        if difficulty_min is not None:
            stmt = stmt.where(WrongQuestion.difficulty >= difficulty_min)
        if difficulty_max is not None:
            stmt = stmt.where(WrongQuestion.difficulty <= difficulty_max)
        if created_after is not None:
            stmt = stmt.where(WrongQuestion.created_at >= created_after)
        if created_before is not None:
            stmt = stmt.where(WrongQuestion.created_at <= created_before)

        return session.scalar(stmt) or 0


def list_paged(
        user_id: str,
        offset: int,
        limit: int,
        difficulty_min: int | None = None,
        difficulty_max: int | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
) -> list[dict]:
    """分页查询某用户的错题。"""
    with SessionLocal() as session:
        stmt = select(WrongQuestion).where(WrongQuestion.user_id == user_id)

        if difficulty_min is not None:
            stmt = stmt.where(WrongQuestion.difficulty >= difficulty_min)
        if difficulty_max is not None:
            stmt = stmt.where(WrongQuestion.difficulty <= difficulty_max)
        if created_after is not None:
            stmt = stmt.where(WrongQuestion.created_at >= created_after)
        if created_before is not None:
            stmt = stmt.where(WrongQuestion.created_at <= created_before)

        stmt = stmt.order_by(WrongQuestion.created_at.desc()).offset(offset).limit(limit)

        orms = session.scalars(stmt).all()
        return [_to_dict(orm) for orm in orms]


def stats_by_error_type(user_id: str) -> list[dict]:
    """按错误类型统计。"""
    with SessionLocal() as session:
        stmt = (
            select(
                WrongQuestion.error_type,
                func.count(WrongQuestion.id).label("count"),
            )
            .where(WrongQuestion.user_id == user_id)
            .group_by(WrongQuestion.error_type)
            .order_by(func.count(WrongQuestion.id).desc())
        )
        rows = session.execute(stmt).all()
        return [
            {"error_type": row.error_type or "未分类", "count": row.count}
            for row in rows
        ]


def stats_by_knowledge_point(user_id: str) -> list[dict]:
    """按知识点统计当前用户的错题数。"""
    with SessionLocal() as session:
        stmt = (
            select(
                KnowledgePoint.id,
                KnowledgePoint.name,
                func.count(QuestionKnowledge.question_id).label("total"),
            )
            .join(QuestionKnowledge, QuestionKnowledge.knowledge_point_id == KnowledgePoint.id)
            .join(WrongQuestion, WrongQuestion.id == QuestionKnowledge.question_id)
            .where(WrongQuestion.user_id == user_id)
            .group_by(KnowledgePoint.id)
            .order_by(func.count(QuestionKnowledge.question_id).desc())
        )
        rows = session.execute(stmt).all()
        return [
            {
                "knowledge_point_id": row.id,
                "name": row.name,
                "total": row.total,
            }
            for row in rows
        ]
