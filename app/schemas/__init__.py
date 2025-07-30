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
    # Domain schemas
    "DomainCheckRequest",
    "DomainCheckResponse",
    "DomainAnalysisResult",
    "WhoisInfo",
    "SSLInfo",
    "WhitelistDomainCreate",
    "WhitelistDomainRead",
    "WhitelistDomainResponse",
    "WhitelistDomainsResponse",
    "DomainDeleteResponse",
    "DomainStatsResponse",
    "BulkDomainRequest",
    "BulkDomainResponse",
    "DomainSearchRequest",
    "DomainSearchResponse",
]
