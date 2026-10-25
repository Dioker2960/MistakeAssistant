import logging

from fastapi import APIRouter, Depends

from api.auth_api import get_current_user
from services import wrong_question_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["统计"])


@router.get("/knowledge-points")
def stats_by_knowledge_point(user: dict = Depends(get_current_user)):
    """按知识点统计当前用户的错题数。"""
    return wrong_question_service.stats_by_knowledge_point(user["id"])


@router.get("/error-types")
def stats_by_error_type(user: dict = Depends(get_current_user)):
    """按错误类型统计当前用户的错题数。"""
    return wrong_question_service.stats_by_error_type(user["id"])