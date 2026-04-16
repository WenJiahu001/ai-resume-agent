"""用户服务"""

import uuid
from typing import Optional, Dict, Any

from services.base import BaseService


class UserService(BaseService):

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, username, created_at, updated_at FROM users WHERE id = %s",
                    (user_id,),
                )
                return cur.fetchone()
        finally:
            conn.close()

    def get_or_create_user(self, user_id: str, username: Optional[str] = None) -> Dict[str, Any]:
        user = self.get_user(user_id)
        if user:
            return user

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                actual_username = username or f"user_{user_id[:8]}"
                cur.execute(
                    "INSERT INTO users (id, username) VALUES (%s, %s)",
                    (user_id, actual_username),
                )
                default_thread_id = str(uuid.uuid4())
                cur.execute(
                    "INSERT INTO threads (id, user_id, title) VALUES (%s, %s, %s)",
                    (default_thread_id, user_id, "默认会话"),
                )
                conn.commit()
            return self.get_user(user_id)
        finally:
            conn.close()

    def create_user(self, username: str) -> Dict[str, Any]:
        user_id = str(uuid.uuid4())
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (id, username) VALUES (%s, %s)",
                    (user_id, username),
                )
                conn.commit()
            return self.get_user(user_id)
        finally:
            conn.close()
