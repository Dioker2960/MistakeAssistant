from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Conversation(Base):
    __tablename__ = "conversation"
    __table_args__ = (
        Index("idx_user_updated", "user_id", "updated_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(128), default="新会话")
    summary: Mapped[str] = mapped_column(Text, default="")   # ← 新增：中期记忆
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


class Message(Base):
    __tablename__ = "message"
    __table_args__ = (
        Index("idx_conv_created", "conversation_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("conversation.id", ondelete="CASCADE"),
        index=True,
    )
    seq: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    references_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)