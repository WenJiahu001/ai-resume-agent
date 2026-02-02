# -*- coding: utf-8 -*-
"""
聊天相关路由
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from deps import get_current_user_id
from models import ChatRequest
from services.agent import get_agent, stream_chat

router = APIRouter(prefix="/api/chat", tags=["聊天"])


@router.post(
    "/stream",
    summary="流式聊天",
    description="""
    发送消息并获取 AI 的流式响应。
    
    **响应格式**: Server-Sent Events (SSE)
    
    每个事件的格式为:
    - `type: token` - AI 响应的文本片段
    - `type: end` - 响应结束标识
    - `type: error` - 错误信息
    
    **使用示例**:
    ```javascript
    const eventSource = new EventSource('/api/chat/stream');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data.content);
    };
    ```
    """,
    responses={
        200: {
            "description": "成功返回流式响应",
            "content": {
                "text/event-stream": {
                    "example": 'data: {"type": "token", "content": "你好"}\n\ndata: {"type": "end"}\n\n'
                }
            }
        },
        400: {"description": "请求参数错误"},
        500: {"description": "服务器内部错误"}
    }
)
def chat_stream(
    req: ChatRequest, 
    current_user_id: str = Depends(get_current_user_id),
    agent=Depends(get_agent)
):
    """流式聊天接口 - 发送消息并获取 AI 的流式响应"""
    # 强制覆盖请求中的 user_id，确保安全性
    req.user_id = current_user_id
    
    return StreamingResponse(
        stream_chat(agent, req),
        media_type="text/event-stream"
    )
