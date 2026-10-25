import math

from ai import embedding_service, vector_store, langchain_store


# 不需要了，使用FAISS解决了
# def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
#     """计算两个向量的余弦相似度。"""
#     """计算两个向量的余弦相似度，范围 [-1, 1]。"""
#     # 点积
#     dot = sum(a * b for a, b in zip(vec_a, vec_b))
#     # 模长
#     norm_a = math.sqrt(sum(a * a for a in vec_a))
#     norm_b = math.sqrt(sum(b * b for b in vec_b))
#     # 避免除以 0
#     if norm_a == 0 or norm_b == 0:
#         return 0.0
#     return dot / (norm_a * norm_b)


# def search(query: str, top_k: int = 3) -> list[dict]:
#     """
#     根据用户问题，检索最相似的 top_k 道错题。
#
#     步骤：
#
#     5. 取前 top_k 条，返回 [{"question_id": ..., "score": ..., "text": ...}, ...]
#     """
#     # TODO 1: query_vec = embedding_service.embed(query)
#     # TODO 2: 拿到所有记录 items = vector_store.all_items()
#     # TODO 3: 对每条记录算相似度，存成 [(qid, score, text), ...]
#     # TODO 4: 按 score 降序排序
#     # TODO 5: 返回前 top_k 条
#     # 1. 把 query 向量化（embed）
#     question_vec = embedding_service.embed(query)
#     # 2. 遍历 vector_store 里所有记录
#     results = vector_store.search(question_vec, top_k)
#     # 3. 补上 text 字段
#     for r in results:
#         record = vector_store.get(r["question_id"])
#         r["text"] = record["text"] if record else ""
#     return results


def search(query: str, top_k: int = 3, min_score: float = 0.5, user_id: str | None = None) -> list[dict]:
    """
    根据用户问题，检索最相似的 top_k 道错题。
    返回 [{"question_id": ..., "score": ..., "text": ...}, ...]
    """
    return langchain_store.search(query, top_k, min_score, user_id=user_id)
