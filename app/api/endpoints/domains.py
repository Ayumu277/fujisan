"""
ABDSシステム - ドメイン管理API
ドメイン判定・ホワイトリスト管理のAPIエンドポイント
"""

import logging
import time
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.domain_classifier import DomainClassifier, get_domain_classifier, DomainInfo
from app.models.whitelist_domain import WhitelistDomain
from app.schemas.domain import (
    DomainCheckRequest,
    DomainCheckResponse,
    DomainAnalysisResult,
    WhoisInfo,
    SSLInfo,
    WhitelistDomainCreate,
    WhitelistDomainRead,
    WhitelistDomainResponse,
    WhitelistDomainsResponse,
    DomainDeleteResponse,
    DomainStatsResponse,
    BulkDomainRequest,
    BulkDomainResponse,
    DomainSearchRequest,
    DomainSearchResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def convert_domain_info_to_schema(domain_info: DomainInfo) -> DomainAnalysisResult:
    """DomainInfoをPydanticスキーマに変換"""
    whois_info = None
    if domain_info.whois_data:
        whois_info = WhoisInfo(**domain_info.whois_data)

    ssl_info = None
    if domain_info.ssl_info:
        ssl_info = SSLInfo(**domain_info.ssl_info)

    return DomainAnalysisResult(
        domain=domain_info.domain,
        subdomain=domain_info.subdomain,
        tld=domain_info.tld,
        is_whitelisted=domain_info.is_whitelisted,
        threat_level=domain_info.threat_level,
        confidence_score=domain_info.confidence_score,
        analysis_timestamp=domain_info.analysis_timestamp,
        whois_data=whois_info,
        ssl_info=ssl_info,
        error_message=domain_info.error_message
    )


@router.post("/check", response_model=DomainCheckResponse)
async def check_domain(
    request: DomainCheckRequest,
    db: Session = Depends(get_db)
):
    """
    ドメインの安全性をチェック

    - **url**: チェック対象のURL
    - **include_whois**: Whois情報を含めるか（デフォルト: true）
    - **include_ssl**: SSL証明書情報を含めるか（デフォルト: true）
    """
    try:
        start_time = time.time()

        classifier = get_domain_classifier(db)
        domain_info = await classifier.classify_domain(request.url)

        # 必要に応じてWhois/SSL情報を削除
        if not request.include_whois:
            domain_info.whois_data = None
        if not request.include_ssl:
            domain_info.ssl_info = None

        execution_time_ms = int((time.time() - start_time) * 1000)

        result = convert_domain_info_to_schema(domain_info)

        return DomainCheckResponse(
            success=True,
            message="ドメインチェックが完了しました",
            data=result,
            execution_time_ms=execution_time_ms
        )

    except Exception as e:
        logger.error(f"Domain check error: {str(e)}")
        return DomainCheckResponse(
            success=False,
            message=f"ドメインチェック中にエラーが発生しました: {str(e)}",
            data=None
        )


@router.get("/whitelist", response_model=WhitelistDomainsResponse)
async def get_whitelist_domains(
    skip: int = Query(0, ge=0, description="スキップする件数"),
    limit: int = Query(100, ge=1, le=1000, description="取得する最大件数"),
    db: Session = Depends(get_db)
):
    """
    ホワイトリストドメイン一覧を取得

    - **skip**: スキップする件数（ページネーション用）
    - **limit**: 取得する最大件数（1-1000）
    """
    try:
        classifier = get_domain_classifier(db)
        domains = await classifier.get_whitelist_domains(skip=skip, limit=limit)

        # 総件数を取得
        total = db.query(WhitelistDomain).count()

        # ページ計算
        page = (skip // limit) + 1
        per_page = limit

        domain_reads = [WhitelistDomainRead.from_orm(domain) for domain in domains]

        return WhitelistDomainsResponse(
            success=True,
            message="ホワイトリストドメインを取得しました",
            data=domain_reads,
            total=total,
            page=page,
            per_page=per_page
        )

    except Exception as e:
        logger.error(f"Get whitelist domains error: {str(e)}")
        return WhitelistDomainsResponse(
            success=False,
            message=f"ホワイトリスト取得中にエラーが発生しました: {str(e)}",
            data=[],
            total=0
        )


@router.post("/whitelist", response_model=WhitelistDomainResponse, status_code=status.HTTP_201_CREATED)
async def add_domain_to_whitelist(
    request: WhitelistDomainCreate,
    db: Session = Depends(get_db)
):
    """
    ドメインをホワイトリストに追加

    - **domain**: 追加するドメイン名
    - **added_by**: 追加者の名前またはID
    - **note**: 備考（オプション）
    """
    try:
        classifier = get_domain_classifier(db)
        whitelist_entry = await classifier.add_to_whitelist(
            domain=request.domain,
            added_by=request.added_by
        )

        domain_read = WhitelistDomainRead.from_orm(whitelist_entry)

        return WhitelistDomainResponse(
            success=True,
            message=f"ドメイン '{request.domain}' をホワイトリストに追加しました",
            data=domain_read
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Add to whitelist error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ホワイトリスト追加中にエラーが発生しました: {str(e)}"
        )


@router.delete("/whitelist/{domain_id}", response_model=DomainDeleteResponse)
async def remove_domain_from_whitelist(
    domain_id: UUID,
    db: Session = Depends(get_db)
):
    """
    ホワイトリストからドメインを削除

    - **domain_id**: 削除するドメインのUUID
    """
    try:
        classifier = get_domain_classifier(db)
        success = await classifier.remove_from_whitelist(str(domain_id))

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたドメインがホワイトリストに見つかりません"
            )

        return DomainDeleteResponse(
            success=True,
            message="ドメインをホワイトリストから削除しました",
            deleted_id=domain_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove from whitelist error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ホワイトリスト削除中にエラーが発生しました: {str(e)}"
        )


@router.get("/whitelist/{domain_id}", response_model=WhitelistDomainResponse)
async def get_whitelist_domain(
    domain_id: UUID,
    db: Session = Depends(get_db)
):
    """
    特定のホワイトリストドメイン情報を取得

    - **domain_id**: 取得するドメインのUUID
    """
    try:
        domain = db.query(WhitelistDomain).filter(
            WhitelistDomain.id == domain_id
        ).first()

        if not domain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定されたドメインがホワイトリストに見つかりません"
            )

        domain_read = WhitelistDomainRead.from_orm(domain)

        return WhitelistDomainResponse(
            success=True,
            message="ホワイトリストドメイン情報を取得しました",
            data=domain_read
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get whitelist domain error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ドメイン取得中にエラーが発生しました: {str(e)}"
        )


@router.post("/check-bulk", response_model=BulkDomainResponse)
async def check_domains_bulk(
    request: BulkDomainRequest,
    db: Session = Depends(get_db)
):
    """
    複数のURLを一括でドメインチェック

    - **urls**: チェック対象のURL群（最大50個）
    - **added_by**: 処理実行者
    """
    try:
        classifier = get_domain_classifier(db)

        results = []
        processed = 0
        failed = 0
        errors = []

        for url in request.urls:
            try:
                domain_info = await classifier.classify_domain(url)
                result_data = convert_domain_info_to_schema(domain_info)

                results.append({
                    "url": url,
                    "success": True,
                    "data": result_data.dict()
                })
                processed += 1

            except Exception as e:
                results.append({
                    "url": url,
                    "success": False,
                    "error": str(e)
                })
                errors.append(f"{url}: {str(e)}")
                failed += 1

        return BulkDomainResponse(
            success=True,
            message=f"一括処理が完了しました（成功: {processed}件、失敗: {failed}件）",
            processed=processed,
            failed=failed,
            results=results,
            errors=errors
        )

    except Exception as e:
        logger.error(f"Bulk domain check error: {str(e)}")
        return BulkDomainResponse(
            success=False,
            message=f"一括処理中にエラーが発生しました: {str(e)}",
            processed=0,
            failed=len(request.urls),
            results=[],
            errors=[str(e)]
        )


@router.post("/whitelist-bulk", response_model=BulkDomainResponse)
async def add_domains_to_whitelist_bulk(
    request: BulkDomainRequest,
    db: Session = Depends(get_db)
):
    """
    複数のドメインを一括でホワイトリストに追加

    - **urls**: 追加対象のURL群（最大50個）
    - **added_by**: 追加者
    """
    try:
        classifier = get_domain_classifier(db)

        results = []
        processed = 0
        failed = 0
        errors = []

        for url in request.urls:
            try:
                # URLからドメインを抽出
                domain_info = await classifier.classify_domain(url)
                domain = domain_info.domain

                if not domain:
                    raise ValueError("有効なドメインを抽出できませんでした")

                # ホワイトリストに追加
                whitelist_entry = await classifier.add_to_whitelist(
                    domain=domain,
                    added_by=request.added_by
                )

                results.append({
                    "url": url,
                    "domain": domain,
                    "success": True,
                    "id": str(whitelist_entry.id)
                })
                processed += 1

            except Exception as e:
                results.append({
                    "url": url,
                    "success": False,
                    "error": str(e)
                })
                errors.append(f"{url}: {str(e)}")
                failed += 1

        return BulkDomainResponse(
            success=True,
            message=f"一括ホワイトリスト追加が完了しました（成功: {processed}件、失敗: {failed}件）",
            processed=processed,
            failed=failed,
            results=results,
            errors=errors
        )

    except Exception as e:
        logger.error(f"Bulk whitelist add error: {str(e)}")
        return BulkDomainResponse(
            success=False,
            message=f"一括追加中にエラーが発生しました: {str(e)}",
            processed=0,
            failed=len(request.urls),
            results=[],
            errors=[str(e)]
        )


@router.get("/stats", response_model=DomainStatsResponse)
async def get_domain_stats(
    db: Session = Depends(get_db)
):
    """
    ドメイン関連の統計情報を取得
    """
    try:
        # ホワイトリストドメイン数
        whitelist_count = db.query(WhitelistDomain).count()

        # 最近追加されたドメイン（過去30日）
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_additions = db.query(WhitelistDomain).filter(
            WhitelistDomain.added_at >= thirty_days_ago
        ).count()

        stats_data = {
            "whitelist_total": whitelist_count,
            "recent_additions_30days": recent_additions,
            "last_updated": datetime.utcnow().isoformat(),
            "system_status": "active"
        }

        return DomainStatsResponse(
            success=True,
            message="統計情報を取得しました",
            data=stats_data
        )

    except Exception as e:
        logger.error(f"Get domain stats error: {str(e)}")
        return DomainStatsResponse(
            success=False,
            message=f"統計情報取得中にエラーが発生しました: {str(e)}",
            data={}
        )