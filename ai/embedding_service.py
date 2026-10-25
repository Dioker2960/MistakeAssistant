import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI

from repositories import wrong_question_repo

load_dotenv()

_embeddings = OpenAIEmbeddings(
    model=os.getenv("EMBEDDING_MODEL", "text-embedding-v3"),
    api_key=os.getenv("EMBEDDING_API_KEY"),
    base_url=os.getenv("EMBEDDING_BASE_URL"),
    check_embedding_ctx_length=False,  # ← 关键参数，下面解释
    chunk_size=10,   # ← 每次最多 10 条，自动分批
)

_client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

# _EMBEDDING_MODEL = os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v3")


def embed(text: str) -> list[float]:
    """把一段文本转成向量。"""
    # response = _client.embeddings.create(
    #     model=_EMBEDDING_MODEL,
    #     input=text,
    # )
    return _embeddings.embed_query(text)


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    批量把多段文本转成向量。
    千问的 Embedding 接口支持一次传多条文本，比循环调用快很多。
    """
    # response = _client.embeddings.create(
    #     model=_EMBEDDING_MODEL,
    #     input=texts,
    # )
    # response.data 是一个列表，顺序和输入一致
    # return [item.embedding for item in response.data]

    return _embeddings.embed_documents(texts)


def build_question_text(question: dict) -> str:
    """
    把错题 dict 拼成一段适合 Embedding 的文本。

    输入示例:
        {
            "question_content": "下列关于二叉树的说法正确的是？",
            "user_answer": "A",
            "correct_answer": "B",
            "analysis": "二叉树每个节点最多有两个子节点。",
            "error_type": "概念理解错误",
        }

    输出示例:
        "题目：下列关于二叉树的说法正确的是？\n"
        "用户答案：A\n"
        "正确答案：B\n"
        "题目解析：二叉树每个节点最多有两个子节点。\n"
        "错误类型：概念理解错误"
    """
    # TODO: 拼接字段
    # 提示：
    #   parts = []
    #   if question.get("question_content"):
    #       parts.append(f"题目：{question['question_content']}")
    #   ...
    #   return "\n".join(parts)
    parts = []
    if question.get("question_content"):
        parts.append(f"题目：{question['question_content']}")
    if question.get("options"):
        options_text = " | ".join(question["options"])
        parts.append(f"选项：{options_text}")
    if question.get("user_answer"):
        parts.append(f"用户答案：{question['user_answer']}")
    if question.get("correct_answer"):
        parts.append(f"正确答案：{question['correct_answer']}")
    if question.get("analysis"):
        parts.append(f"题目解析：{question['analysis']}")
    if question.get("error_type"):
        parts.append(f"错误类型：{question['error_type']}")

    return "\n".join(parts)


# def build_index_for_all_questions() -> int:
#     """
#     从 MySQL 读出所有错题，批量向量化，存入 vector_store。
#     返回成功索引的错题数量。
#     """
#     # 1. 从 MySQL 读出所有错题（返回 dict 列表）
#     questions = wrong_question_repo.list_all()
#     if not questions:
#         return 0
#
#     # 2. 对每个错题，拼接文本
#     question_ids = []
#     texts = []
#     for q in questions:
#         question_ids.append(q["id"])
#         texts.append(build_question_text(q))
#
#     # 3. 批量向量化
#     vectors = embed_batch(texts)
#
#     # 清空旧的，重新构建
#     vector_store.clear()
#
#     # 4. 逐个存入 vector_store
#     for qid, text, vec in zip(question_ids, texts, vectors):
#         vector_store.add(qid, text, vec)
#     # 持久化到磁盘
#     vector_store.save()
#
#     return len(question_ids)
