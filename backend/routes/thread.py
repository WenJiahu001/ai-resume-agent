"""会话路由"""

from fastapi import APIRouter, Depends, HTTPException

from deps import get_current_user_id
from response import success
from models import CreateThreadRequest, UpdateThreadRequest
from services.thread import ThreadService

router = APIRouter(prefix="/api/threads", tags=["会话"])


def _verify_owner(service: ThreadService, thread_id: str, user_id: str) -> None:
    """验证会话归属，不属于当前用户则抛 404"""
    thread = service.get_thread(thread_id)
    if not thread or thread.user_id != user_id:
        raise HTTPException(status_code=404, detail="会话不存在")


@router.post("", summary="创建新会话")
def create_thread(
    req: CreateThreadRequest,
    current_user_id: str = Depends(get_current_user_id),
    service: ThreadService = Depends(ThreadService),
):
    try:
        thread = service.create_thread(user_id=current_user_id, title=req.title)
        return success(data={"thread": thread}, message="已创建会话")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", summary="获取会话列表")
def get_threads(
    page: int = 1,
    page_size: int = 20,
    current_user_id: str = Depends(get_current_user_id),
    service: ThreadService = Depends(ThreadService),
):
    threads, total = service.get_user_threads(current_user_id, page, page_size)
    return success(data={"threads": threads, "total": total, "page": page, "page_size": page_size})


@router.get("/{thread_id}/history", summary="获取会话历史")
def get_thread_history(
    thread_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: ThreadService = Depends(ThreadService),
):
    _verify_owner(service, thread_id, current_user_id)
    messages = service.get_thread_history(current_user_id, thread_id)
    return success(data={"thread_id": thread_id, "messages": messages})


@router.patch("/{thread_id}", summary="更新会话")
def update_thread(
    thread_id: str,
    req: UpdateThreadRequest,
    current_user_id: str = Depends(get_current_user_id),
    service: ThreadService = Depends(ThreadService),
):
    _verify_owner(service, thread_id, current_user_id)
    return success(data=service.update_thread(thread_id=thread_id, title=req.title), message="已更新会话")


@router.delete("/{thread_id}", summary="删除会话")
def delete_thread(
    thread_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: ThreadService = Depends(ThreadService),
):
    _verify_owner(service, thread_id, current_user_id)
    if not service.delete_thread(thread_id):
        raise HTTPException(status_code=404, detail="会话不存在")
    return success(data={"thread_id": thread_id}, message="已删除会话")
