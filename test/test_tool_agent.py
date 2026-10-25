from ai.tool_agent import ask_with_tools

# 场景 1：统计类
print(ask_with_tools("我一共有多少错题？"))

# 场景 2：内容类（应该调 search_wrong_questions）
print(ask_with_tools("二叉树那道题为什么选B？"))

# 场景 3：知识类（可能不调工具，直接回答）
print(ask_with_tools("什么是哈希表？"))