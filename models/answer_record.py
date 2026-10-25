from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Float, Index
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class AnswerRecord(Base):
    __tablename__ = "answer_record"
    __table_args__ = (
        Index("idx_ar_user_question", "user_id", "question_id"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    question_id: Mapped[str] = mapped_column(String(32), index=True)
    user_answer: Mapped[str] = mapped_column(String(255), default="")
    is_correct: Mapped[int] = mapped_column(Integer, default=0)
    source_type: Mapped[str] = mapped_column(String(16), default="INITIAL")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class KnowledgeMastery(Base):
    __tablename__ = "knowledge_mastery"
    __table_args__ = (
        Index("idx_km_user_kp", "user_id", "knowledge_point_id", unique=True),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32))
    knowledge_point_id: Mapped[str] = mapped_column(String(32))
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0)
    accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    consecutive_correct: Mapped[int] = mapped_column(Integer, default=0)
    mastery_status: Mapped[str] = mapped_column(String(16), default="薄弱")
    last_answer_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
