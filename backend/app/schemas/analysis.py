"""
ABDSシステム - 脅威度分析スキーマ
脅威度スコアリングと評価結果のPydanticスキーマ定義
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator, model_validator


class ThreatLevel(str, Enum):
    """脅威レベル"""
    SAFE = "SAFE"           # 安全（スコア: 0-39）
    LOW = "LOW"             # 低リスク（スコア: 40-59）
    MEDIUM = "MEDIUM"       # 中リスク（スコア: 60-79）
    HIGH = "HIGH"           # 高リスク（スコア: 80-100）
    UNKNOWN = "UNKNOWN"     # 不明（評価エラー時）


class ComponentScore(BaseModel):
    """スコア構成要素"""
    score: float = Field(..., ge=0, le=100, description="個別スコア（0-100）")
    weight: float = Field(..., ge=0, le=1, description="重み係数（0-1）")
    contribution: float = Field(..., ge=0, le=100, description="総合スコアへの寄与度")

    @validator('contribution')
    def validate_contribution(cls, v, values):
        """寄与度の検証"""
        if 'score' in values and 'weight' in values:
            expected = values['score'] * values['weight']
            if abs(v - expected) > 0.01:  # 小数点誤差許容
                raise ValueError(f"Contribution {v} doesn't match score * weight = {expected}")
        return v


class ThreatComponents(BaseModel):
    """脅威評価構成要素"""
    domain_trust: ComponentScore = Field(..., description="ドメイン信頼度（40%）")
    ai_analysis: ComponentScore = Field(..., description="AI分析結果（40%）")
    other_factors: ComponentScore = Field(..., description="その他要因（20%）")

    @model_validator(mode='after')
    def validate_weights_sum(self):
        """重みの合計が100%になることを検証"""
        total_weight = (
            self.domain_trust.weight +
            self.ai_analysis.weight +
            self.other_factors.weight
        )
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Total weight must be 1.0, got {total_weight}")
        return self


class ScoreMetadata(BaseModel):
    """スコア計算メタデータ"""
    calculation_version: str = Field(default="1.0", description="計算アルゴリズムバージョン")
    data_completeness: float = Field(..., ge=0, le=1, description="データ完全性（0-1）")
    reliability_score: float = Field(..., ge=0, le=1, description="信頼性スコア（0-1）")
    calculation_time_ms: int = Field(..., ge=0, description="計算時間（ミリ秒）")
    factors_analyzed: int = Field(..., ge=0, description="分析した要因の数")


class ThreatAssessment(BaseModel):
    """脅威度評価結果"""

    # 基本スコア情報
    overall_score: float = Field(..., ge=0, le=100, description="総合脅威スコア（0-100、100が最高リスク）")
    threat_level: ThreatLevel = Field(..., description="脅威レベル")
    confidence: float = Field(..., ge=0, le=1, description="評価の信頼度（0-1）")

    # 構成要素詳細
    components: ThreatComponents = Field(..., description="スコア構成要素")

    # リスク分析
    risk_factors: List[str] = Field(default_factory=list, description="特定されたリスク要因")
    recommendations: List[str] = Field(default_factory=list, description="推奨アクション")

    # メタデータ
    metadata: Optional[ScoreMetadata] = Field(None, description="計算メタデータ")
    calculated_at: datetime = Field(..., description="計算実行日時")
    error_message: Optional[str] = Field(None, description="エラーメッセージ（エラー時のみ）")

    @validator('overall_score')
    def validate_overall_score(cls, v):
        """総合スコアの正規化"""
        return max(0.0, min(100.0, round(v, 2)))

    @validator('threat_level')
    def validate_threat_level_consistency(cls, v, values):
        """脅威レベルとスコアの一貫性チェック"""
        if 'overall_score' in values:
            score = values['overall_score']
            expected_level = cls._score_to_threat_level(score)
            if v != expected_level and v != ThreatLevel.UNKNOWN:
                raise ValueError(f"Threat level {v} inconsistent with score {score} (expected {expected_level})")
        return v

    @staticmethod
    def _score_to_threat_level(score: float) -> ThreatLevel:
        """スコアから脅威レベルを決定"""
        if score >= 80:
            return ThreatLevel.HIGH
        elif score >= 60:
            return ThreatLevel.MEDIUM
        elif score >= 40:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.SAFE


class ThreatAssessmentRequest(BaseModel):
    """脅威度評価リクエスト"""
    domain_data: Dict[str, Any] = Field(..., description="ドメイン関連データ")
    ai_analysis: Dict[str, Any] = Field(..., description="AI分析結果")
    search_data: Dict[str, Any] = Field(..., description="検索関連データ")
    content_data: Dict[str, Any] = Field(..., description="コンテンツデータ")

    # オプション設定
    include_metadata: bool = Field(default=True, description="メタデータを含めるか")
    detailed_breakdown: bool = Field(default=True, description="詳細な内訳を含めるか")


class ThreatAssessmentResponse(BaseModel):
    """脅威度評価レスポンス"""
    success: bool = Field(..., description="評価成功フラグ")
    assessment: Optional[ThreatAssessment] = Field(None, description="脅威度評価結果")
    error: Optional[str] = Field(None, description="エラーメッセージ")
    request_id: Optional[str] = Field(None, description="リクエストID")


class BatchThreatAssessmentRequest(BaseModel):
    """バッチ脅威度評価リクエスト"""
    assessments: List[ThreatAssessmentRequest] = Field(..., max_items=10, description="評価リクエストリスト（最大10件）")
    parallel_processing: bool = Field(default=True, description="並列処理を使用するか")


class BatchThreatAssessmentResponse(BaseModel):
    """バッチ脅威度評価レスポンス"""
    success: bool = Field(..., description="バッチ処理成功フラグ")
    total_count: int = Field(..., description="総件数")
    success_count: int = Field(..., description="成功件数")
    failed_count: int = Field(..., description="失敗件数")
    results: List[ThreatAssessmentResponse] = Field(..., description="個別評価結果")
    processing_time_ms: int = Field(..., description="バッチ処理時間（ミリ秒）")


class ThreatScoreStatistics(BaseModel):
    """脅威スコア統計情報"""
    total_assessments: int = Field(..., description="総評価件数")
    score_distribution: Dict[ThreatLevel, int] = Field(..., description="脅威レベル別分布")
    average_score: float = Field(..., ge=0, le=100, description="平均スコア")
    median_score: float = Field(..., ge=0, le=100, description="中央値スコア")
    score_trend: Dict[str, float] = Field(default_factory=dict, description="スコア傾向（期間別）")
    high_risk_domains: List[str] = Field(default_factory=list, description="高リスクドメインリスト")


class ThreatScoreConfig(BaseModel):
    """脅威スコア設定"""
    weights: Dict[str, float] = Field(..., description="重み設定")
    domain_weights: Dict[str, float] = Field(..., description="ドメイン要因重み")
    ai_weights: Dict[str, float] = Field(..., description="AI分析要因重み")
    other_weights: Dict[str, float] = Field(..., description="その他要因重み")
    threshold_settings: Dict[ThreatLevel, Dict[str, float]] = Field(..., description="閾値設定")

    @validator('weights')
    def validate_main_weights(cls, v):
        """メイン重みの合計が1.0であることを検証"""
        total = sum(v.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Main weights must sum to 1.0, got {total}")
        return v


class ThreatScoreCalibration(BaseModel):
    """脅威スコア較正データ"""
    calibration_date: datetime = Field(..., description="較正実行日")
    sample_size: int = Field(..., description="較正サンプル数")
    accuracy_metrics: Dict[str, float] = Field(..., description="精度指標")
    recommended_adjustments: Dict[str, float] = Field(default_factory=dict, description="推奨調整値")
    validation_results: Dict[str, Any] = Field(default_factory=dict, description="検証結果")


class ThreatAssessmentHistory(BaseModel):
    """脅威評価履歴"""
    assessment_id: str = Field(..., description="評価ID")
    target_url: str = Field(..., description="評価対象URL")
    assessment_date: datetime = Field(..., description="評価日時")
    threat_score: float = Field(..., ge=0, le=100, description="脅威スコア")
    threat_level: ThreatLevel = Field(..., description="脅威レベル")
    key_risk_factors: List[str] = Field(default_factory=list, description="主要リスク要因")
    action_taken: Optional[str] = Field(None, description="実施されたアクション")


class ThreatAssessmentSummary(BaseModel):
    """脅威評価サマリー"""
    summary_period: str = Field(..., description="サマリー期間")
    total_assessments: int = Field(..., description="総評価数")
    threat_level_counts: Dict[ThreatLevel, int] = Field(..., description="脅威レベル別件数")
    average_processing_time: float = Field(..., description="平均処理時間（ミリ秒）")
    top_risk_factors: List[Dict[str, Union[str, int]]] = Field(..., description="上位リスク要因")
    improvement_suggestions: List[str] = Field(default_factory=list, description="改善提案")


# スキーマの設定
class Config:
    """Pydantic設定"""
    json_encoders = {
        datetime: lambda v: v.isoformat()
    }
    schema_extra = {
        "example": {
            "overall_score": 75.5,
            "threat_level": "MEDIUM",
            "confidence": 0.85,
            "components": {
                "domain_trust": {
                    "score": 60.0,
                    "weight": 0.4,
                    "contribution": 24.0
                },
                "ai_analysis": {
                    "score": 80.0,
                    "weight": 0.4,
                    "contribution": 32.0
                },
                "other_factors": {
                    "score": 95.0,
                    "weight": 0.2,
                    "contribution": 19.0
                }
            },
            "risk_factors": [
                "新規ドメイン（30日以内）",
                "著作権侵害の可能性",
                "検索順位が低い"
            ],
            "recommendations": [
                "追加の確認を推奨します",
                "ドメイン所有者に連絡を検討してください",
                "継続的な監視を設定してください"
            ],
            "calculated_at": "2024-01-15T10:30:00Z"
        }
    }


# エクスポート用
__all__ = [
    "ThreatLevel",
    "ComponentScore",
    "ThreatComponents",
    "ScoreMetadata",
    "ThreatAssessment",
    "ThreatAssessmentRequest",
    "ThreatAssessmentResponse",
    "BatchThreatAssessmentRequest",
    "BatchThreatAssessmentResponse",
    "ThreatScoreStatistics",
    "ThreatScoreConfig",
    "ThreatScoreCalibration",
    "ThreatAssessmentHistory",
    "ThreatAssessmentSummary"
]