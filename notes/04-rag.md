## 解决什么问题
让大模型基于"你的私有数据"（错题）回答，而不是凭空生成。
核心：先检索相关内容，再让模型基于这些内容回答。

## 在项目中的位置
- `ai/prompts.py`：Prompt 模板（RAG、改写）
- `ai/llm_client.py` / `ai/langchain_llm.py`：LLM 调用封装
- `services/chat_service.py`：RAG 主流程
- `api/chat_api.py`：`/chat/rag` 和 `/chat/rag/stream` 接口

## 单轮 RAG 执行流程
1. 用户提问
2. `retriever.search(query)` → 检索 Top-K 错题
3. `build_rag_prompt(question, contexts)` → 拼 Prompt
4. `llm.chat(messages)` → 调模型
5. 返回 `{reply, references}`

## 多轮 RAG 执行流程
1. 从 Redis 读历史 `conversation_repo.get_messages(conversation_id)`
2. **问题改写**：结合历史把"那 A 呢？"改写成完整问题
3. 用改写后的问题检索（检索需要完整主题）
4. 拼 Prompt（用**原始** question，不是改写版）
5. 构造 `messages`：`[system] + 历史 + [当前 user]`
6. 调模型
7. **写回 Redis**：存**原始** question，不存 user_prompt
8. 返回

## SSE 流式执行流程
1. `StreamingResponse` 包装生成器
2. 先生成一个 `event: references` 事件
3. 遍历 `llm.stream(messages)` 的每个 chunk → `yield data: {"text": ...}`
4. 生成完 → `yield event: done`
5. 写回 Redis
6. 客户端用 `fetch + ReadableStream` 或 `EventSource` 接收

## 关键概念
- **RAG = Retrieval + Augmented + Generation**
- **messages 结构**：`[{"role": "system/user/assistant", "content": "..."}]`
- **历史消息原样放进 messages**，不能拼成字符串（否则模型分不清角色）
- **参考资料只注入当前轮**，不进历史（否则历史失真）
- **改写只用于检索**，拼 Prompt 用原始问题
- **生成器 yield**：产出值 + 暂停 + 交还控制权
- **SSE 格式**：`event: xxx\ndata: {...}\n\n`（两个换行表示消息结束）
- **流式的意义**：总时间一样，但用户 0.3 秒就能看到第一个字

## 遇到过什么问题
1. 生成器最后一个 chunk 的 `choices` 是空列表，要加 `if not chunk.choices: continue`
2. SSE 消息必须以 `\n\n` 结尾，少了客户端会一直等
3. `json.dumps` 中文转义：加 `ensure_ascii=False`
4. Swagger UI 看不出流式效果，用 `curl -N` 或 Python 客户端
5. 改写只在有历史时进行，没历史直接返回原问题
6. 写回 Redis 存原始 question，不能存 user_prompt

## 面试怎么解释
- **RAG 的核心价值**：让模型基于真实数据回答，减少幻觉
- **为什么需要问题改写**：多轮对话中用户会省略主题（"那 A 呢"），检索需要完整问题
- **为什么用 SSE 不用 WebSocket**：单向推送、基于 HTTP、自动重连、实现简单
- **生成器的本质**：函数可以暂停和继续，适合流式场景
- **多轮 RAG 的关键点**：历史结构化存储、参考资料不进历史、改写只用于检索