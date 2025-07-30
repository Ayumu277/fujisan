"""
ABDSシステム - Webスクレイピング関連Pydanticスキーマ
スクレイピング処理のAPI用スキーマ
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, validator


class ScrapingMode(str, Enum):
    """スクレイピングモード"""
    AUTO = "auto"          # 自動判定
    SIMPLE = "simple"      # 通常のHTTPリクエスト
    JAVASCRIPT = "javascript"  # JavaScript有効


class ScrapingRequest(BaseModel):
    """スクレイピング要求"""
    url: HttpUrl = Field(..., description="スクレイピング対象URL")
    mode: ScrapingMode = Field(default=ScrapingMode.AUTO, description="スクレイピングモード")
    extract_images: bool = Field(default=True, description="画像情報を抽出するか")
    extract_structured_data: bool = Field(default=True, description="構造化データを抽出するか")
    timeout: int = Field(default=30, description="タイムアウト秒数", ge=5, le=120)
    respect_robots: bool = Field(default=True, description="robots.txtを尊重するか")

    @validator('url')
    def validate_url(cls, v):
        url_str = str(v)

        # 除外ドメインチェック
        excluded_domains = [
            'localhost', '127.0.0.1', '0.0.0.0',
            'facebook.com', 'instagram.com', 'twitter.com', 'x.com',
            'linkedin.com', 'tiktok.com', 'youtube.com'
        ]

        for domain in excluded_domains:
            if domain in url_str.lower():
                raise ValueError(f'ドメイン {domain} へのスクレイピングは許可されていません')

        return v


class ImageInfo(BaseModel):
    """画像情報"""
    src: str = Field(..., description="画像URL")
    alt: str = Field(default="", description="alt属性")
    title: str = Field(default="", description="title属性")
    width: str = Field(default="", description="幅")
    height: str = Field(default="", description="高さ")


class StructuredData(BaseModel):
    """構造化データ"""
    type: str = Field(..., description="データタイプ（json-ld, open-graph, twitter-cardなど）")
    data: Dict[str, Any] = Field(..., description="構造化データの内容")


class ScrapedContentData(BaseModel):
    """スクレイピング結果データ"""
    url: str = Field(..., description="スクレイピング対象URL")
    title: str = Field(default="", description="ページタイトル")
    meta_description: str = Field(default="", description="メタディスクリプション")
    content_text: str = Field(default="", description="本文テキスト")
    clean_text: str = Field(default="", description="クリーニング済みテキスト")
    images: List[ImageInfo] = Field(default_factory=list, description="画像情報一覧")
    structured_data: List[StructuredData] = Field(default_factory=list, description="構造化データ一覧")
    meta_data: Dict[str, str] = Field(default_factory=dict, description="メタデータ")
    status_code: int = Field(default=0, description="HTTPステータスコード")
    content_type: str = Field(default="", description="コンテンツタイプ")
    content_length: int = Field(default=0, description="コンテンツ長")
    encoding: str = Field(default="", description="文字エンコーディング")
    language: str = Field(default="", description="言語")
    scraped_at: datetime = Field(..., description="スクレイピング実行日時")
    processing_time_ms: int = Field(default=0, description="処理時間（ミリ秒）")
    javascript_rendered: bool = Field(default=False, description="JavaScript有効でレンダリングしたか")
    robots_allowed: bool = Field(default=True, description="robots.txtで許可されているか")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")


class ScrapingResponse(BaseModel):
    """スクレイピング結果レスポンス"""
    success: bool = Field(..., description="処理成功可否")
    message: str = Field(..., description="処理結果メッセージ")
    data: Optional[ScrapedContentData] = Field(None, description="スクレイピング結果")
    execution_time_ms: Optional[int] = Field(None, description="実行時間（ミリ秒）")


class BulkScrapingRequest(BaseModel):
    """一括スクレイピング要求"""
    urls: List[HttpUrl] = Field(..., description="スクレイピング対象URL群", min_items=1, max_items=20)
    mode: ScrapingMode = Field(default=ScrapingMode.AUTO, description="スクレイピングモード")
    extract_images: bool = Field(default=True, description="画像情報を抽出するか")
    extract_structured_data: bool = Field(default=True, description="構造化データを抽出するか")
    timeout: int = Field(default=30, description="タイムアウト秒数", ge=5, le=120)
    max_concurrent: int = Field(default=3, description="最大同時実行数", ge=1, le=10)
    respect_robots: bool = Field(default=True, description="robots.txtを尊重するか")

    @validator('urls')
    def validate_urls(cls, v):
        if len(v) > 20:
            raise ValueError('一度に処理できるURLは20個までです')
        return v


class BulkScrapingResult(BaseModel):
    """一括スクレイピング個別結果"""
    url: str = Field(..., description="対象URL")
    success: bool = Field(..., description="処理成功可否")
    data: Optional[ScrapedContentData] = Field(None, description="スクレイピング結果")
    error: Optional[str] = Field(None, description="エラーメッセージ")


class BulkScrapingResponse(BaseModel):
    """一括スクレイピング結果レスポンス"""
    success: bool = Field(..., description="全体処理成功可否")
    message: str = Field(..., description="処理結果メッセージ")
    processed: int = Field(default=0, description="処理済み件数")
    failed: int = Field(default=0, description="失敗件数")
    results: List[BulkScrapingResult] = Field(default_factory=list, description="個別処理結果")
    total_execution_time_ms: int = Field(default=0, description="総実行時間（ミリ秒）")


class ContentAnalysisRequest(BaseModel):
    """コンテンツ分析要求"""
    url: HttpUrl = Field(..., description="分析対象URL")
    analyze_sentiment: bool = Field(default=False, description="感情分析を実行するか")
    extract_keywords: bool = Field(default=False, description="キーワード抽出を実行するか")
    analyze_readability: bool = Field(default=False, description="可読性分析を実行するか")
    detect_language: bool = Field(default=True, description="言語検出を実行するか")


class ContentAnalysisData(BaseModel):
    """コンテンツ分析結果データ"""
    url: str = Field(..., description="分析対象URL")
    text_length: int = Field(default=0, description="テキスト長")
    word_count: int = Field(default=0, description="単語数")
    sentence_count: int = Field(default=0, description="文数")
    paragraph_count: int = Field(default=0, description="段落数")
    detected_language: str = Field(default="", description="検出された言語")
    confidence_score: float = Field(default=0.0, description="言語検出信頼度", ge=0.0, le=1.0)
    keywords: List[str] = Field(default_factory=list, description="抽出されたキーワード")
    sentiment_score: Optional[float] = Field(None, description="感情スコア (-1.0 〜 1.0)")
    sentiment_label: Optional[str] = Field(None, description="感情ラベル（positive/negative/neutral）")
    readability_score: Optional[float] = Field(None, description="可読性スコア")
    analyzed_at: datetime = Field(..., description="分析実行日時")


class ContentAnalysisResponse(BaseModel):
    """コンテンツ分析結果レスポンス"""
    success: bool = Field(..., description="処理成功可否")
    message: str = Field(..., description="処理結果メッセージ")
    scraping_data: Optional[ScrapedContentData] = Field(None, description="スクレイピング結果")
    analysis_data: Optional[ContentAnalysisData] = Field(None, description="分析結果")
    execution_time_ms: Optional[int] = Field(None, description="実行時間（ミリ秒）")


class RobotsCheckRequest(BaseModel):
    """robots.txtチェック要求"""
    url: HttpUrl = Field(..., description="チェック対象URL")
    user_agent: str = Field(default="ABDSBot", description="User-Agent名", max_length=100)


class RobotsCheckResponse(BaseModel):
    """robots.txtチェック結果レスポンス"""
    success: bool = Field(..., description="処理成功可否")
    message: str = Field(..., description="処理結果メッセージ")
    url: str = Field(..., description="チェック対象URL")
    robots_url: str = Field(..., description="robots.txtのURL")
    allowed: bool = Field(..., description="アクセス許可されているか")
    robots_content: Optional[str] = Field(None, description="robots.txtの内容")
    crawl_delay: Optional[int] = Field(None, description="クロール間隔（秒）")
    checked_at: datetime = Field(..., description="チェック実行日時")


class ScrapingStatsResponse(BaseModel):
    """スクレイピング統計レスポンス"""
    success: bool = Field(..., description="処理成功可否")
    message: str = Field(..., description="処理結果メッセージ")
    data: Dict[str, Any] = Field(default_factory=dict, description="統計データ")