# import os
# from dotenv import load_dotenv
# from openai import OpenAI
#
# # 加载 .env 文件里的环境变量
# load_dotenv()
#
# # 创建客户端
# client = OpenAI(
#     api_key=os.getenv("DASHSCOPE_API_KEY"),
#     base_url=os.getenv("DASHSCOPE_BASE_URL"),
# )
#
# # 发一条消息给模型
# response = client.chat.completions.create(
#     model=os.getenv("DASHSCOPE_MODEL"),
#     messages=[
#         {"role": "user", "content": "用一句话解释什么是二叉树"}
#     ],
# )
#
# # 打印回答
# print(response.choices[0].message.content)

from ai.llm_client import chat

answer = chat([{"role": "user", "content": "用一句话解释什么是二叉树"}])
print(answer)
