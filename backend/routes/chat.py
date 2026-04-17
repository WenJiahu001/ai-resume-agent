"""聊天路由"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from deps import get_current_user_id
from models import ChatRequest
from services.agent import get_agent, stream_chat

router = APIRouter(prefix="/api/chat", tags=["聊天"])


@router.post("/stream", summary="流式聊天")
async def chat_stream(
    req: ChatRequest,
    request: Request,
    current_user_id: str = Depends(get_current_user_id),
    agent=Depends(get_agent),
):
    req.user_id = current_user_id
    return StreamingResponse(stream_chat(agent, req, request), media_type="text/event-stream")
