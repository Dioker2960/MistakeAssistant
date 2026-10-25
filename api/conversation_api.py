import logging

from fastapi import APIRouter, Depends, HTTPException, status

from api.auth_api import get_current_user
from services import conversation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["会话"])


@router.get("")
def list_conversations(user: dict = Depends(get_current_user)):
    """列出当前用户的所有会话。"""
    return conversation_service.list_conversations(user["id"])


@router.get("/{conversation_id}")
def get_messages(
    conversation_id: str,
    user: dict = Depends(get_current_user),
):
    """查某会话的消息历史。"""
    messages = conversation_service.get_messages(user["id"], conversation_id)
    return {"conversation_id": conversation_id, "messages": messages}


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user),
):
    """删除某会话。"""
    ok = conversation_service.delete_conversation(user["id"], conversation_id)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return None
