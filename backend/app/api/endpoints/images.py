"""
ABDSシステム - 画像アップロードAPI
画像ファイルのアップロード、検証、保存処理
"""

import os
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models import Image, ImageStatus
from app.schemas.image import ImageUploadResponse, ImageStatusEnum
from app.utils.file_handler import (
    validate_file_type,
    validate_file_size,
    get_file_info,
    save_uploaded_file,
    generate_unique_filename
)
from app.utils.image_processor import (
    validate_image_file,
    get_image_info,
    create_thumbnail,
    get_thumbnail_path
)
from app.utils.security import (
    validate_file_content,
    validate_mime_type,
    scan_file_for_virus,
    sanitize_upload_directory
)

# ログ設定
logger = logging.getLogger(__name__)

# ルーター作成
router = APIRouter(prefix="/images", tags=["Images"])

# アップロード設定
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE  # 10MB
UPLOAD_DIR = settings.UPLOAD_DIR
ALLOWED_EXTENSIONS = settings.ALLOWED_EXTENSIONS


@router.post(
    "/upload",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="画像アップロード",
    description="画像ファイルをアップロードして検証・保存を行います"
)
async def upload_image(
    file: UploadFile = File(..., description="アップロードする画像ファイル"),
    db: Session = Depends(get_db)
) -> ImageUploadResponse:
    """
    画像アップロードエンドポイント
    
    - ファイル検証（形式、サイズ、セキュリティ）
    - 画像の保存
    - データベースへの記録
    - サムネイル生成
    
    Args:
        file: アップロードファイル
        db: データベースセッション
        
    Returns:
        ImageUploadResponse: アップロード結果
        
    Raises:
        HTTPException: バリデーションエラーまたは処理エラー
    """
    
    # =================================
    # 1. 基本検証
    # =================================
    
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ファイル名が指定されていません"
        )
    
    logger.info(f"画像アップロード開始: {file.filename}")
    
    try:
        # ファイル情報取得
        filename, file_size, content_type = get_file_info(file)
        
        # ファイルサイズ検証
        if not validate_file_size(file_size):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"ファイルサイズが制限を超えています。最大: {MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
            )
        
        # ファイル拡張子検証
        if not validate_file_type(filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"サポートされていないファイル形式です。許可される形式: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # =================================
        # 2. アップロードディレクトリ検証
        # =================================
        
        if not sanitize_upload_directory(UPLOAD_DIR):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="アップロードディレクトリが安全ではありません"
            )
        
        # =================================
        # 3. ファイル保存
        # =================================
        
        # 画像用サブディレクトリを作成
        images_dir = os.path.join(UPLOAD_DIR, "images")
        file_path, unique_filename = await save_uploaded_file(file, images_dir)
        
        logger.info(f"ファイル保存完了: {file_path}")
        
        # =================================
        # 4. セキュリティ検証
        # =================================
        
        # MIMEタイプ検証
        if not validate_mime_type(file_path, content_type):
            # 危険なファイルを削除
            try:
                os.remove(file_path)
            except:
                pass
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ファイルのMIMEタイプが不正です"
            )
        
        # 包括的なファイル内容検証
        validation_result = validate_file_content(file_path)
        if not validation_result['valid']:
            # 危険なファイルを削除
            try:
                os.remove(file_path)
            except:
                pass
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ファイル検証に失敗しました: {', '.join(validation_result['errors'])}"
            )
        
        # ウイルススキャン結果の確認
        if not validation_result['virus_scan']['clean']:
            # 危険なファイルを削除
            try:
                os.remove(file_path)
            except:
                pass
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="セキュリティスキャンで脅威が検出されました"
            )
        
        # =================================
        # 5. 画像検証
        # =================================
        
        if not validate_image_file(file_path):
            # 無効な画像ファイルを削除
            try:
                os.remove(file_path)
            except:
                pass
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="有効な画像ファイルではありません"
            )
        
        # 画像詳細情報取得
        image_info = get_image_info(file_path)
        if not image_info:
            # 画像情報取得に失敗した場合はファイルを削除
            try:
                os.remove(file_path)
            except:
                pass
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="画像情報の取得に失敗しました"
            )
        
        # =================================
        # 6. データベース記録
        # =================================
        
        try:
            # Imageオブジェクト作成
            db_image = Image(
                filename=unique_filename,
                file_path=file_path,
                upload_date=datetime.utcnow(),
                status=ImageStatus.PENDING
            )
            
            # データベースに保存
            db.add(db_image)
            db.commit()
            db.refresh(db_image)
            
            logger.info(f"データベース記録完了: ID={db_image.id}")
            
        except Exception as e:
            db.rollback()
            # データベース保存に失敗した場合はファイルを削除
            try:
                os.remove(file_path)
            except:
                pass
            logger.error(f"データベース保存エラー: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="データベース保存に失敗しました"
            )
        
        # =================================
        # 7. サムネイル生成
        # =================================
        
        thumbnail_path = None
        try:
            # サムネイルパス生成
            thumbnail_path = get_thumbnail_path(file_path)
            
            # サムネイル作成
            if create_thumbnail(file_path, thumbnail_path):
                logger.info(f"サムネイル生成完了: {thumbnail_path}")
                
                # データベースにサムネイルパスを更新
                db_image.status = ImageStatus.COMPLETED
                db.commit()
            else:
                logger.warning(f"サムネイル生成に失敗: {file_path}")
                # サムネイル生成失敗でもアップロード自体は成功とする
                
        except Exception as e:
            logger.error(f"サムネイル生成エラー: {e}")
            # サムネイル生成失敗でもアップロード自体は成功とする
        
        # =================================
        # 8. レスポンス作成
        # =================================
        
        response = ImageUploadResponse(
            id=db_image.id,
            filename=db_image.filename,
            status=ImageStatusEnum(db_image.status.value),
            file_path=db_image.file_path,
            upload_date=db_image.upload_date,
            thumbnail_path=thumbnail_path,
            file_size=file_size
        )
        
        logger.info(f"画像アップロード完了: ID={db_image.id}, ファイル={unique_filename}")
        return response
        
    except HTTPException:
        # HTTPExceptionはそのまま再発生
        raise
        
    except Exception as e:
        logger.error(f"画像アップロード処理中にエラーが発生しました: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="画像アップロード処理中にエラーが発生しました"
        )


@router.get(
    "/{image_id}",
    response_model=ImageUploadResponse,
    summary="画像情報取得",
    description="指定されたIDの画像情報を取得します"
)
async def get_image(
    image_id: str,
    db: Session = Depends(get_db)
) -> ImageUploadResponse:
    """
    画像情報取得エンドポイント
    
    Args:
        image_id: 画像ID
        db: データベースセッション
        
    Returns:
        ImageUploadResponse: 画像情報
        
    Raises:
        HTTPException: 画像が見つからない場合
    """
    
    # 画像をデータベースから取得
    image = db.query(Image).filter(Image.id == image_id).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定された画像が見つかりません"
        )
    
    # サムネイルパスを生成（存在する場合）
    thumbnail_path = None
    if image.status == ImageStatus.COMPLETED:
        potential_thumbnail = get_thumbnail_path(image.file_path)
        if os.path.exists(potential_thumbnail):
            thumbnail_path = potential_thumbnail
    
    # ファイルサイズを取得
    file_size = None
    if os.path.exists(image.file_path):
        file_size = os.path.getsize(image.file_path)
    
    return ImageUploadResponse(
        id=image.id,
        filename=image.filename,
        status=ImageStatusEnum(image.status.value),
        file_path=image.file_path,
        upload_date=image.upload_date,
        thumbnail_path=thumbnail_path,
        file_size=file_size
    )


@router.delete(
    "/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="画像削除",
    description="指定されたIDの画像を削除します"
)
async def delete_image(
    image_id: str,
    db: Session = Depends(get_db)
):
    """
    画像削除エンドポイント
    
    Args:
        image_id: 画像ID
        db: データベースセッション
        
    Raises:
        HTTPException: 画像が見つからない場合
    """
    
    # 画像をデータベースから取得
    image = db.query(Image).filter(Image.id == image_id).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定された画像が見つかりません"
        )
    
    try:
        # ファイル削除
        if os.path.exists(image.file_path):
            os.remove(image.file_path)
        
        # サムネイル削除
        thumbnail_path = get_thumbnail_path(image.file_path)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
        
        # データベースから削除
        db.delete(image)
        db.commit()
        
        logger.info(f"画像削除完了: ID={image_id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"画像削除エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="画像削除中にエラーが発生しました"
        )
