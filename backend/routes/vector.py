"""向量库路由"""

from fastapi import APIRouter

from response import success
from services.vector import get_vector_service

router = APIRouter(prefix="/api/vector", tags=["向量库"])


@router.get("/ingest", summary="导入文档到向量库")
async def ingest_documents():
    result = get_vector_service().ingest("data")
    if result.get("status") == "error":
        return success(message=result.get("message", "导入失败"))
    return success(data={"count": result.get("count", 0), "files": result.get("files", [])},
                   message=f"已导入 {result.get('count', 0)} 个文档")
