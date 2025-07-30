"""
ABDSシステム - AI分析APIエンドポイント
Gemini APIを使用したコンテンツ分析のAPIエンドポイント
"""

import logging
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.ai_analyzer import AIContentAnalyzer, get_ai_analyzer, AnalysisResult
from app.schemas.ai_analysis import (
    AIAnalysisRequest,
    FocusedAnalysisRequest,
    BatchAnalysisRequest,
    AIAnalysisResponse,
    AIAnalysisError,
    AIAnalysisSummary,
    BatchAnalysisResponse,
    AIAnalysisStats,
    AIAnalysisCapabilities,
    AIAnalysisConfig,
    AIAnalysisConfigUpdate,
    AbuseDetectionResult,
    CopyrightInfringementResult,
    CommercialUseResult,
    UnauthorizedRepostResult,
    ContentModificationResult,
    OverallAssessment,
    AnalysisMetadata,
    AnalysisType,
    AnalysisLevel
)

logger = logging.getLogger(__name__)

router = APIRouter()

# グローバル統計追跡
analysis_stats = {
    "total_analyses": 0,
    "analyses_today": 0,
    "successful_analyses": 0,
    "failed_analyses": 0,
    "total_processing_time_ms": 0,
    "threat_distribution": {"高": 0, "中": 0, "低": 0, "なし": 0},
    "last_reset_date": datetime.utcnow().date()
}


def _convert_analysis_result_to_response(result: AnalysisResult) -> AIAnalysisResponse:
    """AnalysisResultをAIAnalysisResponseに変換"""
    try:
        return AIAnalysisResponse(
            abuse_detection=AbuseDetectionResult(
                risk_level=result.abuse_detection.get("risk_level", "安全"),
                evidence=result.abuse_detection.get("evidence", []),
                details=result.abuse_detection.get("details", ""),
                confidence=result.abuse_detection.get("confidence", 0.0)
            ),
            copyright_infringement=CopyrightInfringementResult(
                probability=result.copyright_infringement.get("probability", "問題なし"),
                evidence=result.copyright_infringement.get("evidence", []),
                details=result.copyright_infringement.get("details", ""),
                confidence=result.copyright_infringement.get("confidence", 0.0)
            ),
            commercial_use=CommercialUseResult(
                status=result.commercial_use.get("status", "判定不可"),
                evidence=result.commercial_use.get("evidence", []),
                details=result.commercial_use.get("details", ""),
                confidence=result.commercial_use.get("confidence", 0.0)
            ),
            unauthorized_repost=UnauthorizedRepostResult(
                status=result.unauthorized_repost.get("status", "オリジナル"),
                evidence=result.unauthorized_repost.get("evidence", []),
                details=result.unauthorized_repost.get("details", ""),
                confidence=result.unauthorized_repost.get("confidence", 0.0)
            ),
            content_modification=ContentModificationResult(
                level=result.content_modification.get("level", "無改変"),
                evidence=result.content_modification.get("evidence", []),
                details=result.content_modification.get("details", ""),
                confidence=result.content_modification.get("confidence", 0.0)
            ),
            overall_assessment=OverallAssessment(
                threat_level=result.overall_assessment.get("threat_level", "なし"),
                risk_score=result.overall_assessment.get("risk_score", 0),
                summary=result.overall_assessment.get("summary", ""),
                recommendations=result.overall_assessment.get("recommendations", [])
            ),
            metadata=AnalysisMetadata(
                analyzed_at=result.analyzed_at,
                analysis_version=result.metadata.get("analysis_version", "1.0"),
                confidence_score=result.metadata.get("confidence_score", 0.0),
                processing_time_ms=result.processing_time_ms
            ),
            raw_response=result.raw_response if result.raw_response else None
        )
    except Exception as e:
        logger.error(f"Failed to convert AnalysisResult to response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Response conversion failed: {e}"
        )


def _update_analysis_stats(result: AnalysisResult):
    """分析統計を更新"""
    global analysis_stats

    # 日付リセットチェック
    today = datetime.utcnow().date()
    if analysis_stats["last_reset_date"] != today:
        analysis_stats["analyses_today"] = 0
        analysis_stats["last_reset_date"] = today

    # 基本統計更新
    analysis_stats["total_analyses"] += 1
    analysis_stats["analyses_today"] += 1
    analysis_stats["total_processing_time_ms"] += result.processing_time_ms

    if result.error_message:
        analysis_stats["failed_analyses"] += 1
    else:
        analysis_stats["successful_analyses"] += 1

        # 脅威レベル分布更新
        threat_level = result.overall_assessment.get("threat_level", "なし")
        if threat_level in analysis_stats["threat_distribution"]:
            analysis_stats["threat_distribution"][threat_level] += 1


@router.post("/analyze", response_model=AIAnalysisResponse)
async def analyze_content(
    request: AIAnalysisRequest,
    analyzer: AIContentAnalyzer = Depends(get_ai_analyzer)
):
    """
    コンテンツの包括的AI分析を実行

    - **html_content**: 分析対象のHTMLコンテンツ
    - **image_context**: 画像のコンテキスト情報
    - **analysis_level**: 分析レベル (basic, comprehensive, copyright_focused, abuse_focused)
    - **focus_areas**: 特定の分析領域にフォーカス
    """
    try:
        logger.info("Starting comprehensive AI analysis")

        # 分析実行
        result = await analyzer.analyze_content(
            html_content=request.html_content,
            image_context=request.image_context.dict(),
            analysis_level=request.analysis_level.value,
            focus_areas=[area.value for area in request.focus_areas] if request.focus_areas else None
        )

        # 統計更新
        _update_analysis_stats(result)

        # エラーチェック
        if result.error_message:
            logger.error(f"AI analysis failed: {result.error_message}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=AIAnalysisError(
                    error_code="ANALYSIS_FAILED",
                    error_message=result.error_message,
                    analyzed_at=result.analyzed_at,
                    processing_time_ms=result.processing_time_ms
                ).dict()
            )

        # レスポンス変換
        response = _convert_analysis_result_to_response(result)

        logger.info(f"AI analysis completed successfully in {result.processing_time_ms}ms")
        return response

    except Exception as e:
        logger.error(f"Unexpected error in AI analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/analyze-focused", response_model=AIAnalysisResponse)
async def analyze_focused(
    request: FocusedAnalysisRequest,
    analyzer: AIContentAnalyzer = Depends(get_ai_analyzer)
):
    """
    特定分野に特化したAI分析を実行

    - **analysis_type**: 分析タイプ (abuse, copyright, commercial, repost, modification)
    - **html_content**: 分析対象のHTMLコンテンツ
    - **image_context**: 画像のコンテキスト情報
    """
    try:
        logger.info(f"Starting focused AI analysis: {request.analysis_type}")

        # 分析実行
        result = await analyzer.analyze_focused(
            analysis_type=request.analysis_type.value,
            html_content=request.html_content,
            image_context=request.image_context.dict()
        )

        # 統計更新
        _update_analysis_stats(result)

        # エラーチェック
        if result.error_message:
            logger.error(f"Focused AI analysis failed: {result.error_message}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=AIAnalysisError(
                    error_code="FOCUSED_ANALYSIS_FAILED",
                    error_message=result.error_message,
                    analyzed_at=result.analyzed_at,
                    processing_time_ms=result.processing_time_ms
                ).dict()
            )

        # レスポンス変換
        response = _convert_analysis_result_to_response(result)

        logger.info(f"Focused AI analysis completed in {result.processing_time_ms}ms")
        return response

    except Exception as e:
        logger.error(f"Unexpected error in focused analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Focused analysis failed: {str(e)}"
        )


@router.post("/analyze-batch", response_model=BatchAnalysisResponse)
async def analyze_batch(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    analyzer: AIContentAnalyzer = Depends(get_ai_analyzer)
):
    """
    複数コンテンツの並行AI分析を実行

    - **analyses**: 分析リクエストリスト（最大10件）
    - **max_concurrent**: 最大同時実行数（1-5）
    """
    try:
        logger.info(f"Starting batch AI analysis for {len(request.analyses)} items")
        start_time = datetime.utcnow()

        # バッチ分析実行
        analysis_data = [
            {
                "html_content": req.html_content,
                "image_context": req.image_context.dict(),
                "analysis_level": req.analysis_level.value,
                "focus_areas": [area.value for area in req.focus_areas] if req.focus_areas else None
            }
            for req in request.analyses
        ]

        results = await analyzer.batch_analyze(
            analyses=analysis_data,
            max_concurrent=request.max_concurrent
        )

        # 結果処理
        successful_results = []
        failed_count = 0
        total_processing_time = 0

        for result in results:
            # 統計更新
            _update_analysis_stats(result)
            total_processing_time += result.processing_time_ms

            if result.error_message:
                failed_count += 1
                logger.warning(f"Batch analysis item failed: {result.error_message}")
            else:
                response = _convert_analysis_result_to_response(result)
                successful_results.append(response)

        # バッチサマリー作成
        batch_processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        batch_summary = {
            "total_items": len(request.analyses),
            "successful_items": len(successful_results),
            "failed_items": failed_count,
            "success_rate": len(successful_results) / len(request.analyses) if request.analyses else 0,
            "average_processing_time_ms": total_processing_time / len(results) if results else 0,
            "batch_processing_time_ms": batch_processing_time
        }

        logger.info(f"Batch AI analysis completed: {len(successful_results)}/{len(request.analyses)} successful")

        return BatchAnalysisResponse(
            results=successful_results,
            summary=batch_summary,
            total_processing_time_ms=batch_processing_time,
            successful_analyses=len(successful_results),
            failed_analyses=failed_count
        )

    except Exception as e:
        logger.error(f"Unexpected error in batch analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch analysis failed: {str(e)}"
        )


@router.get("/summary", response_model=AIAnalysisSummary)
async def get_analysis_summary(
    analyzer: AIContentAnalyzer = Depends(get_ai_analyzer)
):
    """
    AI分析機能のサマリー情報を取得
    """
    try:
        # 基本サマリー情報
        summary = AIAnalysisSummary(
            status="available" if analyzer.client else "unavailable",
            overall_risk_score=0,
            threat_level="なし",
            key_findings={
                "total_analyses": analysis_stats["total_analyses"],
                "analyses_today": analysis_stats["analyses_today"],
                "success_rate": (
                    analysis_stats["successful_analyses"] / analysis_stats["total_analyses"]
                    if analysis_stats["total_analyses"] > 0 else 0
                )
            },
            recommendations=[
                "定期的なAI分析の実行を推奨",
                "高リスクコンテンツの詳細確認",
                "著作権侵害リスクの継続監視"
            ],
            processing_time_ms=0,
            analyzed_at=datetime.utcnow()
        )

        return summary

    except Exception as e:
        logger.error(f"Failed to get analysis summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get summary: {str(e)}"
        )


@router.get("/stats", response_model=AIAnalysisStats)
async def get_analysis_stats():
    """
    AI分析の統計情報を取得
    """
    try:
        avg_processing_time = (
            analysis_stats["total_processing_time_ms"] / analysis_stats["total_analyses"]
            if analysis_stats["total_analyses"] > 0 else 0
        )

        success_rate = (
            analysis_stats["successful_analyses"] / analysis_stats["total_analyses"]
            if analysis_stats["total_analyses"] > 0 else 0
        )

        # 最も一般的なリスクを特定
        threat_dist = analysis_stats["threat_distribution"]
        most_common_risks = sorted(
            threat_dist.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        return AIAnalysisStats(
            total_analyses=analysis_stats["total_analyses"],
            analyses_today=analysis_stats["analyses_today"],
            average_processing_time_ms=avg_processing_time,
            success_rate=success_rate,
            threat_distribution=threat_dist,
            most_common_risks=[risk[0] for risk in most_common_risks if risk[1] > 0]
        )

    except Exception as e:
        logger.error(f"Failed to get analysis stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.get("/capabilities", response_model=AIAnalysisCapabilities)
async def get_analysis_capabilities(
    analyzer: AIContentAnalyzer = Depends(get_ai_analyzer)
):
    """
    AI分析機能の能力情報を取得
    """
    try:
        return AIAnalysisCapabilities(
            available=analyzer.client is not None,
            model_name=analyzer.model_name,
            supported_analysis_types=list(AnalysisType),
            supported_levels=list(AnalysisLevel),
            rate_limit_per_minute=analyzer.max_requests_per_minute,
            max_content_length=analyzer.max_tokens_per_request
        )

    except Exception as e:
        logger.error(f"Failed to get capabilities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get capabilities: {str(e)}"
        )


@router.get("/config", response_model=AIAnalysisConfig)
async def get_analysis_config():
    """
    AI分析の設定情報を取得
    """
    try:
        return AIAnalysisConfig(
            enabled=settings.AI_ANALYSIS_ENABLED,
            model_name=settings.AI_DEFAULT_MODEL,
            backup_model=settings.AI_BACKUP_MODEL,
            max_requests_per_minute=settings.AI_MAX_REQUESTS_PER_MINUTE,
            max_tokens_per_request=settings.AI_MAX_TOKENS_PER_REQUEST,
            default_analysis_level=AnalysisLevel.COMPREHENSIVE
        )

    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get config: {str(e)}"
        )


@router.post("/config", response_model=AIAnalysisConfig)
async def update_analysis_config(
    config_update: AIAnalysisConfigUpdate
):
    """
    AI分析の設定を更新
    """
    try:
        # 注意: 本来は設定ファイルやデータベースを更新する必要がある
        # ここでは現在の設定を返すのみ
        logger.info("AI analysis config update requested")

        return AIAnalysisConfig(
            enabled=config_update.enabled if config_update.enabled is not None else settings.AI_ANALYSIS_ENABLED,
            model_name=config_update.model_name or settings.AI_DEFAULT_MODEL,
            backup_model=config_update.backup_model or settings.AI_BACKUP_MODEL,
            max_requests_per_minute=config_update.max_requests_per_minute or settings.AI_MAX_REQUESTS_PER_MINUTE,
            max_tokens_per_request=config_update.max_tokens_per_request or settings.AI_MAX_TOKENS_PER_REQUEST,
            default_analysis_level=config_update.default_analysis_level or AnalysisLevel.COMPREHENSIVE
        )

    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update config: {str(e)}"
        )


@router.get("/health")
async def ai_analysis_health(
    analyzer: AIContentAnalyzer = Depends(get_ai_analyzer)
):
    """
    AI分析機能のヘルスチェック
    """
    try:
        health_status = {
            "status": "healthy" if analyzer.client else "unhealthy",
            "gemini_available": analyzer.client is not None,
            "api_key_configured": bool(analyzer.api_key),
            "model_name": analyzer.model_name,
            "request_history_size": len(analyzer.request_history),
            "last_check": datetime.utcnow().isoformat()
        }

        if analyzer.client:
            health_status["message"] = "AI analysis service is operational"
        else:
            health_status["message"] = "AI analysis service is not available"
            health_status["details"] = "Gemini client not initialized or API key missing"

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}",
            "last_check": datetime.utcnow().isoformat()
        }