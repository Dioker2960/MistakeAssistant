# import os
# from dotenv import load_dotenv
# from openai import OpenAI
#
# load_dotenv()
#
# client = OpenAI(
#     api_key=os.getenv("DASHSCOPE_API_KEY"),
#     base_url=os.getenv("DASHSCOPE_BASE_URL"),
# )
#
# # 千问的 Embedding 模型
# response = client.embeddings.create(
#     model="text-embedding-v3",
#     input="二叉树的定义",
# )
#
# vec = response.data[0].embedding
# print("向量维度:", len(vec))
# print("前 5 个数:", vec[:5])

# from ai.embedding_service import embed, build_question_text
# from ai import vector_store
#
# question = {
#     "question_content": "下列关于二叉树的说法正确的是？",
#     "user_answer": "A",
#     "correct_answer": "B",
#     "analysis": "二叉树每个节点最多有两个子节点。",
#     "error_type": "概念理解错误",
# }
#
# text = build_question_text(question)
# print("拼接后的文本：")
# print(text)
# print()
#
# vec = embed(text)
# print("向量维度:", len(vec))
# print("前 5 个数:", vec[:5])
#
#
# # 存入
# vector_store.add("q1", text, vec)
#
# # 读取
# record = vector_store.get("q1")
# print("取出的文本:", record["text"])
# print("向量的前 3 个数:", record["vector"][:3])
#
# # 全部
# print("总数:", len(vector_store.all_items()))
#
# # 删除
# print("删除成功:", vector_store.remove("q1"))
# print("删除后总数:", len(vector_store.all_items()))

from ai.embedding_service import build_index_for_all_questions
from ai import vector_store

# 确认 MySQL 里有数据
count = build_index_for_all_questions()
print(f"已索引 {count} 道错题")

# 检查索引内容
items = vector_store.all_items()
print(f"vector_store 中共 {len(items)} 条记录")
for qid, record in items[:3]:   # 只打印前 3 条
    print(f"\nID: {qid}")
    print(f"文本前 50 字: {record['text'][:50]}...")
    print(f"向量维度: {len(record['vector'])}")