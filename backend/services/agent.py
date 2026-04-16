"""Agent 服务 — LangGraph ReAct Agent 创建与流式聊天"""

import asyncio
import json
import os
from collections.abc import AsyncIterator
from datetime import datetime
from queue import Queue, Empty
from threading import Thread

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.mysql.pymysql import PyMySQLSaver
from langgraph.prebuilt import create_react_agent as create_agent

from config import get_settings
from logger import get_logger
from models import ChatRequest
from prompts import SYSTEM_PROMPT
from services.token import TokenUsageService

logger = get_logger(__name__)

# data 目录路径（相对于 backend/）
_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")

# 分类 → 目录名映射
_CATEGORIES = {
    "个人信息": "个人信息",
    "个人技能": "个人技能",
    "工作经历": "工作经历",
    "教育经历": "教育经历",
    "证书": "证书",
    "项目经历": "项目经历",
}


# ── 消息裁剪 ──

def filter_messages(state):
    """保留最近 20 条消息，始终保留首条 SystemMessage，不切断工具调用序列"""
    messages = state["messages"]
    if len(messages) <= 20:
        return {"llm_input_messages": messages}

    system_msg = None
    rest = []
    for msg in messages:
        if isinstance(msg, SystemMessage) and system_msg is None:
            system_msg = msg
        else:
            rest.append(msg)

    max_recent = 19 if system_msg else 20
    recent = rest[-max_recent:]

    # 跳过被截断的 ToolMessage（对应的 AIMessage 已被切掉）
    while recent and isinstance(recent[0], ToolMessage):
        recent = recent[1:]

    result = [system_msg] + recent if system_msg else recent
    return {"llm_input_messages": result}


# ── 文件读取工具 ──

def _read_file(filepath: str) -> str:
    try:
        with open(filepath, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取文件失败 {filepath}: {e}")
        return f"[读取失败: {filepath}]"


def _find_files(category: str, query: str = None) -> list[str]:
    """在指定分类目录下查找文件，query 用于模糊匹配文件名"""
    dir_name = _CATEGORIES.get(category)
    if not dir_name:
        return []

    cat_dir = os.path.join(_DATA_DIR, dir_name)
    if not os.path.isdir(cat_dir):
        return []

    if query and category == "项目经历":
        # 项目经历：模糊匹配文件名
        matched = [
            os.path.join(cat_dir, f) for f in os.listdir(cat_dir)
            if query.lower() in f.lower() and not f.endswith("汇总.md")
        ]
        return matched if matched else [os.path.join(cat_dir, "项目汇总.md")]

    # 其他分类或无 query：读取该分类下所有 .md 文件
    return [
        os.path.join(cat_dir, f)
        for f in sorted(os.listdir(cat_dir))
        if f.endswith(".md")
    ]


@tool
def search_resume(category: str, query: str = None) -> str:
    """查询简历数据。

    根据分类加载对应的简历文档内容。如果指定了 query，会在项目经历中模糊匹配文件名。

    可用分类：个人信息、个人技能、工作经历、教育经历、证书、项目经历

    Args:
        category: 数据分类名称，如 "个人信息"、"项目经历"
        query: 可选关键词，用于在项目经历中定位特定项目文件
    """
    logger.info(f"查询简历: category={category}, query={query}")

    files = _find_files(category, query)
    if not files:
        available = "、".join(_CATEGORIES.keys())
        return f"未找到分类 '{category}' 的数据。可用分类：{available}"

    contents = [_read_file(f) for f in files]
    return "\n\n---\n\n".join(contents)


@tool
def getNowDateTime() -> str:
    """获取当前时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ── SSE 辅助 ──

def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# ── Agent 单例 ──

_agent_service = None


class AgentService:
    _agent = None
    _checkpointer = None

    def get_agent(self):
        if self._agent is None:
            settings = get_settings()
            model = init_chat_model(
                settings.model.model_name,
                temperature=settings.model.temperature,
                timeout=settings.model.timeout,
                max_tokens=settings.model.max_tokens,
            )
            conn = settings.db.get_connection()
            self._checkpointer = PyMySQLSaver(conn)
            self._checkpointer.setup()
            self._agent = create_agent(
                model=model,
                tools=[search_resume, getNowDateTime],
                prompt=SYSTEM_PROMPT,
                checkpointer=self._checkpointer,
                pre_model_hook=filter_messages,
            )
        return self._agent

    def get_checkpointer(self) -> PyMySQLSaver:
        if self._checkpointer is None:
            settings = get_settings()
            conn = settings.db.get_connection()
            self._checkpointer = PyMySQLSaver(conn)
            self._checkpointer.setup()
        return self._checkpointer


def get_agent_service() -> AgentService:
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service


def get_agent():
    return get_agent_service().get_agent()


# ── 流式聊天 ──

_SENTINEL = object()


async def stream_chat(agent, req: ChatRequest) -> AsyncIterator[str]:
    if not all(str(v).strip() for v in (req.user_id, req.thread_id, req.message)):
        yield _sse({"type": "error", "message": "请检查参数后再进行调用"})
        return

    config = {"configurable": {"thread_id": req.get_full_thread_id()}}
    token_service = TokenUsageService()
    model_name = get_settings().model.model_name

    queue: Queue = Queue()

    def _run_stream():
        """在子线程中运行同步 agent.stream()，把结果逐个放入队列"""
        try:
            logger.info("stream start")
            for chunk in agent.stream(
                {"messages": [HumanMessage(content=req.message)]},
                config=config,
            ):
                queue.put(chunk)
        except Exception as exc:
            queue.put(exc)
        finally:
            queue.put(_SENTINEL)

    thread = Thread(target=_run_stream, daemon=True)
    thread.start()

    try:
        while True:
            # 非阻塞轮询，让出事件循环
            while True:
                try:
                    item = queue.get_nowait()
                    break
                except Empty:
                    await asyncio.sleep(0.02)

            if item is _SENTINEL:
                break

            if isinstance(item, Exception):
                raise item

            chunk = item

            # AI 响应
            agent_msg = (chunk.get("agent") or {}).get("messages")
            if agent_msg:
                msg = agent_msg[-1]
                resp = {"type": "token", "content": msg.content}

                if hasattr(msg, "usage_metadata") and msg.usage_metadata:
                    usage = msg.usage_metadata
                    token_service.save_usage(
                        user_id=req.user_id,
                        thread_id=req.thread_id,
                        model_name=model_name,
                        prompt_tokens=usage.get("input_tokens", 0),
                        completion_tokens=usage.get("output_tokens", 0),
                        total_tokens=usage.get("total_tokens", 0),
                    )

                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        yield _sse({
                            "type": "tool_call",
                            "id": tc.get("id", ""),
                            "name": tc.get("name", ""),
                        })

                yield _sse(resp)

            # 工具结果
            tool_msgs = (chunk.get("tools") or {}).get("messages")
            if tool_msgs:
                for tm in tool_msgs:
                    yield _sse({
                        "type": "tool_result",
                        "name": getattr(tm, "name", ""),
                        "tool_call_id": getattr(tm, "tool_call_id", ""),
                        "content": getattr(tm, "content", str(tm)),
                    })

        yield _sse({"type": "end"})
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"流式聊天异常: {type(exc).__name__}: {exc}\n{tb}")
        yield _sse({"type": "error", "content": f"{type(exc).__name__}: {exc}"})
