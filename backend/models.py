# -*- coding: utf-8 -*-
"""
Pydantic 数据模型

定义 API 请求和响应的数据结构。
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ==================== 请求模型 ====================

class ChatRequest(BaseModel):
    """聊天请求"""
    user_id: str = Field(..., description="用户 ID")
    thread_id: str = Field(..., description="会话 ID")
    message: str = Field(..., description="用户消息内容")

    def get_full_thread_id(self) -> str:
        """获取完整的 thread_id（直接使用 thread_id 作为 checkpoint 标识）"""
        return self.thread_id


class CreateThreadRequest(BaseModel):
    """创建会话请求"""
    user_id: str = Field(..., description="用户 ID")
    title: Optional[str] = Field(None, description="会话标题（可选）")


class UpdateThreadRequest(BaseModel):
    """更新会话请求"""
    title: Optional[str] = Field(None, description="会话标题")


# ==================== 响应模型 ====================

class MessageItem(BaseModel):
    """单条消息"""
    role: str = Field(..., description="消息角色: 'user' 或 'assistant'")
    content: str = Field(..., description="消息内容")


class ThreadItem(BaseModel):
    """会话列表项"""
    id: str = Field(..., description="会话唯一标识")
    thread_id: str = Field(..., description="会话 ID（兼容旧接口）")
    user_id: str = Field(..., description="用户 ID")
    title: Optional[str] = Field(None, description="会话标题")
    preview: Optional[str] = Field(None, description="最后一条消息的预览")
    is_empty: bool = Field(True, description="会话是否为空（没有消息）")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class ThreadListResponse(BaseModel):
    """会话列表响应"""
    threads: List[ThreadItem]
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")


class HistoryResponse(BaseModel):
    """历史消息响应"""
    thread_id: str
    messages: List[MessageItem]


class CreateThreadResponse(BaseModel):
    """创建会话响应"""
    thread: ThreadItem


# ==================== SSE 响应类型 ====================

class SSEMessage(BaseModel):
    """SSE 消息格式"""
    type: str = Field(..., description="消息类型: 'token', 'end', 'error'")
    content: Optional[str] = Field(None, description="消息内容")
    message: Optional[str] = Field(None, description="错误信息")

