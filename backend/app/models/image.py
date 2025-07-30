"""
ABDSシステム - Image モデル
アップロードされた画像を管理
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import ImageStatus


class Image(Base):
    """画像モデル"""
    __tablename__ = "images"
    
    # 主キー
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # 画像情報
    filename = Column(String(255), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # ステータス
    status = Column(Enum(ImageStatus), default=ImageStatus.PENDING, nullable=False, index=True)
    
    # リレーション
    search_results = relationship("SearchResult", back_populates="image", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Image(id={self.id}, filename='{self.filename}', status='{self.status.value}')>"
