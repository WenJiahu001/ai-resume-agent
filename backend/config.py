"""应用配置"""

import os
from dataclasses import dataclass, field
from functools import lru_cache

import pymysql
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "3306")))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", "root"))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", "123456"))
    database: str = field(default_factory=lambda: os.getenv("DB_NAME", "eat"))

    def get_connection(self, use_dict_cursor: bool = False) -> pymysql.Connection:
        kwargs = dict(
            host=self.host, port=self.port, user=self.user,
            password=self.password, database=self.database, autocommit=True,
        )
        if use_dict_cursor:
            kwargs["cursorclass"] = pymysql.cursors.DictCursor
        return pymysql.connect(**kwargs)

    def init_tables(self) -> None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file = os.path.join(current_dir, "sql", "init_tables.sql")
        if not os.path.exists(sql_file):
            return

        from logger import get_logger
        logger = get_logger(__name__)

        conn = self.get_connection()
        try:
            sql = open(sql_file, encoding="utf-8").read()
            statements = [
                s.strip() for s in sql.split(";")
                if s.strip() and not s.strip().startswith("--")
            ]
            with conn.cursor() as cur:
                for stmt in statements:
                    cur.execute(stmt)
                conn.commit()
            logger.info("数据库表初始化完成")
        except Exception as e:
            logger.error(f"初始化数据库表失败: {e}")
        finally:
            conn.close()


@dataclass(frozen=True)
class ModelConfig:
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "openai:glm-4.5"))
    temperature: float = field(default_factory=lambda: float(os.getenv("MODEL_TEMPERATURE", "0.3")))
    timeout: int = field(default_factory=lambda: int(os.getenv("MODEL_TIMEOUT", "60")))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MODEL_MAX_TOKENS", "50")))


@dataclass(frozen=True)
class AuthConfig:
    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET", "your-secret-key-should-be-changed"))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = field(default_factory=lambda: int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")))


@dataclass(frozen=True)
class VectorConfig:
    qdrant_url: str = field(default_factory=lambda: os.getenv("QDRANT_URL", "http://localhost:6333"))
    collection_name: str = field(default_factory=lambda: os.getenv("QDRANT_COLLECTION", "demo"))


@dataclass(frozen=True)
class AppConfig:
    cors_origins: list = field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True
    cors_allow_methods: list = field(default_factory=lambda: ["*"])
    cors_allow_headers: list = field(default_factory=lambda: ["*"])


@dataclass
class Settings:
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    vector: VectorConfig = field(default_factory=VectorConfig)
    app: AppConfig = field(default_factory=AppConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)


@lru_cache
def get_settings() -> Settings:
    return Settings()
