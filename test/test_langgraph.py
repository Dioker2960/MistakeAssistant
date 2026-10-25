# # from langgraph.graph import StateGraph, END
# # print("LangGraph 导入成功")
#
#
# # from ai.langgraph_rag import app
# #
# # result = app.invoke({
# #     "question": "二叉树那道题为什么选B？",
# #     "history": [],
# # })
# #
# # print("改写后的问题:", result["search_query"])
# # print("检索到:", len(result["contexts"]), "条")
# # print("回答:", result["reply"][:200])
#
# from ai.langgraph_rag import app
#
# # 情况 1：无历史 → 跳过改写
# print("=== 无历史 ===")
# result = app.invoke({
#     "question": "二叉树那道题为什么选B？",
#     "history": [],
# })
# print("search_query:", result["search_query"])
# print("reply:", result["reply"][:100])
#
# # 情况 2：有历史 → 走改写
# print("\n=== 有历史 ===")
# result = app.invoke({
#     "question": "那A呢？",
#     "history": [
#         {"role": "user", "content": "二叉树那道题为什么选B？"},
#         {"role": "assistant", "content": "因为B符合二叉树的定义..."},
#     ],
# })
# print("search_query:", result["search_query"])
# print("reply:", result["reply"][:100])
#


from ai.langgraph_agent import app

# 测试 1：不调工具
r = app.invoke({"question": "什么是二叉树？", "history": []})
print("最终回答:", r["messages"][-1].content[:100])

# 测试 2：调一个工具（统计）
r = app.invoke({"question": "我一共有多少错题？", "history": []})
print("最终回答:", r["messages"][-1].content[:100])

# 测试 3：调一个工具（检索）
r = app.invoke({"question": "二叉树那道题为什么选B？", "history": []})
print("最终回答:", r["messages"][-1].content[:100])

# 测试 3：调一个工具（检索）
r = app.invoke({"question": "我概念理解错误的题有哪些？", "history": []})
print("最终回答:", r["messages"][-1].content[:100])

# 测试 3：调一个工具（检索）
r = app.invoke({"question": "有什么和二叉树类似的题？", "history": []})
print("最终回答:", r["messages"][-1].content[:100])

# from ai.langgraph_agent import app
#
# # 第一轮
# r1 = app.invoke({
#     "conversation_id": "agent-test-1",
#     "question": "二叉树那道题为什么选B？",
#     "history": [],
# })
# print("第一轮:", r1["messages"][-1].content[:100])
#
# # 第二轮
# r2 = app.invoke({
#     "conversation_id": "agent-test-1",
#     "question": "那A呢？",
#     "history": [],
# })
# print("第二轮:", r2["messages"][-1].content[:100])
# print("search_query:", r2["search_query"])


# from repositories import conversation_repo
# messages = conversation_repo.get_messages("agent-test-1")
# print(f"共 {len(messages)} 条")
# for m in messages:
#     print(f"  {m['role']}: {m['content'][:40]}...")