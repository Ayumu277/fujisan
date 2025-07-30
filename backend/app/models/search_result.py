"""
ABDSシステム - SearchResult モデル
画像検索結果を管理
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, Float, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import ThreatLevel


class SearchResult(Base):
    """検索結果モデル"""
    __tablename__ = "search_results"
    
    # 主キー
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # 外部キー
    image_id = Column(UUID(as_uuid=True), ForeignKey("images.id"), nullable=False, index=True)
    
    # 検索結果情報
    found_url = Column(Text, nullable=False)
    domain = Column(String(255), nullable=False, index=True)
    similarity_score = Column(Float, nullable=False, index=True)
    
    # 分析結果
    is_official = Column(Boolean, default=False, nullable=False, index=True)
    threat_level = Column(Enum(ThreatLevel), default=ThreatLevel.SAFE, nullable=False, index=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # リレーション
    image = relationship("Image", back_populates="search_results")
    content_analysis = relationship("ContentAnalysis", back_populates="search_result", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SearchResult(id={self.id}, domain='{self.domain}', threat_level='{self.threat_level.value}')>"
