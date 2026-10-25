# import json
# import os
#
# import faiss
# import numpy as np
#
# # 文件路径
# _DATA_DIR = "data"
# _INDEX_PATH = os.path.join(_DATA_DIR, "faiss.index")
# _META_PATH = os.path.join(_DATA_DIR, "faiss_meta.json")
#
# # 向量维度
# _DIM = 1024
#
# # 全局状态
# _index: faiss.IndexFlatIP | None = None
# _id_mapping: list[str] = []
# _texts: dict[str, str] = {}
#
#
# def _ensure_loaded() -> None:
#     """
#     确保索引已初始化。
#     如果 _index 为 None，尝试加载磁盘；失败则创建空索引。
#     """
#     global _index
#     if _index is not None:
#         return
#
#     if os.path.exists(_INDEX_PATH) and os.path.exists(_META_PATH):
#         load()
#     else:
#         _index = faiss.IndexFlatIP(_DIM)
#
#
# def _normalize(vector: list[float]) -> np.ndarray:
#     """
#     把向量归一化成单位长度，形状为 (1, DIM) 的 float32 numpy 数组。
#     归一化后，内积 = 余弦相似度。
#     """
#     # TODO 1: 把 list 转成 np.array(dtype="float32")
#     vec = np.array(vector, dtype="float32")
#     # TODO 2: 计算 L2 范数（np.linalg.norm）
#     norm = np.linalg.norm(vec)
#     # TODO 3: 除以范数（注意避免除 0）
#     if norm == 0:
#         return vec.reshape(1, -1)
#     # TODO 4: reshape 成 (1, DIM)
#     return (vec / norm).reshape(1, -1)
#
#
# def add(question_id: str, text: str, vector: list[float]) -> None:
#     """
#     添加一条向量。
#     如果 question_id 已存在，先移除旧的（保持一一对应）。
#     """
#     _ensure_loaded()
#     # TODO 1: 如果 question_id 已经在 _id_mapping 里，跳过（或先删除）
#     if question_id in _texts:
#         return
#     # TODO 2: 把 vector 归一化后 add 到 _index
#     vec = _normalize(vector)
#     _index.add(vec)
#     # TODO 3: _id_mapping.append(question_id)
#     _id_mapping.append(question_id)
#     # TODO 4: _texts[question_id] = text
#     _texts[question_id] = text
#
#
# def get(question_id: str) -> dict | None:
#     """按 question_id 取 {text, ...}，不存在返回 None。"""
#     # 提示：从 _texts 里取。注意你可能需要的信息都从 _texts 和 _id_mapping 里组合
#     if question_id not in _texts:
#         return None
#     return {"text": _texts.get(question_id)}
#
#
# def all_items() -> list[tuple[str, dict]]:
#     """返回所有 (question_id, {"text": ...}) 的列表。"""
#     # 提示：遍历 _texts.items()，构造 (qid, {"text": text}) 的列表
#     return [(question_id, {"text": text}) for question_id, text in _texts.items()]
#
#
# def search(query_vector: list[float], top_k: int = 3) -> list[dict]:
#     """
#     用向量检索最相似的 top_k。
#     返回 [{"question_id": ..., "score": ...}, ...]
#     """
#     _ensure_loaded()
#     if _index.ntotal == 0:
#         return []
#     # TODO 1: 归一化 query_vector
#     q_v = _normalize(query_vector)
#     # TODO 2: distances, indices = _index.search(query_vec, top_k)
#     # 避免 top_k 超过索引数量
#     k = min(top_k, _index.ntotal)
#     distances, indices = _index.search(q_v, k)
#     # TODO 3: distances 和 indices 都是二维数组，取 [0] 拿第一行，查询只拿第一个即可
#     distance, indice = distances[0], indices[0]
#     # TODO 4: 遍历 indices[0]，通过 _id_mapping[idx] 拿到 question_id
#     # TODO 5: 返回 [{"question_id": ..., "score": ...}, ...]
#     result = []
#     for i, idx in enumerate(indice):
#         result.append({
#             "question_id": _id_mapping[int(idx)],
#             "score": float(distance[i])
#         })
#     return result
#
#
# def save() -> None:
#     """把索引和元数据写到磁盘。"""
#     _ensure_loaded()
#     # TODO 1: 确保 data 目录存在（os.makedirs(_DATA_DIR, exist_ok=True)）
#     os.makedirs(_DATA_DIR, exist_ok=True)
#     # TODO 2: faiss.write_index(_index, _INDEX_PATH)
#     faiss.write_index(_index, _INDEX_PATH)
#     # TODO 3: json.dump({"id_mapping": _id_mapping, "texts": _texts}, open(...))
#     with open(_META_PATH, "w", encoding="utf-8") as f:
#         json.dump({"id_mapping": _id_mapping, "texts": _texts}, f, ensure_ascii=False)
#
#
# def load() -> None:
#     """从磁盘加载索引和元数据。"""
#     global _index, _id_mapping, _texts
#     # TODO 1: _index = faiss.read_index(_INDEX_PATH)
#     _index = faiss.read_index(_INDEX_PATH)
#     # TODO 2: 读 _META_PATH 的 JSON
#     # TODO 3: 恢复 _id_mapping 和 _texts
#     with open(_META_PATH, "r", encoding="utf-8") as f:
#         meta_data = json.load(f)
#     _id_mapping = meta_data["id_mapping"]
#     _texts = meta_data["texts"]
#
#
# def is_empty() -> bool:
#     """索引是否为空。"""
#     _ensure_loaded()
#     return _index.ntotal == 0
#
#
# def clear() -> None:
#     """清空索引（用于调试）。"""
#     global _index, _id_mapping, _texts
#     _index = faiss.IndexFlatIP(_DIM)
#     _id_mapping = []
#     _texts = {}
