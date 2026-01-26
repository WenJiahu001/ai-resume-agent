# -*- coding: utf-8 -*-
"""Routes 模块"""

from .chat import router as chat_router
from .thread import router as thread_router
from .vector import router as vector_router

__all__ = ["chat_router", "thread_router", "vector_router"]
