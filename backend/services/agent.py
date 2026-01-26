# -*- coding: utf-8 -*-
"""
Agent 服务

管理 LangGraph Agent 的创建和生命周期。
"""
import json
from datetime import datetime
from typing import Iterator

# from langchain_core.globals import set_debug
# set_debug(True)  # 开启 LangChain 调试模式

from langchain.chat_models import init_chat_model
from langgraph.checkpoint.mysql.pymysql import PyMySQLSaver
from langgraph.prebuilt import create_react_agent as create_agent

from config import get_settings
from models import ChatRequest
from prompts import SYSTEM_PROMPT
from logger import get_logger

from langchain_core.tools import tool
from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, ToolMessage
from services.vector import get_vector_service
logger = get_logger(__name__)


def filter_messages(state):
    """
    只保留最近的 20 条消息（约 10 轮对话），同时：
    1. 始终保留第一条 SystemMessage
    2. 确保不切断工具调用的中间状态（AI 的 tool_calls 和对应的 ToolMessage 保持完整）
    
    返回 llm_input_messages 键，这样原始消息历史保持不变，只修改传给 LLM 的输入。
    """
    messages = state["messages"]
    if len(messages) <= 20:
        return {"llm_input_messages": messages}

    # 1. 提取第一条 SystemMessage（如果存在）
    system_message = None
    remaining_messages = []
    for msg in messages:
        if isinstance(msg, SystemMessage) and system_message is None:
            system_message = msg
        else:
            remaining_messages.append(msg)

    # 2. 从 remaining_messages 中取最后 N 条（为 SystemMessage 预留 1 条位置）
    max_recent = 19 if system_message else 20
    recent_messages = remaining_messages[-max_recent:] if len(remaining_messages) > max_recent else remaining_messages

    # 3. 确保不从工具调用序列中间开始
    #    - 如果第一条是 ToolMessage，说明其对应的 AIMessage (with tool_calls) 被切掉了
    #    - 需要继续向前删除，直到遇到非 ToolMessage
    while recent_messages and isinstance(recent_messages[0], ToolMessage):
        recent_messages = recent_messages[1:]

    # 4. 组合结果
    if system_message:
        return {"llm_input_messages": [system_message] + recent_messages}
    return {"llm_input_messages": recent_messages}

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
                tools=[search,getNowDateTime],
                prompt=SYSTEM_PROMPT,
                checkpointer=self._checkpointer,
                pre_model_hook=filter_messages,
            )
        return self._agent

    def get_checkpointer(self) -> PyMySQLSaver:
        """获取检查点存储器"""
        if self._checkpointer is None:
            self._checkpointer = self._create_checkpointer()
        return self._checkpointer


# ==================== 工具函数 ====================

@tool
def search(query: str, category: str = None) -> list[Document]:
    """
    通过关键词检索知识库。
    
    Args:
        query: 搜索关键词
        category: 分类过滤（可选），使用目录名作为分类
    """
    logger.info(f"正在搜索: {query}, category: {category}")
    vector_service = get_vector_service()
    return vector_service.search(query, category)

@tool
def getNowDateTime()->str:
    """
    获取当前时间。
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
