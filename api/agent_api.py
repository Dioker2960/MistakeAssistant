import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from ai.multi_agent import app as agent_graph
from api.auth_api import get_current_user

router = APIRouter(prefix="/chat", tags=["Agent"])

logger = logging.getLogger(__name__)


class AgentRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = Field(default=None, description="会话 ID，不传则单轮")


class AgentResponse(BaseModel):
    reply: str


@router.post("/agent", response_model=AgentResponse)
def chat_with_agent(
        request: AgentRequest,
        user: dict = Depends(get_current_user),
):
    """带工具调用的问答（LLM 自动决定是否调工具）"""
    logger.info("Agent 请求: %s", request.message[:30])
    result = agent_graph.invoke({
        "user_id": user["id"],
        "conversation_id": request.conversation_id or "",
        "question": request.message,
        "history": [],   # load_history_node 会从 Redis 覆盖
    })
    reply = result["messages"][-1].content
    logger.info("Agent 响应完成: 消息数=%d", len(result["messages"]))
    return AgentResponse(reply=reply)


@router.post("/agent/stream")
async def chat_with_agent_stream(
        request: AgentRequest,
        user: dict = Depends(get_current_user),  # ← 如果还没加，加上
):
    logger.info("Agent 流式请求: %s", request.message[:30])

    async def event_generator():
        async for event in agent_graph.astream_events(
                {
                    "user_id": user["id"],
                    "conversation_id": request.conversation_id or "",
                    "question": request.message,
                    "history": [],
                },
                version="v2",
        ):
            # ← tool 节点执行完，读 references
            if event["event"] == "on_chain_end":
                node = event["metadata"].get("langgraph_node")
                if node == "tool":
                    output = event["data"].get("output", {})
                    # output 可能是 dict（State 更新）或带 .references 的对象
                    refs = None
                    if isinstance(output, dict):
                        refs = output.get("references")
                    else:
                        refs = getattr(output, "references", None)

                    if refs:
                        logger.info("[references] 推送 %d 条", len(refs))
                        yield f"event: references\ndata: {json.dumps({'references': refs}, ensure_ascii=False)}\n\n"

            # LLM 流式输出
            if event["event"] == "on_chat_model_stream":
                node = event["metadata"].get("langgraph_node")
                if node == "agent":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        yield f"data: {json.dumps({'text': chunk.content}, ensure_ascii=False)}\n\n"

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
