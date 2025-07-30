"""
ABDSシステム - 画像処理ユーティリティ
画像の検証、サムネイル生成、メタデータ取得
"""

import os
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS
import magic

from app.core.config import settings


# サポートされる画像フォーマット
SUPPORTED_IMAGE_FORMATS = {
    'JPEG': ['.jpg', '.jpeg'],
    'PNG': ['.png'],
    'GIF': ['.gif'],
    'BMP': ['.bmp'],
    'WEBP': ['.webp']
}

# 画像のMIMEタイプ
IMAGE_MIME_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/gif': ['.gif'],
    'image/bmp': ['.bmp'],
    'image/webp': ['.webp']
}


def validate_image_file(file_path: str) -> bool:
    """
    ファイルが有効な画像かどうか検証
    
    Args:
        file_path: 検証するファイルのパス
        
    Returns:
        有効な画像ファイルの場合True
    """
    try:
        # ファイルの存在確認
        if not os.path.exists(file_path):
            return False
        
        # MIMEタイプ検証
        mime_type = magic.from_file(file_path, mime=True)
        if mime_type not in IMAGE_MIME_TYPES:
            return False
        
        # PILで画像として開けるか確認
        with Image.open(file_path) as img:
            img.verify()  # 画像データの整合性確認
        
        # 再度開いて基本情報取得（verifyで壊れるため）
        with Image.open(file_path) as img:
            # 最小サイズチェック
            if img.width < 10 or img.height < 10:
                return False
            
            # 最大サイズチェック
            if img.width > 10000 or img.height > 10000:
                return False
        
        return True
        
    except Exception:
        return False


def get_image_info(file_path: str) -> Optional[Dict[str, Any]]:
    """
    画像ファイルの詳細情報を取得
    
    Args:
        file_path: 画像ファイルのパス
        
    Returns:
        画像情報の辞書、取得できない場合はNone
    """
    try:
        with Image.open(file_path) as img:
            # 基本情報
            info = {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'file_size': os.path.getsize(file_path),
                'has_transparency': img.mode in ('RGBA', 'LA', 'P'),
            }
            
            # EXIF情報の取得（JPEG画像の場合）
            if hasattr(img, '_getexif') and img._getexif() is not None:
                exif_data = {}
                exif = img._getexif()
                for tag, value in exif.items():
                    tag_name = TAGS.get(tag, tag)
                    exif_data[tag_name] = value
                info['exif'] = exif_data
            
            return info
            
    except Exception:
        return None


def create_thumbnail(
    source_path: str, 
    thumbnail_path: str, 
    size: Tuple[int, int] = (200, 200),
    quality: int = 85
) -> bool:
    """
    サムネイル画像を生成
    
    Args:
        source_path: 元画像のパス
        thumbnail_path: サムネイル保存パス
        size: サムネイルサイズ (width, height)
        quality: JPEG品質 (1-100)
        
    Returns:
        サムネイル生成に成功した場合True
    """
    try:
        # サムネイル保存ディレクトリの作成
        thumbnail_dir = os.path.dirname(thumbnail_path)
        os.makedirs(thumbnail_dir, exist_ok=True)
        
        with Image.open(source_path) as img:
            # EXIF情報に基づく回転補正
            img = ImageOps.exif_transpose(img)
            
            # RGBモードに変換（透明度を保持しつつJPEG保存のため）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 白背景で合成
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # アスペクト比を維持してリサイズ
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # サムネイル保存
            img.save(
                thumbnail_path, 
                'JPEG', 
                quality=quality, 
                optimize=True
            )
        
        return True
        
    except Exception as e:
        print(f"サムネイル生成エラー: {e}")
        return False


def get_thumbnail_path(original_path: str, thumbnail_dir: str = "thumbnails") -> str:
    """
    サムネイルのパスを生成
    
    Args:
        original_path: 元画像のパス
        thumbnail_dir: サムネイル保存ディレクトリ
        
    Returns:
        サムネイルのパス
    """
    # 元ファイルの情報取得
    file_path = Path(original_path)
    base_name = file_path.stem
    
    # サムネイルディレクトリとファイル名
    thumb_dir = Path(settings.UPLOAD_DIR) / thumbnail_dir
    thumb_filename = f"{base_name}_thumb.jpg"
    
    return str(thumb_dir / thumb_filename)


def cleanup_image_files(image_path: str, thumbnail_path: Optional[str] = None) -> bool:
    """
    画像ファイルとサムネイルを削除
    
    Args:
        image_path: 元画像のパス
        thumbnail_path: サムネイルのパス（省略可）
        
    Returns:
        削除に成功した場合True
    """
    success = True
    
    try:
        # 元画像の削除
        if os.path.exists(image_path):
            os.remove(image_path)
    except Exception:
        success = False
    
    try:
        # サムネイルの削除
        if thumbnail_path and os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
    except Exception:
        success = False
    
    return success


def resize_image(
    source_path: str, 
    output_path: str, 
    max_width: int = 1920, 
    max_height: int = 1080,
    quality: int = 90
) -> bool:
    """
    画像をリサイズして保存
    
    Args:
        source_path: 元画像のパス
        output_path: 出力パス
        max_width: 最大幅
        max_height: 最大高さ
        quality: JPEG品質
        
    Returns:
        リサイズに成功した場合True
    """
    try:
        with Image.open(source_path) as img:
            # EXIF情報に基づく回転補正
            img = ImageOps.exif_transpose(img)
            
            # 現在のサイズ
            current_width, current_height = img.size
            
            # リサイズが必要かチェック
            if current_width <= max_width and current_height <= max_height:
                # リサイズ不要の場合はコピー
                img.save(output_path, quality=quality, optimize=True)
                return True
            
            # アスペクト比を維持してリサイズ
            ratio = min(max_width / current_width, max_height / current_height)
            new_width = int(current_width * ratio)
            new_height = int(current_height * ratio)
            
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            resized_img.save(output_path, quality=quality, optimize=True)
        
        return True
        
    except Exception:
        return False
