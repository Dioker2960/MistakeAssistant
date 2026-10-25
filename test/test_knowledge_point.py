import requests

BASE = "http://127.0.0.1:8080"


def login(username, password):
    r = requests.post(f"{BASE}/auth/login", json={"username": username, "password": password})
    return r.json()["access_token"]


def main():
    alice = login("alice", "123456")
    bob = login("bob", "123456")
    h_alice = {"Authorization": f"Bearer {alice}"}
    h_bob = {"Authorization": f"Bearer {bob}"}

    # 1. alice 创建知识点
    r = requests.post(f"{BASE}/knowledge-points", json={"name": "数据结构"}, headers=h_alice)
    print(f"创建'数据结构': {r.status_code}")
    kp_tree = r.json()

    r = requests.post(
        f"{BASE}/knowledge-points",
        json={"name": "二叉树", "parent_id": kp_tree["id"]},
        headers=h_alice,
    )
    print(f"创建'二叉树': {r.status_code}")
    kp_bst = r.json()

    # 2. 同名报错
    r = requests.post(f"{BASE}/knowledge-points", json={"name": "二叉树"}, headers=h_alice)
    print(f"重复创建'二叉树': {r.status_code}（应该 400）")

    # 3. 列出知识点
    r = requests.get(f"{BASE}/knowledge-points", headers=h_alice)
    print(f"\n知识点列表: {r.status_code}, {len(r.json())} 条")

    # 4. alice 创建一道错题
    r = requests.post(
        f"{BASE}/wrong-questions",
        json={"question_content": "二叉树测试题", "user_answer": "A", "correct_answer": "B"},
        headers=h_alice,
    )
    qid = r.json()["id"]
    print(f"\n创建错题: {r.status_code}, id={qid[:8]}")

    # 5. 给题目打知识点
    r = requests.post(
        f"{BASE}/wrong-questions/{qid}/knowledge-points",
        json={"knowledge_point_ids": [kp_bst["id"]]},
        headers=h_alice,
    )
    print(f"打知识点: {r.status_code}（应该 204）")

    # 6. 查该题的知识点
    r = requests.get(f"{BASE}/wrong-questions/{qid}/knowledge-points", headers=h_alice)
    kps = r.json()
    print(f"该题的知识点: {r.status_code}, {[k['name'] for k in kps]}")

    # 7. 查该知识点下的错题（alice）
    r = requests.get(f"{BASE}/knowledge-points/{kp_bst['id']}/questions", headers=h_alice)
    print(f"\nalice 查'二叉树'下的错题: {r.status_code}, {len(r.json())} 条")

    # 8. 查该知识点下的错题（bob）—— 应该看不到 alice 的
    r = requests.get(f"{BASE}/knowledge-points/{kp_bst['id']}/questions", headers=h_bob)
    print(f"bob 查'二叉树'下的错题: {r.status_code}, {len(r.json())} 条（应该 0）")

    # 9. bob 查 alice 题目的知识点 —— 应该 404
    r = requests.get(f"{BASE}/wrong-questions/{qid}/knowledge-points", headers=h_bob)
    print(f"\nbob 查 alice 题目的知识点: {r.status_code}（应该 404）")

    # 10. 打不存在的知识点 —— 应该 400
    r = requests.post(
        f"{BASE}/wrong-questions/{qid}/knowledge-points",
        json={"knowledge_point_ids": ["not_exist"]},
        headers=h_alice,
    )
    print(f"打不存在的知识点: {r.status_code}（应该 400）")


if __name__ == "__main__":
    main()