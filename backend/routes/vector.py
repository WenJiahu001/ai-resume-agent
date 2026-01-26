# -*- coding: utf-8 -*-
from fastapi import APIRouter
from services.vector import get_vector_service

router = APIRouter(prefix="/api/vector", tags=["向量库"])


@router.get("/ingest")
async def ingest_documents():
    """
    导入文档到向量库
    """
    vector_service = get_vector_service()
    result = vector_service.ingest("data")
    return result
