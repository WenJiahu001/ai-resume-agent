"""路由注册"""

from .chat import router as chat_router
from .thread import router as thread_router
from .auth import router as auth_router

__all__ = ["chat_router", "thread_router", "auth_router"]
