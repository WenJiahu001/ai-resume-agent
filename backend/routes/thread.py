# -*- coding: utf-8 -*-
"""
会话相关路由
"""
from fastapi import APIRouter, Depends, HTTPException

from models import (
    HistoryResponse,
    ThreadListResponse,
    CreateThreadRequest,
    CreateThreadResponse,
    UpdateThreadRequest,
    ThreadItem,
)
from services.thread import ThreadService, get_thread_service

router = APIRouter(prefix="/api/threads", tags=["会话"])


@router.post("", response_model=CreateThreadResponse)
def create_thread(
    req: CreateThreadRequest,
    service: ThreadService = Depends(get_thread_service)
):
    """
    创建新会话

    创建一个新的会话，可选指定标题。
    如果用户已存在空会话，则返回 400 错误。
    """
    try:
        thread = service.create_thread(user_id=req.user_id, title=req.title)
        return CreateThreadResponse(thread=thread)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=ThreadListResponse)
def get_threads(
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    service: ThreadService = Depends(get_thread_service)
):
    """
    获取用户的会话列表（分页）

    返回指定用户的所有会话，包含每个会话最后一条消息的预览。
    会话按更新时间倒序排列。
    """
    threads, total = service.get_user_threads(user_id, page, page_size)
    return ThreadListResponse(
        threads=threads,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{user_id}/{thread_id}/history", response_model=HistoryResponse)
def get_thread_history(
    user_id: str,
    thread_id: str,
    service: ThreadService = Depends(get_thread_service)
):
    """
    获取会话的历史消息

    返回指定会话的完整消息历史。
    """
    messages = service.get_thread_history(user_id, thread_id)
    return HistoryResponse(thread_id=thread_id, messages=messages)


@router.patch("/{thread_id}", response_model=ThreadItem)
def update_thread(
    thread_id: str,
    req: UpdateThreadRequest,
    service: ThreadService = Depends(get_thread_service)
):
    """
    更新会话信息

    更新会话的标题等信息。
    """
    thread = service.update_thread(thread_id=thread_id, title=req.title)
    if not thread:
        raise HTTPException(status_code=404, detail="会话不存在")
    return thread


@router.delete("/{thread_id}")
def delete_thread(
    thread_id: str,
    service: ThreadService = Depends(get_thread_service)
):
    """
    删除会话

    删除指定的会话及其所有消息。
    """
    success = service.delete_thread(thread_id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"message": "会话已删除", "thread_id": thread_id}
