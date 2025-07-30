"""
ABDSシステム - Webスクレイピングサービス
robots.txt対応・JavaScript対応のWebコンテンツ抽出
"""

import asyncio
import json
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple, TYPE_CHECKING
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import httpx

# 型チェック時のみインポート（IDE警告回避）
if TYPE_CHECKING:
    import aiohttp
    from bs4 import BeautifulSoup, Comment
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
    from readability import Document

# 条件付きインポート - パッケージが利用可能な場合のみインポート
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    from bs4 import BeautifulSoup, Comment
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from readability import Document
    READABILITY_AVAILABLE = True
except ImportError:
    READABILITY_AVAILABLE = False

logger = logging.getLogger(__name__)


class ScrapedContent:
    """スクレイピング結果を格納するデータクラス"""

    def __init__(self):
        self.url: str = ""
        self.title: str = ""
        self.meta_description: str = ""
        self.content_text: str = ""
        self.clean_text: str = ""
        self.images: List[Dict[str, str]] = []
        self.structured_data: List[Dict] = []
        self.meta_data: Dict[str, str] = {}
        self.status_code: int = 0
        self.content_type: str = ""
        self.content_length: int = 0
        self.encoding: str = ""
        self.language: str = ""
        self.scraped_at: datetime = datetime.utcnow()
        self.processing_time_ms: int = 0
        self.javascript_rendered: bool = False
        self.robots_allowed: bool = True
        self.error_message: Optional[str] = None


class WebScraper:
    """高機能Webスクレイピングクラス"""

    def __init__(self):
        self.session = None
        self.driver = None
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ABDSBot/1.0"
        )
        self.timeout = 30
        self.max_content_length = 10 * 1024 * 1024  # 10MB
        self.robots_cache: Dict[str, RobotFileParser] = {}

        # スクレイピング対象の除外パターン
        self.excluded_domains = {
            'localhost', '127.0.0.1', '0.0.0.0',
            'facebook.com', 'instagram.com', 'twitter.com', 'x.com',
            'linkedin.com', 'tiktok.com', 'youtube.com'
        }

        # JavaScriptが必要なサイトのパターン
        self.js_required_patterns = [
            r'.*\.react\..*',
            r'.*\.angular\..*',
            r'.*\.vue\..*',
            r'.*spa\..*',
            r'.*app\..*'
        ]

    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        await self._init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        await self._cleanup()

    async def _init_session(self):
        """HTTPセッションの初期化"""
        if AIOHTTP_AVAILABLE:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )

            timeout = aiohttp.ClientTimeout(total=self.timeout)

            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers
            )
        else:
            # httpxを代替として使用
            self.session = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    'User-Agent': self.user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )

    async def _cleanup(self):
        """リソースのクリーンアップ"""
        if self.session:
            if AIOHTTP_AVAILABLE:
                await self.session.close()
            else:
                await self.session.aclose()
        if self.driver and SELENIUM_AVAILABLE:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Driver cleanup error: {e}")

    def _init_selenium_driver(self):
        """Seleniumドライバーの初期化"""
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium is not available")

        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')
            options.add_argument('--disable-javascript-harmony-shipping')
            options.add_argument(f'--user-agent={self.user_agent}')

            # メモリ使用量を削減
            options.add_argument('--memory-pressure-off')
            options.add_argument('--max_old_space_size=4096')

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(self.timeout)

            return driver

        except Exception as e:
            logger.error(f"Selenium driver initialization failed: {e}")
            raise

    async def _check_robots_txt(self, url: str) -> bool:
        """robots.txtをチェックしてアクセス許可を確認"""
        try:
            parsed_url = urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

            # キャッシュチェック
            if domain in self.robots_cache:
                rp = self.robots_cache[domain]
            else:
                rp = RobotFileParser()
                robots_url = urljoin(domain, '/robots.txt')

                try:
                    if AIOHTTP_AVAILABLE:
                        async with self.session.get(robots_url, timeout=10) as response:
                            if response.status == 200:
                                robots_content = await response.text()
                                rp.set_url(robots_url)
                                rp.feed(robots_content)
                            else:
                                # robots.txtが見つからない場合は許可とみなす
                                return True
                    else:
                        response = await self.session.get(robots_url, timeout=10)
                        if response.status_code == 200:
                            robots_content = response.text
                            rp.set_url(robots_url)
                            rp.feed(robots_content)
                        else:
                            # robots.txtが見つからない場合は許可とみなす
                            return True
                except Exception as e:
                    logger.debug(f"robots.txt fetch failed for {domain}: {e}")
                    return True

                self.robots_cache[domain] = rp

            # User-Agentに基づいてアクセス許可をチェック
            return rp.can_fetch('ABDSBot', url) or rp.can_fetch('*', url)

        except Exception as e:
            logger.warning(f"robots.txt check failed for {url}: {e}")
            return True

    def _is_javascript_required(self, url: str, html_content: str) -> bool:
        """JavaScriptレンダリングが必要かどうかを判定"""
        try:
            # Seleniumが利用できない場合は常にFalse
            if not SELENIUM_AVAILABLE:
                return False

            # URLパターンによる判定
            for pattern in self.js_required_patterns:
                if re.match(pattern, url, re.IGNORECASE):
                    return True

            # HTMLコンテンツによる判定
            if not html_content or not BS4_AVAILABLE:
                return False

            soup = BeautifulSoup(html_content, 'html.parser')

            # 明らかにJavaScriptが必要な場合
            js_indicators = [
                soup.find_all('script', src=True),
                soup.find_all('script', string=lambda text: text and ('react' in text.lower() or 'angular' in text.lower() or 'vue' in text.lower())),
                soup.find_all(attrs={'data-reactroot': True}),
                soup.find_all(attrs={'ng-app': True}),
                soup.find_all(attrs={'v-app': True}),
            ]

            # スクリプトタグが多い場合
            script_tags = soup.find_all('script')
            if len(script_tags) > 10:
                return True

            # コンテンツが少なすぎる場合
            text_content = soup.get_text(strip=True)
            if len(text_content) < 500:
                return True

            return any(js_indicators)

        except Exception as e:
            logger.warning(f"JavaScript requirement check failed: {e}")
            return False

    async def _fetch_with_requests(self, url: str) -> Tuple[str, Dict]:
        """通常のHTTPリクエストでコンテンツを取得"""
        try:
            if AIOHTTP_AVAILABLE:
                async with self.session.get(url, allow_redirects=True) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}: {response.reason}")

                    content_type = response.headers.get('content-type', '')
                    if not content_type.startswith('text/html'):
                        raise Exception(f"Unsupported content type: {content_type}")

                    content_length = int(response.headers.get('content-length', 0))
                    if content_length > self.max_content_length:
                        raise Exception(f"Content too large: {content_length} bytes")

                    html_content = await response.text()

                    metadata = {
                        'status_code': response.status,
                        'content_type': content_type,
                        'content_length': len(html_content),
                        'encoding': response.charset or 'utf-8',
                        'final_url': str(response.url)
                    }

                    return html_content, metadata
            else:
                # httpxを使用
                response = await self.session.get(url, follow_redirects=True)
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}: {response.reason_phrase}")

                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('text/html'):
                    raise Exception(f"Unsupported content type: {content_type}")

                content_length = int(response.headers.get('content-length', 0))
                if content_length > self.max_content_length:
                    raise Exception(f"Content too large: {content_length} bytes")

                html_content = response.text

                metadata = {
                    'status_code': response.status_code,
                    'content_type': content_type,
                    'content_length': len(html_content),
                    'encoding': response.encoding or 'utf-8',
                    'final_url': str(response.url)
                }

                return html_content, metadata

        except Exception as e:
            logger.error(f"HTTP fetch failed for {url}: {e}")
            raise

    def _fetch_with_selenium(self, url: str) -> Tuple[str, Dict]:
        """Seleniumを使用してJavaScriptレンダリング付きでコンテンツを取得"""
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium is not available")

        try:
            if not self.driver:
                self.driver = self._init_selenium_driver()

            self.driver.get(url)

            # ページの読み込み完了を待つ
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # 動的コンテンツの読み込みを待つ
            time.sleep(2)

            html_content = self.driver.page_source
            current_url = self.driver.current_url

            metadata = {
                'status_code': 200,  # Seleniumでは正確なステータスコードが取得できない
                'content_type': 'text/html',
                'content_length': len(html_content),
                'encoding': 'utf-8',
                'final_url': current_url,
                'javascript_rendered': True
            }

            return html_content, metadata

        except Exception as e:
            if SELENIUM_AVAILABLE and isinstance(e, (TimeoutException, WebDriverException)):
                if isinstance(e, TimeoutException):
                    raise Exception("Page load timeout")
                else:
                    raise Exception(f"Selenium error: {e}")
            else:
                raise Exception(f"Selenium error: {e}")

    def _extract_structured_data(self, soup) -> List[Dict]:
        """構造化データ（JSON-LD）を抽出"""
        structured_data = []

        if not BS4_AVAILABLE:
            return structured_data

        try:
            # JSON-LD形式の構造化データ
            json_ld_scripts = soup.find_all('script', type='application/ld+json')

            for script in json_ld_scripts:
                try:
                    if script.string:
                        data = json.loads(script.string)
                        structured_data.append({
                            'type': 'json-ld',
                            'data': data
                        })
                except json.JSONDecodeError:
                    continue

            # Open Graph メタデータ
            og_data = {}
            og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
            for tag in og_tags:
                property_name = tag.get('property', '').replace('og:', '')
                content = tag.get('content', '')
                if property_name and content:
                    og_data[property_name] = content

            if og_data:
                structured_data.append({
                    'type': 'open-graph',
                    'data': og_data
                })

            # Twitter Card メタデータ
            twitter_data = {}
            twitter_tags = soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')})
            for tag in twitter_tags:
                name = tag.get('name', '').replace('twitter:', '')
                content = tag.get('content', '')
                if name and content:
                    twitter_data[name] = content

            if twitter_data:
                structured_data.append({
                    'type': 'twitter-card',
                    'data': twitter_data
                })

        except Exception as e:
            logger.warning(f"Structured data extraction failed: {e}")

        return structured_data

    def _extract_images(self, soup, base_url: str) -> List[Dict[str, str]]:
        """画像とalt属性を抽出"""
        images = []

        if not BS4_AVAILABLE:
            return images

        try:
            img_tags = soup.find_all('img')

            for img in img_tags:
                src = img.get('src', '')
                alt = img.get('alt', '')
                title = img.get('title', '')

                if src:
                    # 相対URLを絶対URLに変換
                    full_url = urljoin(base_url, src)

                    images.append({
                        'src': full_url,
                        'alt': alt,
                        'title': title,
                        'width': img.get('width', ''),
                        'height': img.get('height', '')
                    })

        except Exception as e:
            logger.warning(f"Image extraction failed: {e}")

        return images

    def _extract_meta_data(self, soup) -> Dict[str, str]:
        """メタデータを抽出"""
        meta_data = {}

        if not BS4_AVAILABLE:
            return meta_data

        try:
            # 基本的なメタタグ
            meta_tags = soup.find_all('meta')

            for tag in meta_tags:
                name = tag.get('name', '') or tag.get('property', '') or tag.get('http-equiv', '')
                content = tag.get('content', '')

                if name and content:
                    meta_data[name] = content

            # 特別なメタデータ
            canonical_link = soup.find('link', rel='canonical')
            if canonical_link:
                meta_data['canonical'] = canonical_link.get('href', '')

            # 言語情報
            html_tag = soup.find('html')
            if html_tag:
                lang = html_tag.get('lang', '')
                if lang:
                    meta_data['language'] = lang

        except Exception as e:
            logger.warning(f"Meta data extraction failed: {e}")

        return meta_data

    def _clean_text(self, text: str) -> str:
        """テキストのクリーニング"""
        if not text:
            return ""

        # 余分な空白を削除
        text = re.sub(r'\s+', ' ', text)
        # 先頭・末尾の空白を削除
        text = text.strip()
        # 制御文字を削除
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

        return text

    async def fetch_content(self, url: str, use_javascript: Optional[bool] = None) -> ScrapedContent:
        """
        指定URLからコンテンツを抽出

        Args:
            url: 抽出対象のURL
            use_javascript: JavaScriptレンダリングを強制するか（None=自動判定）

        Returns:
            ScrapedContent: 抽出されたコンテンツ
        """
        result = ScrapedContent()
        result.url = url
        start_time = time.time()

        try:
            # URLの検証
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid URL format")

            if parsed_url.netloc in self.excluded_domains:
                raise ValueError(f"Domain {parsed_url.netloc} is excluded from scraping")

            # セッションの初期化
            if not self.session:
                await self._init_session()

            # robots.txtのチェック
            result.robots_allowed = await self._check_robots_txt(url)
            if not result.robots_allowed:
                raise ValueError("Robots.txt disallows scraping this URL")

            # 最初に通常のHTTPリクエストを試行
            html_content = ""
            metadata = {}

            try:
                html_content, metadata = await self._fetch_with_requests(url)
                result.javascript_rendered = False

                # JavaScriptが必要かどうかを判定
                needs_js = use_javascript
                if needs_js is None:
                    needs_js = self._is_javascript_required(url, html_content)

                # JavaScriptレンダリングが必要な場合はSeleniumを使用
                if needs_js:
                    logger.info(f"Using Selenium for JavaScript rendering: {url}")
                    html_content, metadata = self._fetch_with_selenium(url)
                    result.javascript_rendered = True

            except Exception as e:
                # 通常のリクエストが失敗した場合はSeleniumを試行
                logger.warning(f"HTTP request failed, trying Selenium: {e}")
                html_content, metadata = self._fetch_with_selenium(url)
                result.javascript_rendered = True

            # メタデータをセット
            result.status_code = metadata.get('status_code', 0)
            result.content_type = metadata.get('content_type', '')
            result.content_length = metadata.get('content_length', 0)
            result.encoding = metadata.get('encoding', '')

            # HTMLパース（BeautifulSoupが利用可能な場合のみ）
            if BS4_AVAILABLE:
                soup = BeautifulSoup(html_content, 'html.parser')

                # タイトル抽出
                title_tag = soup.find('title')
                if title_tag:
                    result.title = self._clean_text(title_tag.get_text())

                # メタディスクリプション抽出
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc:
                    result.meta_description = self._clean_text(meta_desc.get('content', ''))

                # 本文テキスト抽出（readabilityを使用）
                if READABILITY_AVAILABLE:
                    try:
                        doc = Document(html_content)
                        result.content_text = self._clean_text(doc.summary())
                        result.clean_text = self._clean_text(doc.get_clean_html())
                    except Exception:
                        # readabilityが失敗した場合は通常のテキスト抽出
                        for script in soup(["script", "style"]):
                            script.decompose()
                        result.content_text = self._clean_text(soup.get_text())
                else:
                    # readabilityが利用できない場合は通常のテキスト抽出
                    for script in soup(["script", "style"]):
                        script.decompose()
                    result.content_text = self._clean_text(soup.get_text())

                # 画像情報抽出
                result.images = self._extract_images(soup, url)

                # 構造化データ抽出
                result.structured_data = self._extract_structured_data(soup)

                # メタデータ抽出
                result.meta_data = self._extract_meta_data(soup)
            else:
                # BeautifulSoupが利用できない場合の簡易的な抽出
                import re

                # タイトル抽出
                title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
                if title_match:
                    result.title = self._clean_text(title_match.group(1))

                # メタディスクリプション抽出
                meta_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', html_content, re.IGNORECASE)
                if meta_match:
                    result.meta_description = self._clean_text(meta_match.group(1))

                # 簡易的なテキスト抽出
                text_content = re.sub(r'<[^>]+>', '', html_content)
                result.content_text = self._clean_text(text_content)

            # 言語情報
            if result.meta_data.get('language'):
                result.language = result.meta_data['language']

            # 処理時間計算
            result.processing_time_ms = int((time.time() - start_time) * 1000)

            logger.info(f"Successfully scraped {url} in {result.processing_time_ms}ms")

        except Exception as e:
            result.error_message = str(e)
            result.processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Scraping failed for {url}: {e}")

        return result

    async def fetch_multiple(self, urls: List[str], max_concurrent: int = 5) -> List[ScrapedContent]:
        """
        複数URLを並行してスクレイピング

        Args:
            urls: URL一覧
            max_concurrent: 最大同時実行数

        Returns:
            List[ScrapedContent]: スクレイピング結果一覧
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def scrape_with_semaphore(url: str) -> ScrapedContent:
            async with semaphore:
                return await self.fetch_content(url)

        tasks = [scrape_with_semaphore(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=False)


async def get_web_scraper() -> WebScraper:
    """WebScraper インスタンスの取得"""
    return WebScraper()