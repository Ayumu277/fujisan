"""
ABDSシステム - 画像検索サービス
Google画像検索とSerpAPIを使用した類似画像検索
"""

import os
import base64
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path

import httpx
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import serpapi

from app.core.config import settings
from app.utils.rate_limiter import RateLimiter


logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """検索結果のデータクラス"""
    title: str
    url: str
    thumbnail_url: str
    source_domain: str
    similarity_score: float = 0.0
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[str] = None


class ImageSearchService(ABC):
    """画像検索サービスの抽象基底クラス"""
    
    def __init__(self, api_key: str, rate_limit: int = 100):
        """
        Args:
            api_key: API キー
            rate_limit: 1日あたりのレート制限（デフォルト: 100）
        """
        self.api_key = api_key
        self.rate_limiter = RateLimiter(limit=rate_limit, window=86400)  # 24時間
        
    @abstractmethod
    async def search_similar_images(
        self, 
        image_path: str, 
        max_results: int = 10
    ) -> List[SearchResult]:
        """
        類似画像を検索
        
        Args:
            image_path: 検索対象の画像パス
            max_results: 最大結果数
            
        Returns:
            検索結果のリスト
            
        Raises:
            RateLimitExceededError: レート制限に達した場合
            SearchAPIError: 検索API呼び出しに失敗した場合
        """
        pass
    
    @abstractmethod
    def get_service_name(self) -> str:
        """サービス名を取得"""
        pass
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """画像をBase64エンコード"""
        try:
            with open(image_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"画像のBase64エンコードに失敗: {e}")
            raise SearchAPIError(f"画像エンコードエラー: {e}")


class GoogleImageSearchService(ImageSearchService):
    """Google Custom Search APIを使用した画像検索サービス"""
    
    def __init__(self, api_key: str, search_engine_id: str, rate_limit: int = 100):
        """
        Args:
            api_key: Google API キー
            search_engine_id: Custom Search Engine ID
            rate_limit: 1日あたりのレート制限
        """
        super().__init__(api_key, rate_limit)
        self.search_engine_id = search_engine_id
        self.service = None
        
    def _get_service(self):
        """Google Custom Search サービスを取得"""
        if self.service is None:
            try:
                self.service = build(
                    'customsearch', 
                    'v1', 
                    developerKey=self.api_key,
                    cache_discovery=False
                )
            except Exception as e:
                logger.error(f"Google Custom Search サービスの初期化に失敗: {e}")
                raise SearchAPIError(f"Google API初期化エラー: {e}")
        return self.service
    
    async def search_similar_images(
        self, 
        image_path: str, 
        max_results: int = 10
    ) -> List[SearchResult]:
        """
        Google Custom Search APIで類似画像を検索
        """
        # レート制限チェック
        if not await self.rate_limiter.acquire():
            raise RateLimitExceededError("Google検索APIのレート制限に達しました")
        
        try:
            # 画像をBase64エンコード
            image_base64 = self._encode_image_to_base64(image_path)
            
            # Google Custom Search API呼び出し
            service = self._get_service()
            
            # 注意: Google Custom Search APIは画像による検索を直接サポートしていないため、
            # 実際の実装では、画像の特徴量を抽出してテキスト検索に変換するか、
            # Google Vision APIと組み合わせる必要があります。
            # ここではプレースホルダー実装を提供します。
            
            # TODO: 実際の実装では以下を行う：
            # 1. Google Vision APIで画像のラベルを取得
            # 2. そのラベルを使ってCustom Search APIで検索
            # 3. 類似度スコアを計算
            
            results = []
            
            # プレースホルダー検索（実際の実装では適切なクエリを生成）
            search_query = "similar image"
            
            response = service.cse().list(
                q=search_query,
                cx=self.search_engine_id,
                searchType='image',
                num=min(max_results, 10),
                safe='medium'
            ).execute()
            
            items = response.get('items', [])
            
            for i, item in enumerate(items):
                try:
                    result = SearchResult(
                        title=item.get('title', ''),
                        url=item.get('link', ''),
                        thumbnail_url=item.get('image', {}).get('thumbnailLink', ''),
                        source_domain=self._extract_domain(item.get('displayLink', '')),
                        similarity_score=1.0 - (i * 0.1),  # 順位ベースの仮スコア
                        width=item.get('image', {}).get('width'),
                        height=item.get('image', {}).get('height'),
                        file_size=item.get('image', {}).get('byteSize')
                    )
                    results.append(result)
                except Exception as e:
                    logger.warning(f"検索結果の解析でエラー: {e}")
                    continue
            
            logger.info(f"Google検索完了: {len(results)}件の結果")
            return results
            
        except HttpError as e:
            logger.error(f"Google API HTTPエラー: {e}")
            raise SearchAPIError(f"Google API エラー: {e}")
        except Exception as e:
            logger.error(f"Google検索処理中にエラー: {e}")
            raise SearchAPIError(f"検索処理エラー: {e}")
    
    def get_service_name(self) -> str:
        return "Google Custom Search"
    
    def _extract_domain(self, url: str) -> str:
        """URLからドメインを抽出"""
        try:
            if url.startswith('www.'):
                return url[4:]
            return url
        except:
            return url


class SerpAPISearchService(ImageSearchService):
    """SerpAPIを使用した画像検索サービス"""
    
    def __init__(self, api_key: str, rate_limit: int = 100):
        super().__init__(api_key, rate_limit)
        
    async def search_similar_images(
        self, 
        image_path: str, 
        max_results: int = 10
    ) -> List[SearchResult]:
        """
        SerpAPIで類似画像を検索
        """
        # レート制限チェック
        if not await self.rate_limiter.acquire():
            raise RateLimitExceededError("SerpAPIのレート制限に達しました")
        
        try:
            # 画像をBase64エンコード
            image_base64 = self._encode_image_to_base64(image_path)
            
            # SerpAPI検索パラメータ
            params = {
                "engine": "google_reverse_image",
                "image_data": image_base64,
                "api_key": self.api_key,
                "num": min(max_results, 100)
            }
            
            # SerpAPI呼び出し
            search = serpapi.GoogleSearch(params)
            response = search.get_dict()
            
            results = []
            
            # 逆画像検索結果を処理
            inline_images = response.get('inline_images', [])
            
            for i, item in enumerate(inline_images):
                try:
                    result = SearchResult(
                        title=item.get('title', ''),
                        url=item.get('original', ''),
                        thumbnail_url=item.get('thumbnail', ''),
                        source_domain=self._extract_domain_from_url(item.get('source', '')),
                        similarity_score=1.0 - (i * 0.05),  # 順位ベースの仮スコア
                        width=item.get('original_width'),
                        height=item.get('original_height')
                    )
                    results.append(result)
                    
                    if len(results) >= max_results:
                        break
                        
                except Exception as e:
                    logger.warning(f"SerpAPI結果の解析でエラー: {e}")
                    continue
            
            # 類似画像検索結果も処理
            visual_matches = response.get('visual_matches', [])
            
            for i, item in enumerate(visual_matches):
                if len(results) >= max_results:
                    break
                    
                try:
                    result = SearchResult(
                        title=item.get('title', ''),
                        url=item.get('link', ''),
                        thumbnail_url=item.get('thumbnail', ''),
                        source_domain=self._extract_domain_from_url(item.get('source', '')),
                        similarity_score=0.8 - (i * 0.05),  # 視覚的一致の仮スコア
                        width=None,
                        height=None
                    )
                    results.append(result)
                    
                except Exception as e:
                    logger.warning(f"SerpAPI視覚的一致結果の解析でエラー: {e}")
                    continue
            
            logger.info(f"SerpAPI検索完了: {len(results)}件の結果")
            return results
            
        except Exception as e:
            logger.error(f"SerpAPI検索処理中にエラー: {e}")
            raise SearchAPIError(f"SerpAPI検索エラー: {e}")
    
    def get_service_name(self) -> str:
        return "SerpAPI"
    
    def _extract_domain_from_url(self, url: str) -> str:
        """URLからドメインを抽出"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return url


# =================================
# 例外クラス
# =================================

class SearchAPIError(Exception):
    """検索API関連のエラー"""
    pass


class RateLimitExceededError(SearchAPIError):
    """レート制限エラー"""
    pass


# =================================
# ファクトリー関数
# =================================

def create_image_search_service(service_type: str = "serpapi") -> ImageSearchService:
    """
    画像検索サービスのファクトリー関数
    
    Args:
        service_type: "google" または "serpapi"
        
    Returns:
        ImageSearchService インスタンス
        
    Raises:
        ValueError: 無効なservice_type
        SearchAPIError: API設定エラー
    """
    if service_type.lower() == "google":
        api_key = getattr(settings, 'GOOGLE_API_KEY', None)
        search_engine_id = getattr(settings, 'GOOGLE_SEARCH_ENGINE_ID', None)
        
        if not api_key or not search_engine_id:
            raise SearchAPIError("Google API設定が不完全です")
            
        return GoogleImageSearchService(
            api_key=api_key,
            search_engine_id=search_engine_id,
            rate_limit=100
        )
        
    elif service_type.lower() == "serpapi":
        api_key = getattr(settings, 'SERPAPI_KEY', None)
        
        if not api_key:
            raise SearchAPIError("SerpAPI設定が不完全です")
            
        return SerpAPISearchService(
            api_key=api_key,
            rate_limit=100
        )
        
    else:
        raise ValueError(f"無効なservice_type: {service_type}")


# =================================
# Celeryタスク（コメント実装）
# =================================

# TODO: Celery統合のための実装例
# 
# from celery import Celery
# from app.core.celery_app import celery_app
# 
# @celery_app.task(bind=True)
# def search_similar_images_task(self, image_id: str, service_type: str = "serpapi"):
#     """
#     非同期画像検索タスク
#     
#     Args:
#         image_id: 画像ID
#         service_type: 検索サービスタイプ
#         
#     Returns:
#         タスク結果
#     """
#     try:
#         # 1. データベースから画像情報を取得
#         from app.models import Image
#         from app.core.database import SessionLocal
#         
#         db = SessionLocal()
#         image = db.query(Image).filter(Image.id == image_id).first()
#         
#         if not image:
#             raise ValueError(f"画像が見つかりません: {image_id}")
#         
#         # 2. 画像検索サービスを作成
#         search_service = create_image_search_service(service_type)
#         
#         # 3. 画像検索を実行
#         results = await search_service.search_similar_images(
#             image_path=image.file_path,
#             max_results=20
#         )
#         
#         # 4. 結果をデータベースに保存
#         from app.models import SearchResult as DBSearchResult
#         from app.models import ThreatLevel
#         
#         for result in results:
#             db_result = DBSearchResult(
#                 image_id=image_id,
#                 found_url=result.url,
#                 domain=result.source_domain,
#                 similarity_score=result.similarity_score,
#                 is_official=False,  # TODO: 公式サイト判定ロジック
#                 threat_level=ThreatLevel.SAFE,  # TODO: 脅威レベル判定
#                 analyzed_at=datetime.utcnow()
#             )
#             db.add(db_result)
#         
#         # 5. 画像ステータスを更新
#         image.status = ImageStatus.COMPLETED
#         db.commit()
#         
#         return {
#             "status": "completed",
#             "results_count": len(results),
#             "image_id": image_id
#         }
#         
#     except Exception as e:
#         logger.error(f"画像検索タスクでエラー: {e}")
#         
#         # エラー時は画像ステータスを失敗に更新
#         if image:
#             image.status = ImageStatus.FAILED
#             db.commit()
#         
#         # Celeryタスクの再試行
#         raise self.retry(exc=e, countdown=60, max_retries=3)
#         
#     finally:
#         db.close()
