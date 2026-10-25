import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# llm = ChatOpenAI(
#     model=os.getenv("DASHSCOPE_MODEL", "qwen-turbo"),
#     api_key=os.getenv("DASHSCOPE_API_KEY"),
#     base_url=os.getenv("DASHSCOPE_BASE_URL"),
# )
#
# response = llm.invoke("用一句话解释什么是二叉树")
# print(response.content)


# from ai.langchain_llm import get_llm
#
# llm = get_llm()
#
# # 测试一次性调用
# response = llm.invoke([
#     {"role": "system", "content": "你是一个简洁的助手"},
#     {"role": "user", "content": "用一句话解释二叉树"},
# ])
# print("=== invoke ===")
# print(response.content)
#
# # 测试流式调用
# print("\n=== stream ===")
# for chunk in llm.stream([
#     {"role": "user", "content": "用三句话解释二叉树"},
# ]):
#     print(chunk.content, end="", flush=True)
# print()


# from ai.embedding_service import embed, embed_batch
#
# # 单个
# vec = embed("二叉树的定义")
# print("单条向量维度:", len(vec))
# print("前 5 个:", vec[:5])
#
# # 批量
# vecs = embed_batch(["二叉树", "快速排序"])
# print("批量条数:", len(vecs))
# print("每条维度:", len(vecs[0]))

# from ai.embedding_service import build_index_for_all_questions
# from ai import vector_store
#
# vector_store.clear()
# count = build_index_for_all_questions()
# print(f"索引了 {count} 条")
# print(f"索引中条数: {len(vector_store.all_items())}")

from ai import retriever

results = retriever.search("二叉树", top_k=3)
for r in results:
    print(r["question_id"], r["score"])
