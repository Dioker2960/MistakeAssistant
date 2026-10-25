# 需要修改的问题总结

> 依据：仅静态阅读源码，未实际运行验证。按优先级排序。

## 🔴 高优先级：多用户隔离缺陷

### 1. 相似题推荐跨用户泄露数据
- **位置**：`ai/tools.py:93`
- **依据**：
  ```python
  results = langchain_store.search(question_content, top_k=3, min_score=0.3)  # 未传 user_id
  ```
  而 `ai/langchain_store.py:114` 为 `filter={"user_id": user_id} if user_id else None`，传 `None` 时检索全库。
- **对比**：同文件 `search_wrong_questions`（`:62`）正确传了 `user_id=user_id`。
- **影响**：用户 A 使用"推荐相似题"时会拿到用户 B 的错题，与 README"用户隔离"宣称矛盾。
- **修复**：改为 `langchain_store.search(..., user_id=current_user_id.get())`。

### 2. deprecated 接口无鉴权 + 检索无用户过滤
- **位置**：`api/chat_api.py`（`/chat`、`/chat/rag`、`/chat/rag/stream`）、`services/chat_service.py`、`ai/retriever.py:45`
- **依据**：三个接口均无 `Depends(get_current_user)`；`chat_service.ask_with_rag` → `retriever.search(search_query, top_k)` → `langchain_store.search` 不带 `user_id`。
- **影响**：未登录即可调用 LLM，且 RAG 检索全库错题（无隔离）。
- **修复**：二选一——补上鉴权与 `user_id` 过滤，或直接删除这些已标记 deprecated 的接口。

## 🟡 中优先级：逻辑 Bug

### 3. 有摘要时历史消息被重复拼接
- **位置**：`ai/multi_agent.py:88-105`（`load_history_node`）
- **依据**：
  ```python
  if summary:
      summary_pair = [摘要对...] + history   # ← 已包含完整 history
  ...
  truncated = history[-MAX_RECENT_MESSAGES:]  # 或 history 本身
  history = summary_pair + truncated          # ← 又一次拼接 history
  ```
- **影响**：当存在摘要时，历史会以"完整 + 截断"两份进入 Prompt，浪费上下文并可能误导模型。
- **修复**：`summary_pair` 只保留摘要两条，最后 `history = summary_pair + truncated`。

## 🟢 低优先级：冗余与误写

### 4. 误导入 `limit` / `offset` 模块及无关依赖
- **位置**：`repositories/wrong_question_repo.py:3-4`、`requirements.txt:19-20`
- **依据**：`import limit as limit`、`import offset as offset` 是把分页参数名误当模块导入；`requirements.txt` 里 `limit~=0.2.3`、`offset~=0.0.2` 是无关的第三方包，仅为让该 import 不报错。
- **修复**：删除这两个 import 行及 requirements 中对应依赖。

### 5. 启动时索引构建逻辑重复
- **位置**：`main.py:24-42`（lifespan 内）与 `main.py:90-100`（模块级）
- **依据**：两处都执行"空则 build_store / 非空则加载"的同一套逻辑，模块级在 `if __name__` 之前也会执行一次。
- **修复**：保留 lifespan 内实现，删除模块级重复代码。

### 6. 未使用的导入
- **位置**：`ai/tools.py:6`
- **依据**：`from ai.context import current_user_id, last_references` 中 `last_references` 未被使用。
- **修复**：删除 `last_references`。

## 📄 文档一致性（需与作者确认后更新）

### 7. README 描述与实际实现不符
- **位置**：`README.md:11、83、85、189`
- **依据**：README 称"Redis 会话管理 / Redis key `conversation:{user_id}:{conv_id}`"，但 `repositories/conversation_repo.py` 全程用 MySQL 的 `Message` 表；`core/redis_client.py` 仅定义、未被会话链路调用。
- **修复**：确认作者意图后，要么更新 README 改为 MySQL，要么补回 Redis 实现；同时决定是否移除 `redis` 依赖。
