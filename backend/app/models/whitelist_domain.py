"""
ABDSシステム - WhitelistDomain モデル
ホワイトリストドメインを管理
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class WhitelistDomain(Base):
    """ホワイトリストドメインモデル"""
    __tablename__ = "whitelist_domains"
    
    # 主キー
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # ドメイン情報
    domain = Column(String(255), nullable=False, index=True)
    
    # 管理情報
    added_by = Column(String(255), nullable=False, index=True)  # 追加者
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 制約
    __table_args__ = (
        UniqueConstraint('domain', name='uq_whitelist_domains_domain'),
    )
    
    def __repr__(self):
        return f"<WhitelistDomain(id={self.id}, domain='{self.domain}')>"
