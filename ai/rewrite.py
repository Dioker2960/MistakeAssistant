# ai/rewrite.py
import logging

from ai import prompts
from ai.langchain_llm import get_llm

logger = logging.getLogger(__name__)


def rewrite_question(question: str, history: list[dict]) -> str:
    """
    结合历史，把当前问题改写为完整问题。
    没有历史时直接返回原问题。
    """
    if not history:
        logger.debug("改写: 无历史，跳过。问题=%s...", question[:30])
        return question

    logger.debug("改写: 有 %d 条历史，开始改写", len(history))
    messages = prompts.build_rewrite_messages(question, history)
    response = get_llm().invoke(messages)
    rewritten = response.content.strip()
    logger.info("改写: %s... → %s...", question[:20], rewritten)

    return rewritten
