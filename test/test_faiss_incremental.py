"""
测试 FAISS 索引的增量更新。
场景：运行期间新增错题，不重启服务，索引应自动更新。

注意：测试脚本和服务是两个进程，需要每次重新加载索引才能看到更新。
"""

import requests
import ai.langchain_store as ls_module
from repositories import wrong_question_repo

BASE = "http://127.0.0.1:8080"


def fresh_count():
    """强制从磁盘重新加载索引，再返回条数。"""
    ls_module._store = None   # 清空内存缓存
    return ls_module.count()


# 登录
token = requests.post(f"{BASE}/auth/login", json={
    "username": "alice", "password": "123456"
}).json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# 1. 当前条数
before_count = fresh_count()
db_before = len(wrong_question_repo.list_all())
print(f"新增前：索引 {before_count} 条，数据库 {db_before} 条")

# 2. 通过 API 创建一条
r = requests.post(f"{BASE}/wrong-questions", json={
    "question_content": "【测试】线程和进程的核心区别是什么？",
    "question_type": "single_choice",
    "user_answer": "A",
    "correct_answer": "B",
    "analysis": "线程是CPU调度单位，进程是资源分配单位。",
    "error_type": "概念混淆",
    "difficulty": 3,
    "knowledge_point_names": ["数据结构"],
}, headers=h)

print(f"\n创建错题: {r.status_code}")
qid = r.json()["id"]
print(f"新错题 ID: {qid[:8]}")

# 3. 重新加载后看条数
after_count = fresh_count()
db_after = len(wrong_question_repo.list_all())
print(f"\n新增后：索引 {after_count} 条，数据库 {db_after} 条")
print(f"索引增量: {after_count - before_count}（期望 1）")

# 4. 检索验证
ls_module._store = None
user_id = wrong_question_repo.get_by_id(qid)["user_id"]
results = ls_module.search(
    "【测试】线程和进程的核心区别是什么",   # ← 用原文
    top_k=10,                              # ← 调大
    user_id=user_id,
)
found = any(r["question_id"] == qid for r in results)
print(f"\n检索验证: {'✅ 新错题已被检索到' if found else '❌ 新错题未进索引'}")

# 5. 清理——删掉测试题
requests.delete(f"{BASE}/wrong-questions/{qid}", headers=h)
print(f"\n已删除测试题: {qid[:8]}")