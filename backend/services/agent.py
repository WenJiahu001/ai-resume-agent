# -*- coding: utf-8 -*-
"""
Agent 服务

管理 LangGraph Agent 的创建和生命周期。
"""
import json
from typing import Iterator

from langchain.chat_models import init_chat_model
from langgraph.checkpoint.mysql.pymysql import PyMySQLSaver
from langgraph.prebuilt import create_react_agent as create_agent

from config import get_settings
from models import ChatRequest
from prompts import SYSTEM_PROMPT

from langchain_core.tools import tool
from langchain_core.documents import Document
from services.vector import get_vector_service_instance

# GLOBAL_VECTOR_STORE = None # Removed


class AgentService:
    """Agent 服务类（单例模式）"""

    _instance = None
    _agent = None
    _checkpointer = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _create_model(self):
        """创建语言模型"""
        settings = get_settings()
        return init_chat_model(
            settings.model.model_name,
            temperature=settings.model.temperature,
            timeout=settings.model.timeout,
            max_tokens=settings.model.max_tokens,
        )

    def _create_checkpointer(self) -> PyMySQLSaver:
        """创建检查点存储器"""
        settings = get_settings()
        conn = settings.db.get_connection()
        checkpointer = PyMySQLSaver(conn)
        checkpointer.setup()  # 初始化数据库表结构
        return checkpointer

    def get_agent(self):
        """获取或创建 Agent 实例"""
        if self._agent is None:
            # global GLOBAL_VECTOR_STORE
            # if GLOBAL_VECTOR_STORE is None:
            #     GLOBAL_VECTOR_STORE = myVector2()

            model = self._create_model()
            self._checkpointer = self._create_checkpointer()
            self._agent = create_agent(
                model=model,
                tools=[search],
                prompt=SYSTEM_PROMPT,
                checkpointer=self._checkpointer,
            )
        return self._agent

    def get_checkpointer(self) -> PyMySQLSaver:
        """获取检查点存储器"""
        if self._checkpointer is None:
            self._checkpointer = self._create_checkpointer()
        return self._checkpointer


# ==================== 工具函数 ====================

@tool
def search(query: str) -> list[Document]:
    """通过关键词检索知识库。"""
    print("正在搜索...")
    vector_service = get_vector_service_instance()
    return vector_service.search(query)

def sse_format(data: str) -> str:
    """格式化 SSE 消息"""
    return f"data: {data}\n\n"


def stream_chat(agent, req: ChatRequest) -> Iterator[str]:
    """
    流式聊天处理

    Args:
        agent: LangGraph Agent 实例
        req: 聊天请求

    Yields:
        SSE 格式的响应数据
    """
    # 参数校验
    if any(not v or not str(v).strip() for v in (req.user_id, req.thread_id, req.message)):
        yield sse_format(json.dumps({"type": "error", "message": "请检查参数后再进行调用"}))
        return

    config = {"configurable": {"thread_id": req.get_full_thread_id()}}

    try:
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": req.message}]},
            config=config,
        ):
            agent_chunk = chunk.get("agent")
            if agent_chunk and "messages" in agent_chunk:
                msg = agent_chunk["messages"][-1]
                if msg.content and msg.content != "\n":
                    yield sse_format(
                        json.dumps(
                            {"type": "token", "content": msg.content},
                            ensure_ascii=False,
                        )
                    )
        yield sse_format(json.dumps({"type": "end"}))
    except Exception as exc:
        yield sse_format(json.dumps({"type": "error", "content": str(exc)}))


# ==================== 依赖注入 ====================

def get_agent_service() -> AgentService:
    """获取 Agent 服务实例（用于 FastAPI 依赖注入）"""
    return AgentService()


def get_agent():
    """获取 Agent 实例（用于 FastAPI 依赖注入）"""
    return AgentService().get_agent()
