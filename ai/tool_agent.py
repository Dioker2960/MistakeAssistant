# import json
#
# from langchain_core.messages import ToolMessage
#
# from ai.langchain_llm import get_llm
# from ai.tools import get_wrong_question_stats, search_wrong_questions
#
# # 注册工具列表
# _TOOLS = [get_wrong_question_stats, search_wrong_questions]
#
# # 工具名 → 函数的映射（用于执行）
# _TOOL_MAP = {t.name: t for t in _TOOLS}
#
#
# def ask_with_tools(question: str) -> str:
#     """
#     带工具调用的问答。
#     模型可能直接回答，也可能调用工具后再回答。
#     """
#     llm_with_tools = get_llm().bind_tools(_TOOLS)
#
#     # ① 第一次调 LLM
#     messages = [{"role": "user", "content": question}]
#     response = llm_with_tools.invoke(messages)
#
#     # ② 如果 LLM 决定调工具
#     if not response.tool_calls:
#         # 没调工具，直接返回回答
#         return response.content
#
#     # ③ 执行每个工具调用
#     messages.append(response)  # 把 LLM 的 tool_calls 消息加入历史
#     for tool_call in response.tool_calls:
#         tool_name = tool_call["name"]
#         tool_args = tool_call["args"]
#         tool_func = _TOOL_MAP.get(tool_name)
#
#         if tool_func is None:
#             result = f"错误：工具 {tool_name} 不存在"
#         else:
#             try:
#                 result = tool_func.invoke(tool_args)
#             except Exception as e:
#                 result = f"工具执行失败：{e}"
#
#         # 把工具结果作为 ToolMessage 加入历史
#         messages.append(ToolMessage(
#             content=result,
#             tool_call_id=tool_call["id"],
#         ))
#     print(messages)
#     # ④ 第二次调 LLM，让它基于工具结果生成回答
#     final_response = llm_with_tools.invoke(messages)
#     return final_response.content
