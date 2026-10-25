from ai.langchain_llm import get_llm
from ai.tools import get_wrong_question_stats

llm = get_llm()
llm_with_tools = llm.bind_tools([get_wrong_question_stats])

# 测试 1：会触发工具调用的问题
print("=== 测试 1 ===")
response = llm_with_tools.invoke([
    {"role": "user", "content": "我一共有多少错题？"}
])
print("content:", repr(response.content))
print("tool_calls:", response.tool_calls)

# 测试 2：不会触发工具调用的问题
print("\n=== 测试 2 ===")
response = llm_with_tools.invoke([
    {"role": "user", "content": "什么是二叉树？"}
])
print("content:", repr(response.content))
print("tool_calls:", response.tool_calls)