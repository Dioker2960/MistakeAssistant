import json
import logging
import os
from typing import TypedDict, Literal

from langchain_core.messages import (
    BaseMessage, HumanMessage, ToolMessage, AIMessage, SystemMessage,
)
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from ai.context import current_user_id
from ai.langchain_llm import get_llm
from ai.prompts import INTENT_PROMPTS, ROUTER_PROMPT
from ai.rewrite import rewrite_question
from ai.summary import summarize_history
from ai.tools import INTENT_TOOLS, TOOL_MAP
from repositories import conversation_repo

logger = logging.getLogger(__name__)

# 短期记忆：保留最近多少条消息
MAX_RECENT_MESSAGES = int(os.getenv("MAX_RECENT_MESSAGES", 10))

# 触发压缩的阈值：消息数超过这个值就压缩
COMPRESS_THRESHOLD = int(os.getenv("COMPRESS_THRESHOLD", 16))

# 压缩后保留多少条未压缩消息
COMPRESS_KEEP = int(os.getenv("COMPRESS_KEEP", 8))


# ========== State ==========
class AgentState(TypedDict):
    user_id: str
    conversation_id: str
    question: str
    history: list
    search_query: str
    intent: str  # ← 新增：Router 判断的意图
    messages: list[BaseMessage]
    references: list


# ========== Router ==========
class IntentOutput(BaseModel):
    intent: Literal["knowledge", "diagnosis", "recommendation", "stats", "list_by_kp"] = Field(
        description="用户意图分类"
    )


def router_node(state: AgentState) -> dict:
    """Router Agent：判断用户意图。"""
    llm = get_llm().with_structured_output(IntentOutput)
    history = state["history"][-6:] if state["history"] else []

    messages = ROUTER_PROMPT.invoke({
        "history": history,
        "question": state["question"],
    }).to_messages()

    result = llm.invoke(messages)
    logger.info("Router 判断意图: %s, 问题=%s...", result.intent, state["question"][:30])
    return {"intent": result.intent}


# ========== 其他节点 ==========
def _history_to_messages(history: list[dict]) -> list[BaseMessage]:
    result = []
    for m in history:
        if m["role"] == "user":
            result.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            result.append(AIMessage(content=m["content"]))
    return result


def load_history_node(state: AgentState) -> dict:
    user_id = state.get("user_id", "")
    conversation_id = state.get("conversation_id")
    if not user_id or not conversation_id:
        return {"history": []}

    # 拉历史 + 摘要
    history = conversation_repo.get_messages(user_id, conversation_id)
    summary = conversation_repo.get_summary(user_id, conversation_id)

    # 如果有摘要，作为第一条特殊消息插进去
    summary_pair = []
    if summary:
        summary_pair = [
                      {"role": "user", "content": f"【以下是之前的对话摘要】\n{summary}"},
                      {"role": "assistant", "content": "好的，我已经了解之前的对话内容。"},
                  ]

    # 滑动窗口：只保留最近 N 条
    if len(history) > MAX_RECENT_MESSAGES:
        truncated = history[-MAX_RECENT_MESSAGES:]
        while truncated and truncated[0]["role"] != "user":
            truncated = truncated[1:]
    else:
        truncated = history

    # 摘要在前，原始在后
    history = summary_pair + truncated
    logger.info("对话历史截断: %d 条", len(history))

    return {"history": history}


def init_node(state: AgentState) -> dict:
    return {
        "search_query": state["question"],
        "messages": _history_to_messages(state["history"]) + [HumanMessage(content=state["question"])],
    }


def rewrite_node(state: AgentState) -> dict:
    search_query = rewrite_question(state["question"], state["history"])
    return {"search_query": search_query}


def agent_node(state: AgentState) -> dict:
    """通用 Agent 节点：根据 intent 动态选工具和 Prompt。"""
    intent = state.get("intent", "knowledge")
    tools = INTENT_TOOLS.get(intent, INTENT_TOOLS["knowledge"])
    system = INTENT_PROMPTS.get(intent, INTENT_PROMPTS["knowledge"])

    logger.info("执行 %s Agent，工具数=%d", intent, len(tools))

    llm_with_tools = get_llm().bind_tools(tools)
    messages = [SystemMessage(content=system)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": state["messages"] + [response]}


def tool_node(state: AgentState) -> dict:
    current_user_id.set(state["user_id"])
    last_message = state["messages"][-1]
    tool_messages = []
    all_refs = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        tool_func = TOOL_MAP.get(tool_name)
        if tool_func is None:
            result = f"工具 {tool_name} 不存在"
        else:
            valid_args = {k: v for k, v in tool_args.items() if k in tool_func.args}
            try:
                result = tool_func.invoke(valid_args)
                logger.info("工具 %s 执行成功", tool_name)

                # ← 解析结构化返回
                if tool_name == "search_wrong_questions":
                    try:
                        parsed = json.loads(result)
                        if isinstance(parsed, dict) and "context" in parsed:
                            all_refs.extend(parsed.get("references", []))
                            result = parsed["context"]  # ← 只把 context 给 LLM
                    except (json.JSONDecodeError, TypeError):
                        pass
            except Exception as e:
                result = f"工具执行失败：{e}"
                logger.error("工具 %s 失败: %s", tool_name, e)

        tool_messages.append(ToolMessage(
            content=result,
            tool_call_id=tool_call["id"],
        ))

    return {
        "messages": state["messages"] + tool_messages,
        "references": all_refs,  # ← 通过 State 传，不用 ContextVar
    }


def save_history_node(state: AgentState) -> dict:
    user_id = state.get("user_id", "")
    conversation_id = state.get("conversation_id")
    if not user_id or not conversation_id:
        return {}

    reply = state["messages"][-1].content
    refs = state.get("references", [])   # ← 取出 references

    conversation_repo.append_messages(user_id, conversation_id, [
        {"role": "user", "content": state["question"]},
        {"role": "assistant", "content": reply, "references": refs},
    ])
    logger.debug("保存历史: %d 条", len(state["messages"]))
    # 2. 检查消息数，超过阈值就压缩
    total = conversation_repo.count_messages(conversation_id)
    if total > COMPRESS_THRESHOLD:
        _compress_history(user_id, conversation_id)

    return {}


def _compress_history(user_id: str, conversation_id: str) -> None:
    """把最旧的消息压缩成摘要，并从表里删掉它们。"""
    # 1. 计算要压缩多少条
    total = conversation_repo.count_messages(conversation_id)
    to_compress = total - COMPRESS_KEEP  # 保留最近 COMPRESS_KEEP 条，其他压缩
    if to_compress <= 0:
        return

    # 2. 取最旧的 N 条 + 已有摘要
    old_messages = conversation_repo.get_oldest_messages(conversation_id, to_compress)
    existing_summary = conversation_repo.get_summary(user_id, conversation_id)

    # 3. 生成新摘要
    new_summary = summarize_history(old_messages, existing_summary)

    # 4. 更新摘要 + 删除旧消息
    conversation_repo.update_summary(user_id, conversation_id, new_summary)
    ids_to_delete = [m["id"] for m in old_messages]
    conversation_repo.delete_messages_by_ids(ids_to_delete)

    logger.info(
        "会话压缩: conversation=%s, 压缩 %d 条, 摘要长度 %d",
        conversation_id[:8], to_compress, len(new_summary),
    )

# ========== 路由函数 ==========
def route_by_history(state: AgentState) -> str:
    if state["history"]:
        return "rewrite"
    return "router"


def route_by_tool_calls(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tool"
    return "save"


# ========== 构建图 ==========
graph = StateGraph(AgentState)

graph.add_node("load_history", load_history_node)
graph.add_node("init", init_node)
graph.add_node("rewrite", rewrite_node)
graph.add_node("router", router_node)
graph.add_node("agent", agent_node)
graph.add_node("tool", tool_node)
graph.add_node("save_history", save_history_node)

graph.add_edge(START, "load_history")
graph.add_edge("load_history", "init")

graph.add_conditional_edges("init", route_by_history, {
    "rewrite": "rewrite",
    "router": "router",
})

graph.add_edge("rewrite", "router")
graph.add_edge("router", "agent")

graph.add_conditional_edges("agent", route_by_tool_calls, {
    "tool": "tool",
    "save": "save_history",
})

graph.add_edge("tool", "agent")
graph.add_edge("save_history", END)

app = graph.compile()