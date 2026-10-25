import json
import logging
from uuid import uuid4
from datetime import datetime

from sqlalchemy import select, delete, func
from core.database import SessionLocal
from models.conversation import Conversation, Message
from core.redis_client import get_client

logger = logging.getLogger(__name__)


def _to_dict(obj: Message) -> dict:
    """
    把 ORM 对象转成 dict，供 Service 和 Schema 使用。
    提示：直接读 obj.__dict__ 会包含 SQLAlchemy 内部字段，
    推荐手动列出所有字段。
    """
    # TODO: 返回包含所有业务字段的 dict
    return {
        "id": obj.id,
        "conversation_id": obj.conversation_id,
        "role": obj.role,
        "content": obj.content,
        "references_json": obj.references_json,
        "created_at": obj.created_at,
    }


def get_messages(user_id: str, conversation_id: str) -> list[dict]:
    """
    读取会话的历史消息列表。
    只返回属于该用户的会话的消息。
    """
    # TODO 1: 先验证 conversation 存在且属于 user_id
    with SessionLocal() as session:
        obj = session.get(Conversation, conversation_id)
        if obj is None or obj.user_id != user_id:
            return []
        # TODO 2: 按 created_at 升序查 message
        # 2. 按 created_at 升序查消息
        stmt = (
            select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.seq.asc())
        )
        objs = session.scalars(stmt).all()
        # 3. 转成 dict
        result = []
        for m in objs:
            # references_json 是字符串，解析成 list
            try:
                refs = json.loads(m.references_json) if m.references_json else []
            except (json.JSONDecodeError, TypeError):
                refs = []

            result.append({
                "role": m.role,
                "content": m.content,
                "references": refs,
                "created_at": m.created_at.isoformat(),
            })
        return result


def append_messages(user_id: str, conversation_id: str, new_messages: list[dict]) -> None:
    """
    追加消息。
    如果会话不存在，自动创建（标题取首条用户消息的前 20 字）。
    """
    # TODO 1: 查 conversation，不存在则创建
    now = datetime.now()
    with SessionLocal() as session:
        conv = session.get(Conversation, conversation_id)
        if conv is None:
            title = "新会话"
            # 从 new_messages 里找第一条 user 消息做标题
            for message in new_messages:
                if message["role"] == "user":
                    title = message["content"][:20]
                    break
            conv = Conversation(
                id=conversation_id,
                user_id=user_id,
                title=title,
                created_at=now,
                updated_at=now,
            )
            session.add(conv)
        # TODO 2: 遍历 new_messages，逐个 add 到 message 表
        max_seq = session.scalar(
            select(func.max(Message.seq)).where(Message.conversation_id == conversation_id)
        ) or 0
        for i, message in enumerate(new_messages, 1):
            session.add(Message(
                id=uuid4().hex,
                conversation_id=conversation_id,
                seq=max_seq + i,
                role=message["role"],
                content=message["content"],
                references_json=json.dumps(message.get("references", []), ensure_ascii=False),
                created_at=datetime.now(),
            ))
        #         references 字段用 json.dumps 存到 references_json
        # TODO 3: 更新 conversation 的 updated_at
        conv.updated_at = datetime.now()
        session.commit()


def delete_conversation(user_id: str, conversation_id: str) -> bool:
    """
    删除会话。级联删除所有消息。
    只删除属于该用户的会话。
    """
    # TODO 1: 查 conversation，验证 user_id 匹配
    with SessionLocal() as session:
        obj = session.get(Conversation, conversation_id)
        if obj is None or obj.user_id != user_id:
            return False
        # TODO 2: session.delete(conv) → 级联删除消息
        session.delete(obj)
        session.commit()
        return True


def list_conversations(user_id: str) -> list[dict]:
    """
    列出用户的所有会话。
    返回：[{conversation_id, title, updated_at, message_count}, ...]，按时间倒序。
    """
    # TODO 1: 查该用户的所有 conversation，按 updated_at 倒序
    with SessionLocal() as session:
        # TODO 2: 对每个会话统计 message 数量
        #         提示：可以用子查询或简单循环
        # TODO 3: 组装成返回结构
        stmt = (
            select(
                Conversation.id,
                Conversation.title,
                Conversation.updated_at,
                func.count(Message.id).label("message_count"),
            )
                .outerjoin(Message, Message.conversation_id == Conversation.id)
                .where(Conversation.user_id == user_id)
                .group_by(Conversation.id)
                .order_by(Conversation.updated_at.desc())
        )
        rows = session.execute(stmt).all()
        return [
            {
                "conversation_id": row.id,
                "title": row.title,
                "updated_at": row.updated_at,
                "message_count": row.message_count,
            }
            for row in rows
        ]


def get_summary(user_id: str, conversation_id: str) -> str:
    """获取会话的摘要。"""
    with SessionLocal() as session:
        conv = session.get(Conversation, conversation_id)
        if conv is None or conv.user_id != user_id:
            return ""
        return conv.summary or ""


def update_summary(user_id: str, conversation_id: str, summary: str) -> None:
    """更新会话摘要。"""
    with SessionLocal() as session:
        conv = session.get(Conversation, conversation_id)
        if conv is None or conv.user_id != user_id:
            return
        conv.summary = summary
        session.commit()


def count_messages(conversation_id: str) -> int:
    """统计会话消息数。"""
    with SessionLocal() as session:
        stmt = select(func.count()).select_from(Message).where(
            Message.conversation_id == conversation_id
        )
        return session.scalar(stmt) or 0


def get_oldest_messages(conversation_id: str, limit: int) -> list[dict]:
    """取最旧的 N 条消息。"""
    with SessionLocal() as session:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.seq.asc())
            .limit(limit)
        )
        objs = session.scalars(stmt).all()
        return [
            {
                "id": o.id,
                "role": o.role,
                "content": o.content,
            }
            for o in objs
        ]


def delete_messages_by_ids(ids: list[str]) -> None:
    """按 id 批量删除消息。"""
    if not ids:
        return
    with SessionLocal() as session:
        stmt = delete(Message).where(Message.id.in_(ids))
        session.execute(stmt)
        session.commit()
