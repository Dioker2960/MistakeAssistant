from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class KnowledgePoint(Base):
    __tablename__ = "knowledge_point"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    parent_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


class QuestionKnowledge(Base):
    __tablename__ = "question_knowledge"
    __table_args__ = (
        UniqueConstraint("question_id", "knowledge_point_id", name="uk_qk"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    question_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("wrong_question.id", ondelete="CASCADE"), index=True
    )
    knowledge_point_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("knowledge_point.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)