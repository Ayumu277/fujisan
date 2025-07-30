"""
ABDSシステム - アプリケーション設定
"""

import os
from typing import List, Optional
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        # Fallback for environments without pydantic
        class BaseSettings:
            pass


class Settings:
    """アプリケーション設定クラス（簡略版）"""

    PROJECT_NAME: str = "ABDS System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # データベース設定（開発用SQLite）
    DATABASE_URL: str = "sqlite:///./abds_dev.db"

    # ファイル設定
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp"]

    # CORS設定
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://frontend:3000"
    ]

    # 検索API設定
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_SEARCH_ENGINE_ID: Optional[str] = None
    SERPAPI_KEY: Optional[str] = None

    # ログ設定
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


settings = Settings()