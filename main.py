import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from ai import langchain_store
from ai.embedding_service import build_question_text
from api import chat_api, agent_api, auth_api, wrong_question_api, knowledge_point_api, conversation_api, stats_api, \
    answer_api
from core.database import Base, engine
from core.error_handlers import register_error_handlers
from core.logging_config import setup_logging
from repositories import wrong_question_repo


logger = logging.getLogger(__name__)

# 先配置日志（放在最前）
setup_logging(level="INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化，关闭时清理。"""
    # ===== 启动时执行（只一次）=====
    db_count = len(wrong_question_repo.list_all())  # 注意：不带 user_id，是全量
    index_count = langchain_store.count()

    Base.metadata.create_all(bind=engine)
    logger.info("[启动] 数据库表已就绪")

    if langchain_store.is_empty() or index_count != db_count:
        questions = wrong_question_repo.list_all()
        docs_data = [{"id": q["id"], "user_id": q["user_id"], "text": build_question_text(q)} for q in questions]
        langchain_store.build_store(docs_data)
        if index_count != db_count:
            logger.info("[启动] 重建索引，共 %d 条（旧 %d 条）", len(docs_data), index_count)
        else:
            logger.info("[启动] 首次构建索引，共 %d 条", len(docs_data))
    else:
        logger.info("[启动] 从磁盘加载索引，共 %d 条", index_count)

    yield  # ← 服务运行中

    # ===== 关闭时执行 =====
    logger.info("[关闭] 服务停止")


# TODO 2: 创建 FastAPI 实例，带上 title / version / description
app = FastAPI(
    title="错题知识库助手",
    version="0.1.0",
    description="基于错题知识库的智能问答助手 - 后端 API",
    lifespan=lifespan,  # ← 加上
)

# 加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# TODO 3: 把 _api.router 挂到 app 上
app.include_router(knowledge_point_api.router)
app.include_router(wrong_question_api.router)
app.include_router(chat_api.router)
app.include_router(conversation_api.router)
app.include_router(agent_api.router)
app.include_router(auth_api.router)
app.include_router(stats_api.router)
app.include_router(answer_api.router)
register_error_handlers(app)


# TODO 4: 定义一个 GET /health 健康检查接口
@app.get("/health", tags=["系统"])
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # TODO 5: 用 uvicorn.run 启动服务
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)
