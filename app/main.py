"""
ABDSシステム - FastAPI メインアプリケーション
"""

import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn

from app.core.config import settings
from app.api.router import api_router

# ログ設定
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリケーションのライフサイクル管理
    起動時と終了時の処理を定義
    """
    # 起動時の処理
    logger.info(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} starting...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # アップロードディレクトリの作成
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(exist_ok=True)
    logger.info(f"Upload directory created: {upload_dir.absolute()}")

    yield

    # 終了時の処理
    logger.info(f"📴 {settings.PROJECT_NAME} shutting down...")


# FastAPIアプリケーションの初期化
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="ABDSシステムのAPIサーバー - FastAPI + PostgreSQL + Redis",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# =================================
# ミドルウェア設定
# =================================

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 信頼できるホスト設定（セキュリティ）
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# =================================
# 静的ファイル設定
# =================================

# アップロードファイル用の静的ファイルマウント
if os.path.exists(settings.UPLOAD_DIR):
    app.mount(
        "/uploads",
        StaticFiles(directory=settings.UPLOAD_DIR),
        name="uploads"
    )

# 静的アセット用ディレクトリ（存在する場合）
static_dir = Path("static")
if static_dir.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(static_dir)),
        name="static"
    )

# =================================
# エラーハンドラー
# =================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    HTTPエラーのカスタムハンドラー
    """
    logger.error(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    バリデーションエラーのカスタムハンドラー
    """
    logger.error(f"Validation error on {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "status_code": 422,
            "message": "Validation error",
            "details": exc.errors(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    一般的な例外のハンドラー
    """
    logger.exception(f"Unexpected error on {request.url}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "message": "Internal server error" if not settings.DEBUG else str(exc),
            "path": str(request.url.path)
        }
    )

# =================================
# APIルーター統合
# =================================

# APIルーターを追加
app.include_router(api_router)

# =================================
# ルートエンドポイント
# =================================

@app.get("/", tags=["Root"])
async def root():
    """
    ルートエンドポイント - 基本的な情報を返す
    """
    return {
        "message": f"{settings.PROJECT_NAME} API is running",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs" if settings.DEBUG else None,
        "status": "healthy"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    詳細なヘルスチェックエンドポイント
    システムの状態を確認
    """
    health_status = {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "api": "healthy",
            "database": "unknown",  # 実際にはDB接続チェック
            "redis": "unknown",     # 実際にはRedis接続チェック
        },
        "system": {
            "python_version": "3.11+",
            "fastapi_version": "0.109.0"
        }
    }

    return health_status


@app.get("/info", tags=["Info"])
async def app_info():
    """
    アプリケーション情報エンドポイント
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "api_version": settings.API_V1_STR,
        "debug": settings.DEBUG,
        "features": {
            "cors_enabled": True,
            "static_files": True,
            "file_uploads": True,
            "database": "PostgreSQL",
            "cache": "Redis",
        }
    }

# =================================
# API ルーターの登録
# =================================

# ここで個別のAPIルーターを登録
# from app.api.api_v1.api import api_router
# app.include_router(api_router, prefix=settings.API_V1_STR)

# 例: 認証関連のルーター
# from app.api.auth import router as auth_router
# app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])

# =================================
# 開発用の起動設定
# =================================

if __name__ == "__main__":
    # 開発用サーバーの起動設定
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        reload_dirs=["app"] if settings.DEBUG else None,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG,
    )