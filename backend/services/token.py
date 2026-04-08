# -*- coding: utf-8 -*-
"""
Token 消耗统计服务

处理 Token 消耗的持久化和查询。
"""
from typing import List, Dict, Any, Optional
from config import get_settings
from logger import get_logger

logger = get_logger(__name__)

class TokenUsageService:
    """Token 消耗统计服务类"""

    def __init__(self):
        self.settings = get_settings()

    def _get_connection(self):
        """获取数据库连接"""
        return self.settings.db.get_connection(use_dict_cursor=True)

    def save_usage(
        self,
        user_id: str,
        thread_id: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int = 0
    ) -> bool:
        """
        保存一条 Token 消耗记录
        """
        if total_tokens == 0:
            total_tokens = prompt_tokens + completion_tokens

        # 简单估算成本 (示例：每 1k tokens 约 0.002 元，实际应根据 model 分情况)
        cost = (total_tokens / 1000) * 0.002

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                sql = """
                    INSERT INTO token_usage
                    (user_id, thread_id, model_name, prompt_tokens, completion_tokens, total_tokens, cost)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cur.execute(sql, (user_id, thread_id, model_name, prompt_tokens, completion_tokens, total_tokens, cost))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"保存 Token 消耗记录失败: {e}")
            return False
        finally:
            conn.close()

    def get_user_total_usage(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户的累计消耗统计
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                sql = """
                    SELECT
                        SUM(prompt_tokens) as total_prompt_tokens,
                        SUM(completion_tokens) as total_completion_tokens,
                        SUM(total_tokens) as grand_total_tokens,
                        SUM(cost) as total_cost,
                        COUNT(*) as call_count
                    FROM token_usage
                    WHERE user_id = %s
                """
                cur.execute(sql, (user_id,))
                result = cur.fetchone()
                return result if result and result['grand_total_tokens'] else {
                    "total_prompt_tokens": 0,
                    "total_completion_tokens": 0,
                    "grand_total_tokens": 0,
                    "total_cost": 0,
                    "call_count": 0
                }
        finally:
            conn.close()

def get_token_usage_service() -> TokenUsageService:
    """获取 TokenUsageService 实例"""
    return TokenUsageService()
