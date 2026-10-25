import logging

from ai.langchain_llm import get_llm

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """你是一个对话摘要助手。

下面是用户和 AI 助手的对话历史。请把它们压缩成一段简短的摘要，
保留：
1. 用户关心的主要话题（如"二叉树的性质"、"TCP 三次握手"）
2. 用户已经问过的问题（避免重复回答）
3. 关键结论或结论性的信息

要求：
- 300 字以内
- 不要简单追加，而是重新组织
- 用第三人称描述（"用户问了…"、"助手解释了…"）
- 只输出摘要，不要其他内容

对话历史：
{history}

摘要："""


def summarize_history(history: list[dict], existing_summary: str = "") -> str:
    """
    把历史消息压缩成摘要。
    如果已有摘要，会在其基础上滚动更新。
    """
    if not history:
        return existing_summary

    # 拼成对话文本
    lines = []
    if existing_summary:
        lines.append(f"【已有摘要】{existing_summary}\n")

    for m in history:
        role = "用户" if m["role"] == "user" else "助手"
        lines.append(f"{role}：{m['content']}")

    history_text = "\n".join(lines)

    messages = [{"role": "user", "content": SUMMARY_PROMPT.format(history=history_text)}]

    try:
        response = get_llm().invoke(messages)
        summary = response.content.strip()
        logger.info("生成摘要成功，长度=%d", len(summary))
        return summary
    except Exception as e:
        logger.error("生成摘要失败: %s", e)
        return existing_summary  # 失败时保留旧摘要
