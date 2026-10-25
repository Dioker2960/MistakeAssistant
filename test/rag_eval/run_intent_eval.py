"""意图评测——验证 Router 准确率。"""

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from intent_eval_set import INTENT_EVAL_SET
from ai.multi_agent import router_node


def evaluate():
    total = 0
    correct = 0
    failed = []
    by_intent = defaultdict(lambda: {"total": 0, "correct": 0})

    for item in INTENT_EVAL_SET:
        total += 1
        expected = item["expected_intent"]
        question = item["question"]

        # 直接调 router_node（不走完整图）
        state = {
            "question": question,
            "history": [],
            "user_id": "",
            "conversation_id": "",
        }
        result = router_node(state)
        actual = result["intent"]

        by_intent[expected]["total"] += 1
        if actual == expected:
            correct += 1
            by_intent[expected]["correct"] += 1
        else:
            failed.append({
                "question": question,
                "expected": expected,
                "actual": actual,
            })

    print(f"\n{'=' * 60}")
    print(f"意图判断准确率")
    print(f"{'=' * 60}")
    print(f"总样本: {total}")
    print(f"准确率: {correct / total:.2%} ({correct}/{total})")

    print(f"\n分类准确率:")
    for intent in sorted(by_intent.keys()):
        stats = by_intent[intent]
        t = stats["total"]
        c = stats["correct"]
        print(f"  {intent:15s} | {c}/{t} ({c / t:.0%})")

    if failed:
        print(f"\n失败案例:")
        for f in failed:
            print(f"  ❌ {f['question'][:30]}")
            print(f"     期望: {f['expected']}, 实际: {f['actual']}")


if __name__ == "__main__":
    evaluate()