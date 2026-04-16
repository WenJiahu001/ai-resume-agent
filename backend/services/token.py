"""Token 消耗统计服务"""

from typing import Dict, Any

from services.base import BaseService
from logger import get_logger

logger = get_logger(__name__)


class TokenUsageService(BaseService):

    def save_usage(
        self,
        user_id: str,
        thread_id: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int = 0,
    ) -> bool:
        total_tokens = total_tokens or prompt_tokens + completion_tokens
        cost = (total_tokens / 1000) * 0.002

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO token_usage
                       (user_id, thread_id, model_name, prompt_tokens, completion_tokens, total_tokens, cost)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (user_id, thread_id, model_name, prompt_tokens, completion_tokens, total_tokens, cost),
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"保存 Token 消耗记录失败: {e}")
            return False
        finally:
            conn.close()

    def get_user_total_usage(self, user_id: str) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT
                         SUM(prompt_tokens) as total_prompt_tokens,
                         SUM(completion_tokens) as total_completion_tokens,
                         SUM(total_tokens) as grand_total_tokens,
                         SUM(cost) as total_cost,
                         COUNT(*) as call_count
                       FROM token_usage WHERE user_id = %s""",
                    (user_id,),
                )
                result = cur.fetchone()
                return result if result and result["grand_total_tokens"] else {
                    "total_prompt_tokens": 0,
                    "total_completion_tokens": 0,
                    "grand_total_tokens": 0,
                    "total_cost": 0,
                    "call_count": 0,
                }
        finally:
            conn.close()
