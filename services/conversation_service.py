from repositories import conversation_repo


def list_conversations(user_id: str) -> list[dict]:
    """列出用户的所有会话。"""
    return conversation_repo.list_conversations(user_id)


def get_messages(user_id: str, conversation_id: str) -> list[dict]:
    """查某会话的消息。"""
    return conversation_repo.get_messages(user_id, conversation_id)


def delete_conversation(user_id: str, conversation_id: str) -> bool:
    """删除某会话。"""
    return conversation_repo.delete_conversation(user_id, conversation_id)