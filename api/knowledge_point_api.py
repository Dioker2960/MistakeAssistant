import logging

from fastapi import APIRouter, status, Depends, HTTPException

from api.auth_api import get_current_user
from schemas.knowledge_point import KnowledgePointResponse, KnowledgePointCreate, QuestionKnowledgeCreate
from services import knowledge_point_service, wrong_question_service
from schemas.wrong_question import WrongQuestionResponse

logger = logging.getLogger(__name__)


# 所有路由统一加前缀和标签
router = APIRouter(prefix="/knowledge-points", tags=["知识点管理"])


@router.post(
    "",
    response_model=KnowledgePointResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_kp(
        data: KnowledgePointCreate,
        user: dict = Depends(get_current_user),
):
    """创建知识点。"""
    # TODO: 调用 services 的 create，返回结果
    return knowledge_point_service.create(data)


# GET /knowledge-points	列出所有知识点
@router.get("", response_model=list[KnowledgePointResponse])
def list_knowledge_points(
        user: dict = Depends(get_current_user)
):
    """列出所有知识点。"""
    return knowledge_point_service.list_all()


@router.get("/{kp_id}/questions", response_model=list[WrongQuestionResponse])
def get_knowledge_points(
        kp_id: str,
        user: dict = Depends(get_current_user)
):
    """查某知识点下当前用户的错题。"""
    return knowledge_point_service.get_questions_by_kp(kp_id, user["id"])
