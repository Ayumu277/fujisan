"""
ABDSシステム - AI分析用スキーマ
Gemini APIを使用したコンテンツ分析のリクエスト/レスポンススキーマ
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator


class AnalysisLevel(str, Enum):
    """分析レベル"""
    BASIC = "basic"
    COMPREHENSIVE = "comprehensive"
    COPYRIGHT_FOCUSED = "copyright_focused"
    ABUSE_FOCUSED = "abuse_focused"


class AnalysisType(str, Enum):
    """分析タイプ"""
    ABUSE = "abuse"
    COPYRIGHT = "copyright"
    COMMERCIAL = "commercial"
    REPOST = "repost"
    MODIFICATION = "modification"


class ThreatLevel(str, Enum):
    """脅威レベル"""
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"
    NONE = "なし"


class RiskLevel(str, Enum):
    """リスクレベル"""
    HIGH_RISK = "高リスク"
    MEDIUM_RISK = "中リスク"
    LOW_RISK = "低リスク"
    SAFE = "安全"


class CopyrightProbability(str, Enum):
    """著作権侵害確率"""
    HIGH_PROBABILITY = "高確率"
    MEDIUM_PROBABILITY = "中確率"
    LOW_PROBABILITY = "低確率"
    NO_PROBLEM = "問題なし"


class CommercialUseStatus(str, Enum):
    """商用利用状況"""
    CLEAR_COMMERCIAL = "明確な商用利用"
    SUSPECTED_COMMERCIAL = "疑わしい商用利用"
    NON_COMMERCIAL = "非商用利用"
    UNDETERMINED = "判定不可"


class RepostStatus(str, Enum):
    """転載状況"""
    CLEAR_UNAUTHORIZED = "明確な無断転載"
    SUSPECTED_REPOST = "疑わしい転載"
    PROPER_CITATION = "適切な引用"
    ORIGINAL = "オリジナル"


class ModificationLevel(str, Enum):
    """改変レベル"""
    MAJOR_MODIFICATION = "大幅改変"
    PARTIAL_MODIFICATION = "部分改変"
    MINOR_MODIFICATION = "軽微改変"
    NO_MODIFICATION = "無改変"


# =================================
# リクエストスキーマ
# =================================

class ImageContextData(BaseModel):
    """画像コンテキストデータ"""
    filename: Optional[str] = None
    upload_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    similar_images: Optional[List[Dict[str, Any]]] = None
    search_results: Optional[List[Dict[str, Any]]] = None


class AIAnalysisRequest(BaseModel):
    """AI分析リクエスト"""
    html_content: str = Field(..., description="分析対象のHTMLコンテンツ", max_length=50000)
    image_context: ImageContextData = Field(..., description="画像コンテキスト情報")
    analysis_level: AnalysisLevel = Field(
        default=AnalysisLevel.COMPREHENSIVE,
        description="分析レベル"
    )
    focus_areas: Optional[List[AnalysisType]] = Field(
        default=None,
        description="特定分析領域にフォーカス"
    )

    @validator('html_content')
    def validate_html_content(cls, v):
        if not v.strip():
            raise ValueError("HTMLコンテンツは空にできません")
        return v


class FocusedAnalysisRequest(BaseModel):
    """特化分析リクエスト"""
    analysis_type: AnalysisType = Field(..., description="分析タイプ")
    html_content: str = Field(..., description="分析対象のHTMLコンテンツ", max_length=50000)
    image_context: ImageContextData = Field(..., description="画像コンテキスト情報")

    @validator('html_content')
    def validate_html_content(cls, v):
        if not v.strip():
            raise ValueError("HTMLコンテンツは空にできません")
        return v


class BatchAnalysisRequest(BaseModel):
    """バッチ分析リクエスト"""
    analyses: List[AIAnalysisRequest] = Field(
        ...,
        description="分析リクエストリスト",
        min_items=1,
        max_items=10
    )
    max_concurrent: int = Field(
        default=3,
        description="最大同時実行数",
        ge=1,
        le=5
    )


# =================================
# レスポンススキーマ - 分析結果詳細
# =================================

class AnalysisEvidence(BaseModel):
    """分析根拠"""
    evidence: List[str] = Field(default_factory=list, description="具体的な根拠")
    details: str = Field(default="", description="詳細説明")
    confidence: float = Field(default=0.0, description="信頼度", ge=0.0, le=1.0)


class AbuseDetectionResult(AnalysisEvidence):
    """悪用検出結果"""
    risk_level: RiskLevel = Field(..., description="リスクレベル")


class CopyrightInfringementResult(AnalysisEvidence):
    """著作権侵害結果"""
    probability: CopyrightProbability = Field(..., description="侵害確率")


class CommercialUseResult(AnalysisEvidence):
    """商用利用結果"""
    status: CommercialUseStatus = Field(..., description="商用利用状況")


class UnauthorizedRepostResult(AnalysisEvidence):
    """無断転載結果"""
    status: RepostStatus = Field(..., description="転載状況")


class ContentModificationResult(AnalysisEvidence):
    """コンテンツ改変結果"""
    level: ModificationLevel = Field(..., description="改変レベル")


class OverallAssessment(BaseModel):
    """総合評価"""
    threat_level: ThreatLevel = Field(..., description="脅威レベル")
    risk_score: int = Field(..., description="リスクスコア", ge=0, le=100)
    summary: str = Field(..., description="分析サマリー")
    recommendations: List[str] = Field(default_factory=list, description="推奨アクション")


class AnalysisMetadata(BaseModel):
    """分析メタデータ"""
    analyzed_at: datetime = Field(..., description="分析実行日時")
    analysis_version: str = Field(default="1.0", description="分析バージョン")
    confidence_score: float = Field(default=0.0, description="全体信頼度", ge=0.0, le=1.0)
    processing_time_ms: int = Field(default=0, description="処理時間（ミリ秒）")


# =================================
# レスポンススキーマ - メイン
# =================================

class AIAnalysisResponse(BaseModel):
    """AI分析レスポンス"""
    abuse_detection: AbuseDetectionResult = Field(..., description="悪用検出結果")
    copyright_infringement: CopyrightInfringementResult = Field(..., description="著作権侵害結果")
    commercial_use: CommercialUseResult = Field(..., description="商用利用結果")
    unauthorized_repost: UnauthorizedRepostResult = Field(..., description="無断転載結果")
    content_modification: ContentModificationResult = Field(..., description="コンテンツ改変結果")
    overall_assessment: OverallAssessment = Field(..., description="総合評価")
    metadata: AnalysisMetadata = Field(..., description="分析メタデータ")
    raw_response: Optional[str] = Field(default=None, description="生レスポンス")


class AIAnalysisError(BaseModel):
    """AI分析エラー"""
    error_code: str = Field(..., description="エラーコード")
    error_message: str = Field(..., description="エラーメッセージ")
    details: Optional[str] = Field(default=None, description="詳細情報")
    analyzed_at: datetime = Field(..., description="エラー発生日時")
    processing_time_ms: int = Field(default=0, description="処理時間（ミリ秒）")


class AIAnalysisSummary(BaseModel):
    """AI分析サマリー"""
    status: str = Field(..., description="分析状況")
    overall_risk_score: int = Field(..., description="総合リスクスコア", ge=0, le=100)
    threat_level: ThreatLevel = Field(..., description="脅威レベル")
    key_findings: Dict[str, Optional[str]] = Field(..., description="主要な発見")
    recommendations: List[str] = Field(default_factory=list, description="推奨事項")
    processing_time_ms: int = Field(default=0, description="処理時間（ミリ秒）")
    analyzed_at: datetime = Field(..., description="分析日時")


class BatchAnalysisResponse(BaseModel):
    """バッチ分析レスポンス"""
    results: List[AIAnalysisResponse] = Field(..., description="分析結果リスト")
    summary: Dict[str, Any] = Field(..., description="バッチサマリー")
    total_processing_time_ms: int = Field(..., description="総処理時間（ミリ秒）")
    successful_analyses: int = Field(..., description="成功した分析数")
    failed_analyses: int = Field(..., description="失敗した分析数")


# =================================
# ステータス・統計スキーマ
# =================================

class AIAnalysisStats(BaseModel):
    """AI分析統計"""
    total_analyses: int = Field(..., description="総分析数")
    analyses_today: int = Field(..., description="今日の分析数")
    average_processing_time_ms: float = Field(..., description="平均処理時間（ミリ秒）")
    success_rate: float = Field(..., description="成功率", ge=0.0, le=1.0)
    threat_distribution: Dict[str, int] = Field(..., description="脅威レベル分布")
    most_common_risks: List[str] = Field(..., description="最も一般的なリスク")


class AIAnalysisCapabilities(BaseModel):
    """AI分析機能"""
    available: bool = Field(..., description="利用可能性")
    model_name: str = Field(..., description="使用モデル名")
    supported_analysis_types: List[AnalysisType] = Field(..., description="サポート分析タイプ")
    supported_levels: List[AnalysisLevel] = Field(..., description="サポート分析レベル")
    rate_limit_per_minute: int = Field(..., description="分間リクエスト制限")
    max_content_length: int = Field(..., description="最大コンテンツ長")


# =================================
# 設定・管理スキーマ
# =================================

class AIAnalysisConfig(BaseModel):
    """AI分析設定"""
    enabled: bool = Field(..., description="有効状態")
    model_name: str = Field(..., description="使用モデル")
    backup_model: str = Field(..., description="バックアップモデル")
    max_requests_per_minute: int = Field(..., description="分間最大リクエスト数")
    max_tokens_per_request: int = Field(..., description="リクエスト当たり最大トークン数")
    default_analysis_level: AnalysisLevel = Field(..., description="デフォルト分析レベル")


class AIAnalysisConfigUpdate(BaseModel):
    """AI分析設定更新"""
    enabled: Optional[bool] = None
    model_name: Optional[str] = None
    backup_model: Optional[str] = None
    max_requests_per_minute: Optional[int] = Field(None, ge=1, le=100)
    max_tokens_per_request: Optional[int] = Field(None, ge=1000, le=100000)
    default_analysis_level: Optional[AnalysisLevel] = None