import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载 .env（只执行一次）
load_dotenv()

# 模块级客户端，全局复用（不要每次调用都创建）
_client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

_MODEL = os.getenv("LLM_MODEL", "deepseek-v4-flash")


def chat(messages: list[dict]) -> str:
    """
    发送消息列表给大模型，返回回答文本。

    参数:
        messages: [{"role": "user", "content": "..."}, ...]

    返回:
        模型回答的纯文本
    """
    response = _client.chat.completions.create(
        model=_MODEL,
        messages=messages,
    )
    return response.choices[0].message.content


def chat_stream(messages: list[dict]):
    """流式调用大模型，逐段 yield 文本片段。"""
    stream = _client.chat.completions.create(
        model=_MODEL,
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        content = chunk.choices[0].delta.content
        if content:
            yield content
