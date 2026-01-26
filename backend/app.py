# -*- coding: utf-8 -*-
"""
食品配料分析 AI 助手 - 后端入口

启动命令: uv run uvicorn app:app --reload
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from routes import chat_router, thread_router, vector_router
from exceptions import AppException, NotFoundError, ValidationError
from logger import get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    settings = get_settings()

    # 初始化数据库表
    settings.db.init_tables()

    app = FastAPI(
        title="食品配料分析 AI 助手",
        description="使用 AI 分析食品配料表，揭露食品真相",
        version="1.0.0",
    )

    # 配置 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app.cors_origins,
        allow_credentials=settings.app.cors_allow_credentials,
        allow_methods=settings.app.cors_allow_methods,
        allow_headers=settings.app.cors_allow_headers,
    )

    # 注册路由
    app.include_router(chat_router)
    app.include_router(thread_router)
    app.include_router(vector_router)

    # 注册全局异常处理器
    register_exception_handlers(app)

    return app


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器"""
    
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        logger.warning(f"资源未找到: {exc.message}")
        return JSONResponse(
            status_code=404,
            content={"code": exc.code, "message": exc.message}
        )
    
    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError):
        logger.warning(f"验证错误: {exc.message}")
        return JSONResponse(
            status_code=400,
            content={"code": exc.code, "message": exc.message, "field": exc.field}
        )
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.error(f"应用异常: {exc.message}")
        return JSONResponse(
            status_code=500,
            content={"code": exc.code, "message": exc.message}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"未处理异常: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"code": "INTERNAL_ERROR", "message": "服务器内部错误"}
        )


# 创建应用实例
app = create_app()


# ==================== 健康检查 ====================

@app.get("/health", tags=["系统"])
def health_check():
    """健康检查接口"""
    return {"status": "ok"}


@app.get("/test", tags=["系统"])
def test():
    """测试接口"""
    return "test"