"""RAG 评测 v2：多指标 + 分类统计。"""

import sys
from collections import defaultdict
from pathlib import Path


# 把项目根目录加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rag_eval_v2 import EVAL_SET
from ai import retriever


def evaluate(top_k: int = 3):
    total = 0
    hit_count = 0
    mrr_sum = 0.0
    failed = []
    by_category = defaultdict(lambda: {"total": 0, "hit": 0, "mrr": 0.0})

    print("=" * 60)
    print("空答案测试（不计入总分）")
    print("=" * 60)

    for item in EVAL_SET:
        question = item["question"]
        expected = set(item["expected_ids"])
        category = item.get("category", "unknown")

        if not expected:
            results = retriever.search(question, top_k=top_k)
            if results:
                top = results[0]["score"]
                print(f"[{category}] {question[:25]} → {len(results)} 条, 最高分 {top:.4f}")
            else:
                print(f"[{category}] {question[:25]} → 0 条 ✅")
            continue

        total += 1
        by_category[category]["total"] += 1

        results = retriever.search(question, top_k=top_k)
        retrieved_ids = [r["question_id"] for r in results]

        hit = any(rid in expected for rid in retrieved_ids)
        if hit:
            hit_count += 1
            by_category[category]["hit"] += 1
        else:
            failed.append({
                "question": question,
                "expected": list(expected),
                "retrieved": retrieved_ids,
                "category": category,
            })

        for rank, rid in enumerate(retrieved_ids, 1):
            if rid in expected:
                mrr_sum += 1.0 / rank
                by_category[category]["mrr"] += 1.0 / rank
                break

    hit_rate = hit_count / total if total else 0
    mrr = mrr_sum / total if total else 0

    print(f"\n{'=' * 60}")
    print(f"总体指标")
    print(f"{'=' * 60}")
    print(f"有效测试: {total} 条")
    print(f"Hit@{top_k}: {hit_rate:.2%} ({hit_count}/{total})")
    print(f"MRR: {mrr:.4f}")

    print(f"\n{'=' * 60}")
    print(f"分类指标")
    print(f"{'=' * 60}")
    for cat in sorted(by_category.keys()):
        stats = by_category[cat]
        t = stats["total"]
        h = stats["hit"]
        m = stats["mrr"] / t if t else 0
        print(f"{cat:15s} | Hit@{top_k}: {h / t:.2%} ({h}/{t}) | MRR: {m:.4f}")

    if failed:
        print(f"\n{'=' * 60}")
        print(f"失败案例 ({len(failed)} 条)")
        print(f"{'=' * 60}")
        for f in failed:
            print(f"\n[{f['category']}] {f['question']}")
            print(f"  期望: {f['expected'][:2]}")
            print(f"  实际: {f['retrieved']}")


if __name__ == "__main__":
    evaluate(top_k=3)