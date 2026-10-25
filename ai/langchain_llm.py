import logging
import os

from dotenv import load_dotenv
from langchain_core.callbacks import BaseCallbackHandler
from langchain_openai import ChatOpenAI

from core.retry import retry

load_dotenv()

logger = logging.getLogger(__name__)


class LLMLoggingCallback(BaseCallbackHandler):
    """LangChain 回调：自动记录 LLM 调用。"""

    def on_llm_start(self, serialized, prompts, **kwargs):
        model_name = serialized.get("name", "unknown") if serialized else "unknown"
        logger.info("LLM 调用开始: model=%s, prompts=%d", model_name, len(prompts))

    def on_llm_end(self, response, **kwargs):
        # 从 response 里拿 token 使用信息
        try:
            usage = response.llm_output.get("token_usage", {})
            logger.info(
                "LLM 调用完成: input_tokens=%s, output_tokens=%s",
                usage.get("prompt_tokens", "?"),
                usage.get("completion_tokens", "?"),
            )
        except Exception:
            logger.info("LLM 调用完成")

    def on_llm_error(self, error, **kwargs):
        logger.error("LLM 调用失败: %s", error)


# 模块级实例，全局复用
_llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "deepseek-v4-flash"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    temperature=0.7,
    callbacks=[LLMLoggingCallback()],
)


def get_llm() -> ChatOpenAI:
    """返回全局 LLM 实例。"""
    return _llm


@retry(max_attempts=3, delay=1.0)
def invoke_with_retry(llm, messages):
    """带重试的 LLM 调用。"""
    return llm.invoke(messages)
