"""
ABDSシステム - 脅威度スコアリングAPIエンドポイント
総合的な脅威度評価と分析機能
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse

# 条件付きインポート
try:
    from app.services.threat_scorer import ThreatScorer, get_threat_scorer
    from app.schemas.analysis import (
        ThreatAssessment,
        ThreatAssessmentRequest,
        ThreatAssessmentResponse,
        BatchThreatAssessmentRequest,
        BatchThreatAssessmentResponse,
        ThreatScoreStatistics,
        ThreatScoreConfig,
        ThreatAssessmentSummary,
        ThreatLevel,
        ComponentScore,
        ThreatComponents,
        ScoreMetadata
    )
    THREAT_SCORING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Threat scoring components not available: {e}")
    THREAT_SCORING_AVAILABLE = False

logger = logging.getLogger(__name__)

# ルーター初期化
router = APIRouter(prefix="/threat-scoring", tags=["脅威度スコアリング"])

# 統計データ（インメモリ - 本番環境ではRedisやDBを使用）
threat_stats = {
    'total_assessments': 0,
    'assessments_by_level': {level: 0 for level in ThreatLevel},
    'average_score': 0.0,
    'assessment_history': []
}


@router.post("/assess", response_model=ThreatAssessmentResponse)
async def assess_threat(
    request: ThreatAssessmentRequest,
    background_tasks: BackgroundTasks,
    scorer: ThreatScorer = Depends(get_threat_scorer)
) -> ThreatAssessmentResponse:
    """
    脅威度評価を実行

    ドメイン信頼度、AI分析結果、その他要因を統合して総合脅威スコアを算出
    """
    if not THREAT_SCORING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="脅威度スコアリングサービスが利用できません"
        )

    request_id = str(uuid.uuid4())
    start_time = datetime.utcnow()

    try:
        logger.info(f"Starting threat assessment: {request_id}")

        # 脅威度スコア計算
        raw_result = scorer.calculate_score(
            domain_data=request.domain_data,
            ai_analysis=request.ai_analysis,
            search_data=request.search_data,
            content_data=request.content_data
        )

        # エラーチェック
        if raw_result.get('error'):
            return ThreatAssessmentResponse(
                success=False,
                error=raw_result['error'],
                request_id=request_id
            )

        # スキーマ形式に変換
        assessment = _convert_to_threat_assessment(raw_result, request)

        # 統計更新（バックグラウンド）
        background_tasks.add_task(
            _update_statistics,
            assessment.overall_score,
            assessment.threat_level
        )

        # 成功レスポンス
        response = ThreatAssessmentResponse(
            success=True,
            assessment=assessment,
            request_id=request_id
        )

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(f"Threat assessment completed: {request_id} in {processing_time:.2f}ms")

        return response

    except Exception as e:
        logger.error(f"Threat assessment failed: {request_id} - {e}")
        return ThreatAssessmentResponse(
            success=False,
            error=f"脅威度評価エラー: {str(e)}",
            request_id=request_id
        )


@router.post("/assess-batch", response_model=BatchThreatAssessmentResponse)
async def assess_threat_batch(
    request: BatchThreatAssessmentRequest,
    background_tasks: BackgroundTasks,
    scorer: ThreatScorer = Depends(get_threat_scorer)
) -> BatchThreatAssessmentResponse:
    """
    バッチ脅威度評価を実行

    複数の評価リクエストを並列処理で効率的に処理
    """
    if not THREAT_SCORING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="脅威度スコアリングサービスが利用できません"
        )

    start_time = datetime.utcnow()
    total_count = len(request.assessments)

    try:
        logger.info(f"Starting batch threat assessment: {total_count} items")

        if request.parallel_processing:
            # 並列処理
            tasks = [
                _process_single_assessment(assessment_req, scorer, i)
                for i, assessment_req in enumerate(request.assessments)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # 順次処理
            results = []
            for i, assessment_req in enumerate(request.assessments):
                result = await _process_single_assessment(assessment_req, scorer, i)
                results.append(result)

        # 結果集計
        success_count = sum(1 for r in results if isinstance(r, ThreatAssessmentResponse) and r.success)
        failed_count = total_count - success_count

        # 例外をエラーレスポンスに変換
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ThreatAssessmentResponse(
                    success=False,
                    error=f"評価エラー: {str(result)}",
                    request_id=f"batch_item_{i}"
                ))
            else:
                processed_results.append(result)

        # 統計更新（バックグラウンド）
        successful_assessments = [
            r.assessment for r in processed_results
            if r.success and r.assessment
        ]
        if successful_assessments:
            background_tasks.add_task(
                _update_batch_statistics,
                successful_assessments
            )

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        response = BatchThreatAssessmentResponse(
            success=failed_count == 0,
            total_count=total_count,
            success_count=success_count,
            failed_count=failed_count,
            results=processed_results,
            processing_time_ms=int(processing_time)
        )

        logger.info(f"Batch threat assessment completed: {success_count}/{total_count} successful")
        return response

    except Exception as e:
        logger.error(f"Batch threat assessment failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"バッチ脅威度評価エラー: {str(e)}"
        )


@router.get("/statistics", response_model=ThreatScoreStatistics)
async def get_threat_statistics() -> ThreatScoreStatistics:
    """脅威スコア統計情報を取得"""

    if not THREAT_SCORING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="脅威度スコアリングサービスが利用できません"
        )

    try:
        # 統計情報計算
        assessment_history = threat_stats.get('assessment_history', [])

        # スコア分布計算
        score_distribution = {}
        total_score = 0
        scores = []

        for assessment in assessment_history:
            level = assessment.get('threat_level')
            if level in score_distribution:
                score_distribution[level] += 1
            else:
                score_distribution[level] = 1

            score = assessment.get('overall_score', 0)
            total_score += score
            scores.append(score)

        # 平均・中央値計算
        total_assessments = len(assessment_history)
        average_score = total_score / total_assessments if total_assessments > 0 else 0.0

        scores.sort()
        median_score = scores[len(scores) // 2] if scores else 0.0

        # 高リスクドメイン抽出
        high_risk_domains = [
            assessment.get('domain', 'unknown')
            for assessment in assessment_history[-50:]  # 最新50件
            if assessment.get('threat_level') == ThreatLevel.HIGH
        ]

        # 期間別トレンド（簡易版）
        now = datetime.utcnow()
        last_24h = [
            a for a in assessment_history
            if datetime.fromisoformat(a.get('calculated_at', '2024-01-01T00:00:00'))
            > now - timedelta(hours=24)
        ]
        last_7d = [
            a for a in assessment_history
            if datetime.fromisoformat(a.get('calculated_at', '2024-01-01T00:00:00'))
            > now - timedelta(days=7)
        ]

        score_trend = {
            'last_24h': sum(a.get('overall_score', 0) for a in last_24h) / len(last_24h) if last_24h else 0,
            'last_7d': sum(a.get('overall_score', 0) for a in last_7d) / len(last_7d) if last_7d else 0,
            'all_time': average_score
        }

        return ThreatScoreStatistics(
            total_assessments=total_assessments,
            score_distribution=score_distribution,
            average_score=round(average_score, 2),
            median_score=round(median_score, 2),
            score_trend=score_trend,
            high_risk_domains=list(set(high_risk_domains))[:10]  # 重複除去、上位10件
        )

    except Exception as e:
        logger.error(f"Failed to get threat statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"統計情報取得エラー: {str(e)}"
        )


@router.get("/config", response_model=ThreatScoreConfig)
async def get_threat_scoring_config(
    scorer: ThreatScorer = Depends(get_threat_scorer)
) -> ThreatScoreConfig:
    """脅威度スコアリング設定を取得"""

    if not THREAT_SCORING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="脅威度スコアリングサービスが利用できません"
        )

    try:
        threshold_settings = {
            ThreatLevel.SAFE: {"min_score": 0, "max_score": 39},
            ThreatLevel.LOW: {"min_score": 40, "max_score": 59},
            ThreatLevel.MEDIUM: {"min_score": 60, "max_score": 79},
            ThreatLevel.HIGH: {"min_score": 80, "max_score": 100}
        }

        return ThreatScoreConfig(
            weights=scorer.weights,
            domain_weights=scorer.domain_weights,
            ai_weights=scorer.ai_weights,
            other_weights=scorer.other_weights,
            threshold_settings=threshold_settings
        )

    except Exception as e:
        logger.error(f"Failed to get threat scoring config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"設定取得エラー: {str(e)}"
        )


@router.get("/summary")
async def get_threat_assessment_summary(
    period: str = Query("7d", description="サマリー期間 (24h, 7d, 30d)")
) -> ThreatAssessmentSummary:
    """脅威評価サマリーを取得"""

    if not THREAT_SCORING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="脅威度スコアリングサービスが利用できません"
        )

    try:
        # 期間フィルタリング
        now = datetime.utcnow()
        if period == "24h":
            cutoff = now - timedelta(hours=24)
        elif period == "7d":
            cutoff = now - timedelta(days=7)
        elif period == "30d":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = now - timedelta(days=7)  # デフォルト

        assessment_history = threat_stats.get('assessment_history', [])
        period_assessments = [
            a for a in assessment_history
            if datetime.fromisoformat(a.get('calculated_at', '2024-01-01T00:00:00')) > cutoff
        ]

        # 脅威レベル別集計
        threat_level_counts = {}
        total_processing_time = 0
        risk_factor_counts = {}

        for assessment in period_assessments:
            # 脅威レベル集計
            level = assessment.get('threat_level')
            threat_level_counts[level] = threat_level_counts.get(level, 0) + 1

            # 処理時間集計
            total_processing_time += assessment.get('processing_time_ms', 0)

            # リスク要因集計
            for factor in assessment.get('risk_factors', []):
                risk_factor_counts[factor] = risk_factor_counts.get(factor, 0) + 1

        # 上位リスク要因
        top_risk_factors = [
            {"factor": factor, "count": count}
            for factor, count in sorted(risk_factor_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        # 改善提案生成
        improvement_suggestions = _generate_improvement_suggestions(
            period_assessments, threat_level_counts
        )

        return ThreatAssessmentSummary(
            summary_period=period,
            total_assessments=len(period_assessments),
            threat_level_counts=threat_level_counts,
            average_processing_time=total_processing_time / len(period_assessments) if period_assessments else 0,
            top_risk_factors=top_risk_factors,
            improvement_suggestions=improvement_suggestions
        )

    except Exception as e:
        logger.error(f"Failed to get threat summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"サマリー取得エラー: {str(e)}"
        )


@router.get("/health")
async def threat_scoring_health() -> Dict[str, Any]:
    """脅威度スコアリングサービスのヘルスチェック"""

    return {
        "service": "threat_scoring",
        "status": "healthy" if THREAT_SCORING_AVAILABLE else "unavailable",
        "components": {
            "threat_scorer": THREAT_SCORING_AVAILABLE,
            "analysis_schemas": THREAT_SCORING_AVAILABLE
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# ヘルパー関数

async def _process_single_assessment(
    request: ThreatAssessmentRequest,
    scorer: ThreatScorer,
    index: int
) -> ThreatAssessmentResponse:
    """単一の脅威度評価を処理"""
    request_id = f"batch_item_{index}"

    try:
        raw_result = scorer.calculate_score(
            domain_data=request.domain_data,
            ai_analysis=request.ai_analysis,
            search_data=request.search_data,
            content_data=request.content_data
        )

        if raw_result.get('error'):
            return ThreatAssessmentResponse(
                success=False,
                error=raw_result['error'],
                request_id=request_id
            )

        assessment = _convert_to_threat_assessment(raw_result, request)

        return ThreatAssessmentResponse(
            success=True,
            assessment=assessment,
            request_id=request_id
        )

    except Exception as e:
        return ThreatAssessmentResponse(
            success=False,
            error=f"評価エラー: {str(e)}",
            request_id=request_id
        )


def _convert_to_threat_assessment(
    raw_result: Dict[str, Any],
    request: ThreatAssessmentRequest
) -> ThreatAssessment:
    """ThreatScorerの結果をThreatAssessmentスキーマに変換"""

    components_data = raw_result.get('components', {})

    # ComponentScore オブジェクト作成
    domain_trust = ComponentScore(
        score=components_data.get('domain_trust', {}).get('score', 0),
        weight=components_data.get('domain_trust', {}).get('weight', 0),
        contribution=components_data.get('domain_trust', {}).get('contribution', 0)
    )

    ai_analysis = ComponentScore(
        score=components_data.get('ai_analysis', {}).get('score', 0),
        weight=components_data.get('ai_analysis', {}).get('weight', 0),
        contribution=components_data.get('ai_analysis', {}).get('contribution', 0)
    )

    other_factors = ComponentScore(
        score=components_data.get('other_factors', {}).get('score', 0),
        weight=components_data.get('other_factors', {}).get('weight', 0),
        contribution=components_data.get('other_factors', {}).get('contribution', 0)
    )

    components = ThreatComponents(
        domain_trust=domain_trust,
        ai_analysis=ai_analysis,
        other_factors=other_factors
    )

    # メタデータ作成
    metadata = None
    if request.include_metadata:
        metadata = ScoreMetadata(
            data_completeness=_calculate_data_completeness(request),
            reliability_score=raw_result.get('confidence', 0.5),
            calculation_time_ms=0,  # 別途設定
            factors_analyzed=_count_analyzed_factors(request)
        )

    return ThreatAssessment(
        overall_score=raw_result.get('overall_score', 50.0),
        threat_level=ThreatLevel(raw_result.get('threat_level', 'UNKNOWN')),
        confidence=raw_result.get('confidence', 0.5),
        components=components,
        risk_factors=raw_result.get('risk_factors', []),
        recommendations=raw_result.get('recommendations', []),
        metadata=metadata,
        calculated_at=datetime.fromisoformat(raw_result.get('calculated_at', datetime.utcnow().isoformat())),
        error_message=raw_result.get('error')
    )


def _calculate_data_completeness(request: ThreatAssessmentRequest) -> float:
    """データ完全性を計算"""
    total_fields = 4  # domain_data, ai_analysis, search_data, content_data
    non_empty_fields = 0

    if request.domain_data:
        non_empty_fields += 1
    if request.ai_analysis:
        non_empty_fields += 1
    if request.search_data:
        non_empty_fields += 1
    if request.content_data:
        non_empty_fields += 1

    return non_empty_fields / total_fields


def _count_analyzed_factors(request: ThreatAssessmentRequest) -> int:
    """分析した要因の数を計算"""
    factor_count = 0

    # ドメイン要因
    domain_data = request.domain_data
    if domain_data.get('creation_date'):
        factor_count += 1
    if domain_data.get('ssl_info'):
        factor_count += 1
    if domain_data.get('whois_info'):
        factor_count += 1

    # AI分析要因
    ai_analysis = request.ai_analysis
    if ai_analysis.get('abuse_detection'):
        factor_count += 1
    if ai_analysis.get('copyright_infringement'):
        factor_count += 1
    if ai_analysis.get('commercial_use'):
        factor_count += 1

    # その他要因
    search_data = request.search_data
    content_data = request.content_data
    if search_data.get('ranking'):
        factor_count += 1
    if content_data.get('similarity_score'):
        factor_count += 1
    if content_data.get('last_updated'):
        factor_count += 1

    return factor_count


async def _update_statistics(score: float, threat_level: ThreatLevel):
    """統計情報を更新"""
    try:
        threat_stats['total_assessments'] += 1
        threat_stats['assessments_by_level'][threat_level] += 1

        # 評価履歴に追加
        assessment_record = {
            'overall_score': score,
            'threat_level': threat_level,
            'calculated_at': datetime.utcnow().isoformat()
        }

        threat_stats['assessment_history'].append(assessment_record)

        # 履歴サイズ制限（最新1000件のみ保持）
        if len(threat_stats['assessment_history']) > 1000:
            threat_stats['assessment_history'] = threat_stats['assessment_history'][-1000:]

        # 平均スコア更新
        all_scores = [a['overall_score'] for a in threat_stats['assessment_history']]
        threat_stats['average_score'] = sum(all_scores) / len(all_scores) if all_scores else 0

    except Exception as e:
        logger.error(f"Failed to update statistics: {e}")


async def _update_batch_statistics(assessments: List[ThreatAssessment]):
    """バッチ統計情報を更新"""
    try:
        for assessment in assessments:
            await _update_statistics(assessment.overall_score, assessment.threat_level)
    except Exception as e:
        logger.error(f"Failed to update batch statistics: {e}")


def _generate_improvement_suggestions(
    assessments: List[Dict],
    threat_level_counts: Dict[str, int]
) -> List[str]:
    """改善提案を生成"""
    suggestions = []

    total = len(assessments)
    if total == 0:
        return ["評価データが不足しています"]

    high_risk_ratio = threat_level_counts.get(ThreatLevel.HIGH, 0) / total
    medium_risk_ratio = threat_level_counts.get(ThreatLevel.MEDIUM, 0) / total

    if high_risk_ratio > 0.3:
        suggestions.append("高リスクコンテンツが多く検出されています。フィルタリング強化を検討してください")

    if medium_risk_ratio > 0.5:
        suggestions.append("中リスクコンテンツの割合が高いです。追加の検証プロセスを導入してください")

    # よく見つかるリスク要因に基づく提案
    common_factors = {}
    for assessment in assessments:
        for factor in assessment.get('risk_factors', []):
            common_factors[factor] = common_factors.get(factor, 0) + 1

    if common_factors.get('新規ドメイン（30日以内）', 0) > total * 0.3:
        suggestions.append("新規ドメインからの検出が多いです。ドメイン年齢フィルタの導入を検討してください")

    if common_factors.get('SSL証明書なし', 0) > total * 0.2:
        suggestions.append("SSL証明書のないサイトが多く検出されています。HTTPS必須ポリシーを検討してください")

    if not suggestions:
        suggestions.append("現在の検出状況は良好です。継続的な監視を維持してください")

    return suggestions


# 条件付きエクスポート
if THREAT_SCORING_AVAILABLE:
    __all__ = ["router"]
else:
    router = APIRouter()  # 空のルーター
    __all__ = ["router"]