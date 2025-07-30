"""
ABDSシステム - Pydanticスキーマ
APIリクエスト・レスポンスの検証用スキーマ
"""

from app.schemas.image import (
    ImageUploadResponse,
    ImageStatusEnum,
    ImageCreate,
    ImageRead,
)

from app.schemas.search import (
    SearchStatus,
    SearchServiceType,
    SearchResultItem,
    SearchStartRequest,
    SearchStartResponse,
    SearchStatusResponse,
    SearchResultsResponse,
    SearchErrorResponse,
    RateLimitInfo,
)

# 条件付きインポート
try:
    from app.schemas.domain import (
        DomainCheckRequest,
        DomainCheckResponse,
        DomainAnalysisResult,
        WhoisInfo,
        SSLInfo,
        WhitelistDomainCreate,
        WhitelistDomainRead,
        WhitelistDomainResponse,
        WhitelistDomainsResponse,
        DomainDeleteResponse,
        DomainStatsResponse,
        BulkDomainRequest,
        BulkDomainResponse,
        DomainSearchRequest,
        DomainSearchResponse,
    )
except ImportError:
    pass

try:
    from app.schemas.scraping import (
        ScrapingRequest,
        ScrapingResponse,
        ScrapedContentData,
        BulkScrapingRequest,
        BulkScrapingResponse,
        BulkScrapingResult,
        ContentAnalysisRequest,
        ContentAnalysisResponse,
        ContentAnalysisData,
        RobotsCheckRequest,
        RobotsCheckResponse,
        ScrapingStatsResponse,
        ImageInfo,
        StructuredData,
        ScrapingMode
    )
except ImportError:
    pass

# AI分析スキーマ（メイン機能）
from app.schemas.ai_analysis import (
    AIAnalysisRequest,
    FocusedAnalysisRequest,
    BatchAnalysisRequest,
    AIAnalysisResponse,
    AIAnalysisError,
    AIAnalysisSummary,
    BatchAnalysisResponse,
    AIAnalysisStats,
    AIAnalysisCapabilities,
    AIAnalysisConfig,
    AIAnalysisConfigUpdate,
    AnalysisLevel,
    AnalysisType,
    ThreatLevel,
    RiskLevel,
    CopyrightProbability,
    CommercialUseStatus,
    RepostStatus,
    ModificationLevel,
    ImageContextData,
    AbuseDetectionResult,
    CopyrightInfringementResult,
    CommercialUseResult,
    UnauthorizedRepostResult,
    ContentModificationResult,
    OverallAssessment,
    AnalysisMetadata
)

__all__ = [
    # Image schemas
    "ImageUploadResponse",
    "ImageStatusEnum",
    "ImageCreate",
    "ImageRead",
    # Search schemas
    "SearchStatus",
    "SearchServiceType",
    "SearchResultItem",
    "SearchStartRequest",
    "SearchStartResponse",
    "SearchStatusResponse",
    "SearchResultsResponse",
    "SearchErrorResponse",
    "RateLimitInfo",
    # Domain schemas temporarily disabled
    # Scraping schemas
    "ScrapingRequest",
    "ScrapingResponse",
    "ScrapedContentData",
    "BulkScrapingRequest",
    "BulkScrapingResponse",
    "ContentAnalysisRequest",
    "ContentAnalysisResponse",
    "RobotsCheckRequest",
    "RobotsCheckResponse",
    "ScrapingStatsResponse",
    "ScrapingMode",
    "ImageInfo",
    "StructuredData",
]