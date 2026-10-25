import requests

BASE = "http://127.0.0.1:8080"

alice_token = requests.post(f"{BASE}/auth/login", json={"username": "alice", "password": "123456"}).json()["access_token"]
bob_token = requests.post(f"{BASE}/auth/login", json={"username": "bob", "password": "123456"}).json()["access_token"]

alice_list = requests.get(f"{BASE}/wrong-questions", headers={"Authorization": f"Bearer {alice_token}"}).json()
qid = alice_list[0]["id"]

print(f"alice 有 {len(alice_list)} 条")
print(f"访问错题 ID: {qid}")

# alice 访问自己的
r = requests.get(f"{BASE}/wrong-questions/{qid}", headers={"Authorization": f"Bearer {alice_token}"})
print(f"alice 访问自己的: {r.status_code}（应该是 200）")

# bob 访问 alice 的
r = requests.get(f"{BASE}/wrong-questions/{qid}", headers={"Authorization": f"Bearer {bob_token}"})
print(f"bob 访问 alice 的: {r.status_code}（应该是 404）")

# 未登录
r = requests.get(f"{BASE}/wrong-questions/{qid}")
print(f"未登录: {r.status_code}（应该是 401）")