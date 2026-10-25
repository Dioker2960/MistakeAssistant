# LangGraph Agent

## 解决什么问题

把"改写 → 检索 → 生成"的流程从**函数里的线性代码**，
升级成**可可视化、可组合、支持分支和循环的图**。

核心解决三类场景：

1. **条件分支**：有历史才改写，无历史直接进 Agent。
2. **循环**：LLM 可以连续调用多个工具（ReAct 模式）。
3. **状态共享**：所有节点共享 State，中间结果不靠函数参数传递。

## 在项目中的位置

- `ai/langgraph_agent.py`：Agent 图（多轮 + 工具 + 改写）
- `api/agent_api.py`：HTTP 接口（`/chat/agent`、`/chat/agent/stream`）
- 复用 `ai/tools.py`、`ai/rewrite.py`、`ai/langchain_llm.py`

## 执行流程

```text
START
  ↓
load_history（从 Redis 读会话历史）
  ↓
init（拼 messages、设 search_query 默认值）
  ↓
条件路由：有历史？
  ├── 有 → rewrite（改写）→ agent
  └── 无 → agent
              ↓
           agent（调 LLM，判断是否要工具）
              ↓
           条件路由：有 tool_calls？
              ├── 有 → tool（执行工具）→ agent（循环）
              └── 无 → save_history（写 Redis）→ END
```

## 关键概念

### State

所有节点共享的 dict，用 `TypedDict` 定义。

- 节点**读**：从 `state["xxx"]` 取。
- 节点**写**：返回 `{"xxx": ...}`，LangGraph 自动合并。
- **默认合并是"覆盖"**，不是"追加"。列表字段要手动拼接或配累加器。

### Node

一个函数，签名是 `(state) -> dict`。

- 只返回**要更新的字段**。
- 不返回的字段保持原值。

### Edge

- **普通边**：`add_edge("A", "B")`，A 执行完直接到 B。
- **条件边**：`add_conditional_edges("A", router, {"key": "target"})`，根据 router 返回值决定走哪。

### 循环

`tool → agent` 形成循环。
**结束条件**：LLM 不再返回 `tool_calls`（由 LLM 自己决定）。

### `astream_events`

流式输出。只推 `content` 非空的 chunk：

python

```
async for event in app.astream_events(input, version="v2"):
    if event["event"] == "on_chat_model_stream":
        chunk = event["data"]["chunk"]
        if chunk.content:
            yield chunk.content
```



## 遇到的坑

### 1. 节点顺序

`init` 用了 `state["history"]`，但 `load_history` 还没跑 → `KeyError`。
**修复**：`START → load_history → init`。

### 2. `search_query` 字段不存在

无条件路由跳过 `rewrite` 后，`retrieve` 读 `search_query` 报 `KeyError`。
**修复**：加 `init` 节点设置默认值。

### 3. `is not None` 让条件边失效

`if state["history"] is not None` 对空列表也返回 True，导致改写节点仍执行。
**修复**：用 `if state["history"]`（空列表是 falsy）。

### 4. 工具返回的参数错误

LLM 给无参工具传了 `query` 参数 → `TypeError`。
**修复**：`valid_args = {k: v for k, v in tool_args.items() if k in tool_func.args}`。

### 5. 消息追加 vs 覆盖

`return {"messages": [response]}` 会覆盖，应该 `state["messages"] + [response]`。

### 6. Redis 连接

Redis 是独立进程，Python 服务启动不代表 Redis 启动。

## 面试时如何解释

### Q：为什么用 LangGraph？

> 项目里有三个流程逻辑：
>
> 1. **条件分支**：有历史才改写问题，无历史跳过。
> 2. **循环**：LLM 可能连续调多个工具，直到不再需要。
> 3. **状态共享**：改写结果、检索结果、工具结果都要传给下游。
>
> 手写函数时，这些逻辑混在一起，加一个步骤就要改函数。
> LangGraph 把它们拆成节点，用边连接，每个节点只关心自己的一小步。

### Q：State 怎么传递？

> State 是所有节点共享的 dict。节点通过参数读，通过返回值写。
> LangGraph 自动把返回值合并到 State。默认是覆盖，列表字段要手动拼接。

### Q：循环怎么结束？

> `tool → agent` 形成循环，但**不是固定次数**。
> 结束条件是 LLM 不再返回 `tool_calls`——**LLM 自己决定"够了"**。
> 这是 ReAct Agent 的本质：LLM 作为决策者，决定何时停止。

### Q：为什么要有 `init` 节点？

> LangGraph 的 State 是"部分更新"的——没被任何节点写过的字段不存在。
> `init` 负责设置默认值（如 `search_query = question`），
> 保证后续节点读取时不会 KeyError。

### Q：LangGraph 和手写循环的区别？

> 手写版只支持一轮工具调用：调一次工具，再调一次 LLM。
> LangGraph 版天然支持任意轮：`tool → agent` 的边自动循环。
> 这就是图结构比函数更强的表达能力。