from repositories import wrong_question_repo
from ai import langchain_store
from ai.embedding_service import build_question_text

questions = wrong_question_repo.list_all()
docs_data = [
    {"id": q["id"], "text": build_question_text(q)}
    for q in questions
]
print(f"共 {len(docs_data)} 条错题")

for q in questions:
    print(f"ID: {q['id']}")
    print(f"  题目: {q['question_content']}")
    print(f"  错误类型: {q.get('error_type', '')}")
    print()

langchain_store.build_store(docs_data)
print("索引已构建并保存")

results = langchain_store.search("二叉树的性质", top_k=3)
for r in results:
    print(f"score={r['score']:.4f} | id={r['question_id'][:8]} | text={r['text'][:30]}...")