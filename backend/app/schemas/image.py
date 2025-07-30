"""
ABDSシステム - Image関連スキーマ
画像アップロード・管理用Pydanticスキーマ
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator


class ImageStatusEnum(str, Enum):
    """画像処理ステータス列挙型"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImageUploadResponse(BaseModel):
    """画像アップロードレスポンス"""
    id: UUID
    filename: str
    status: ImageStatusEnum
    file_path: Optional[str] = None
    upload_date: datetime
    thumbnail_path: Optional[str] = None
    file_size: Optional[int] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class ImageCreate(BaseModel):
    """画像作成用スキーマ（内部使用）"""
    filename: str = Field(..., min_length=1, max_length=255)
    file_path: str = Field(..., min_length=1, max_length=500)
    status: ImageStatusEnum = ImageStatusEnum.PENDING
    
    @validator('filename')
    def validate_filename(cls, v):
        """ファイル名のバリデーション"""
        # 危険な文字の除去
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in v:
                raise ValueError(f"ファイル名に使用できない文字が含まれています: {char}")
        return v


class ImageRead(BaseModel):
    """画像読み取り用スキーマ"""
    id: UUID
    filename: str
    file_path: str
    upload_date: datetime
    status: ImageStatusEnum
    thumbnail_path: Optional[str] = None
    file_size: Optional[int] = None
    
    # リレーション情報
    search_results_count: Optional[int] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class ImageUpdate(BaseModel):
    """画像更新用スキーマ"""
    status: Optional[ImageStatusEnum] = None
    thumbnail_path: Optional[str] = None
    file_size: Optional[int] = None


class ImageListResponse(BaseModel):
    """画像一覧レスポンス"""
    items: list[ImageRead]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool
