from uuid import uuid4
from datetime import datetime

from sqlalchemy import select, func

from core.database import SessionLocal
from models.answer_record import AnswerRecord, KnowledgeMastery


# ========== 答题记录 ==========

def save_record(data: dict) -> dict:
    """写入一条答题记录。"""
    obj = AnswerRecord(**data)
    with SessionLocal() as session:
        session.add(obj)
        session.commit()
        return {
            "id": obj.id,
            "question_id": obj.question_id,
            "user_answer": obj.user_answer,
            "is_correct": obj.is_correct,
            "created_at": obj.created_at,
        }


def list_records_by_question(user_id: str, question_id: str) -> list[dict]:
    """查某题的所有答题记录，按时间倒序。"""
    with SessionLocal() as session:
        stmt = (
            select(AnswerRecord)
                .where(
                AnswerRecord.user_id == user_id,
                AnswerRecord.question_id == question_id,
            )
                .order_by(AnswerRecord.created_at.desc())
        )
        objs = session.scalars(stmt).all()
        return [
            {
                "id": o.id,
                "user_answer": o.user_answer,
                "is_correct": o.is_correct,
                "source_type": o.source_type,
                "created_at": o.created_at.isoformat(),
            }
            for o in objs
        ]


# ========== 知识点掌握度 ==========

def get_mastery(user_id: str, kp_id: str) -> dict | None:
    """查某用户在某知识点上的掌握度。"""
    with SessionLocal() as session:
        stmt = select(KnowledgeMastery).where(
            KnowledgeMastery.user_id == user_id,
            KnowledgeMastery.knowledge_point_id == kp_id,
        )
        obj = session.scalars(stmt).first()
        if obj is None:
            return None
        return _mastery_to_dict(obj)


def upsert_mastery(user_id: str, kp_id: str, is_correct: bool) -> dict:
    """累加一次答题结果到掌握度。"""
    with SessionLocal() as session:
        stmt = select(KnowledgeMastery).where(
            KnowledgeMastery.user_id == user_id,
            KnowledgeMastery.knowledge_point_id == kp_id,
        )
        obj = session.scalars(stmt).first()
        now = datetime.now()

        if obj is None:
            obj = KnowledgeMastery(
                id=uuid4().hex,
                user_id=user_id,
                knowledge_point_id=kp_id,
                total_count=0,
                correct_count=0,
                wrong_count=0,
                consecutive_correct=0,
                updated_at=now,
            )
            session.add(obj)

        # 更新计数
        obj.total_count += 1
        if is_correct:
            obj.correct_count += 1
            obj.consecutive_correct += 1
        else:
            obj.wrong_count += 1
            obj.consecutive_correct = 0

        # 正确率
        obj.accuracy = obj.correct_count / obj.total_count

        # 掌握状态（规则）
        obj.mastery_status = _calc_status(obj.accuracy, obj.consecutive_correct)
        obj.last_answer_time = now
        obj.updated_at = now

        session.commit()
        return _mastery_to_dict(obj)


def _calc_status(accuracy: float, consecutive: int) -> str:
    """根据正确率和连续答对计算掌握状态。"""
    if accuracy < 0.6:
        return "薄弱"
    if accuracy >= 0.8 and consecutive >= 3:
        return "已掌握"
    return "学习中"


def _mastery_to_dict(obj: KnowledgeMastery) -> dict:
    return {
        "knowledge_point_id": obj.knowledge_point_id,
        "total_count": obj.total_count,
        "correct_count": obj.correct_count,
        "wrong_count": obj.wrong_count,
        "accuracy": round(obj.accuracy, 4),
        "consecutive_correct": obj.consecutive_correct,
        "mastery_status": obj.mastery_status,
        "last_answer_time": obj.last_answer_time.isoformat() if obj.last_answer_time else "",
    }


def list_mastery(user_id: str) -> list[dict]:
    """查某用户所有知识点的掌握度。"""
    with SessionLocal() as session:
        stmt = (
            select(KnowledgeMastery)
                .where(KnowledgeMastery.user_id == user_id)
                .order_by(KnowledgeMastery.accuracy.asc())
        )
        objs = session.scalars(stmt).all()
        return [_mastery_to_dict(o) for o in objs]


def get_mastery_by_name(user_id: str, kp_name: str) -> dict | None:
    """按知识点名字查掌握度。"""
    from repositories import knowledge_point_repo

    # 1. 按名字查知识点
    kp = knowledge_point_repo.get_by_name(kp_name)
    if kp is None:
        return None

    # 2. 查掌握度
    mastery = get_mastery(user_id, kp["id"])
    if mastery is None:
        return {
            "knowledge_point_id": kp["id"],
            "knowledge_point_name": kp["name"],
            "total_count": 0,
            "correct_count": 0,
            "wrong_count": 0,
            "accuracy": 0.0,
            "consecutive_correct": 0,
            "mastery_status": "无记录",
        }

    mastery["knowledge_point_name"] = kp["name"]
    return mastery
