# -*- coding: utf-8 -*-
"""
聊天相关路由
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from models import ChatRequest
from services.agent import get_agent, stream_chat

router = APIRouter(prefix="/api/chat", tags=["聊天"])


@router.post("/stream")
def chat_stream(req: ChatRequest, agent=Depends(get_agent)):
    """
    流式聊天接口

    发送消息并获取 AI 的流式响应。
    """
    return StreamingResponse(
        stream_chat(agent, req),
        media_type="text/event-stream"
    )
