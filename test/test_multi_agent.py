from ai.multi_agent import app

questions = [
    ("什么是二叉树？", "knowledge"),
    ("二叉树那道题为什么选B？", "diagnosis"),
    ("有什么和二叉树类似的题？", "recommendation"),
    ("我一共有多少错题？", "stats"),
    ("我概念理解错误的题有哪些？", "stats"),
]

for q, expected in questions:
    print(f"\n{'=' * 60}")
    print(f"问题: {q}")
    print(f"期望意图: {expected}")
    print(f"{'=' * 60}")

    result = app.invoke({
        "conversation_id": "",
        "question": q,
        "history": [],
    })

    print(f"判断意图: {result['intent']}")
    print(f"回答: {result['messages'][-1].content[:150]}...")