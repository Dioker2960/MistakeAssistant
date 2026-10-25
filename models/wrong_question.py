from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class WrongQuestion(Base):
    __tablename__ = "wrong_question"

    # 主键
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)

    # 题目相关
    question_content: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(String(32), default="single_choice")
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)  # ← 存 JSON

    user_answer: Mapped[str] = mapped_column(String(255))
    correct_answer: Mapped[str] = mapped_column(String(255))
    analysis: Mapped[str] = mapped_column(Text, default="")
    error_type: Mapped[str] = mapped_column(String(64), default="未分类")
    difficulty: Mapped[int] = mapped_column(Integer, default=3)

    # 状态字段
    mastery_status: Mapped[str] = mapped_column(String(16), default="薄弱")
    wrong_count: Mapped[int] = mapped_column(Integer, default=1)

    # 时间字段
    last_wrong_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)