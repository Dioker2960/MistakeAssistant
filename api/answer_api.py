import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.auth_api import get_current_user
from services import answer_record_service, wrong_question_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/answers", tags=["答题记录"])


class AnswerSubmit(BaseModel):
    question_id: str
    user_answer: str = Field(default="")
    is_correct: bool
    source_type: str = Field(default="PRACTICE")


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
def submit_answer(data: AnswerSubmit, user: dict = Depends(get_current_user)):
    """提交一次答题结果，更新掌握度。"""
    # 校验题目属于该用户
    q = wrong_question_service.get_one(data.question_id, user["id"])
    if q is None:
        raise HTTPException(status_code=404, detail="错题不存在")

    answer_record_service.record_answer(
        user_id=user["id"],
        question_id=data.question_id,
        user_answer=data.user_answer,
        is_correct=data.is_correct,
        source_type=data.source_type,
    )
    return None


@router.get("/questions/{question_id}")
def get_records(question_id: str, user: dict = Depends(get_current_user)):
    """查某题的所有答题记录。"""
    return answer_record_service.get_records_by_question(user["id"], question_id)


@router.get("/mastery")
def get_mastery(user: dict = Depends(get_current_user)):
    """查当前用户所有知识点的掌握度。"""
    return answer_record_service.get_mastery_list(user["id"])