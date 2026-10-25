from typing import TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, START, END

# 1. 定义状态
from ai import retriever, prompts
from ai.rewrite import rewrite_question
from ai.tools import TOOLS, TOOL_MAP
from ai.langchain_llm import get_llm

# 工具注册表：新增工具时在这里加上
from repositories import conversation_repo


class RAGState(TypedDict):
    user_id: str
    question: str
    history: list
    search_query: str
    contexts: list
    reply: str


class AgentState(TypedDict):
    user_id: str
    conversation_id: str  # 新增：会话 ID
    question: str  # 用户原始问题
    history: list  # 历史消息
    search_query: str  # 改写后的问题
    messages: list[BaseMessage]  # 完整对话消息（含 tool_calls 和 tool 结果）
    reply: str  # 最终回答


def _history_to_messages(history: list[dict]) -> list[BaseMessage]:
    """把 Redis 的 dict 历史转成 LangChain 消息对象。"""
    result = []
    for m in history:
        if m["role"] == "user":
            result.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            result.append(AIMessage(content=m["content"]))
    return result


# 2. 定义节点

def init_node(state: AgentState) -> dict:
    """初始化：设置 search_query，并把历史 + 当前问题拼成 messages。"""
    return {
        "search_query": state["question"],
        "messages": _history_to_messages(state["history"]) + [HumanMessage(content=state["question"])],
    }


def load_history_node(state: AgentState) -> dict:
    user_id = state.get("user_id", "")
    # 从 Redis 读 history
    conversation_id = state.get("conversation_id")
    if not conversation_id:
        return {"history": []}
    history = conversation_repo.get_messages(user_id, conversation_id)
    return {"history": history}


def save_history_node(state):
    user_id = state.get("user_id", "")
    # 把 (question, reply) 写回 Redis
    conversation_id = state.get("conversation_id")
    if not conversation_id:
        return {}  # 没有会话 ID，不写

    reply = state["messages"][-1].content
    conversation_repo.append_messages(user_id, conversation_id, [
        {"role": "user", "content": state["question"]},
        {"role": "assistant", "content": reply},
    ])
    return {}


def rewrite_node(state: AgentState) -> dict:
    """改写节点：有历史时改写问题。"""
    # TODO 1: 从 state 取 question 和 history
    # TODO 2: 调 _rewrite_question 得到 search_query
    search_query = rewrite_question(state["question"], state["history"])
    # TODO 3: 返回 {"search_query": search_query}
    return {"search_query": search_query}


def retrieve_node(state: RAGState) -> dict:
    """检索节点：用改写后的问题检索。"""
    # TODO 1: 从 state 取 search_query
    # TODO 2: 调 retriever.search 得到 contexts
    contexts = retriever.search(state["search_query"])
    # TODO 3: 返回 {"contexts": contexts}
    return {"contexts": contexts}


def generate_node(state: RAGState) -> dict:
    """生成节点：拼 Prompt，调模型。"""
    # TODO 1: 从 state 取 question、contexts、history
    # TODO 2: 调 prompts.build_rag_messages 得到 messages
    messages = prompts.build_rag_messages(state["question"], state["contexts"], state["history"])
    # TODO 3: 调 llm.invoke 得到 reply
    reply = get_llm().invoke(messages).content
    # TODO 4: 返回 {"reply": reply}
    return {"reply": reply}


def agent_node(state: AgentState) -> dict:
    llm_with_tools = get_llm().bind_tools(TOOLS)
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}


def tool_node(state: AgentState) -> dict:
    user_id = state["user_id"]
    last_message = state["messages"][-1]
    tool_messages = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        tool_func = TOOL_MAP.get(tool_name)
        if tool_func is None:
            result = f"工具 {tool_name} 不存在"
        else:
            valid_args = {k: v for k, v in tool_args.items() if k in tool_func.args}
            # 用 config 传 runtime context
            try:
                result = tool_func.invoke(
                    valid_args,
                    config={"configurable": {"user_id": user_id}},
                )
            except Exception as e:
                result = f"工具执行失败：{e}"

        tool_messages.append(ToolMessage(
            content=result,
            tool_call_id=tool_call["id"],
        ))

    return {"messages": state["messages"] + tool_messages}


# 定义路由函数
def route_after_init(state: AgentState) -> str:
    if state["history"]:
        return "rewrite"
    return "agent"


def route_after_agent(state: AgentState) -> str:
    """LLM 返回后有 tool_calls 就走工具节点，否则结束。"""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tool"
    return "save_history"


# 3. 构建图
graph = StateGraph(AgentState)

# 添加节点
graph.add_node("init", init_node)
graph.add_node("load_history", load_history_node)
graph.add_node("save_history", save_history_node)
graph.add_node("rewrite", rewrite_node)
graph.add_node("retrieve", retrieve_node)
graph.add_node("generate", generate_node)
graph.add_node("agent", agent_node)
graph.add_node("tool", tool_node)

# 添加边（执行顺序）
graph.add_edge(START, "load_history")
graph.add_edge("load_history", "init")
graph.add_conditional_edges(
    "init",  # 从哪个节点出发
    route_after_init,  # 路由函数，返回下一个节点名
    {
        "rewrite": "rewrite",  # 返回值 → 目标节点
        "agent": "agent",
    },
)
graph.add_edge("rewrite", "agent")
graph.add_conditional_edges(
    "agent",
    route_after_agent,
    {
        "tool": "tool",  # 返回值 → 目标节点
        "save_history": "save_history",
    },
)
graph.add_edge("tool", "agent")
graph.add_edge("save_history", END)


# 编译
app = graph.compile()
