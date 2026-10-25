# FastAPI 基础

## 解决什么问题
提供 HTTP 接口，让前端/客户端能调用后端服务。
用 Pydantic 自动完成请求校验和响应序列化，用自动生成的 /docs 做接口调试。

## 在项目中的位置
- `main.py`：应用入口，挂载所有路由
- `api/`：路由层，只负责接收请求、调用 Service、返回响应
- `schemas/`：Pydantic 模型，定义请求/响应的数据结构

## 执行流程
1. 客户端发请求 → FastAPI 路由匹配
2. 请求数据用 Pydantic Schema 校验（失败返回 422）
3. 调用 Service 层处理业务
4. Service 返回结果 → 用 response_model 校验 → 序列化为 JSON
5. 返回给客户端

## 分层架构
- API 层：HTTP 语义（接收、返回、404/201/204）
- Service 层：业务逻辑（生成 id、时间戳、默认值）
- Repository 层：数据存取（内存/MySQL）

## 遇到过什么问题
1. `@router.post("")` 用空字符串，不要用 `"/"`，否则会出现 307 重定向
2. 返回 `None` 时要 `raise HTTPException(404)`，不能直接 return
3. `response_model` 校验失败会返回 500（ResponseValidationError），不是 422
4. 422 是请求校验失败，500 是响应校验失败

## 面试怎么解释
- FastAPI 的核心优势：Pydantic 自动校验 + 自动生成 OpenAPI 文档
- 分层架构的价值：换存储只改 Repository，Service 和 API 不动
- Schema vs Model：Schema 面向 API（Pydantic），Model 面向数据库（SQLAlchemy）