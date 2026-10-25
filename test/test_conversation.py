import requests

BASE = "http://127.0.0.1:8080"
token = requests.post(f"{BASE}/auth/login", json={"username": "alice", "password": "123456"}).json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# 1. 列会话（最开始是空的，或只有之前的）
r = requests.get(f"{BASE}/conversations", headers=h)
print(f"会话列表: {r.status_code}")
for c in r.json():
    print(f"  - {c['conversation_id']}: {c['title']} ({c['message_count']} 条)")

# 2. 用某个 conv_id 发消息（触发写 Redis）
requests.post(f"{BASE}/chat/agent", json={
    "message": "什么是二叉树？",
    "conversation_id": "test-conv-1",
}, headers=h)

# 3. 再列一次
r = requests.get(f"{BASE}/conversations", headers=h)
print(f"\n再列: {len(r.json())} 个会话")
for c in r.json():
    print(f"  - {c['conversation_id']}: {c['title']} ({c['message_count']} 条)")

# 4. 查会话消息
r = requests.get(f"{BASE}/conversations/test-conv-1", headers=h)
print(f"\n会话消息: {len(r.json()['messages'])} 条")