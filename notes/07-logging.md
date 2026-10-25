# 日志系统

## 解决什么问题
- 排查问题靠 print，服务重启后日志丢失
- 没有级别区分，信息混在一起
- 没有时间戳和来源，定位困难
- 生产环境无法排查

## 在项目中的位置
- `core/logging_config.py`：全局配置
- 各模块顶部：`logger = logging.getLogger(__name__)`
- `main.py`：启动时调用 `setup_logging(level="INFO")`

## 执行流程
1. `setup_logging` 在 main.py 启动时调用一次
2. 配置根 logger 的级别和 handler
3. 各模块用 `logging.getLogger(__name__)` 拿 logger
4. 日志向上冒泡到根 logger，被两个 handler 处理
5. 同时输出到控制台和文件

## 关键概念
- **Logger 层级**：root → ai → ai.tools
- **冒泡机制**：子 logger 的日志向上传递到 root
- **Handler**：决定输出到哪（StreamHandler / TimedRotatingFileHandler）
- **Formatter**：决定日志格式
- **Level**：DEBUG < INFO < WARNING < ERROR < CRITICAL

## 日志级别使用规范
| 级别    | 什么时候用                               |
| :------ | :--------------------------------------- |
| DEBUG   | 高频操作（检索、Redis 读写）             |
| INFO    | 重要业务动作（创建错题、LLM 调用、改写） |
| WARNING | 可恢复的问题（404、查不到）              |
| ERROR   | 明确的错误（LLM 失败、未处理异常）       |

## 遇到的坑
1. `logging.getLogger(_LOG_DIR)` → 创建了错误的 logger，应该用 `logging.getLogger()`
2. `echo=True` 导致 SQLAlchemy 日志重复 → 改成 `echo=False`
3. 第三方库噪音（httpx、faiss、watchfiles）→ 统一调高到 WARNING
4. `response[:40]` 报 TypeError → `response` 是对象，要先 `.content`
5. 模块级代码被多次执行 → 移到 `lifespan`

## 面试怎么讲
> 我用 Python 标准库 logging 搭了分层日志系统。
> 根 logger 配置两个 handler：控制台 + 按天轮转的文件。
> 各模块用 `getLogger(__name__)` 拿 logger，日志自动冒泡到根。
> 级别上：检索、Redis 读写用 DEBUG，业务动作用 INFO，404 用 WARNING。
> 第三方库的噪音日志统一调到 WARNING，避免刷屏。