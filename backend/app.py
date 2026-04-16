"""简历 AI 助手 — 后端入口

启动命令: uv run uvicorn app:app --app-dir backend --reload
"""
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import get_settings
from routes import chat_router, thread_router, vector_router, auth_router
from exceptions import AppException, NotFoundError, ValidationError
from response import success
from logger import get_logger

logger = get_logger(__name__)


def _error_response(code: int, exc_code: str, message: str, data=None) -> JSONResponse:
    return JSONResponse(status_code=code, content={"code": exc_code, "message": message, "data": data})


def create_app() -> FastAPI:
    settings = get_settings()
    settings.db.init_tables()

    app = FastAPI(title="简历 AI 助手", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.cors_origins,
        allow_credentials=settings.app.cors_allow_credentials,
        allow_methods=settings.app.cors_allow_methods,
        allow_headers=settings.app.cors_allow_headers,
    )

    for r in (auth_router, chat_router, thread_router, vector_router):
        app.include_router(r)

    # 异常处理
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        logger.warning(f"资源未找到: {exc.message}")
        return _error_response(404, exc.code, exc.message)

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError):
        logger.warning(f"验证错误: {exc.message}")
        return _error_response(400, exc.code, exc.message, {"field": exc.field} if exc.field else None)

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.error(f"应用异常: {exc.message}")
        return _error_response(500, exc.code, exc.message)

    @app.exception_handler(Exception)
    async def general_handler(request: Request, exc: Exception):
        logger.error(f"未处理异常: {exc}", exc_info=True)
        return _error_response(500, "INTERNAL_ERROR", "服务器内部错误")

    # 前端静态文件
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
    if os.path.exists(frontend_dir):
        app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")
    else:
        logger.warning(f"前端目录不存在: {frontend_dir}")

    return app


app = create_app()


@app.get("/health", tags=["系统"], summary="健康检查")
def health_check():
    return success(message="服务正常")
