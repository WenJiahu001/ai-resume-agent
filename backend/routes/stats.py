from fastapi import APIRouter, Depends
from services.token import TokenUsageService
from deps import get_current_user_id

router = APIRouter(prefix="/stats", tags=["stats"])
token_service = TokenUsageService()

@router.get("/usage")
async def get_usage_stats(user_id: str = Depends(get_current_user_id)):
    """获取当前用户的 Token 消耗统计"""
    # 这里我们简单聚合数据
    # 在实际生产中，可以在 TokenUsageService 中实现更复杂的聚合查询
    stats = await token_service.get_user_stats(user_id)
    return {
        "code": "SUCCESS",
        "data": stats
    }
