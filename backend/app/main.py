"""
ABDSシステム - FastAPI メインアプリケーション
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(
    title="ABDS System API",
    description="ABDSシステムのAPIサーバー",
    version="1.0.0",
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """
    ヘルスチェックエンドポイント
    """
    return {"message": "ABDS System API is running"}

@app.get("/health")
async def health_check():
    """
    詳細なヘルスチェック
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "system": "ABDS"
    }

# API ルーターの追加
# from app.api.endpoints import router
# app.include_router(router, prefix="/api/v1")