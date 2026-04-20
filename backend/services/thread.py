"""会话服务"""

import uuid
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from langgraph.checkpoint.mysql.pymysql import PyMySQLSaver

from services.base import BaseService
from exceptions import ValidationError
from models import MessageItem, ThreadItem
from services.user import UserService


@dataclass
class CheckpointInfo:
    preview: Optional[str] = None
    message_count: int = 0


class ThreadService(BaseService):

    def __init__(self):
        super().__init__()
        self.user_service = UserService()

    def _get_checkpointer(self) -> tuple[PyMySQLSaver, object]:
        """获取 checkpointer 和连接（调用方负责关闭连接）"""
        conn = self.settings.db.get_connection(use_dict_cursor=True)
        return PyMySQLSaver(conn), conn

    def _get_checkpoint_info(self, checkpointer: PyMySQLSaver, thread_id: str, max_length: int = 50) -> CheckpointInfo:
        """获取会话的 checkpoint 信息（预览 + 消息数量），只读取一次"""
        config = {"configurable": {"thread_id": thread_id}}
        ct = checkpointer.get_tuple(config)
        if not ct:
            return CheckpointInfo()

        messages = ct.checkpoint.get("channel_values", {}).get("messages", [])
        if not messages:
            return CheckpointInfo()

        content = getattr(messages[-1], "content", "")
        preview = (content[:max_length] + "...") if len(content) > max_length else content
        return CheckpointInfo(preview=preview, message_count=len(messages))

    def _row_to_thread_item(self, row: Dict[str, Any], info: CheckpointInfo = None) -> ThreadItem:
        info = info or CheckpointInfo()
        return ThreadItem(
            id=row["id"],
            user_id=row["user_id"],
            title=row.get("title"),
            preview=info.preview or row.get("preview"),
            is_empty=info.message_count == 0,
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    # ── CRUD ──

    def create_thread(self, user_id: str, title: Optional[str] = None) -> ThreadItem:
        self.user_service.get_or_create_user(user_id)

        if self.has_empty_thread(user_id):
            raise ValidationError("已存在一个空会话，请先在该会话中发送消息后再新建会话")

        thread_id = str(uuid.uuid4())
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                if not title:
                    cur.execute("SELECT COUNT(*) as total FROM threads WHERE user_id = %s", (user_id,))
                    row = cur.fetchone()
                    title = f"新会话 {(row['total'] if row else 0) + 1}"

                cur.execute(
                    "INSERT INTO threads (id, user_id, title) VALUES (%s, %s, %s)",
                    (thread_id, user_id, title),
                )
                conn.commit()

                cur.execute("SELECT * FROM threads WHERE id = %s", (thread_id,))
                return self._row_to_thread_item(cur.fetchone())
        finally:
            conn.close()

    def get_thread(self, thread_id: str) -> Optional[ThreadItem]:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM threads WHERE id = %s", (thread_id,))
                row = cur.fetchone()
                return self._row_to_thread_item(row) if row else None
        finally:
            conn.close()

    def get_user_threads(self, user_id: str, page: int = 1, page_size: int = 20) -> tuple[List[ThreadItem], int]:
        conn = self._get_connection()
        checkpointer, cp_conn = self._get_checkpointer()
        try:
            offset = (page - 1) * page_size
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as total FROM threads WHERE user_id = %s", (user_id,))
                total = (cur.fetchone() or {}).get("total", 0)

                if total == 0:
                    return [], 0

                cur.execute(
                    """SELECT * FROM threads
                       WHERE user_id = %s ORDER BY updated_at DESC
                       LIMIT %s OFFSET %s""",
                    (user_id, page_size, offset),
                )
                rows = cur.fetchall()

            threads = []
            for row in rows:
                info = self._get_checkpoint_info(checkpointer, row["id"])
                threads.append(self._row_to_thread_item(row, info))
            return threads, total
        finally:
            conn.close()
            cp_conn.close()

    def has_empty_thread(self, user_id: str) -> bool:
        """检查是否存在空会话，使用 SQL 层面 LIMIT 1 优化"""
        checkpointer, conn = self._get_checkpointer()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM threads WHERE user_id = %s ORDER BY updated_at DESC LIMIT 1",
                    (user_id,),
                )
                row = cur.fetchone()
                if not row:
                    return False
                thread_id = row["id"]
            ct = checkpointer.get_tuple({"configurable": {"thread_id": thread_id}})
            if not ct:
                return True
            messages = ct.checkpoint.get("channel_values", {}).get("messages", [])
            return len(messages) == 0
        finally:
            conn.close()

    def get_thread_history(self, user_id: str, thread_id: str) -> List[MessageItem]:
        checkpointer, conn = self._get_checkpointer()
        try:
            ct = checkpointer.get_tuple({"configurable": {"thread_id": thread_id}})
            if not ct:
                return []

            raw_messages = ct.checkpoint.get("channel_values", {}).get("messages", [])
            return [
                MessageItem(
                    content=getattr(m, "content", ""),
                    type=getattr(m, "type", ""),
                    name=getattr(m, "name", None),
                    tool_calls=getattr(m, "tool_calls", None),
                    tool_call_id=getattr(m, "tool_call_id", None),
                    id=getattr(m, "id", None),
                    response_metadata=getattr(m, "response_metadata", None),
                )
                for m in raw_messages
            ]
        finally:
            conn.close()

    def update_thread(self, thread_id: str, title: Optional[str] = None, preview: Optional[str] = None) -> Optional[ThreadItem]:
        updates, params = [], []
        if title is not None:
            updates.append("title = %s")
            params.append(title)
        if preview is not None:
            updates.append("preview = %s")
            params.append(preview)

        if not updates:
            return self.get_thread(thread_id)

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE threads SET {', '.join(updates)} WHERE id = %s",
                    (*params, thread_id),
                )
                conn.commit()
            return self.get_thread(thread_id)
        finally:
            conn.close()

    def delete_thread(self, thread_id: str) -> bool:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM threads WHERE id = %s", (thread_id,))
                conn.commit()
                return cur.rowcount > 0
        finally:
            conn.close()
