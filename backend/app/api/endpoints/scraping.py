"""
ABDSシステム - Webスクレイピング API
スクレイピング・コンテンツ抽出のAPIエンドポイント
"""

import asyncio
import logging
import time
from typing import List
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.services.web_scraper import WebScraper, get_web_scraper, ScrapedContent
from app.schemas.scraping import (
    ScrapingRequest,
    ScrapingResponse,
    ScrapedContentData,
    BulkScrapingRequest,
    BulkScrapingResponse,
    BulkScrapingResult,
    ContentAnalysisRequest,
    ContentAnalysisResponse,
    ContentAnalysisData,
    RobotsCheckRequest,
    RobotsCheckResponse,
    ScrapingStatsResponse,
    ImageInfo,
    StructuredData,
    ScrapingMode
)

logger = logging.getLogger(__name__)

router = APIRouter()


def convert_scraped_content_to_schema(content: ScrapedContent) -> ScrapedContentData:
    """ScrapedContentをPydanticスキーマに変換"""

    # 画像情報の変換
    images = [
        ImageInfo(
            src=img.get('src', ''),
            alt=img.get('alt', ''),
            title=img.get('title', ''),
            width=img.get('width', ''),
            height=img.get('height', '')
        )
        for img in content.images
    ]

    # 構造化データの変換
    structured_data = [
        StructuredData(type=data.get('type', ''), data=data.get('data', {}))
        for data in content.structured_data
    ]

    return ScrapedContentData(
        url=content.url,
        title=content.title,
        meta_description=content.meta_description,
        content_text=content.content_text,
        clean_text=content.clean_text,
        images=images,
        structured_data=structured_data,
        meta_data=content.meta_data,
        status_code=content.status_code,
        content_type=content.content_type,
        content_length=content.content_length,
        encoding=content.encoding,
        language=content.language,
        scraped_at=content.scraped_at,
        processing_time_ms=content.processing_time_ms,
        javascript_rendered=content.javascript_rendered,
        robots_allowed=content.robots_allowed,
        error_message=content.error_message
    )


@router.post("/scrape", response_model=ScrapingResponse)
async def scrape_url(request: ScrapingRequest):
    """
    単一URLのスクレイピング

    - **url**: スクレイピング対象のURL
    - **mode**: スクレイピングモード（auto/simple/javascript）
    - **extract_images**: 画像情報を抽出するか
    - **extract_structured_data**: 構造化データを抽出するか
    - **timeout**: タイムアウト秒数
    - **respect_robots**: robots.txtを尊重するか
    """
    try:
        start_time = time.time()

        async with WebScraper() as scraper:
            scraper.timeout = request.timeout

            # スクレイピングモードに応じて処理
            use_javascript = None
            if request.mode == ScrapingMode.SIMPLE:
                use_javascript = False
            elif request.mode == ScrapingMode.JAVASCRIPT:
                use_javascript = True

            # スクレイピング実行
            content = await scraper.fetch_content(
                str(request.url),
                use_javascript=use_javascript
            )

            # 必要に応じて情報を除外
            if not request.extract_images:
                content.images = []
            if not request.extract_structured_data:
                content.structured_data = []

            # robots.txtチェック
            if request.respect_robots and not content.robots_allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="robots.txtによりアクセスが禁止されています"
                )

            # エラーがある場合の処理
            if content.error_message:
                logger.warning(f"Scraping completed with errors: {content.error_message}")

            execution_time_ms = int((time.time() - start_time) * 1000)
            result = convert_scraped_content_to_schema(content)

            return ScrapingResponse(
                success=True,
                message="スクレイピングが完了しました",
                data=result,
                execution_time_ms=execution_time_ms
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scraping error for {request.url}: {str(e)}")
        execution_time_ms = int((time.time() - start_time) * 1000)

        return ScrapingResponse(
            success=False,
            message=f"スクレイピング中にエラーが発生しました: {str(e)}",
            data=None,
            execution_time_ms=execution_time_ms
        )


@router.post("/scrape-bulk", response_model=BulkScrapingResponse)
async def scrape_multiple_urls(request: BulkScrapingRequest):
    """
    複数URLの一括スクレイピング

    - **urls**: スクレイピング対象URL群（最大20個）
    - **mode**: スクレイピングモード
    - **max_concurrent**: 最大同時実行数
    - その他のオプションは単一URLと同様
    """
    try:
        start_time = time.time()

        async with WebScraper() as scraper:
            scraper.timeout = request.timeout

            # 並行スクレイピング実行
            urls = [str(url) for url in request.urls]
            contents = await scraper.fetch_multiple(urls, max_concurrent=request.max_concurrent)

            # 結果の処理
            results = []
            processed = 0
            failed = 0

            for url, content in zip(urls, contents):
                try:
                    # robots.txtチェック
                    if request.respect_robots and not content.robots_allowed:
                        results.append(BulkScrapingResult(
                            url=url,
                            success=False,
                            data=None,
                            error="robots.txtによりアクセスが禁止されています"
                        ))
                        failed += 1
                        continue

                    # 必要に応じて情報を除外
                    if not request.extract_images:
                        content.images = []
                    if not request.extract_structured_data:
                        content.structured_data = []

                    result_data = convert_scraped_content_to_schema(content)

                    results.append(BulkScrapingResult(
                        url=url,
                        success=True,
                        data=result_data,
                        error=content.error_message
                    ))

                    if content.error_message:
                        failed += 1
                    else:
                        processed += 1

                except Exception as e:
                    results.append(BulkScrapingResult(
                        url=url,
                        success=False,
                        data=None,
                        error=str(e)
                    ))
                    failed += 1

            total_execution_time_ms = int((time.time() - start_time) * 1000)

            return BulkScrapingResponse(
                success=True,
                message=f"一括スクレイピングが完了しました（成功: {processed}件、失敗: {failed}件）",
                processed=processed,
                failed=failed,
                results=results,
                total_execution_time_ms=total_execution_time_ms
            )

    except Exception as e:
        logger.error(f"Bulk scraping error: {str(e)}")
        total_execution_time_ms = int((time.time() - start_time) * 1000)

        return BulkScrapingResponse(
            success=False,
            message=f"一括スクレイピング中にエラーが発生しました: {str(e)}",
            processed=0,
            failed=len(request.urls),
            results=[],
            total_execution_time_ms=total_execution_time_ms
        )


@router.post("/analyze", response_model=ContentAnalysisResponse)
async def analyze_content(request: ContentAnalysisRequest):
    """
    URLのコンテンツを分析

    - **url**: 分析対象URL
    - **analyze_sentiment**: 感情分析を実行するか
    - **extract_keywords**: キーワード抽出を実行するか
    - **analyze_readability**: 可読性分析を実行するか
    - **detect_language**: 言語検出を実行するか
    """
    try:
        start_time = time.time()

        # まずスクレイピングを実行
        async with WebScraper() as scraper:
            content = await scraper.fetch_content(str(request.url))

            if content.error_message:
                raise Exception(f"スクレイピングエラー: {content.error_message}")

            # コンテンツ分析の実行
            analysis_data = await _analyze_text_content(
                content.content_text,
                request
            )

            scraping_data = convert_scraped_content_to_schema(content)
            execution_time_ms = int((time.time() - start_time) * 1000)

            return ContentAnalysisResponse(
                success=True,
                message="コンテンツ分析が完了しました",
                scraping_data=scraping_data,
                analysis_data=analysis_data,
                execution_time_ms=execution_time_ms
            )

    except Exception as e:
        logger.error(f"Content analysis error for {request.url}: {str(e)}")
        execution_time_ms = int((time.time() - start_time) * 1000)

        return ContentAnalysisResponse(
            success=False,
            message=f"コンテンツ分析中にエラーが発生しました: {str(e)}",
            scraping_data=None,
            analysis_data=None,
            execution_time_ms=execution_time_ms
        )


@router.post("/robots-check", response_model=RobotsCheckResponse)
async def check_robots_txt(request: RobotsCheckRequest):
    """
    robots.txtをチェック

    - **url**: チェック対象URL
    - **user_agent**: User-Agent名
    """
    try:
        from urllib.parse import urljoin, urlparse
        from urllib.robotparser import RobotFileParser
        from datetime import datetime

        try:
            import aiohttp
            AIOHTTP_AVAILABLE = True
        except ImportError:
            import httpx
            AIOHTTP_AVAILABLE = False

        parsed_url = urlparse(str(request.url))
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        robots_url = urljoin(domain, '/robots.txt')

        # robots.txtを取得
        if AIOHTTP_AVAILABLE:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(robots_url, timeout=10) as response:
                        if response.status == 200:
                            robots_content = await response.text()

                            # robots.txtをパース
                            rp = RobotFileParser()
                            rp.set_url(robots_url)
                            rp.feed(robots_content)

                            # アクセス許可をチェック
                            allowed = rp.can_fetch(request.user_agent, str(request.url))
                            crawl_delay = rp.crawl_delay(request.user_agent)

                            return RobotsCheckResponse(
                                success=True,
                                message="robots.txtのチェックが完了しました",
                                url=str(request.url),
                                robots_url=robots_url,
                                allowed=allowed,
                                robots_content=robots_content,
                                crawl_delay=crawl_delay,
                                checked_at=datetime.utcnow()
                            )
                        else:
                            # robots.txtが見つからない場合は許可とみなす
                            return RobotsCheckResponse(
                                success=True,
                                message="robots.txtが見つからないため、アクセス許可とみなします",
                                url=str(request.url),
                                robots_url=robots_url,
                                allowed=True,
                                robots_content=None,
                                crawl_delay=None,
                                checked_at=datetime.utcnow()
                            )
                except Exception as e:
                    # アクセスエラーの場合も許可とみなす
                    return RobotsCheckResponse(
                        success=True,
                        message=f"robots.txtにアクセスできないため、許可とみなします: {str(e)}",
                        url=str(request.url),
                        robots_url=robots_url,
                        allowed=True,
                        robots_content=None,
                        crawl_delay=None,
                        checked_at=datetime.utcnow()
                    )
        else:
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(robots_url, timeout=10)
                    if response.status_code == 200:
                        robots_content = response.text

                        # robots.txtをパース
                        rp = RobotFileParser()
                        rp.set_url(robots_url)
                        rp.feed(robots_content)

                        # アクセス許可をチェック
                        allowed = rp.can_fetch(request.user_agent, str(request.url))
                        crawl_delay = rp.crawl_delay(request.user_agent)

                        return RobotsCheckResponse(
                            success=True,
                            message="robots.txtのチェックが完了しました",
                            url=str(request.url),
                            robots_url=robots_url,
                            allowed=allowed,
                            robots_content=robots_content,
                            crawl_delay=crawl_delay,
                            checked_at=datetime.utcnow()
                        )
                    else:
                        # robots.txtが見つからない場合は許可とみなす
                        return RobotsCheckResponse(
                            success=True,
                            message="robots.txtが見つからないため、アクセス許可とみなします",
                            url=str(request.url),
                            robots_url=robots_url,
                            allowed=True,
                            robots_content=None,
                            crawl_delay=None,
                            checked_at=datetime.utcnow()
                        )
                except Exception as e:
                    # アクセスエラーの場合も許可とみなす
                    return RobotsCheckResponse(
                        success=True,
                        message=f"robots.txtにアクセスできないため、許可とみなします: {str(e)}",
                        url=str(request.url),
                        robots_url=robots_url,
                        allowed=True,
                        robots_content=None,
                        crawl_delay=None,
                        checked_at=datetime.utcnow()
                    )

    except Exception as e:
        logger.error(f"Robots check error for {request.url}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"robots.txtチェック中にエラーが発生しました: {str(e)}"
        )


@router.get("/stats", response_model=ScrapingStatsResponse)
async def get_scraping_stats():
    """
    スクレイピング統計情報を取得
    """
    try:
        from datetime import datetime

        # 基本的な統計情報
        stats_data = {
            "service_status": "active",
            "supported_modes": ["auto", "simple", "javascript"],
            "max_concurrent_requests": 10,
            "max_urls_per_bulk": 20,
            "default_timeout": 30,
            "selenium_available": False,  # 条件付きインポートのため動的に判定が必要
            "last_updated": datetime.utcnow().isoformat(),
            "features": {
                "robots_txt_respect": True,
                "javascript_rendering": True,
                "structured_data_extraction": True,
                "image_extraction": True,
                "content_analysis": True
            }
        }

        return ScrapingStatsResponse(
            success=True,
            message="スクレイピング統計情報を取得しました",
            data=stats_data
        )

    except Exception as e:
        logger.error(f"Get scraping stats error: {str(e)}")
        return ScrapingStatsResponse(
            success=False,
            message=f"統計情報取得中にエラーが発生しました: {str(e)}",
            data={}
        )


async def _analyze_text_content(text: str, request: ContentAnalysisRequest) -> ContentAnalysisData:
    """テキストコンテンツの分析"""
    from datetime import datetime
    import re

    # 基本的な統計
    text_length = len(text)
    words = re.findall(r'\b\w+\b', text)
    word_count = len(words)
    sentences = re.split(r'[.!?]+', text)
    sentence_count = len([s for s in sentences if s.strip()])
    paragraphs = text.split('\n\n')
    paragraph_count = len([p for p in paragraphs if p.strip()])

    # 簡単な言語検出（より高度な分析には外部ライブラリが必要）
    detected_language = "ja" if any('\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' or '\u4E00' <= char <= '\u9FAF' for char in text) else "en"
    confidence_score = 0.8  # 簡易実装のため固定値

    # キーワード抽出（簡易版）
    keywords = []
    if request.extract_keywords and words:
        # 頻出単語を抽出（より高度な分析には形態素解析が必要）
        word_freq = {}
        for word in words:
            if len(word) > 3:  # 短い単語は除外
                word_lower = word.lower()
                word_freq[word_lower] = word_freq.get(word_lower, 0) + 1

        # 上位10個のキーワードを抽出
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        keywords = [word for word, freq in keywords]

    # 感情分析（簡易版 - より高度な分析には専用ライブラリが必要）
    sentiment_score = None
    sentiment_label = None
    if request.analyze_sentiment:
        # 簡易的なポジティブ/ネガティブ単語カウント
        positive_words = ["good", "great", "excellent", "amazing", "wonderful", "良い", "素晴らしい", "最高"]
        negative_words = ["bad", "terrible", "awful", "horrible", "worst", "悪い", "ひどい", "最悪"]

        positive_count = sum(1 for word in words if word.lower() in positive_words)
        negative_count = sum(1 for word in words if word.lower() in negative_words)

        if positive_count + negative_count > 0:
            sentiment_score = (positive_count - negative_count) / (positive_count + negative_count)
            if sentiment_score > 0.1:
                sentiment_label = "positive"
            elif sentiment_score < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"

    # 可読性分析（簡易版）
    readability_score = None
    if request.analyze_readability and sentence_count > 0:
        # 簡易的な可読性スコア（文の平均長）
        avg_sentence_length = word_count / sentence_count
        readability_score = max(0, min(100, 100 - (avg_sentence_length - 10) * 2))

    return ContentAnalysisData(
        url=str(request.url),
        text_length=text_length,
        word_count=word_count,
        sentence_count=sentence_count,
        paragraph_count=paragraph_count,
        detected_language=detected_language,
        confidence_score=confidence_score,
        keywords=keywords,
        sentiment_score=sentiment_score,
        sentiment_label=sentiment_label,
        readability_score=readability_score,
        analyzed_at=datetime.utcnow()
    )