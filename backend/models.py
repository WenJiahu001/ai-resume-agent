"""Pydantic 数据模型"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


# ── 请求模型 ──

class ChatRequest(BaseModel):
    user_id: Optional[str] = None
    thread_id: str
    message: str

    def get_full_thread_id(self) -> str:
        return self.thread_id


class CreateThreadRequest(BaseModel):
    user_id: Optional[str] = None
    title: Optional[str] = None


class UpdateThreadRequest(BaseModel):
    title: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# ── 响应模型 ──

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str


class MessageItem(BaseModel):
    content: str
    type: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    id: Optional[str] = None
    response_metadata: Optional[Dict[str, Any]] = None


class ThreadItem(BaseModel):
    id: str
    thread_id: str = None  # 兼容旧前端，序列化时自动等于 id
    user_id: str
    title: Optional[str] = None
    preview: Optional[str] = None
    is_empty: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def model_post_init(self, __context):
        if self.thread_id is None:
            self.thread_id = self.id


class ThreadListResponse(BaseModel):
    threads: List[ThreadItem]
    total: int
    page: int
    page_size: int


class HistoryResponse(BaseModel):
    thread_id: str
    messages: List[MessageItem]


class CreateThreadResponse(BaseModel):
    thread: ThreadItem
