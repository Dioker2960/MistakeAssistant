import os

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import logging
from ai.embedding_service import _embeddings  # 复用 LangChain 的 embedding 实例

logger = logging.getLogger(__name__)

load_dotenv()

# 项目根目录（langchain_store.py 在 ai/ 下，往上两级）
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STORE_DIR = os.path.join(_BASE_DIR, "data", "faiss_lc")

# 全局缓存
_store: FAISS | None = None


def is_empty() -> bool:
    """索引是否为空（磁盘文件不存在或未加载）。"""
    return _get_store() is None


def count() -> int:
    """返回索引里的文档数。"""
    store = _get_store()
    if store is None:
        return 0
    return store.index.ntotal


def build_store(questions: list[dict]) -> None:
    """
    用错题列表构建 FAISS store，并保存到磁盘。
    每个错题是一个 dict（含 id 和拼接好的文本）。
    """
    # TODO 1: 把 questions 转成 list[Document]
    #         每个 Document：
    #           page_content = 文本
    #           metadata = {"question_id": id}
    #         提示：Document(page_content=..., metadata={...})
    global _store
    documents = []
    for q in questions:
        documents.append(Document(
            page_content=q["text"],
            metadata={
                "question_id": q["id"],
                "user_id": q["user_id"],
            }
        ))
    # TODO 2: 用 FAISS.from_documents(docs, _embeddings) 构建 store
    #         from_documents 是类方法，不是实例方法
    _store = FAISS.from_documents(documents, _embeddings)
    # TODO 3: store.save_local(_STORE_DIR)
    _store.save_local(_STORE_DIR)


def add_document(question_id: str, user_id: str, text: str) -> None:
    """增量添加一条文档到索引（不重建）。"""
    global _store

    # 确保 store 已加载
    store = _get_store()
    if store is None:
        return
    _store = store

    doc = Document(
        page_content=text,
        metadata={"question_id": question_id, "user_id": user_id},
    )
    _store.add_documents([doc])
    _store.save_local(_STORE_DIR)
    logger.info("[FAISS] 增量添加: question_id=%s", question_id[:8])


def _get_store() -> FAISS | None:
    """
    获取全局 store。内存没有就从磁盘加载，加载失败返回 None。
    懒加载模式
    """
    # TODO 1: 检查 _STORE_DIR 是否存在（os.path.exists）
    # TODO 2: 用 FAISS.load_local(路径, embeddings, allow_dangerous_deserialization=True)
    #         注意：allow_dangerous_deserialization=True 是必须的，否则会拒绝加载
    global _store
    # 如果_store不为空就直接返回，为空说明还没有加载，则从磁盘加载
    if _store is not None:
        return _store
    if os.path.exists(_STORE_DIR):
        _store = FAISS.load_local(_STORE_DIR, _embeddings, allow_dangerous_deserialization=True)
    return _store


def load_store() -> FAISS | None:
    """对外暴露的加载函数，实际转发给 _get_store。"""
    return _get_store()


def search(query: str, top_k: int = 3, min_score: float = 0.0, user_id: str = None) -> list[dict]:
    """
    检索最相似的 top_k 条，返回和旧接口一致的格式：
    [{"question_id": ..., "score": ..., "text": ...}, ...]
    """
    # TODO 1: store = load_store()，为 None 返回 []
    # TODO 2: results = store.similarity_search_with_score(query, k=top_k)
    #         similarity_search_with_score 返回 [(Document, score), ...]
    #         注意：这里的 score 是"距离"，越小越相似（L2 距离），和你之前的相似度相反
    store = load_store()
    if store is None:
        return []
    results = store.similarity_search_with_score(query, k=top_k, filter={"user_id": user_id} if user_id else None,)
    # TODO 3: 转成统一格式：
    #         for doc, distance in results:
    #             {"question_id": doc.metadata["question_id"],
    #              "score": 1 / (1 + distance),   # 距离转相似度，范围 (0, 1]
    #              "text": doc.page_content}
    res = []
    for doc, distance in results:
        score = float(1 / (1 + distance))
        if score < min_score:      # ← 过滤
            continue
        res.append({
            "question_id": doc.metadata["question_id"],
            "score": score,  # 距离转相似度，范围 (0, 1]
            "text": doc.page_content,
        })
    return res
