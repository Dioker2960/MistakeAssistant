import logging

from repositories import answer_record_repo, knowledge_point_repo

logger = logging.getLogger(__name__)


def record_answer(
        user_id: str,
        question_id: str,
        user_answer: str,
        is_correct: bool,
        source_type: str = "PRACTICE",
) -> None:
    """记录一次答题，并更新相关知识点的掌握度。"""
    from uuid import uuid4
    from datetime import datetime

    # 1. 写答题记录
    answer_record_repo.save_record({
        "id": uuid4().hex,
        "user_id": user_id,
        "question_id": question_id,
        "user_answer": user_answer,
        "is_correct": 1 if is_correct else 0,
        "source_type": source_type,
        "created_at": datetime.now(),
    })

    # 2. 更新该题所有知识点的掌握度
    kp_ids = knowledge_point_repo.list_kp_ids_for_question(question_id)
    for kp_id in kp_ids:
        answer_record_repo.upsert_mastery(user_id, kp_id, is_correct)

    logger.info(
        "记录答题: user=%s, qid=%s, correct=%s, kp数=%d",
        user_id, question_id[:8], is_correct, len(kp_ids),
    )


def get_records_by_question(user_id: str, question_id: str) -> list[dict]:
    return answer_record_repo.list_records_by_question(user_id, question_id)


def get_mastery_list(user_id: str) -> list[dict]:
    return answer_record_repo.list_mastery(user_id)