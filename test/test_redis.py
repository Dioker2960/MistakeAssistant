# import redis
#
# client = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)
#
# client.set("test", "hello")
# print(client.get("test"))   # hello
#
# client.delete("test")


# from repositories import conversation_repo
#
# conversation_repo.append_messages("conv-test", [
#     {"role": "user", "content": "你好"},
#     {"role": "assistant", "content": "你好，有什么可以帮你？"},
# ])
#
# messages = conversation_repo.get_messages("conv-test")
# print(f"共 {len(messages)} 条：")
# for m in messages:
#     print(f"  {m['role']}: {m['content']}")
#
# conversation_repo.append_messages("conv-test", [
#     {"role": "user", "content": "二叉树是什么？"},
# ])
#
# messages = conversation_repo.get_messages("conv-test")
# print(f"追加后共 {len(messages)} 条")
#
# from core.redis_client import get_client
# client = get_client()
# print(f"剩余过期时间: {client.ttl('conversation:conv-test')} 秒")
#
# print("删除成功:", conversation_repo.delete_conversation("conv-test"))
# print("删除后再读:", conversation_repo.get_messages("conv-test"))


from repositories import conversation_repo
messages = conversation_repo.get_messages("conv-1")
print(f"共 {len(messages)} 条")
for m in messages:
    print(f"  {m['role']}: {m['content'][:40]}...")