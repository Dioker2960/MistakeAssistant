"""导出当前用户的所有错题，用于设计评测集。"""

from repositories import wrong_question_repo


def dump(user_id: str):
    questions = wrong_question_repo.list_all(user_id)
    print(f"用户 {user_id[:8]} 共 {len(questions)} 道错题\n")
    for q in questions:
        print(f'    "{q["id"]}",  # {q["question_content"][:40]}')


if __name__ == "__main__":
    # alice 的 user_id
    dump("7639d8c5686f4ee8882115e937d40396")