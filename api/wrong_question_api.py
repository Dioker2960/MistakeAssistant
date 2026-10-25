from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends, Query

from api.auth_api import get_current_user
from schemas.knowledge_point import QuestionKnowledgeCreate, KnowledgePointResponse
from schemas.wrong_question import (
    WrongQuestionCreate,
    WrongQuestionResponse,
    WrongQuestionUpdate,
)
from services import wrong_question_service, knowledge_point_service
from pydantic import BaseModel, Field

import logging
logger = logging.getLogger(__name__)

# 所有路由统一加前缀和标签
router = APIRouter(prefix="/wrong-questions", tags=["错题管理"])


class WrongQuestionListResponse(BaseModel):
    """分页列表响应。"""
    items: list[WrongQuestionResponse]
    total: int
    page: int
    size: int


@router.post(
    "",
    response_model=WrongQuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_wrong_question(
        data: WrongQuestionCreate,
        user: dict = Depends(get_current_user),
):
    """新增一道错题"""
    # TODO: 调用 services 的 create，返回结果
    logger.info("接收创建错题请求: %s", data.question_content[:30])
    question = wrong_question_service.create(data, user["id"])
    logger.info("创建错题成功: id=%s", question["id"])
    return question


@router.get("", response_model=WrongQuestionListResponse)
def list_wrong_questions(
        page: int = 1,
        size: int = 10,
        difficulty_min: int | None = Query(default=None, ge=1, le=5),
        difficulty_max: int | None = Query(default=None, ge=1, le=5),
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        user: dict = Depends(get_current_user),
):
    """分页查询当前用户的错题，支持难度、时间范围筛选。"""
    # TODO: 调用 services 的 get_list，把 user_id 传进去，返回结果
    logger.info(
        "list_wrong_questions: user_id=%s, page=%d, diff=[%s,%s], time=[%s,%s]",
        user["id"], page, difficulty_min, difficulty_max, created_after, created_before,
    )
    return wrong_question_service.get_list(
        user["id"], page, size,
        difficulty_min, difficulty_max, created_after, created_before,
    )


@router.get("/{question_id}", response_model=WrongQuestionResponse)
def get_wrong_question(
        question_id: str,
        user: dict = Depends(get_current_user)
):
    """查看错题详情"""
    # TODO:
    # 1. 调用 services 的 get_one
    # 2. 如果返回 None，抛 HTTPException(404, "错题不存在")
    # 3. 否则返回查询结果
    question = wrong_question_service.get_one(question_id, user["id"])
    if question is None:
        logger.warning("查询错题不存在: id=%s", question_id)
        raise HTTPException(status_code=404, detail="错题不存在")
    return question


@router.put("/{question_id}", response_model=WrongQuestionResponse)
def update_wrong_question(
        question_id: str,
        data: WrongQuestionUpdate,
        user: dict = Depends(get_current_user)
):
    """修改错题"""
    # TODO:
    # 1. 调用 services 的 update_one
    # 2. 如果返回 None，抛 HTTPException(404, "错题不存在")
    # 3. 否则返回更新后的结果
    question = wrong_question_service.update_one(question_id, data, user["id"])
    if question is None:
        raise HTTPException(status_code=404, detail="错题不存在")
    return question


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wrong_question(
        question_id: str,
        user: dict = Depends(get_current_user)
):
    """删除错题"""
    # TODO:
    # 1. 调用 services 的 delete_one
    # 2. 如果返回 False，抛 HTTPException(404, "错题不存在")
    # 3. 成功则返回 None（204 不能带 body）
    ok = wrong_question_service.delete_one(question_id, user["id"])
    if not ok:
        logger.warning("删除错题不存在: id=%s", question_id)
        raise HTTPException(status_code=404, detail="错题不存在")
    logger.info("删除错题: id=%s", question_id)
    return None


@router.get("/{question_id}/knowledge-points", response_model=list[KnowledgePointResponse])
def get_kps_by_question(
    question_id: str,
    user: dict = Depends(get_current_user),
):
    """查某题关联的知识点。"""
    # 先校验题目属于当前用户
    question = wrong_question_service.get_one(question_id, user["id"])
    if question is None:
        raise HTTPException(status_code=404, detail="错题不存在")
    return knowledge_point_service.get_kps_by_question(question_id)


@router.post("/{question_id}/knowledge-points", status_code=204)
def tag_question(
    question_id: str,
    data: QuestionKnowledgeCreate,
    user: dict = Depends(get_current_user),
):
    """给题目打知识点（覆盖旧关联）。"""
    knowledge_point_service.tag_question(question_id, data.knowledge_point_ids, user["id"])
    return None
