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
        """初始化用户表和会话表"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # 创建用户表
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id VARCHAR(36) PRIMARY KEY COMMENT '用户唯一标识（UUID）',
                        username VARCHAR(100) NOT NULL UNIQUE COMMENT '用户名，唯一',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表'
                """)

                # 创建会话表
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS threads (
                        id VARCHAR(36) PRIMARY KEY COMMENT '会话唯一标识（UUID）',
                        user_id VARCHAR(36) NOT NULL COMMENT '所属用户ID',
                        title VARCHAR(255) COMMENT '会话标题（可从首条消息自动生成）',
                        preview TEXT COMMENT '最后一条消息预览',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        INDEX idx_user_id (user_id) COMMENT '用户ID索引，加速按用户查询',
                        INDEX idx_updated_at (updated_at) COMMENT '更新时间索引，加速排序查询'
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话表'
                """)

                conn.commit()
                print("✅ 用户表和会话表初始化完成")
        finally:
            conn.close()


@dataclass(frozen=True)
class ModelConfig:
    """模型配置"""
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "openai:glm-4.5"))
    temperature: float = field(default_factory=lambda: float(os.getenv("MODEL_TEMPERATURE", "0.5")))
    timeout: int = field(default_factory=lambda: int(os.getenv("MODEL_TIMEOUT", "10")))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MODEL_MAX_TOKENS", "50")))


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
    app: AppConfig = field(default_factory=AppConfig)


@lru_cache
def get_settings() -> Settings:
    """获取全局配置（单例）"""
    return Settings()
