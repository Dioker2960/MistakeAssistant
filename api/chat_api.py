from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from schemas.chat import ChatRequest, ChatResponse, RagChatResponse
from services import chat_service
from api.auth_api import get_current_user

router = APIRouter(prefix="/chat", tags=["对话"])


@router.post("", response_model=ChatResponse, deprecated=True)
def chat(request: ChatRequest, user: dict = Depends(get_current_user)):
    """发送一条消息给大模型，返回回答"""
    reply = chat_service.ask(request)
    return ChatResponse(reply=reply)


@router.post("/rag", response_model=RagChatResponse, deprecated=True)
def chat_with_rag(request: ChatRequest, user: dict = Depends(get_current_user)):
    """基于错题知识库的问答"""
    result = chat_service.ask_with_rag(
        request.message,
        user["id"],
        request.conversation_id,
    )
    return RagChatResponse(reply=result["reply"], references=result["references"])


@router.post("/rag/stream", deprecated=True)
def chat_with_rag_stream(request: ChatRequest, user: dict = Depends(get_current_user)):
    return StreamingResponse(
        chat_service.ask_with_rag_stream(
            request.message,
            user["id"],
            request.conversation_id,
        ),
        media_type="text/event-stream",
    )