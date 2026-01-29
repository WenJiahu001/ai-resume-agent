# -*- coding: utf-8 -*-
"""
会话相关路由
"""
from fastapi import APIRouter, Depends, HTTPException

from response import success, fail, ApiResponse
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


@router.post(
    "",
    response_model=ApiResponse[CreateThreadResponse],
    summary="创建新会话",
    description="""
    创建一个新的会话。
    
    **注意事项**:
    - 可选指定会话标题
    - 如果用户已存在空会话（没有任何消息的会话），则返回 400 错误
    - 建议在用户开始新对话时调用此接口
    """,
    responses={
        200: {"description": "成功创建会话"},
        400: {"description": "用户已存在空会话或参数错误"}
    }
)
def create_thread(
    req: CreateThreadRequest,
    service: ThreadService = Depends(get_thread_service)
):
    """创建新会话"""
    try:
        thread = service.create_thread(user_id=req.user_id, title=req.title)
        return success(data={"thread": thread}, message="已创建会话")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{user_id}",
    response_model=ApiResponse[ThreadListResponse],
    summary="获取会话列表",
    description="""
    获取指定用户的会话列表（支持分页）。
    
    **返回内容**:
    - 会话按更新时间倒序排列
    - 每个会话包含最后一条消息的预览
    - 支持分页查询
    """,
    responses={
        200: {"description": "成功返回会话列表"}
    }
)
def get_threads(
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    service: ThreadService = Depends(get_thread_service)
):
    """获取用户的会话列表（分页）"""
    threads, total = service.get_user_threads(user_id, page, page_size)
    return success(
        data={"threads": threads, "total": total, "page": page, "page_size": page_size},
        message="已获取会话列表"
    )


@router.get(
    "/{user_id}/{thread_id}/history",
    response_model=ApiResponse[HistoryResponse],
    summary="获取会话历史",
    description="""
    获取指定会话的完整消息历史记录。
    
    **返回内容**:
    - 按时间顺序排列的所有消息
    - 每条消息包含角色（user/assistant）和内容
    """,
    responses={
        200: {"description": "成功返回消息历史"},
        404: {"description": "会话不存在"}
    }
)
def get_thread_history(
    user_id: str,
    thread_id: str,
    service: ThreadService = Depends(get_thread_service)
):
    """获取会话的历史消息"""
    messages = service.get_thread_history(user_id, thread_id)
    return success(
        data={"thread_id": thread_id, "messages": messages},
        message="已获取历史消息"
    )


@router.patch(
    "/{thread_id}",
    response_model=ApiResponse[ThreadItem],
    summary="更新会话",
    description="""
    更新指定会话的信息。
    
    **可更新内容**:
    - 会话标题
    """,
    responses={
        200: {"description": "成功更新会话"},
        404: {"description": "会话不存在"}
    }
)
def update_thread(
    thread_id: str,
    req: UpdateThreadRequest,
    service: ThreadService = Depends(get_thread_service)
):
    """更新会话信息"""
    thread = service.update_thread(thread_id=thread_id, title=req.title)
    if not thread:
        raise HTTPException(status_code=404, detail="会话不存在")
    return success(data=thread, message="已更新会话")


@router.delete(
    "/{thread_id}",
    response_model=ApiResponse[dict],
    summary="删除会话",
    description="""
    删除指定的会话及其所有关联数据。
    
    **删除内容**:
    - 会话记录
    - 会话中的所有消息
    - 相关的 checkpoint 数据
    
    **警告**: 此操作不可逆！
    """,
    responses={
        200: {"description": "成功删除会话"},
        404: {"description": "会话不存在"}
    }
)
def delete_thread(
    thread_id: str,
    service: ThreadService = Depends(get_thread_service)
):
    """删除会话及其所有消息"""
    deleted = service.delete_thread(thread_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在")
    return success(data={"thread_id": thread_id}, message="已删除会话")
