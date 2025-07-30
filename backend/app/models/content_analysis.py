"""
ABDSシステム - ContentAnalysis モデル
コンテンツ分析結果を管理
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class ContentAnalysis(Base):
    """コンテンツ分析モデル"""
    __tablename__ = "content_analyses"
    
    # 主キー
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # 外部キー
    search_result_id = Column(UUID(as_uuid=True), ForeignKey("search_results.id"), nullable=False, index=True)
    
    # 分析内容
    html_content = Column(Text, nullable=True)  # HTMLコンテンツ（大容量の場合もあるためnullable=True）
    ai_analysis = Column(JSON, nullable=False)  # AI分析結果（JSON形式）
    threat_score = Column(Integer, nullable=False, index=True)  # 脅威スコア（0-100）
    
    # タイムスタンプ
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # リレーション
    search_result = relationship("SearchResult", back_populates="content_analysis")
    
    def __repr__(self):
        return f"<ContentAnalysis(id={self.id}, threat_score={self.threat_score})>"
