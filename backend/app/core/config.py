"""
ABDSシステム - アプリケーション設定
"""

import os
from typing import List

from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    アプリケーション設定クラス
    """

    # アプリケーション設定
    PROJECT_NAME: str = "ABDS System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # セキュリティ設定
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS設定
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # データベース設定
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "abds_db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis設定
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # 開発モード
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()