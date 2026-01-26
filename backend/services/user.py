# -*- coding: utf-8 -*-
"""
用户服务

处理用户相关的业务逻辑。
"""
import uuid
from typing import Optional, Dict, Any

from config import get_settings


class UserService:
    """用户服务类"""

    def __init__(self):
        self.settings = get_settings()

    def _get_connection(self):
        """获取数据库连接"""
        return self.settings.db.get_connection(use_dict_cursor=True)

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户信息

        Args:
            user_id: 用户 ID

        Returns:
            用户信息字典，不存在则返回 None
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, username, created_at, updated_at FROM users WHERE id = %s",
                    (user_id,)
                )
                return cur.fetchone()
        finally:
            conn.close()

    def get_or_create_user(self, user_id: str, username: Optional[str] = None) -> Dict[str, Any]:
        """
        获取或创建用户

        如果用户不存在则自动创建，并同时创建一个默认会话。

        Args:
            user_id: 用户 ID
            username: 用户名（创建时使用，默认为 user_id）

        Returns:
            用户信息字典
        """
        # 先尝试获取
        user = self.get_user(user_id)
        if user:
            return user

        # 不存在则创建用户和默认会话
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                actual_username = username or f"user_{user_id[:8]}"
                # 创建用户
                cur.execute(
                    "INSERT INTO users (id, username) VALUES (%s, %s)",
                    (user_id, actual_username)
                )
                
                # 创建默认会话
                default_thread_id = str(uuid.uuid4())
                cur.execute(
                    "INSERT INTO threads (id, user_id, title) VALUES (%s, %s, %s)",
                    (default_thread_id, user_id, "默认会话")
                )
                
                conn.commit()
            return self.get_user(user_id)
        finally:
            conn.close()

    def create_user(self, username: str) -> Dict[str, Any]:
        """
        创建新用户

        Args:
            username: 用户名

        Returns:
            新创建的用户信息
        """
        user_id = str(uuid.uuid4())
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (id, username) VALUES (%s, %s)",
                    (user_id, username)
                )
                conn.commit()
            return self.get_user(user_id)
        finally:
            conn.close()


# ==================== 依赖注入 ====================

def get_user_service() -> UserService:
    """获取用户服务实例（用于 FastAPI 依赖注入）"""
    return UserService()
