"""向量存储服务 — Qdrant 向量数据库"""

import os
import glob

from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, Filter, FieldCondition, MatchValue
from langchain_qdrant import QdrantVectorStore

from config import get_settings
from logger import get_logger

logger = get_logger(__name__)


class VectorService:
    def __init__(self):
        settings = get_settings()
        self._cfg = settings.vector
        self.client = QdrantClient(url=self._cfg.qdrant_url)
        self.embeddings = OpenAIEmbeddings(model="embedding-3")
        self._ensure_collection()
        self._init_store()

    def _ensure_collection(self):
        name = self._cfg.collection_name
        if self.client.collection_exists(name):
            return
        dim = len(self.embeddings.embed_query("test"))
        logger.info(f"创建集合 '{name}'，维度: {dim}")
        self.client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

    def _init_store(self):
        self.vectorstore = QdrantVectorStore(
            client=self.client,
            collection_name=self._cfg.collection_name,
            embedding=self.embeddings,
        )

    def search(self, query: str, category: str = None) -> list[Document]:
        kwargs = {"k": 3, "lambda_mult": 0.5}
        if category:
            kwargs["filter"] = Filter(must=[
                FieldCondition(key="metadata.category", match=MatchValue(value=category))
            ])
        return self.vectorstore.max_marginal_relevance_search(query, **kwargs)

    def ingest(self, data_dir: str = "data") -> dict:
        if not os.path.isabs(data_dir):
            project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
            candidate = os.path.join(project_root, data_dir)
            data_dir = candidate if os.path.exists(candidate) else data_dir

        if not os.path.exists(data_dir):
            return {"status": "error", "message": f"目录不存在: {data_dir}"}

        files = []
        for ext in ("*.txt", "*.md"):
            files.extend(glob.glob(os.path.join(data_dir, "**", ext), recursive=True))

        if not files:
            return {"status": "warning", "message": "未找到文档", "count": 0}

        docs = []
        for fp in files:
            try:
                content = open(fp, encoding="utf-8").read()
                docs.append(Document(
                    page_content=content,
                    metadata={"source": fp, "category": os.path.basename(os.path.dirname(fp))},
                ))
            except Exception as e:
                logger.warning(f"读取文件失败 {fp}: {e}")

        if not docs:
            return {"status": "warning", "message": "没有有效的文档被加载", "count": 0}

        # 重建集合
        try:
            self.client.delete_collection(self._cfg.collection_name)
        except Exception:
            pass
        self._ensure_collection()
        self._init_store()
        self.vectorstore.add_documents(docs)

        return {
            "status": "success",
            "count": len(docs),
            "files": [os.path.basename(f) for f in files],
        }


# ── 单例 ──

_vector_service = None


def get_vector_service() -> VectorService:
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
