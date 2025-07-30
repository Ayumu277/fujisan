"""
ABDSシステム - データベース接続設定
SQLAlchemy エンジンとセッション管理
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

# データベースエンジンの作成
engine = create_engine(
    settings.DATABASE_URL,
    # 開発環境での接続プール設定
    poolclass=NullPool if settings.DEBUG else None,
    pool_pre_ping=True,
    echo=settings.DEBUG,  # デバッグモードでSQLログを出力
)

# セッションローカルの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ベースクラスの作成
Base = declarative_base()

# メタデータの設定（テーブル命名規則）
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)
Base.metadata = metadata


def get_db():
    """
    データベースセッションの依存性注入用ジェネレータ
    
    Yields:
        Session: SQLAlchemyセッション
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """
    データベースの初期化
    テーブル作成とデータセットアップ
    """
    # テーブルの作成（本番環境ではAlembicを使用）
    if settings.DEBUG:
        Base.metadata.create_all(bind=engine)


async def close_db():
    """
    データベース接続のクリーンアップ
    """
    engine.dispose()
