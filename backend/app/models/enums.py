"""
ABDSシステム - SQLAlchemy Enum定義
"""

import enum


class ImageStatus(enum.Enum):
    """画像処理ステータス"""
    PENDING = "pending"         # 処理待ち
    PROCESSING = "processing"   # 処理中
    COMPLETED = "completed"     # 処理完了
    FAILED = "failed"          # 処理失敗


class ThreatLevel(enum.Enum):
    """脅威レベル"""
    SAFE = "safe"      # 安全
    LOW = "low"        # 低脅威
    MEDIUM = "medium"  # 中脅威
    HIGH = "high"      # 高脅威
