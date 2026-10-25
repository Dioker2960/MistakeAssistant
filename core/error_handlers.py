import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.exceptions import AppError, BusinessError

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    """注册全局异常处理器。"""

    @app.exception_handler(BusinessError)
    async def business_error_handler(request: Request, exc: BusinessError):
        logger.warning("业务错误: %s, path=%s", exc.message, request.url.path)
        return JSONResponse(
            status_code=400,
            content={"code": exc.code, "message": exc.message},
        )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.error("应用错误: %s, path=%s", exc.message, request.url.path, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"code": exc.code, "message": exc.message},
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        # 捕获所有未处理的异常，避免堆栈暴露给用户
        logger.error(
            "未处理异常: %s, path=%s",
            exc, request.url.path, exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"code": "INTERNAL_ERROR", "message": "系统内部错误，请稍后重试"},
        )