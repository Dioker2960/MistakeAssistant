from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000, description="用户消息")
    conversation_id: str | None = Field(default=None, description="会话ID，不传则单轮对话")


class ChatResponse(BaseModel):
    reply: str = Field(description="模型回答")


class Reference(BaseModel):
    question_id: str
    score: float


class RagChatResponse(BaseModel):
    reply: str
    references: list[Reference]
