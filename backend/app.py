# -*- coding: utf-8 -*-
"""
食品配料分析 AI 助手 - 后端入口

启动命令: uv run uvicorn app:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routes import chat_router, thread_router, vector_router


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

    return app


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