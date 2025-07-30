"""
ABDSシステム - 画像検索API
類似画像検索のAPIエンドポイント
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models import Image, SearchResult as DBSearchResult, ImageStatus, ThreatLevel
from app.schemas.search import (
    SearchStartRequest,
    SearchStartResponse,
    SearchStatusResponse,
    SearchResultsResponse,
    SearchErrorResponse,
    SearchStatus,
    SearchServiceType,
    SearchResultItem,
    RateLimitInfo
)
from app.services.image_search import (
    create_image_search_service,
    SearchAPIError,
    RateLimitExceededError
)
from app.utils.rate_limiter import global_rate_limiter

# ログ設定
logger = logging.getLogger(__name__)

# ルーター作成
router = APIRouter(prefix="/search", tags=["Image Search"])

# インメモリ検索ジョブストレージ（本番環境ではRedisを使用）
search_jobs: Dict[str, Dict[str, Any]] = {}


class SearchJobManager:
    """検索ジョブ管理クラス"""
    
    @staticmethod
    def create_job(image_id: UUID, service_type: SearchServiceType, max_results: int) -> str:
        """検索ジョブを作成"""
        job_id = str(uuid.uuid4())
        search_jobs[job_id] = {
            "id": job_id,
            "image_id": str(image_id),
            "service_type": service_type,
            "status": SearchStatus.PENDING,
            "max_results": max_results,
            "progress": 0.0,
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "error_message": None,
            "results_count": None,
            "results": []
        }
        return job_id
    
    @staticmethod
    def get_job(job_id: str) -> Optional[Dict[str, Any]]:
        """検索ジョブを取得"""
        return search_jobs.get(job_id)
    
    @staticmethod
    def update_job(job_id: str, **updates):
        """検索ジョブを更新"""
        if job_id in search_jobs:
            search_jobs[job_id].update(updates)
    
    @staticmethod
    def get_jobs_by_image_id(image_id: str) -> List[Dict[str, Any]]:
        """画像IDに関連する検索ジョブを取得"""
        return [job for job in search_jobs.values() if job["image_id"] == image_id]


async def background_search_task(
    job_id: str, 
    image_path: str, 
    service_type: SearchServiceType, 
    max_results: int,
    db: Session
):
    """
    バックグラウンド検索タスク
    
    Args:
        job_id: ジョブID
        image_path: 画像パス
        service_type: 検索サービスタイプ
        max_results: 最大結果数
        db: データベースセッション
    """
    try:
        # ジョブステータスを更新
        SearchJobManager.update_job(
            job_id,
            status=SearchStatus.IN_PROGRESS,
            progress=0.1
        )
        
        # 検索サービスを作成
        search_service = create_image_search_service(service_type.value)
        
        # 進捗更新
        SearchJobManager.update_job(job_id, progress=0.3)
        
        # 画像検索を実行
        logger.info(f"画像検索開始: job_id={job_id}, service={service_type.value}")
        search_results = await search_service.search_similar_images(
            image_path=image_path,
            max_results=max_results
        )
        
        # 進捗更新
        SearchJobManager.update_job(job_id, progress=0.7)
        
        # 結果をデータベースに保存
        job = SearchJobManager.get_job(job_id)
        image_id = job["image_id"]
        
        saved_results = []
        for result in search_results:
            try:
                db_result = DBSearchResult(
                    image_id=image_id,
                    found_url=result.url,
                    domain=result.source_domain,
                    similarity_score=result.similarity_score,
                    is_official=False,  # TODO: 公式サイト判定ロジック
                    threat_level=ThreatLevel.SAFE,  # TODO: 脅威レベル判定
                    analyzed_at=datetime.utcnow()
                )
                db.add(db_result)
                
                # API結果用の形式に変換
                result_item = SearchResultItem(
                    title=result.title,
                    url=result.url,
                    thumbnail_url=result.thumbnail_url,
                    source_domain=result.source_domain,
                    similarity_score=result.similarity_score,
                    width=result.width,
                    height=result.height,
                    file_size=result.file_size
                )
                saved_results.append(result_item.dict())
                
            except Exception as e:
                logger.warning(f"検索結果の保存でエラー: {e}")
                continue
        
        db.commit()
        
        # ジョブ完了
        SearchJobManager.update_job(
            job_id,
            status=SearchStatus.COMPLETED,
            progress=1.0,
            completed_at=datetime.utcnow(),
            results_count=len(saved_results),
            results=saved_results
        )
        
        logger.info(f"画像検索完了: job_id={job_id}, results={len(saved_results)}")
        
    except RateLimitExceededError as e:
        logger.warning(f"レート制限エラー: {e}")
        SearchJobManager.update_job(
            job_id,
            status=SearchStatus.FAILED,
            error_message=str(e),
            completed_at=datetime.utcnow()
        )
        
    except SearchAPIError as e:
        logger.error(f"検索APIエラー: {e}")
        SearchJobManager.update_job(
            job_id,
            status=SearchStatus.FAILED,
            error_message=str(e),
            completed_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"検索処理中にエラー: {e}")
        SearchJobManager.update_job(
            job_id,
            status=SearchStatus.FAILED,
            error_message=f"予期しないエラー: {str(e)}",
            completed_at=datetime.utcnow()
        )
    
    finally:
        db.close()


@router.post(
    "/start/{image_id}",
    response_model=SearchStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="画像検索開始",
    description="指定された画像の類似画像検索を開始します"
)
async def start_search(
    image_id: UUID,
    request: SearchStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> SearchStartResponse:
    """
    画像検索開始エンドポイント
    
    Args:
        image_id: 検索対象の画像ID
        request: 検索リクエスト
        background_tasks: バックグラウンドタスク
        db: データベースセッション
        
    Returns:
        SearchStartResponse: 検索開始レスポンス
        
    Raises:
        HTTPException: 画像が見つからない、またはエラーが発生した場合
    """
    
    # レート制限チェック
    rate_limit_key = f"search_{request.service_type.value}"
    if not await global_rate_limiter.acquire(rate_limit_key, limit=100, window=86400):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="検索APIのレート制限に達しました。明日再試行してください。"
        )
    
    # 画像の存在確認
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定された画像が見つかりません"
        )
    
    # 画像ファイルの存在確認
    import os
    if not os.path.exists(image.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="画像ファイルが見つかりません"
        )
    
    try:
        # 検索ジョブを作成
        job_id = SearchJobManager.create_job(
            image_id=image_id,
            service_type=request.service_type,
            max_results=request.max_results
        )
        
        # バックグラウンドタスクを開始
        background_tasks.add_task(
            background_search_task,
            job_id,
            image.file_path,
            request.service_type,
            request.max_results,
            db
        )
        
        # レスポンスを作成
        estimated_completion = datetime.utcnow() + timedelta(minutes=2)
        
        response = SearchStartResponse(
            search_id=UUID(job_id),
            image_id=image_id,
            status=SearchStatus.PENDING,
            service_type=request.service_type,
            max_results=request.max_results,
            started_at=datetime.utcnow(),
            estimated_completion=estimated_completion
        )
        
        logger.info(f"検索開始: image_id={image_id}, job_id={job_id}")
        return response
        
    except Exception as e:
        logger.error(f"検索開始処理中にエラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="検索開始処理中にエラーが発生しました"
        )


@router.get(
    "/status/{search_id}",
    response_model=SearchStatusResponse,
    summary="検索ステータス取得",
    description="指定された検索IDのステータスを取得します"
)
async def get_search_status(search_id: UUID) -> SearchStatusResponse:
    """
    検索ステータス取得エンドポイント
    
    Args:
        search_id: 検索ID
        
    Returns:
        SearchStatusResponse: 検索ステータス
        
    Raises:
        HTTPException: 検索が見つからない場合
    """
    
    job = SearchJobManager.get_job(str(search_id))
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定された検索が見つかりません"
        )
    
    response = SearchStatusResponse(
        search_id=search_id,
        image_id=UUID(job["image_id"]),
        status=SearchStatus(job["status"]),
        service_type=SearchServiceType(job["service_type"]),
        progress=job["progress"],
        started_at=job["started_at"],
        completed_at=job.get("completed_at"),
        error_message=job.get("error_message"),
        results_count=job.get("results_count")
    )
    
    return response


@router.get(
    "/results/{image_id}",
    response_model=SearchResultsResponse,
    summary="検索結果取得",
    description="指定された画像の検索結果を取得します"
)
async def get_search_results(
    image_id: UUID,
    db: Session = Depends(get_db)
) -> SearchResultsResponse:
    """
    検索結果取得エンドポイント
    
    Args:
        image_id: 画像ID
        db: データベースセッション
        
    Returns:
        SearchResultsResponse: 検索結果
        
    Raises:
        HTTPException: 画像または結果が見つからない場合
    """
    
    # 画像の存在確認
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定された画像が見つかりません"
        )
    
    # データベースから検索結果を取得
    db_results = db.query(DBSearchResult).filter(
        DBSearchResult.image_id == image_id
    ).order_by(DBSearchResult.similarity_score.desc()).all()
    
    # インメモリジョブから最新の結果も取得
    jobs = SearchJobManager.get_jobs_by_image_id(str(image_id))
    completed_jobs = [job for job in jobs if job["status"] == SearchStatus.COMPLETED]
    
    # 結果をマージ
    all_results = []
    
    # データベースの結果
    for db_result in db_results:
        result_item = SearchResultItem(
            title="",  # データベースにはタイトルが保存されていない
            url=db_result.found_url,
            thumbnail_url="",  # データベースにはサムネイルURLが保存されていない
            source_domain=db_result.domain,
            similarity_score=db_result.similarity_score,
            width=None,
            height=None,
            file_size=None
        )
        all_results.append(result_item)
    
    # インメモリ結果（最新）
    for job in completed_jobs:
        for result_data in job.get("results", []):
            result_item = SearchResultItem(**result_data)
            all_results.append(result_item)
    
    # 重複除去と並び替え
    unique_results = {}
    for result in all_results:
        key = result.url
        if key not in unique_results or result.similarity_score > unique_results[key].similarity_score:
            unique_results[key] = result
    
    final_results = sorted(unique_results.values(), key=lambda x: x.similarity_score, reverse=True)
    
    # 最後の検索情報
    last_completed_job = max(completed_jobs, key=lambda x: x["completed_at"]) if completed_jobs else None
    
    response = SearchResultsResponse(
        image_id=image_id,
        total_results=len(final_results),
        search_completed_at=last_completed_job["completed_at"] if last_completed_job else None,
        service_used=SearchServiceType(last_completed_job["service_type"]) if last_completed_job else SearchServiceType.SERPAPI,
        results=final_results,
        stats={
            "database_results": len(db_results),
            "memory_results": sum(len(job.get("results", [])) for job in completed_jobs),
            "unique_domains": len(set(r.source_domain for r in final_results)),
            "average_similarity": sum(r.similarity_score for r in final_results) / len(final_results) if final_results else 0
        }
    )
    
    return response


@router.get(
    "/rate-limit/{service_type}",
    response_model=RateLimitInfo,
    summary="レート制限情報取得",
    description="指定されたサービスのレート制限情報を取得します"
)
async def get_rate_limit_info(service_type: SearchServiceType) -> RateLimitInfo:
    """
    レート制限情報取得エンドポイント
    
    Args:
        service_type: 検索サービスタイプ
        
    Returns:
        RateLimitInfo: レート制限情報
    """
    
    rate_limit_key = f"search_{service_type.value}"
    limiter = global_rate_limiter.get_limiter(rate_limit_key, limit=100, window=86400)
    
    response = RateLimitInfo(
        service=service_type.value,
        limit=100,
        remaining=limiter.get_remaining_requests(),
        reset_time=limiter.get_reset_time(),
        window_seconds=86400
    )
    
    return response


@router.delete(
    "/jobs/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="検索ジョブ削除",
    description="指定された検索ジョブを削除します"
)
async def delete_search_job(search_id: UUID):
    """
    検索ジョブ削除エンドポイント
    
    Args:
        search_id: 検索ID
        
    Raises:
        HTTPException: 検索が見つからない場合
    """
    
    job_id = str(search_id)
    if job_id not in search_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定された検索が見つかりません"
        )
    
    del search_jobs[job_id]
    logger.info(f"検索ジョブ削除: {job_id}")


# =================================
# 管理用エンドポイント
# =================================

@router.get(
    "/admin/jobs",
    summary="全検索ジョブ取得（管理用）",
    description="管理用：全ての検索ジョブを取得します"
)
async def get_all_search_jobs():
    """管理用：全検索ジョブ取得"""
    return {
        "total_jobs": len(search_jobs),
        "jobs": list(search_jobs.values())
    }


@router.post(
    "/admin/cleanup",
    summary="完了済みジョブクリーンアップ（管理用）",
    description="管理用：完了済みの検索ジョブをクリーンアップします"
)
async def cleanup_completed_jobs():
    """管理用：完了済みジョブクリーンアップ"""
    before_count = len(search_jobs)
    
    # 24時間以上前の完了済みジョブを削除
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    jobs_to_delete = []
    
    for job_id, job in search_jobs.items():
        if (job["status"] in [SearchStatus.COMPLETED, SearchStatus.FAILED] and 
            job.get("completed_at") and 
            job["completed_at"] < cutoff_time):
            jobs_to_delete.append(job_id)
    
    for job_id in jobs_to_delete:
        del search_jobs[job_id]
    
    after_count = len(search_jobs)
    cleaned_count = before_count - after_count
    
    logger.info(f"検索ジョブクリーンアップ完了: {cleaned_count}件削除")
    
    return {
        "message": f"{cleaned_count}件の古い検索ジョブを削除しました",
        "jobs_before": before_count,
        "jobs_after": after_count,
        "cleaned": cleaned_count
    }
