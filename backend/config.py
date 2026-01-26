# -*- coding: utf-8 -*-
"""
应用配置管理

所有配置集中管理，支持通过环境变量覆盖默认值。
"""
import os
from dataclasses import dataclass, field
from functools import lru_cache

import pymysql
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class DatabaseConfig:
    """数据库配置"""
    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "3306")))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", "root"))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", "123456"))
    database: str = field(default_factory=lambda: os.getenv("DB_NAME", "eat"))

    def get_connection(self, use_dict_cursor: bool = False) -> pymysql.Connection:
        """获取数据库连接"""
        kwargs = {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "autocommit": True,
        }
        if use_dict_cursor:
            kwargs["cursorclass"] = pymysql.cursors.DictCursor
        return pymysql.connect(**kwargs)

    def init_tables(self) -> None:
        """
        初始化用户表和会话表
        
        从 sql/init_tables.sql 文件读取 DDL 语句执行
        """
        import os
        from logger import get_logger
        
        logger = get_logger(__name__)
        
        # 获取 SQL 文件路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file = os.path.join(current_dir, "sql", "init_tables.sql")
        
        if not os.path.exists(sql_file):
            logger.warning(f"SQL 初始化文件不存在: {sql_file}")
            return
        
        conn = self.get_connection()
        try:
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割 SQL 语句（按分号分割，过滤空语句和注释行）
            statements = [
                stmt.strip() 
                for stmt in sql_content.split(';') 
                if stmt.strip() and not stmt.strip().startswith('--')
            ]
            
            with conn.cursor() as cur:
                for stmt in statements:
                    if stmt:
                        cur.execute(stmt)
                conn.commit()
            
            logger.info("用户表和会话表初始化完成")
        except Exception as e:
            logger.error(f"初始化数据库表失败: {e}")
        finally:
            conn.close()


@dataclass(frozen=True)
class ModelConfig:
    """模型配置"""
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "openai:glm-4.5"))
    temperature: float = field(default_factory=lambda: float(os.getenv("MODEL_TEMPERATURE", "0.3")))
    timeout: int = field(default_factory=lambda: int(os.getenv("MODEL_TIMEOUT", "60")))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MODEL_MAX_TOKENS", "50")))


@dataclass(frozen=True)
class VectorConfig:
    """向量存储配置"""
    embedding_dim: int = field(default_factory=lambda: int(os.getenv("EMBEDDING_DIM", "1024")))
    qdrant_url: str = field(default_factory=lambda: os.getenv("QDRANT_URL", "http://localhost:6333"))
    collection_name: str = field(default_factory=lambda: os.getenv("QDRANT_COLLECTION", "demo"))


@dataclass(frozen=True)
class AppConfig:
    """应用配置"""
    cors_origins: list = field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True
    cors_allow_methods: list = field(default_factory=lambda: ["*"])
    cors_allow_headers: list = field(default_factory=lambda: ["*"])


@dataclass
class Settings:
    """全局配置容器"""
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    vector: VectorConfig = field(default_factory=VectorConfig)
    app: AppConfig = field(default_factory=AppConfig)


@lru_cache
def get_settings() -> Settings:
    """获取全局配置（单例）"""
    return Settings()
