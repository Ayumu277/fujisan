"""
ABDSシステム - 検索関連スキーマ
画像検索APIのリクエスト・レスポンス用Pydanticスキーマ
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator


class SearchStatus(str, Enum):
    """検索ステータス"""
    PENDING = "pending"          # 検索待ち
    IN_PROGRESS = "in_progress"  # 検索中
    COMPLETED = "completed"      # 検索完了
    FAILED = "failed"           # 検索失敗


class SearchServiceType(str, Enum):
    """検索サービスタイプ"""
    GOOGLE = "google"
    SERPAPI = "serpapi"


class SearchResultItem(BaseModel):
    """個別の検索結果アイテム"""
    title: str = Field(..., description="画像タイトル")
    url: str = Field(..., description="画像URL")
    thumbnail_url: str = Field(..., description="サムネイルURL")
    source_domain: str = Field(..., description="ソースドメイン")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="類似度スコア")
    width: Optional[int] = Field(None, description="画像幅")
    height: Optional[int] = Field(None, description="画像高さ")
    file_size: Optional[str] = Field(None, description="ファイルサイズ")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SearchStartRequest(BaseModel):
    """検索開始リクエスト"""
    service_type: SearchServiceType = Field(SearchServiceType.SERPAPI, description="検索サービスタイプ")
    max_results: int = Field(10, ge=1, le=100, description="最大結果数")
    
    @validator('max_results')
    def validate_max_results(cls, v):
        if v > 100:
            raise ValueError('最大結果数は100以下である必要があります')
        return v


class SearchStartResponse(BaseModel):
    """検索開始レスポンス"""
    search_id: UUID = Field(..., description="検索ID")
    image_id: UUID = Field(..., description="画像ID")
    status: SearchStatus = Field(..., description="検索ステータス")
    service_type: SearchServiceType = Field(..., description="使用する検索サービス")
    max_results: int = Field(..., description="最大結果数")
    started_at: datetime = Field(..., description="検索開始時刻")
    estimated_completion: Optional[datetime] = Field(None, description="完了予定時刻")
    
    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class SearchStatusResponse(BaseModel):
    """検索ステータスレスポンス"""
    search_id: UUID = Field(..., description="検索ID")
    image_id: UUID = Field(..., description="画像ID")
    status: SearchStatus = Field(..., description="検索ステータス")
    service_type: SearchServiceType = Field(..., description="検索サービスタイプ")
    progress: float = Field(..., ge=0.0, le=1.0, description="進捗率")
    started_at: datetime = Field(..., description="検索開始時刻")
    completed_at: Optional[datetime] = Field(None, description="検索完了時刻")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")
    results_count: Optional[int] = Field(None, description="見つかった結果数")
    
    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class SearchResultsResponse(BaseModel):
    """検索結果レスポンス"""
    image_id: UUID = Field(..., description="画像ID")
    total_results: int = Field(..., description="総結果数")
    search_completed_at: Optional[datetime] = Field(None, description="検索完了時刻")
    service_used: SearchServiceType = Field(..., description="使用した検索サービス")
    results: List[SearchResultItem] = Field(..., description="検索結果一覧")
    
    # 統計情報
    stats: Dict[str, Any] = Field(default_factory=dict, description="検索統計")
    
    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class SearchErrorResponse(BaseModel):
    """検索エラーレスポンス"""
    error: bool = Field(True, description="エラーフラグ")
    error_type: str = Field(..., description="エラータイプ")
    message: str = Field(..., description="エラーメッセージ")
    details: Optional[Dict[str, Any]] = Field(None, description="エラー詳細")
    retry_after: Optional[int] = Field(None, description="再試行可能時間（秒）")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BulkSearchRequest(BaseModel):
    """一括検索リクエスト"""
    image_ids: List[UUID] = Field(..., min_items=1, max_items=10, description="画像IDリスト")
    service_type: SearchServiceType = Field(SearchServiceType.SERPAPI, description="検索サービスタイプ")
    max_results_per_image: int = Field(10, ge=1, le=50, description="画像あたりの最大結果数")
    
    @validator('image_ids')
    def validate_image_ids(cls, v):
        if len(set(v)) != len(v):
            raise ValueError('重複した画像IDが含まれています')
        return v


class BulkSearchResponse(BaseModel):
    """一括検索レスポンス"""
    batch_id: UUID = Field(..., description="バッチID")
    search_ids: List[UUID] = Field(..., description="個別検索IDリスト")
    total_images: int = Field(..., description="総画像数")
    status: SearchStatus = Field(..., description="バッチステータス")
    started_at: datetime = Field(..., description="開始時刻")
    
    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class SearchAnalytics(BaseModel):
    """検索分析データ"""
    total_searches: int = Field(..., description="総検索数")
    successful_searches: int = Field(..., description="成功した検索数")
    failed_searches: int = Field(..., description="失敗した検索数")
    average_results_per_search: float = Field(..., description="検索あたりの平均結果数")
    most_common_domains: List[Dict[str, Any]] = Field(..., description="よく見つかるドメイン")
    search_performance: Dict[str, float] = Field(..., description="検索性能統計")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RateLimitInfo(BaseModel):
    """レート制限情報"""
    service: str = Field(..., description="サービス名")
    limit: int = Field(..., description="制限回数")
    remaining: int = Field(..., description="残り回数")
    reset_time: Optional[datetime] = Field(None, description="制限リセット時刻")
    window_seconds: int = Field(..., description="時間窓（秒）")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# =================================
# データベースモデル用スキーマ
# =================================

class SearchJobCreate(BaseModel):
    """検索ジョブ作成用スキーマ"""
    image_id: UUID
    service_type: SearchServiceType
    max_results: int = 10
    priority: int = 0  # 優先度（高い数値ほど優先）


class SearchJobUpdate(BaseModel):
    """検索ジョブ更新用スキーマ"""
    status: Optional[SearchStatus] = None
    progress: Optional[float] = None
    error_message: Optional[str] = None
    results_count: Optional[int] = None
    completed_at: Optional[datetime] = None


class SearchJobRead(BaseModel):
    """検索ジョブ読み取り用スキーマ"""
    id: UUID
    image_id: UUID
    service_type: SearchServiceType
    status: SearchStatus
    max_results: int
    progress: float
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    results_count: Optional[int]
    
    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
