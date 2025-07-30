"""
ABDSシステム - ファイル処理ユーティリティ
ファイルのアップロード、検証、保存処理
"""

import os
import uuid
import re
from pathlib import Path
from typing import Tuple, Optional
import magic
from fastapi import UploadFile, HTTPException
from datetime import datetime

from app.core.config import settings


def sanitize_filename(filename: str) -> str:
    """
    ファイル名をサニタイズして安全にする
    
    Args:
        filename: 元のファイル名
        
    Returns:
        サニタイズされたファイル名
    """
    # 基本的なサニタイズ
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # 連続するアンダースコアを単一に
    filename = re.sub(r'_+', '_', filename)
    
    # 先頭・末尾のアンダースコア、ピリオドを除去
    filename = filename.strip('_.')
    
    # 空の場合はデフォルト名
    if not filename:
        filename = "unnamed_file"
    
    # 長すぎる場合は切り詰め
    if len(filename) > 100:
        name_part, ext_part = os.path.splitext(filename)
        filename = name_part[:90] + ext_part
    
    return filename


def generate_unique_filename(filename: str) -> str:
    """
    ユニークなファイル名を生成
    
    Args:
        filename: 元のファイル名
        
    Returns:
        ユニークなファイル名
    """
    # ファイル名をサニタイズ
    safe_filename = sanitize_filename(filename)
    
    # 拡張子を取得
    name_part, ext_part = os.path.splitext(safe_filename)
    
    # タイムスタンプとUUIDを追加
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    return f"{timestamp}_{unique_id}_{name_part}{ext_part}"


def validate_file_type(filename: str) -> bool:
    """
    ファイル拡張子の検証
    
    Args:
        filename: ファイル名
        
    Returns:
        有効な拡張子の場合True
    """
    if not filename:
        return False
    
    _, ext = os.path.splitext(filename.lower())
    return ext in settings.ALLOWED_EXTENSIONS


def validate_file_size(file_size: int) -> bool:
    """
    ファイルサイズの検証
    
    Args:
        file_size: ファイルサイズ（バイト）
        
    Returns:
        サイズが制限内の場合True
    """
    return 0 < file_size <= settings.MAX_UPLOAD_SIZE


def get_file_info(file: UploadFile) -> Tuple[str, int, str]:
    """
    アップロードファイルの情報を取得
    
    Args:
        file: FastAPIのUploadFileオブジェクト
        
    Returns:
        (ファイル名, サイズ, MIMEタイプ)
        
    Raises:
        HTTPException: ファイル情報の取得に失敗した場合
    """
    try:
        # ファイルサイズを取得
        file.file.seek(0, 2)  # ファイル末尾へ
        size = file.file.tell()
        file.file.seek(0)  # ファイル先頭に戻す
        
        return file.filename or "unknown", size, file.content_type or "application/octet-stream"
    
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"ファイル情報の取得に失敗しました: {str(e)}"
        )


async def save_uploaded_file(
    file: UploadFile, 
    upload_dir: str = settings.UPLOAD_DIR
) -> Tuple[str, str]:
    """
    アップロードされたファイルを保存
    
    Args:
        file: FastAPIのUploadFileオブジェクト
        upload_dir: 保存先ディレクトリ
        
    Returns:
        (保存されたファイルパス, ユニークファイル名)
        
    Raises:
        HTTPException: ファイル保存に失敗した場合
    """
    try:
        # アップロードディレクトリの作成
        upload_path = Path(upload_dir)
        upload_path.mkdir(parents=True, exist_ok=True)
        
        # ユニークなファイル名を生成
        unique_filename = generate_unique_filename(file.filename or "unknown")
        file_path = upload_path / unique_filename
        
        # ファイルを保存
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return str(file_path), unique_filename
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ファイルの保存に失敗しました: {str(e)}"
        )
    
    finally:
        # ファイルポインタをリセット
        await file.seek(0)


def get_file_mime_type(file_path: str) -> Optional[str]:
    """
    ファイルの実際のMIMEタイプを取得
    
    Args:
        file_path: ファイルパス
        
    Returns:
        MIMEタイプ文字列、取得できない場合はNone
    """
    try:
        return magic.from_file(file_path, mime=True)
    except Exception:
        return None


def delete_file(file_path: str) -> bool:
    """
    ファイルを安全に削除
    
    Args:
        file_path: 削除するファイルのパス
        
    Returns:
        削除に成功した場合True
    """
    try:
        file_path_obj = Path(file_path)
        if file_path_obj.exists() and file_path_obj.is_file():
            file_path_obj.unlink()
            return True
        return False
    except Exception:
        return False
