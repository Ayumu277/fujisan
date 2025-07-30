"""
ABDSシステム - AI分析サービス
Gemini APIを使用したコンテンツ分析機能
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import httpx

# 条件付きインポート
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from app.core.config import settings
from app.prompts.analysis_prompt import AnalysisPromptBuilder, ANALYSIS_LEVELS

logger = logging.getLogger(__name__)


class AnalysisResult:
    """AI分析結果を格納するデータクラス"""

    def __init__(self):
        self.abuse_detection: Dict[str, Any] = {}
        self.copyright_infringement: Dict[str, Any] = {}
        self.commercial_use: Dict[str, Any] = {}
        self.unauthorized_repost: Dict[str, Any] = {}
        self.content_modification: Dict[str, Any] = {}
        self.overall_assessment: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self.raw_response: str = ""
        self.processing_time_ms: int = 0
        self.error_message: Optional[str] = None
        self.analyzed_at: datetime = datetime.utcnow()


class AIContentAnalyzer:
    """Gemini APIを使用したコンテンツ分析クラス"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'GEMINI_API_KEY', None)
        self.model_name = "gemini-1.5-pro"
        self.backup_model = "gemini-1.5-flash"
        self.client = None
        self.prompt_builder = AnalysisPromptBuilder()

        # レート制限設定
        self.max_requests_per_minute = 15
        self.max_tokens_per_request = 32000
        self.request_history: List[datetime] = []

        # 分析設定
        self.generation_config = {
            "temperature": 0.1,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 4096,
        }

        # 安全性設定
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]

        self._init_client()

    def _init_client(self):
        """Gemini クライアントの初期化"""
        if not GEMINI_AVAILABLE:
            logger.warning("Google Generative AI library not available")
            return

        if not self.api_key:
            logger.warning("Gemini API key not configured")
            return

        try:
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            logger.info(f"Gemini client initialized with model: {self.model_name}")

        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.client = None

    async def _check_rate_limit(self) -> bool:
        """レート制限をチェック"""
        now = datetime.utcnow()

        # 1分以内のリクエスト履歴をフィルタ
        self.request_history = [
            req_time for req_time in self.request_history
            if (now - req_time).total_seconds() < 60
        ]

        if len(self.request_history) >= self.max_requests_per_minute:
            logger.warning("Rate limit exceeded, waiting...")
            return False

        self.request_history.append(now)
        return True

    async def _make_gemini_request(
        self,
        prompt: str,
        model_name: Optional[str] = None
    ) -> str:
        """Gemini APIリクエストを実行"""
        if not self.client:
            raise Exception("Gemini client not initialized")

        # レート制限チェック
        if not await self._check_rate_limit():
            await asyncio.sleep(60)  # 1分待機

        try:
            # 使用するモデルの選択
            if model_name and model_name != self.model_name:
                client = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=self.generation_config,
                    safety_settings=self.safety_settings
                )
            else:
                client = self.client

            # プロンプトの長さをチェック
            if len(prompt) > self.max_tokens_per_request:
                logger.warning(f"Prompt too long ({len(prompt)} chars), truncating...")
                prompt = prompt[:self.max_tokens_per_request]

            # 非同期リクエスト実行
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.generate_content(prompt)
            )

            if not response.text:
                raise Exception("Empty response from Gemini API")

            return response.text

        except Exception as e:
            logger.error(f"Gemini API request failed: {e}")

            # バックアップモデルで再試行
            if model_name != self.backup_model:
                logger.info(f"Retrying with backup model: {self.backup_model}")
                return await self._make_gemini_request(prompt, self.backup_model)

            raise

    def _parse_analysis_response(self, response_text: str) -> AnalysisResult:
        """分析レスポンスをパース"""
        result = AnalysisResult()
        result.raw_response = response_text

        try:
            # JSONブロックを抽出
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # JSONブロックがない場合は全体をJSONとして解析を試行
                json_text = response_text.strip()

            # JSONパース
            data = json.loads(json_text)

            # 分析結果を抽出
            analysis_result = data.get('analysis_result', {})

            result.abuse_detection = analysis_result.get('abuse_detection', {})
            result.copyright_infringement = analysis_result.get('copyright_infringement', {})
            result.commercial_use = analysis_result.get('commercial_use', {})
            result.unauthorized_repost = analysis_result.get('unauthorized_repost', {})
            result.content_modification = analysis_result.get('content_modification', {})
            result.overall_assessment = data.get('overall_assessment', {})
            result.metadata = data.get('metadata', {})

            # 信頼度スコアの検証
            self._validate_confidence_scores(result)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            result.error_message = f"Response parsing failed: {e}"

            # フォールバック: テキスト解析
            self._parse_text_response(response_text, result)

        except Exception as e:
            logger.error(f"Unexpected error parsing response: {e}")
            result.error_message = f"Parsing error: {e}"

        return result

    def _validate_confidence_scores(self, result: AnalysisResult):
        """信頼度スコアの妥当性をチェック"""
        categories = [
            result.abuse_detection,
            result.copyright_infringement,
            result.commercial_use,
            result.unauthorized_repost,
            result.content_modification
        ]

        for category in categories:
            confidence = category.get('confidence', 0)
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                category['confidence'] = 0.5  # デフォルト値
                logger.warning("Invalid confidence score detected, using default")

    def _parse_text_response(self, response_text: str, result: AnalysisResult):
        """JSONパースが失敗した場合のテキスト解析フォールバック"""
        try:
            # キーワードベースの簡易分析
            text_lower = response_text.lower()

            # 悪用検出
            abuse_keywords = ['高リスク', 'high risk', '詐欺', 'fraud', 'phishing']
            abuse_risk = 'high' if any(keyword in text_lower for keyword in abuse_keywords) else 'low'

            result.abuse_detection = {
                'risk_level': abuse_risk,
                'confidence': 0.3,
                'evidence': ['テキスト解析による推定'],
                'details': 'JSON解析失敗のためテキスト解析を使用'
            }

            # 著作権侵害
            copyright_keywords = ['著作権', 'copyright', '侵害', 'infringement']
            copyright_risk = 'high' if any(keyword in text_lower for keyword in copyright_keywords) else 'low'

            result.copyright_infringement = {
                'probability': copyright_risk,
                'confidence': 0.3,
                'evidence': ['テキスト解析による推定'],
                'details': 'JSON解析失敗のためテキスト解析を使用'
            }

            # 総合評価
            result.overall_assessment = {
                'threat_level': 'medium',
                'risk_score': 50,
                'summary': 'JSON解析失敗のため詳細分析不可',
                'recommendations': ['詳細な手動確認を推奨']
            }

        except Exception as e:
            logger.error(f"Text parsing fallback failed: {e}")

    async def analyze_content(
        self,
        html_content: str,
        image_context: Dict,
        analysis_level: str = 'comprehensive',
        focus_areas: Optional[List[str]] = None
    ) -> AnalysisResult:
        """
        コンテンツの包括的AI分析を実行

        Args:
            html_content: 分析対象のHTMLコンテンツ
            image_context: 画像のコンテキスト情報
            analysis_level: 分析レベル (basic, comprehensive, copyright_focused, abuse_focused)
            focus_areas: 特定の分析領域にフォーカス

        Returns:
            AnalysisResult: 分析結果
        """
        start_time = datetime.utcnow()
        result = AnalysisResult()

        try:
            if not self.client:
                raise Exception("Gemini client not available")

            # 分析設定の取得
            level_config = ANALYSIS_LEVELS.get(analysis_level, ANALYSIS_LEVELS['comprehensive'])
            if not focus_areas:
                focus_areas = level_config['focus_areas']

            # プロンプト生成
            prompt = self.prompt_builder.build_comprehensive_prompt(
                html_content=html_content,
                image_context=image_context,
                focus_areas=focus_areas
            )

            logger.info(f"Starting AI analysis with level: {analysis_level}")

            # Gemini API リクエスト
            response_text = await self._make_gemini_request(prompt)

            # レスポンス解析
            result = self._parse_analysis_response(response_text)

            # 処理時間計算
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.processing_time_ms = int(processing_time)

            logger.info(f"AI analysis completed in {result.processing_time_ms}ms")

        except Exception as e:
            result.error_message = str(e)
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.processing_time_ms = int(processing_time)
            logger.error(f"AI analysis failed: {e}")

        return result

    async def analyze_focused(
        self,
        analysis_type: str,
        html_content: str,
        image_context: Dict
    ) -> AnalysisResult:
        """
        特定分野に特化した分析を実行

        Args:
            analysis_type: 分析タイプ (abuse, copyright, commercial, repost, modification)
            html_content: HTMLコンテンツ
            image_context: 画像コンテキスト

        Returns:
            AnalysisResult: 分析結果
        """
        start_time = datetime.utcnow()
        result = AnalysisResult()

        try:
            if not self.client:
                raise Exception("Gemini client not available")

            # 特化プロンプト生成
            prompt = self.prompt_builder.build_focused_prompt(
                analysis_type=analysis_type,
                html_content=html_content,
                image_context=image_context
            )

            logger.info(f"Starting focused AI analysis: {analysis_type}")

            # Gemini API リクエスト
            response_text = await self._make_gemini_request(prompt)

            # レスポンス解析
            result = self._parse_analysis_response(response_text)

            # 処理時間計算
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.processing_time_ms = int(processing_time)

            logger.info(f"Focused AI analysis completed in {result.processing_time_ms}ms")

        except Exception as e:
            result.error_message = str(e)
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.processing_time_ms = int(processing_time)
            logger.error(f"Focused AI analysis failed: {e}")

        return result

    async def batch_analyze(
        self,
        analyses: List[Dict[str, Any]],
        max_concurrent: int = 3
    ) -> List[AnalysisResult]:
        """
        複数コンテンツの並行分析

        Args:
            analyses: 分析リクエストリスト
            max_concurrent: 最大同時実行数

        Returns:
            List[AnalysisResult]: 分析結果リスト
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_semaphore(analysis_data: Dict) -> AnalysisResult:
            async with semaphore:
                return await self.analyze_content(**analysis_data)

        tasks = [analyze_with_semaphore(data) for data in analyses]
        return await asyncio.gather(*tasks, return_exceptions=False)

    def get_analysis_summary(self, result: AnalysisResult) -> Dict[str, Any]:
        """分析結果のサマリーを生成"""
        if result.error_message:
            return {
                'status': 'error',
                'error': result.error_message,
                'analyzed_at': result.analyzed_at.isoformat()
            }

        # リスクスコア計算
        risk_scores = []

        if result.abuse_detection.get('confidence', 0) > 0.5:
            abuse_risk = result.abuse_detection.get('risk_level', '').lower()
            if '高' in abuse_risk or 'high' in abuse_risk:
                risk_scores.append(90)
            elif '中' in abuse_risk or 'medium' in abuse_risk:
                risk_scores.append(60)
            else:
                risk_scores.append(30)

        if result.copyright_infringement.get('confidence', 0) > 0.5:
            copyright_risk = result.copyright_infringement.get('probability', '').lower()
            if '高' in copyright_risk or 'high' in copyright_risk:
                risk_scores.append(85)
            elif '中' in copyright_risk or 'medium' in copyright_risk:
                risk_scores.append(55)
            else:
                risk_scores.append(25)

        overall_risk = max(risk_scores) if risk_scores else 0

        return {
            'status': 'completed',
            'overall_risk_score': overall_risk,
            'threat_level': result.overall_assessment.get('threat_level', 'unknown'),
            'key_findings': {
                'abuse_risk': result.abuse_detection.get('risk_level'),
                'copyright_risk': result.copyright_infringement.get('probability'),
                'commercial_use': result.commercial_use.get('status'),
                'unauthorized_repost': result.unauthorized_repost.get('status'),
                'modification_level': result.content_modification.get('level')
            },
            'recommendations': result.overall_assessment.get('recommendations', []),
            'processing_time_ms': result.processing_time_ms,
            'analyzed_at': result.analyzed_at.isoformat()
        }


async def get_ai_analyzer() -> AIContentAnalyzer:
    """AI分析器インスタンスの取得"""
    return AIContentAnalyzer()