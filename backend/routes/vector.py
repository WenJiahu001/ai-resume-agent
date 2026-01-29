# -*- coding: utf-8 -*-
from fastapi import APIRouter
from services.vector import get_vector_service
from response import success

router = APIRouter(prefix="/api/vector", tags=["向量库"])


@router.get(
    "/ingest",
    summary="导入文档",
    description="""
    将指定目录下的文档导入到向量数据库。
    
    **处理流程**:
    1. 读取 data 目录下的所有文档
    2. 对文档进行分块处理
    3. 生成文本向量
    4. 存储到向量数据库
    
    **支持的文档格式**:
    - PDF
    - TXT
    - Markdown
    
    **注意**: 此操作可能需要较长时间，取决于文档数量和大小
    """,
    responses={
        200: {"description": "成功导入文档", "content": {"application/json": {"example": {"code": "SUCCESS", "message": "已导入文档", "data": {"count": 10, "files": []}}}}},
        500: {"description": "导入过程中发生错误"}
    }
)
async def ingest_documents():
    """导入文档到向量库"""
    vector_service = get_vector_service()
    result = vector_service.ingest("data")
    
    if result.get("status") == "error":
        return success(data=None, message=result.get("message", "导入失败"))
    
    return success(
        data={"count": result.get("count", 0), "files": result.get("files", [])},
        message=f"已导入 {result.get('count', 0)} 个文档"
    )
