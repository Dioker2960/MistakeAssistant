import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

stream = client.chat.completions.create(
    model=os.getenv("LLM_MODEL"),
    messages=[{"role": "user", "content": "用三句话解释什么是二叉树"}],
    stream=True,   # ← 关键参数
)

for chunk in stream:
    if not chunk.choices:        # ← 跳过没有 choices 的 chunk
        continue
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
print()








