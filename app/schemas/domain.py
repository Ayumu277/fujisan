"""
ABDSシステム - ドメイン関連Pydanticスキーマ
ドメイン判定・ホワイトリスト管理のAPI用スキーマ
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, validator

from app.models.enums import ThreatLevel


class DomainCheckRequest(BaseModel):
    """ドメインチェック要求"""
    url: str = Field(..., description="チェック対象のURL", min_length=1, max_length=2048)
    include_whois: bool = Field(default=True, description="Whois情報を含めるか")
    include_ssl: bool = Field(default=True, description="SSL証明書情報を含めるか")

    @validator('url')
    def validate_url(cls, v):
        if not v or v.isspace():
            raise ValueError('URLは必須です')

        # 基本的なURL形式チェック
        if not any(v.startswith(prefix) for prefix in ['http://', 'https://', 'www.', 'ftp://']):
            if '.' not in v:
                raise ValueError('有効なURL形式ではありません')

        return v.strip()


class WhoisInfo(BaseModel):
    """Whois情報"""
    creation_date: Optional[str] = Field(None, description="ドメイン作成日")
    expiration_date: Optional[str] = Field(None, description="ドメイン有効期限")
    registrar: Optional[str] = Field(None, description="レジストラ")
    status: Optional[List[str]] = Field(None, description="ドメインステータス")
    name_servers: Optional[List[str]] = Field(None, description="ネームサーバー")
    org: Optional[str] = Field(None, description="組織名")
    country: Optional[str] = Field(None, description="国")


class SSLInfo(BaseModel):
    """SSL証明書情報"""
    ssl_available: bool = Field(..., description="SSL証明書が利用可能か")
    subject: Optional[Dict] = Field(None, description="証明書のサブジェクト")
    issuer: Optional[Dict] = Field(None, description="証明書の発行者")
    not_before: Optional[str] = Field(None, description="有効期間開始日")
    not_after: Optional[str] = Field(None, description="有効期間終了日")
    serial_number: Optional[str] = Field(None, description="シリアル番号")
    version: Optional[int] = Field(None, description="証明書バージョン")
    error: Optional[str] = Field(None, description="SSL取得エラー")
    details: Optional[str] = Field(None, description="詳細情報")


class DomainAnalysisResult(BaseModel):
    """ドメイン分析結果"""
    domain: str = Field(..., description="メインドメイン")
    subdomain: str = Field(default="", description="サブドメイン")
    tld: str = Field(..., description="トップレベルドメイン")
    is_whitelisted: bool = Field(..., description="ホワイトリストに登録済みか")
    threat_level: ThreatLevel = Field(..., description="脅威レベル")
    confidence_score: float = Field(..., description="信頼度スコア (0.0-1.0)", ge=0.0, le=1.0)
    analysis_timestamp: datetime = Field(..., description="分析実行日時")
    whois_data: Optional[WhoisInfo] = Field(None, description="Whois情報")
    ssl_info: Optional[SSLInfo] = Field(None, description="SSL証明書情報")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")


class DomainCheckResponse(BaseModel):
    """ドメインチェック結果レスポンス"""
    success: bool = Field(..., description="処理成功可否")
    message: str = Field(..., description="処理結果メッセージ")
    data: Optional[DomainAnalysisResult] = Field(None, description="分析結果データ")
    execution_time_ms: Optional[int] = Field(None, description="実行時間（ミリ秒）")


class WhitelistDomainCreate(BaseModel):
    """ホワイトリストドメイン作成"""
    domain: str = Field(..., description="追加するドメイン", min_length=1, max_length=253)
    added_by: str = Field(..., description="追加者", min_length=1, max_length=100)
    note: Optional[str] = Field(None, description="備考", max_length=500)

    @validator('domain')
    def validate_domain(cls, v):
        if not v or v.isspace():
            raise ValueError('ドメインは必須です')

        domain = v.strip().lower()

        # 基本的なドメイン形式チェック
        if not domain.replace('-', '').replace('.', '').isalnum():
            raise ValueError('ドメインに無効な文字が含まれています')

        if '..' in domain or domain.startswith('.') or domain.endswith('.'):
            raise ValueError('ドメイン形式が正しくありません')

        return domain


class WhitelistDomainRead(BaseModel):
    """ホワイトリストドメイン読み取り"""
    id: UUID = Field(..., description="ドメインID")
    domain: str = Field(..., description="ドメイン名")
    added_by: str = Field(..., description="追加者")
    added_at: datetime = Field(..., description="追加日時")

    class Config:
        from_attributes = True


class WhitelistDomainUpdate(BaseModel):
    """ホワイトリストドメイン更新"""
    note: Optional[str] = Field(None, description="備考", max_length=500)


class WhitelistDomainsResponse(BaseModel):
    """ホワイトリストドメイン一覧レスポンス"""
    success: bool = Field(..., description="処理成功可否")
    message: str = Field(..., description="処理結果メッセージ")
    data: List[WhitelistDomainRead] = Field(default_factory=list, description="ドメインリスト")
    total: int = Field(default=0, description="総件数")
    page: int = Field(default=1, description="現在のページ")
    per_page: int = Field(default=100, description="1ページあたりの件数")


class WhitelistDomainResponse(BaseModel):
    """ホワイトリストドメイン単体レスポンス"""
    success: bool = Field(..., description="処理成功可否")
    message: str = Field(..., description="処理結果メッセージ")
    data: Optional[WhitelistDomainRead] = Field(None, description="ドメインデータ")


class DomainDeleteResponse(BaseModel):
    """ドメイン削除レスポンス"""
    success: bool = Field(..., description="処理成功可否")
    message: str = Field(..., description="処理結果メッセージ")
    deleted_id: Optional[UUID] = Field(None, description="削除されたドメインID")


class DomainStatsResponse(BaseModel):
    """ドメイン統計レスポンス"""
    success: bool = Field(..., description="処理成功可否")
    message: str = Field(..., description="処理結果メッセージ")
    data: Dict = Field(default_factory=dict, description="統計データ")


class BulkDomainRequest(BaseModel):
    """一括ドメイン処理要求"""
    urls: List[str] = Field(..., description="処理対象URL群", min_items=1, max_items=50)
    added_by: str = Field(..., description="追加者", min_length=1, max_length=100)

    @validator('urls')
    def validate_urls(cls, v):
        if not v:
            raise ValueError('URLは最低1つ必要です')
        if len(v) > 50:
            raise ValueError('一度に処理できるURLは50個までです')
        return v


class BulkDomainResponse(BaseModel):
    """一括ドメイン処理レスポンス"""
    success: bool = Field(..., description="処理成功可否")
    message: str = Field(..., description="処理結果メッセージ")
    processed: int = Field(default=0, description="処理済み件数")
    failed: int = Field(default=0, description="失敗件数")
    results: List[Dict] = Field(default_factory=list, description="個別処理結果")
    errors: List[str] = Field(default_factory=list, description="エラーメッセージ群")


class DomainSearchRequest(BaseModel):
    """ドメイン検索要求"""
    query: str = Field(..., description="検索クエリ", min_length=1, max_length=100)
    threat_level: Optional[ThreatLevel] = Field(None, description="脅威レベルフィルタ")
    is_whitelisted: Optional[bool] = Field(None, description="ホワイトリスト状態フィルタ")
    page: int = Field(default=1, description="ページ番号", ge=1)
    per_page: int = Field(default=20, description="1ページあたりの件数", ge=1, le=100)


class DomainSearchResponse(BaseModel):
    """ドメイン検索結果レスポンス"""
    success: bool = Field(..., description="処理成功可否")
    message: str = Field(..., description="処理結果メッセージ")
    data: List[DomainAnalysisResult] = Field(default_factory=list, description="検索結果")
    total: int = Field(default=0, description="総件数")
    page: int = Field(default=1, description="現在のページ")
    per_page: int = Field(default=20, description="1ページあたりの件数")
    has_next: bool = Field(default=False, description="次のページがあるか")
    has_prev: bool = Field(default=False, description="前のページがあるか")