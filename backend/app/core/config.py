"""
ABDSシステム - アプリケーション設定（簡略版）
"""

import os
from typing import List, Optional


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

    # ログ設定
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Search API settings
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_SEARCH_ENGINE_ID: Optional[str] = None
    SERPAPI_KEY: Optional[str] = None

    # AI分析API設定
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

    # AI分析設定
    AI_ANALYSIS_ENABLED: bool = True
    AI_MAX_REQUESTS_PER_MINUTE: int = 15
    AI_MAX_TOKENS_PER_REQUEST: int = 32000
    AI_DEFAULT_MODEL: str = "gemini-1.5-pro"
    AI_BACKUP_MODEL: str = "gemini-1.5-flash"


settings = Settings()
