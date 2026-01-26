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
from qdrant_client.models import VectorParams, Distance

load_dotenv()


class VectorService:
    """向量存储服务类（单例模式）"""
    
    # 默认集合名称
    DEFAULT_COLLECTION_NAME = "demo"
    
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
            
        self.client = QdrantClient(
            url="http://localhost:6333"
        )
        self.embeddings = OpenAIEmbeddings(
            model="embedding-3"
        )
        
        # 确保集合存在
        self._ensure_collection_exists()
        
        self.vectorstore = QdrantVectorStore(
            client=self.client,
            collection_name=self.DEFAULT_COLLECTION_NAME,
            embedding=self.embeddings,
        )

        self.retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 2,
                "lambda_mult": 0.5  # α 参数，越大越倾向 query 相似度
            }
        )
        
        VectorService._initialized = True
    
    def _ensure_collection_exists(self, collection_name: str = None):
        """
        确保指定的集合存在，如果不存在则创建
        
        Args:
            collection_name: 集合名称，默认使用 DEFAULT_COLLECTION_NAME
        """
        collection_name = collection_name or self.DEFAULT_COLLECTION_NAME
        
        if not self.client.collection_exists(collection_name=collection_name):
            try:
                print(f"集合 '{collection_name}' 不存在，正在创建...")
                # 通过一次嵌入调用获取向量维度
                dummy_vector = self.embeddings.embed_query("初始化")
                dim = len(dummy_vector)
                
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
                )
                print(f"已创建集合 '{collection_name}'，向量维度: {dim}")
            except Exception as e:
                print(f"创建集合时发生错误: {e}")

    def search(self, query: str) -> list[Document]:
        """
        搜索相关文档
        
        Args:
            query: 搜索查询文本
            
        Returns:
            相关文档列表
        """
        docs = self.retriever.invoke(query)
        return docs

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
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    docs.append(Document(page_content=content, metadata={"source": file_path}))
            except Exception as e:
                print(f"读取文件失败 {file_path}: {e}")

        if not docs:
            return {"status": "warning", "message": "没有有效的文档被加载", "count": 0}

        # 删除现有集合
        try:
            self.client.delete_collection(self.DEFAULT_COLLECTION_NAME)
        except Exception:
            pass  # 集合不存在时忽略

        # 重新创建集合
        self._ensure_collection_exists()
        
        # 重新初始化 vectorstore（因为集合被重建了）
        self.vectorstore = QdrantVectorStore(
            client=self.client,
            collection_name=self.DEFAULT_COLLECTION_NAME,
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
        
        return {
            "status": "success", 
            "count": len(docs), 
            "files": [os.path.basename(f) for f in files]
        }


# ==================== 依赖注入 ====================

def get_vector_service() -> VectorService:
    """获取向量服务实例（用于 FastAPI 依赖注入）"""
    return VectorService()


# 延迟初始化的单例访问器
_vector_service = None

def get_vector_service_instance() -> VectorService:
    """获取向量服务单例实例（延迟初始化）"""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
