# 错题知识库智能问答助手

基于 RAG + 多 Agent 的错题管理问答系统。用户录入错题后，系统建立语义索引，
支持基于错题知识库的智能问答、错因分析、相似题推荐、学习统计与知识点掌握度分析。

## 核心功能

- **错题管理**：录入、查询、修改、删除、分页、按难度/时间范围筛选
- **知识点体系**：支持层级（数据结构 → 树 → 二叉树）+ 多对多关联
- **RAG 问答**：语义检索 + 大模型生成，回答可溯源到具体错题
- **多轮对话**：MySQL 存储会话消息 + 历史截断 + 摘要压缩，支持上下文追问
- **问题改写**：结合历史，把"那 A 呢"改写成完整问题
- **多 Agent 路由**：Router 判断意图，分派到 5 类专职 Agent
- **工具调用**：检索、统计、推荐、按类型筛选、按知识点列举、掌握度查询
- **SSE 流式输出**：逐 token 推送，用户可实时看到回答
- **答题记录与掌握度**：提交答题结果，按知识点统计掌握度
- **多用户隔离**：JWT 认证 + 数据层/向量层隔离，用户只能访问自己的数据
- **Redis 缓存**：token 白名单 + 用户对象缓存 + 错题单条缓存（逻辑过期）

## 技术栈

| 层次     | 技术                                            |
| :------- | :---------------------------------------------- |
| 后端框架 | Python 3.11 / FastAPI / Pydantic                |
| 数据库   | MySQL（核心数据）/ Redis（token 白名单 + 热点缓存）/ FAISS（向量） |
| ORM      | SQLAlchemy 2.0                                  |
| AI 框架  | LangChain / LangGraph                           |
| 大模型   | 千问（对话 + Embedding），OpenAI 兼容接口       |
| 认证     | JWT（含 jti）+ Redis 白名单 + bcrypt            |
| 前端     | Vue3 / Vite / Element Plus                      |
| 日志     | Python logging（分级 + 文件轮转）               |

## 架构

```
┌─────────────────────────────────────────────────────┐
│ Vue3 前端                                            │
│   登录   │   对话（SSE）  │ 错题管理 │ 知识点管理 │ 掌握度 │
└────────────────────────┬────────────────────────────┘
                         │ HTTP / SSE
┌────────────────────────▼────────────────────────────┐
│ FastAPI 接口层                                       │
│ /auth /wrong-questions /knowledge-points             │
│ /chat /conversations /stats /answers                 │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│ Service 层                                           │
│ 用户 │ 错题 │ 知识点 │ 会话 │ 答题记录 │ 对话编排      │
└──────┬─────────────────┬──────────────────┬─────────┘
       │                 │                  │
┌──────▼──────┐  ┌───────▼──────┐   ┌───────▼────────┐
│ Repository  │  │ AI 能力层     │   │ LangGraph      │
│ MySQL/Redis │  │ LLM/Embed/   │   │ 多 Agent 图     │
│             │  │ FAISS/工具    │   │                │
└─────────────┘  └──────────────┘   └────────────────┘
```

### 请求链路（以"二叉树的说法正确的是...为什么选B"为例）

用户提问
↓
① JWT 解析 → 校验 Redis token 白名单 → 获取 user_id
↓
② MySQL 读会话历史（按 user_id 隔离）+ 摘要
↓
③ 有历史 → LLM 改写问题
↓
④ Router Agent 判断意图（diagnosis）
↓
⑤ Diagnosis Agent → 调用 search_wrong_questions 工具
↓
⑥ FAISS 语义检索（metadata filter: user_id）
↓
⑦ 拼 Prompt（历史 + 检索结果 + 问题）
↓
⑧ LLM 生成回答 → SSE 逐 token 推送
↓
⑨ 写回 MySQL（含 references），超阈值触发摘要压缩

## 快速启动

### 前置依赖

- Python 3.11+
- MySQL 8.0+
- Redis 6.0+（Windows 推荐用 tporadowski/redis 的 7.x 版本）
- Node.js 18+（前端）
- 千问 API Key（[申请地址](https://dashscope.console.aliyun.com/)）

### 后端

```bash
# 1. 创建虚拟环境
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # Linux/macOS

# 2. 安装依赖
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入数据库密码、Redis、千问 API Key

# 4. 创建数据库
mysql -uroot -p
> CREATE DATABASE mistake_assistant DEFAULT CHARACTER SET utf8mb4;

# 5. 启动 Redis（另开终端，登录/鉴权依赖它）
redis-server

# 6. 启动后端
python main.py
# 访问 http://127.0.0.1:8080/docs
```

### 前端

```
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

## 项目结构

```
project/
├── ai/                    # AI 能力层
│   ├── context.py         # ContextVar 传递 user_id
│   ├── embedding_service.py
│   ├── langchain_llm.py   # ChatOpenAI 封装
│   ├── langchain_store.py # FAISS 向量存储封装
│   ├── multi_agent.py     # 多 Agent 图（Router + 5 类意图）
│   ├── prompts.py         # Prompt 模板
│   ├── retriever.py       # 检索封装
│   ├── rewrite.py         # 问题改写
│   └── tools.py           # 6 个工具定义
│
├── api/                   # HTTP 接口层
│   ├── auth_api.py        # 注册/登录/改密码/登出
│   ├── agent_api.py       # /chat/agent（含流式）
│   ├── chat_api.py        # /chat、/chat/rag（已 deprecated）
│   ├── conversation_api.py
│   ├── knowledge_point_api.py
│   ├── wrong_question_api.py
│   ├── stats_api.py       # 统计
│   └── answer_api.py      # 答题记录/掌握度
│
├── core/                  # 基础设施
│   ├── database.py        # SQLAlchemy 连接
│   ├── redis_client.py    # Redis 封装（key 前缀 + json/str 读写）
│   ├── jwt_utils.py       # JWT 生成/解析（含 jti）
│   ├── security.py        # bcrypt
│   ├── exceptions.py
│   ├── error_handlers.py  # 全局异常处理
│   ├── retry.py           # 重试装饰器
│   └── logging_config.py
│
├── models/                # SQLAlchemy ORM
├── schemas/               # Pydantic 模型
├── repositories/          # 数据访问
├── services/              # 业务逻辑
├── frontend/              # Vue3 前端
│   └── src/
│       ├── views/         # 页面
│       ├── stores/        # 状态管理
│       ├── api/           # 接口封装
│       └── utils/         # SSE 解析等
├── notes/                 # 学习笔记
├── test/                  # 测试脚本
└── main.py                # 应用入口
```

## 关键技术点

### 1. 分层架构

API / Service / Repository 三层分离，换存储只改 Repository，加 AI 流程只改 Service。

### 2. 多用户隔离

- **接口层**：`Depends(get_current_user)` 统一鉴权
- **数据层**：所有查询强制带 `user_id`
- **向量层**：FAISS metadata filter，检索只返回当前用户的错题
- **会话层**：MySQL 会话消息按 `user_id` 校验归属

### 3. RAG 流程

```
问题 → Embedding → FAISS 检索 Top-K → 拼 Prompt → LLM 生成
```

- 归一化向量 + `IndexFlatIP`，内积等价余弦相似度
- metadata filter 实现用户级隔离
- 相似度阈值过滤低分结果

### 4. 问题改写

多轮对话中，用户会省略主题（如"那 A 呢"）。
先用 LLM 结合历史改写为完整问题，再用于检索。
改写只影响检索，不影响拼给模型的 Prompt。

### 5. 多 Agent 架构

```
用户提问 → Router 判断意图
            ├── knowledge       → 知识问答
            ├── diagnosis       → 错因分析
            ├── recommendation  → 相似题推荐
            ├── stats           → 统计查询
            └── list_by_kp      → 按知识点列举
```

每个 Agent 绑定专属工具集和 System Prompt。
`tool → agent` 循环支持多轮工具调用，结束条件由 LLM 决定（不再返回 `tool_calls`）。

### 6. SSE 流式输出

- 用 `fetch` + `ReadableStream`（不用 `EventSource`，因为它只支持 GET）
- 后端 `astream_events` 捕获 LLM token
- 只推 `agent` 节点的输出，过滤 Router 和 rewrite 的中间结果
- 额外推送 `references` 事件，前端展示引用的错题

### 7. 引用溯源

`search_wrong_questions` 工具返回 JSON（含正文 + references），
`tool_node` 解析后存到 State，API 层通过 `on_chain_end` 事件推送给前端。
references 存入 MySQL 会话消息，刷新后仍可查看。

### 8. 认证与 Redis 白名单

- 登录生成含 `jti` 的 JWT，并写 Redis 白名单 `auth:token:{jti}`（TTL 与 token 一致）
- 鉴权时校验白名单：记录不存在即视为已登出/失效
- 登出、改密时删除对应白名单记录
- **容错策略（有意设计）**：登录写白名单失败 → 直接返回 503；鉴权读白名单失败 → 降级为纯 JWT 校验（优先可用性，代价是降级期间登出/改密的失效能力暂时失效）

### 9. Redis 热点数据缓存

- **用户对象缓存**：`auth:user:{user_id}`，读取免查库，改密时失效
- **错题单条缓存**：`cache:question:{user_id}:{question_id}`，逻辑过期（返回旧值 + 异步重建）+ 空值防穿透，更新/删除时主动失效
- datetime 字段在写入时序列化为 ISO 字符串、读出时还原，保证类型一致

## 评测

### 检索评测（历史结果，未在本轮复跑）

- **测试集**：21 条问题，覆盖直接问、换问法、偏门问法
- **Hit@3**：100%
- **MRR**：1.0

### 已知薄弱场景

- **缩写**："BST" vs "二叉搜索树"，相似度偏低
- **模糊问法**："我数据结构有哪些错题"，缺少主题词

改进方向：Query 改写 + 意图识别。

## 开发历程

1. FastAPI 基础 → 错题 CRUD
2. MySQL 持久化（SQLAlchemy）
3. 大模型调用（千问 OpenAI 兼容接口）
4. Embedding + FAISS 向量检索
5. 单轮 RAG
6. 多轮对话 + 会话管理
7. SSE 流式输出
8. 问题改写
9. FAISS 持久化（索引写磁盘）
10. LangChain 重构（统一接口）
11. 工具调用（Function Calling）
12. LangGraph Agent（状态图 + 条件路由）
13. 日志 + 错误处理
14. RAG 评测
15. 多用户认证 + 数据隔离
16. 知识点体系（层级 + 多对多）
17. 多 Agent 路由
18. 前端（Vue3 + SSE + 侧边栏）
19. 引用溯源
20. 对话历史管理（摘要压缩）

## 后续计划

- 知识点掌握度计算细化
- RAG 评测集扩充到 100 条
- Docker 部署
- 单元测试
