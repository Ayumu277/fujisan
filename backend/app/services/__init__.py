"""
ABDSシステム - サービス層
ビジネスロジックとサードパーティAPI統合
"""

# 条件付きインポート
try:
    from app.services.image_search import (
        ImageSearchService,
        GoogleImageSearchService,
        SerpAPISearchService,
        SearchResult,
    )
    IMAGE_SEARCH_AVAILABLE = True
except ImportError:
    IMAGE_SEARCH_AVAILABLE = False

try:
    from app.services.threat_scorer import ThreatScorer, get_threat_scorer
    THREAT_SCORING_AVAILABLE = True
except ImportError:
    THREAT_SCORING_AVAILABLE = False

# 条件付きエクスポート
__all__ = []

if IMAGE_SEARCH_AVAILABLE:
    __all__.extend([
        "ImageSearchService",
        "GoogleImageSearchService",
        "SerpAPISearchService",
        "SearchResult",
    ])

if THREAT_SCORING_AVAILABLE:
    __all__.extend([
        "ThreatScorer",
        "get_threat_scorer",
    ])
