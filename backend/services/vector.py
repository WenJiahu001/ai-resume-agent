# -*- coding: utf-8 -*-
"""
向量存储服务

提供文档向量化存储和检索功能，基于 Qdrant 向量数据库。
"""
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from dotenv import load_dotenv
from langchain_core.documents import Document
from qdrant_client.models import VectorParams, Distance, Filter, FieldCondition, MatchValue

from logger import get_logger

load_dotenv()

logger = get_logger(__name__)


class VectorService:
    """向量存储服务类（单例模式）"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # 避免重复初始化
        if VectorService._initialized:
            return
        
        from config import get_settings
        settings = get_settings()
        
        self.settings = settings.vector
        self.client = QdrantClient(
            url=self.settings.qdrant_url
        )
        self.embeddings = OpenAIEmbeddings(
            model="embedding-3"
        )
        
        # 确保集合存在
        self._ensure_collection_exists()
        
        self.vectorstore = QdrantVectorStore(
            client=self.client,
            collection_name=self.settings.collection_name,
            embedding=self.embeddings,
        )

        self.retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 3,
                "lambda_mult": 0.5  # α 参数，越大越倾向 query 相似度
            }
        )
        
        VectorService._initialized = True
    
    def _ensure_collection_exists(self, collection_name: str = None):
        """
        确保指定的集合存在，如果不存在则创建
        
        Args:
            collection_name: 集合名称，默认使用配置中的 collection_name
        """
        collection_name = collection_name or self.settings.collection_name
        
        if not self.client.collection_exists(collection_name=collection_name):
            try:
                logger.info(f"集合 '{collection_name}' 不存在，正在创建...")
                dim = self.settings.embedding_dim
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
                )
                logger.info(f"已创建集合 '{collection_name}'，向量维度: {dim}")
            except Exception as e:
                logger.error(f"创建集合时发生错误: {e}")

    def search(self, query: str, category: str = None) -> list[Document]:
        """
        搜索相关文档
        
        Args:
            query: 搜索查询文本
            category: 分类 filtering (optional)
            
        Returns:
            相关文档列表
        """
        kwargs = {
            "k": 3,
            "lambda_mult": 0.5
        }
        
        if category:
            kwargs["filter"] = Filter(
                must=[
                    FieldCondition(
                        key="metadata.category",
                        match=MatchValue(value=category)
                    )
                ]
            )
            
        return self.vectorstore.max_marginal_relevance_search(query, **kwargs)

    def ingest(self, data_dir: str = "data") -> dict:
        """
        导入文档到向量库
        
        Args:
            data_dir: 文档目录路径，支持绝对路径和相对路径
            
        Returns:
            导入结果，包含状态和文档数量
        """
        import os
        import glob
        
        # 处理相对路径
        if not os.path.isabs(data_dir):
            if not os.path.exists(data_dir):
                # 尝试相对于项目根目录查找
                current_dir = os.path.dirname(os.path.abspath(__file__))
                potential_path = os.path.join(current_dir, "../../", data_dir)
                if os.path.exists(potential_path):
                    data_dir = potential_path
        
        if not os.path.exists(data_dir):
            return {"status": "error", "message": f"目录不存在: {data_dir}"}

        docs = []
        # 支持 .txt 和 .md 文件
        extensions = ['*.txt', '*.md']
        files = []
        for ext in extensions:
            files.extend(glob.glob(os.path.join(data_dir, "**", ext), recursive=True))
            
        if not files:
            return {"status": "warning", "message": "未找到文档", "count": 0}

        for file_path in files:
            try:
                # 获取父目录名称作为 category
                category = os.path.basename(os.path.dirname(file_path))
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    docs.append(Document(
                        page_content=content, 
                        metadata={
                            "source": file_path,
                            "category": category
                        }
                    ))
            except Exception as e:
                logger.warning(f"读取文件失败 {file_path}: {e}")

        if not docs:
            return {"status": "warning", "message": "没有有效的文档被加载", "count": 0}

        # 删除现有集合
        try:
            self.client.delete_collection(self.settings.collection_name)
        except Exception:
            pass  # 集合不存在时忽略

        # 重新创建集合
        self._ensure_collection_exists()
        
        # 重新初始化 vectorstore（因为集合被重建了）
        self.vectorstore = QdrantVectorStore(
            client=self.client,
            collection_name=self.settings.collection_name,
            embedding=self.embeddings,
        )

        # 添加文档到向量库
        self.vectorstore.add_documents(docs)
        
        # 更新 retriever
        self.retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 2,
                "lambda_mult": 0.5 
            }
        )
        
        # 更新 retriever
        self.retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 2,
                "lambda_mult": 0.5 
            }
        )
        
        return {
            "status": "success", 
            "count": len(docs), 
            "files": [os.path.basename(f) for f in files]
        }


# ==================== 依赖注入 ====================

# 延迟初始化的单例访问器
_vector_service = None

def get_vector_service() -> VectorService:
    """
    获取向量服务实例（用于 FastAPI 依赖注入）
    
    使用延迟初始化的单例模式，确保全局只有一个实例。
    """
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
