# LangChain 重构

## 解决什么问题

把自研的 LLM 调用、Embedding、Prompt 拼接、向量检索等模块，
替换成 LangChain 的标准组件。核心价值：

1. **统一接口**：`invoke` / `stream` / `batch` 是标准方法，不用每个模型自己写调用代码。
2. **组件可组合**：`prompt | llm | parser` 通过 Runnable 协议拼成链。
3. **工具调用支持**：`llm.bind_tools([...])` 自动生成 JSON schema 和解析工具调用。
4. **生态统一抽象**：`Document`、`BaseMessage`、`Runnable` 是后续 LangGraph、Agent 的基础。

## 在项目中的位置

### 新增文件
- `ai/langchain_llm.py`：封装 `ChatOpenAI`
- `ai/langchain_store.py`：封装 LangChain FAISS vectorstore

### 修改文件
- `ai/embedding_service.py`：`openai` 库 → `OpenAIEmbeddings`
- `ai/prompts.py`：`f-string` → `ChatPromptTemplate` + `MessagesPlaceholder`
- `ai/retriever.py`：从 10 行缩到 1 行
- `services/chat_service.py`：调用改为 LangChain 版
- `main.py`：启动逻辑改用 `langchain_store`

### 未修改
- `api/`（对外接口不变）
- `repositories/`（MySQL 和 Redis 操作）
- `models/`、`schemas/`、`core/`
- **这就是分层的价值：换内部实现，对外零感知**

### 删除文件
- `ai/vector_store.py`（自研 FAISS 封装，被 `langchain_store` 替代）

## 具体执行流程

### 1. LLM 调用

```python
from ai.langchain_llm import get_llm

llm = get_llm()

# 一次性调用
response = llm.invoke(messages)   # 返回 AIMessage
reply = response.content

# 流式调用
for chunk in llm.stream(messages):   # 返回 AIMessageChunk
    piece = chunk.content
```

### 2. Embedding

```
from langchain_openai import OpenAIEmbeddings

_embeddings = OpenAIEmbeddings(
    model="text-embedding-v3",
    api_key=...,
    base_url=...,
    check_embedding_ctx_length=False,   # 跳过 tiktoken 长度检查
)

# 查询用 embed_query，文档用 embed_documents
vec = _embeddings.embed_query(text)
vecs = _embeddings.embed_documents(texts)
```

### 3. Prompt 模板

```
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

_RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("history"),   # 变长历史消息插槽
    ("user", "以下是相关错题：\n\n{contexts}\n\n用户问题：{question}"),
])

messages = _RAG_PROMPT.invoke({
    "history": history,
    "contexts": contexts_text,
    "question": question,
}).to_messages()
```

### 4. FAISS 向量存储

```
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# 构建
docs = [Document(page_content=text, metadata={"question_id": qid}) for ...]
store = FAISS.from_documents(docs, _embeddings)
store.save_local("data/faiss_lc")

# 加载
store = FAISS.load_local(
    "data/faiss_lc",
    _embeddings,
    allow_dangerous_deserialization=True,   # 必须，因为用了 pickle
)

# 检索
results = store.similarity_search_with_score(query, k=3)
# 返回 [(Document, distance), ...]
# distance 是 L2 距离，越小越相似
# 转相似度：1 / (1 + distance)
```

### 5. 懒加载缓存模式

```
_store: FAISS | None = None

def _get_store() -> FAISS | None:
    global _store
    if _store is not None:
        return _store
    if not os.path.exists(_STORE_DIR):
        return None
    _store = FAISS.load_local(...)
    return _store
```

## 关键概念

### Document

LangChain 的统一文档抽象，两个属性：

- `page_content`：文本内容
- `metadata`：元数据（如 question_id）

替代了之前的手写 `{question_id, text, score}` dict。

### Runnable 协议

所有 LangChain 组件都支持 `invoke` / `stream` / `batch`。
可以组合：`chain = prompt | llm | parser`。

### MessagesPlaceholder

Prompt 模板里的**变长消息列表插槽**。

- 普通 `{question}`：插入字符串
- `MessagesPlaceholder("history")`：插入消息列表

### 距离 vs 相似度

- FAISS 返回**距离**（越小越相似）
- 用户期望**相似度**（越大越相似）
- 转换：`similarity = 1 / (1 + distance)`

## 遇到过什么问题

1. `langchain-community` 已被弃用警告，但 FAISS 还没独立包，可继续使用
2. `OpenAIEmbeddings` 默认用 tiktoken 检查长度，和千问分词器不一致，要加 `check_embedding_ctx_length=False`
3. `json.dump` vs `json.dumps`：一个写文件，一个转字符串
4. `FAISS.load_local` 必须加 `allow_dangerous_deserialization=True`
5. `is_empty()` 返回 bool，`_get_store()` 返回对象或 None，判断写法不同
6. LangChain 返回的是 `AIMessage` 对象，文本在 `.content`，不是裸字符串
7. `llm.stream()` 会产出空 content 的 chunk，要加 `if not piece: continue`
8. `similarity_search_with_score` 返回的距离是 numpy 类型，JSON 序列化前要 `float()`

## 面试时如何解释

### Q：为什么用 LangChain？

分三段答：

**第一段：LangChain 解决了什么具体问题**

> 主要有三点：
>
> 1. 统一接口：`invoke` / `stream` / `batch` 是标准方法。
> 2. 组件可组合：`prompt | llm | parser` 通过 Runnable 协议拼成链。
> 3. 工具调用支持：`llm.bind_tools([...])` 自动生成 JSON schema 和解析工具调用，这是自己写最麻烦的部分。

**第二段：在这个项目里用了什么**

> 我的项目里，最开始自研了 `llm_client`、`embedding_service`、`vector_store`。
> 重构后：
>
> - LLM 调用换成 `ChatOpenAI`，代码从 40 行变成 10 行。
> - Prompt 换成 `ChatPromptTemplate`，业务层少写 3 行消息拼接。
> - 向量存储换成 LangChain 的 FAISS 封装，从 150 行变成 30 行。
>   更重要的是：后面要做的工具调用和 LangGraph，都基于 LangChain 的抽象。

**第三段：什么时候不该用**

> 如果只是简单调用模型，直接用 `openai` 库就够，加 LangChain 是过度设计。
> 如果对性能要求极高（毫秒级延迟），框架的抽象层会带来额外开销。
> 如果团队不熟悉 LangChain，学习成本可能超过收益。

### Q：重构后哪些文件没变？

> `api/`、`repositories/`、`models/`、`schemas/` 全都没变。
> 因为分层架构里，Service 层对接 Repository 和 AI 模块，接口保持稳定。
> 换实现只影响内部，对外零感知。

### Q：ChatOpenAI 和直接用 openai 库的区别？

> 三点：
>
> 1. 统一接口，能和其他 LangChain 组件组合。
> 2. 自动适配 OpenAI 兼容接口（千问只改 base_url）。
> 3. 内置工具调用支持 `bind_tools`，这是后面做 Agent 的基础。