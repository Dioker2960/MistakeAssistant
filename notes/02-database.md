# 数据库（MySQL + Redis）

## 解决什么问题
- **MySQL**：持久化核心业务数据（错题），保证不丢
- **Redis**：存储临时会话历史，高频读写、可过期

## 在项目中的位置
- `core/database.py`：SQLAlchemy 连接管理
- `core/redis_client.py`：Redis 连接管理
- `models/`：SQLAlchemy ORM 模型（表结构）
- `repositories/wrong_question_repo.py`：MySQL 数据访问
- `repositories/conversation_repo.py`：Redis 会话读写

## MySQL 执行流程
1. ORM 模型定义表结构
2. `Base.metadata.create_all()` 自动建表（只建不改）
3. Repository 用 `Session` 操作数据
4. 查询用 `select(Model).where(...)`，增删改用 `session.add/delete` + `commit`
5. ORM 有脏检查机制：改对象属性后 `commit` 时自动生成 UPDATE

## Redis 执行流程
1. Key 格式：`conversation:{conversation_id}`
2. Value 是 JSON 字符串：`{"messages": [...], "created_at": ..., "updated_at": ...}`
3. 每次写入用 `setex` 设 TTL（1 小时）
4. 读用 `get` + `json.loads`

## 关键概念
- **Session**：工作单元，跟踪对象状态，相当于 JPA 的 EntityManager
- **脏检查**：改内存对象 → Session 记录变化 → commit 时自动发 SQL
- **onupdate**：ORM 自动更新 `updated_at`，不用手动设置
- **`exclude_unset=True`**：部分更新时只更新用户实际传的字段
- **`decode_responses=True`**：Redis 自动把 bytes 转 str

## 遇到过什么问题
1. `create_all` 只建表，不改表结构，改模型后要 DROP 重建
2. `list.append()` 返回 None，不返回新长度
3. Redis 存 dict 要 `json.dumps()`，读回来要 `json.loads()`
4. `json.dump` 是写文件，`json.dumps` 是转字符串，别搞混
5. Redis 需要独立启动 `redis-server.exe`

## 面试怎么解释
- **为什么用 SQLAlchemy**：跨数据库、防 SQL 注入、类型注解 + IDE 支持
- **为什么用 Redis 存会话**：临时数据、高频读写、TTL 自动过期、不阻塞 MySQL
- **存储分层**：MySQL 核心数据、Redis 临时数据、FAISS 派生索引
- **MySQL 是根**：删了其他都能重建，所以核心数据必须存 MySQL