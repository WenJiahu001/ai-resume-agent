# -*- coding: utf-8 -*-
"""
会话服务

处理会话列表和历史消息的业务逻辑。
"""
import uuid
from typing import List, Optional, Dict, Any

from langgraph.checkpoint.mysql.pymysql import PyMySQLSaver

from config import get_settings
from models import MessageItem, ThreadItem
from services.user import UserService, get_user_service


class ThreadService:
    """会话服务类"""

    # 消息类型映射：LangChain 类型 -> 前端 role
    MESSAGE_TYPE_MAP = {
        "human": "user",
        "ai": "assistant",
    }

    def __init__(self, user_service: UserService = None):
        self.settings = get_settings()
        self.user_service = user_service or get_user_service()

    def _get_connection(self):
        """获取数据库连接"""
        return self.settings.db.get_connection(use_dict_cursor=True)

    def _get_checkpointer(self) -> tuple:
        """获取 checkpointer 和连接（调用方需要关闭连接）"""
        conn = self.settings.db.get_connection(use_dict_cursor=True)
        checkpointer = PyMySQLSaver(conn)
        return checkpointer, conn

    def _get_message_preview(self, checkpointer: PyMySQLSaver, thread_id: str, max_length: int = 50) -> str | None:
        """获取会话最后一条消息的预览"""
        config = {"configurable": {"thread_id": thread_id}}
        ct = checkpointer.get_tuple(config)

        if not ct:
            return None

        messages = ct.checkpoint.get("channel_values", {}).get("messages", [])
        if not messages:
            return None

        last_msg = messages[-1]
        content = getattr(last_msg, "content", "")
        return content[:max_length] + "..." if len(content) > max_length else content

    def _get_message_count(self, checkpointer: PyMySQLSaver, thread_id: str) -> int:
        """获取会话的消息数量"""
        config = {"configurable": {"thread_id": thread_id}}
        ct = checkpointer.get_tuple(config)

        if not ct:
            return 0

        messages = ct.checkpoint.get("channel_values", {}).get("messages", [])
        return len(messages)

    def _convert_message_role(self, msg_type: str) -> str:
        """转换消息类型为前端 role"""
        return self.MESSAGE_TYPE_MAP.get(msg_type, msg_type)

    def _row_to_thread_item(self, row: Dict[str, Any], preview: Optional[str] = None, is_empty: bool = True) -> ThreadItem:
        """将数据库行转换为 ThreadItem"""
        return ThreadItem(
            id=row["id"],
            thread_id=row["id"],  # 兼容旧接口
            user_id=row["user_id"],
            title=row.get("title"),
            preview=preview or row.get("preview"),
            is_empty=is_empty,
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def create_thread(self, user_id: str, title: Optional[str] = None) -> ThreadItem:
        """
        创建新会话

        Args:
            user_id: 用户 ID
            title: 会话标题（可选）

        Returns:
            新创建的会话

        Raises:
            ValueError: 如果用户已存在空会话
        """
        # 确保用户存在
        self.user_service.get_or_create_user(user_id)

        # 检查是否已存在空会话
        if self.has_empty_thread(user_id):
            raise ValueError("已存在一个空会话，请先在该会话中发送消息后再新建会话")

        thread_id = str(uuid.uuid4())
        conn = self._get_connection()

        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO threads (id, user_id, title) VALUES (%s, %s, %s)",
                    (thread_id, user_id, title)
                )
                conn.commit()

                # 获取新创建的会话
                cur.execute(
                    "SELECT * FROM threads WHERE id = %s",
                    (thread_id,)
                )
                row = cur.fetchone()
                return self._row_to_thread_item(row)
        finally:
            conn.close()

    def get_thread(self, thread_id: str) -> Optional[ThreadItem]:
        """
        获取单个会话

        Args:
            thread_id: 会话 ID

        Returns:
            会话信息，不存在则返回 None
        """
        conn = self._get_connection()

        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM threads WHERE id = %s", (thread_id,))
                row = cur.fetchone()
                if row:
                    return self._row_to_thread_item(row)
                return None
        finally:
            conn.close()

    def get_user_threads(self, user_id: str) -> List[ThreadItem]:
        """
        获取指定用户的所有会话列表

        Args:
            user_id: 用户 ID

        Returns:
            会话列表（按更新时间倒序）
        """
        conn = self._get_connection()
        checkpointer, cp_conn = self._get_checkpointer()

        try:
            threads = []
            with conn.cursor() as cur:
                # 查询用户的所有会话，按更新时间倒序
                cur.execute(
                    """SELECT * FROM threads 
                       WHERE user_id = %s 
                       ORDER BY updated_at DESC""",
                    (user_id,)
                )
                rows = cur.fetchall()

                for row in rows:
                    # 获取实时的消息预览和消息数量
                    preview = self._get_message_preview(checkpointer, row["id"])
                    message_count = self._get_message_count(checkpointer, row["id"])
                    is_empty = message_count == 0
                    threads.append(self._row_to_thread_item(row, preview, is_empty))

            return threads
        finally:
            conn.close()
            cp_conn.close()

    def has_empty_thread(self, user_id: str) -> bool:
        """
        检查用户是否存在空会话（没有消息的会话）

        Args:
            user_id: 用户 ID

        Returns:
            是否存在空会话
        """
        threads = self.get_user_threads(user_id)
        return any(thread.is_empty for thread in threads)

    def get_thread_history(self, user_id: str, thread_id: str) -> List[MessageItem]:
        """
        获取指定会话的历史消息

        Args:
            user_id: 用户 ID（用于权限验证）
            thread_id: 会话 ID

        Returns:
            消息列表
        """
        checkpointer, conn = self._get_checkpointer()

        try:
            # 使用 thread_id 作为 checkpoint 标识
            config = {"configurable": {"thread_id": thread_id}}
            ct = checkpointer.get_tuple(config)

            messages = []
            if ct:
                raw_messages = ct.checkpoint.get("channel_values", {}).get("messages", [])
                for msg in raw_messages:
                    msg_type = getattr(msg, "type", "")
                    content = getattr(msg, "content", "")
                    
                    # 过滤掉不需要展示的消息类型
                    # 1. 只保留 human（用户）和 ai（助手）类型的消息
                    if msg_type not in ("human", "ai"):
                        continue
                    
                    # 2. 对于 AI 消息，过滤掉工具调用相关的消息
                    if msg_type == "ai":
                        # 检查是否有 tool_calls 属性（表示这是一个工具调用请求）
                        tool_calls = getattr(msg, "tool_calls", None)
                        if tool_calls:
                            continue
                        # 过滤掉没有实际内容的消息
                        if not content or not content.strip():
                            continue
                    
                    role = self._convert_message_role(msg_type)
                    messages.append(MessageItem(role=role, content=content))

            return messages
        finally:
            conn.close()

    def update_thread(self, thread_id: str, title: Optional[str] = None, preview: Optional[str] = None) -> Optional[ThreadItem]:
        """
        更新会话信息

        Args:
            thread_id: 会话 ID
            title: 新标题（可选）
            preview: 新预览（可选）

        Returns:
            更新后的会话，不存在则返回 None
        """
        conn = self._get_connection()

        try:
            updates = []
            params = []

            if title is not None:
                updates.append("title = %s")
                params.append(title)

            if preview is not None:
                updates.append("preview = %s")
                params.append(preview)

            if not updates:
                return self.get_thread(thread_id)

            params.append(thread_id)

            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE threads SET {', '.join(updates)} WHERE id = %s",
                    tuple(params)
                )
                conn.commit()

            return self.get_thread(thread_id)
        finally:
            conn.close()

    def delete_thread(self, thread_id: str) -> bool:
        """
        删除会话

        Args:
            thread_id: 会话 ID

        Returns:
            是否删除成功
        """
        conn = self._get_connection()

        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM threads WHERE id = %s", (thread_id,))
                conn.commit()
                return cur.rowcount > 0
        finally:
            conn.close()


# ==================== 依赖注入 ====================

def get_thread_service() -> ThreadService:
    """获取会话服务实例（用于 FastAPI 依赖注入）"""
    return ThreadService()
