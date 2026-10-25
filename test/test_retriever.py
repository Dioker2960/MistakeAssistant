from ai.embedding_service import build_index_for_all_questions
from ai import retriever

# 先构建索引
build_index_for_all_questions()

# 检索
results = retriever.search("二叉树有什么特性？", top_k=3)

for i, r in enumerate(results, 1):
    print(f"\n--- Top {i} ---")
    print(f"分数: {r['score']:.4f}")
    print(f"内容: {r['text'][:80]}...")