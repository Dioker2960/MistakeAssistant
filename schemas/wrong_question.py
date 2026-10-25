from datetime import datetime
from pydantic import BaseModel, Field


class WrongQuestionBase(BaseModel):
    """所有错题 Schema 共享的字段"""
    question_content: str = Field(min_length=1, description="题目内容")
    question_type: str = Field(default="single_choice", description="题型")
    options: list[str] | None = Field(default=None, description="选择题选项")
    user_answer: str = Field(description="用户答案")
    correct_answer: str = Field(description="正确答案")
    analysis: str = Field(default="", description="题目解析")
    error_type: str = Field(default="未分类", description="错误类型")
    difficulty: int = Field(default=3, ge=1, le=5, description="难度 1~5")


class WrongQuestionCreate(WrongQuestionBase):
    """创建错题时的请求体"""
    knowledge_point_names: list[str] = Field(default_factory=list)


class WrongQuestionUpdate(BaseModel):
    """更新错题时的请求体，所有字段可选"""
    question_content: str | None = None
    question_type: str | None = None
    options: list[str] | None = None
    user_answer: str | None = None
    correct_answer: str | None = None
    analysis: str | None = None
    error_type: str | None = None
    difficulty: int | None = Field(default=None, ge=1, le=5)


class WrongQuestionResponse(WrongQuestionBase):
    """返回给客户端的错题结构"""
    id: str
    user_id: str
    mastery_status: str
    wrong_count: int
    last_wrong_time: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
