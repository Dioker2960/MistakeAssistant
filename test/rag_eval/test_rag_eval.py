"""RAG 检索评测脚本。"""

from rag_eval_set import EVAL_SET
from ai import retriever


def evaluate(top_k: int = 3):
    """跑评测，输出 Hit@K 和 MRR。"""
    total = len(EVAL_SET)
    hit_count = 0
    mrr_sum = 0.0
    failed = []  # 记录失败案例

    for item in EVAL_SET:
        question = item["question"]
        expected = set(item["expected_ids"])

        # 空期望：不算 hit，也不算 miss，单独处理
        if not expected:
            results = retriever.search(question, top_k=top_k)
            if results:
                top_score = results[0]["score"]
                print(f"[空期望] {question[:30]}... → 返回 {len(results)} 条，最高分 {top_score:.4f}")
            continue

        results = retriever.search(question, top_k=top_k)
        retrieved_ids = [r["question_id"] for r in results]

        # Hit@K
        hit = any(rid in expected for rid in retrieved_ids)
        if hit:
            hit_count += 1
        else:
            failed.append({
                "question": question,
                "expected": list(expected)[:2],
                "retrieved": retrieved_ids,
            })

        # MRR
        for rank, rid in enumerate(retrieved_ids, 1):
            if rid in expected:
                mrr_sum += 1.0 / rank
                break

    # 只统计有期望的条目
    effective_total = sum(1 for item in EVAL_SET if item["expected_ids"])
    hit_rate = hit_count / effective_total if effective_total else 0
    mrr = mrr_sum / effective_total if effective_total else 0

    print(f"\n{'=' * 50}")
    print(f"有效测试条数: {effective_total}（另有 {total - effective_total} 条空期望）")
    print(f"Hit@{top_k}: {hit_rate:.2%} ({hit_count}/{effective_total})")
    print(f"MRR: {mrr:.4f}")
    print(f"{'=' * 50}\n")

    if failed:
        print("失败案例：")
        for f in failed:
            print(f"\n问题: {f['question']}")
            print(f"期望: {f['expected']}")
            print(f"实际: {f['retrieved']}")


if __name__ == "__main__":
    evaluate(top_k=3)