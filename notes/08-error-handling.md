# 错误处理

## 解决什么问题
- LLM 超时、Redis 挂了 → 用户看到 500 堆栈
- 业务错误信息不友好
- 临时故障没有重试
- 未处理异常暴露内部细节

## 在项目中的位置
- `core/exceptions.py`：自定义异常
- `core/retry.py`：重试装饰器
- `core/error_handlers.py`：全局异常处理器
- `main.py`：注册处理器

## 四个层次
1. **自定义异常**：`AppError` / `BusinessError` / `LLMError`
2. **重试机制**：`@retry(max_attempts=3, delay=1.0, backoff=2.0)`
3. **全局异常处理器**：注册到 FastAPI
4. **友好错误信息**：返回统一格式

## 执行流程

业务代码 raise BusinessError("...")
↓
FastAPI 捕获
↓
匹配 @app.exception_handler(BusinessError)
↓
返回 JSONResponse(status_code=400, content={"code": ..., "message": ...})

## 异常处理链
| 异常类型        | 状态码 | 用途                     |
| :-------------- | :----- | :----------------------- |
| `BusinessError` | 400    | 业务错误（资源不存在等） |
| `AppError`      | 500    | 其他自定义异常           |
| `Exception`     | 500    | 兜底，返回友好提示       |

## 重试机制
```python
@retry(max_attempts=3, delay=1.0, backoff=2.0)
def call_llm(messages):
    return llm.invoke(messages)
```

- **第 1 次失败** → 等 1 秒
- **第 2 次失败** → 等 2 秒
- **第 3 次失败** → 抛异常

**为什么指数退避**：服务真挂了时，疯狂重试会加重负担。

## 遇到的坑

1. API 层和全局处理器都打 WARNING → 日志冗余（记到 todo）
2. `BusinessError` 返回 400，但“资源不存在”语义上应该是 404
3. 不是所有异常都该重试（401、400 重试无用）

## 面试怎么讲

> 我做了三层错误处理：
>
> 1. 自定义异常区分业务错误和系统错误。
> 2. 重试装饰器处理临时故障（超时、限流），指数退避。
> 3. FastAPI 全局异常处理器，统一返回格式，未处理异常兜底。
>    这样用户看到的永远是友好的错误信息，堆栈只进日志。