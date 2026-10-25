from datetime import datetime
from pydantic import BaseModel, Field


class KnowledgePointCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    parent_id: str | None = None
    description: str = ""


class KnowledgePointResponse(BaseModel):
    id: str
    name: str
    parent_id: str | None
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestionKnowledgeCreate(BaseModel):
    """给题目打知识点的请求。"""
    knowledge_point_ids: list[str] = Field(default_factory=list)
