"""
ABDSシステム - API ルーター
全てのAPIエンドポイントを統合
"""

from fastapi import APIRouter

# 安全なインポート
from app.api.endpoints import ai_analysis

# 条件付きインポート
try:
    from app.api.endpoints import images
except ImportError:
    images = None

try:
    from app.api.endpoints import search
except ImportError:
    search = None

try:
    from app.api.endpoints import domains
except ImportError:
    domains = None

try:
    from app.api.endpoints import scraping
except ImportError:
    scraping = None

# メインAPIルーター
api_router = APIRouter(prefix="/api/v1")

# AI分析エンドポイント（メイン機能）
api_router.include_router(
    ai_analysis.router,
    prefix="/ai-analysis",
    tags=["ai-analysis"],
    responses={404: {"description": "Not found"}}
)

# 条件付きルーター追加
if images:
    api_router.include_router(
        images.router,
        prefix="/images",
        tags=["images"],
        responses={404: {"description": "Not found"}}
    )

if search:
    api_router.include_router(
        search.router,
        prefix="/search",
        tags=["search"],
        responses={404: {"description": "Not found"}}
    )

if domains:
    api_router.include_router(
        domains.router,
        prefix="/domains",
        tags=["domains"],
        responses={404: {"description": "Not found"}}
    )

if scraping:
    api_router.include_router(
        scraping.router,
        prefix="/scraping",
        tags=["scraping"],
        responses={404: {"description": "Not found"}}
    )


@api_router.get("/health")
async def api_health():
    """API健康状態チェック"""
    available_endpoints = {
        "ai_analysis": "/api/v1/ai-analysis"
    }

    if images:
        available_endpoints["images"] = "/api/v1/images"
    if search:
        available_endpoints["search"] = "/api/v1/search"
    if domains:
        available_endpoints["domains"] = "/api/v1/domains"
    if scraping:
        available_endpoints["scraping"] = "/api/v1/scraping"

    return {
        "status": "healthy",
        "message": "ABDS API is running",
        "primary_feature": "AI分析機能が利用可能です",
        "endpoints": available_endpoints
    }
