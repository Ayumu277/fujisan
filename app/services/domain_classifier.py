"""
ABDSシステム - ドメイン分類サービス
URLドメインの安全性判定とホワイトリスト管理
"""

import logging
import re
import socket
import ssl
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import asyncio
import httpx
import tldextract
import whois
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.whitelist_domain import WhitelistDomain
from app.models.enums import ThreatLevel

logger = logging.getLogger(__name__)


class DomainInfo:
    """ドメイン情報を格納するデータクラス"""

    def __init__(self):
        self.domain: str = ""
        self.subdomain: str = ""
        self.tld: str = ""
        self.is_whitelisted: bool = False
        self.whois_data: Optional[Dict] = None
        self.ssl_info: Optional[Dict] = None
        self.threat_level: ThreatLevel = ThreatLevel.MEDIUM
        self.confidence_score: float = 0.0
        self.analysis_timestamp: datetime = datetime.utcnow()
        self.error_message: Optional[str] = None


class DomainClassifier:
    """ドメイン分類・判定クラス"""

    def __init__(self, db: Session):
        self.db = db
        self.whois_cache: Dict[str, Dict] = {}
        self.cache_ttl = timedelta(hours=24)

        # 既知の安全なドメインパターン
        self.safe_patterns = [
            r'.*\.google\.com$',
            r'.*\.youtube\.com$',
            r'.*\.wikipedia\.org$',
            r'.*\.github\.com$',
            r'.*\.stackoverflow\.com$',
        ]

        # 疑わしいドメインパターン
        self.suspicious_patterns = [
            r'.*\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}.*',  # IPアドレス直接指定
            r'.*[0-9]{10,}.*',  # 長い数字列
            r'.*[-_.]{3,}.*',  # 連続するハイフンやアンダースコア
            r'.*\.(tk|ml|ga|cf)$',  # 無料ドメイン
        ]

    async def classify_domain(self, url: str) -> DomainInfo:
        """
        URLのドメインを分析・分類する

        Args:
            url: 分析対象のURL

        Returns:
            DomainInfo: ドメイン分析結果
        """
        domain_info = DomainInfo()

        try:
            # URLからドメイン抽出
            extracted = self._extract_domain_parts(url)
            if not extracted:
                domain_info.error_message = "Invalid URL format"
                domain_info.threat_level = ThreatLevel.HIGH
                return domain_info

            domain_info.domain = extracted['domain']
            domain_info.subdomain = extracted['subdomain']
            domain_info.tld = extracted['tld']

            # ホワイトリストチェック
            domain_info.is_whitelisted = await self._check_whitelist(domain_info.domain)

            if domain_info.is_whitelisted:
                domain_info.threat_level = ThreatLevel.SAFE
                domain_info.confidence_score = 1.0
                return domain_info

            # 並行してドメイン情報を取得
            tasks = [
                self._get_whois_info(domain_info.domain),
                self._get_ssl_info(domain_info.domain),
                self._analyze_domain_patterns(domain_info.domain)
            ]

            whois_data, ssl_info, pattern_analysis = await asyncio.gather(
                *tasks, return_exceptions=True
            )

            # 結果を統合
            if not isinstance(whois_data, Exception):
                domain_info.whois_data = whois_data
            if not isinstance(ssl_info, Exception):
                domain_info.ssl_info = ssl_info
            if not isinstance(pattern_analysis, Exception):
                threat_level, confidence = pattern_analysis
                domain_info.threat_level = threat_level
                domain_info.confidence_score = confidence

            # 総合判定
            domain_info = self._calculate_final_threat_level(domain_info)

        except Exception as e:
            logger.error(f"Domain classification error for {url}: {str(e)}")
            domain_info.error_message = str(e)
            domain_info.threat_level = ThreatLevel.MEDIUM

        return domain_info

    def _extract_domain_parts(self, url: str) -> Optional[Dict[str, str]]:
        """URLからドメイン部分を抽出"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            parsed = urlparse(url)
            if not parsed.netloc:
                return None

            extracted = tldextract.extract(parsed.netloc)

            return {
                'subdomain': extracted.subdomain,
                'domain': f"{extracted.domain}.{extracted.suffix}",
                'tld': extracted.suffix
            }
        except Exception as e:
            logger.error(f"Domain extraction error: {str(e)}")
            return None

    async def _check_whitelist(self, domain: str) -> bool:
        """ホワイトリストとの照合"""
        try:
            whitelist_entry = self.db.query(WhitelistDomain).filter(
                WhitelistDomain.domain == domain
            ).first()
            return whitelist_entry is not None
        except Exception as e:
            logger.error(f"Whitelist check error: {str(e)}")
            return False

    async def _get_whois_info(self, domain: str) -> Dict:
        """Whois情報の取得（キャッシュ付き）"""
        try:
            # キャッシュチェック
            if domain in self.whois_cache:
                cached_data = self.whois_cache[domain]
                if datetime.utcnow() - cached_data.get('timestamp', datetime.min) < self.cache_ttl:
                    return cached_data['data']

            # Whois情報取得
            loop = asyncio.get_event_loop()
            whois_data = await loop.run_in_executor(None, whois.whois, domain)

            result = {
                'creation_date': str(whois_data.creation_date) if whois_data.creation_date else None,
                'expiration_date': str(whois_data.expiration_date) if whois_data.expiration_date else None,
                'registrar': whois_data.registrar,
                'status': whois_data.status,
                'name_servers': whois_data.name_servers,
                'org': whois_data.org,
                'country': whois_data.country,
            }

            # キャッシュに保存
            self.whois_cache[domain] = {
                'data': result,
                'timestamp': datetime.utcnow()
            }

            return result

        except Exception as e:
            logger.warning(f"Whois lookup failed for {domain}: {str(e)}")
            return {}

    async def _get_ssl_info(self, domain: str) -> Dict:
        """SSL証明書情報の取得"""
        try:
            context = ssl.create_default_context()

            async with httpx.AsyncClient(verify=context, timeout=10.0) as client:
                response = await client.get(f"https://{domain}", follow_redirects=True)

                # SSL証明書情報を取得
                if hasattr(response, 'extensions') and response.extensions.get('network_stream'):
                    stream = response.extensions['network_stream']
                    if hasattr(stream, 'get_extra_info'):
                        cert = stream.get_extra_info('peercert')
                        if cert:
                            return {
                                'subject': dict(cert.get('subject', [])),
                                'issuer': dict(cert.get('issuer', [])),
                                'not_before': cert.get('notBefore'),
                                'not_after': cert.get('notAfter'),
                                'serial_number': cert.get('serialNumber'),
                                'version': cert.get('version'),
                            }

                return {'ssl_available': True, 'details': 'Limited info available'}

        except Exception as e:
            logger.warning(f"SSL check failed for {domain}: {str(e)}")
            return {'ssl_available': False, 'error': str(e)}

    async def _analyze_domain_patterns(self, domain: str) -> Tuple[ThreatLevel, float]:
        """ドメインパターン分析"""
        try:
            confidence = 0.5  # 基本値
            threat_level = ThreatLevel.MEDIUM

            # 安全なパターンチェック
            for pattern in self.safe_patterns:
                if re.match(pattern, domain, re.IGNORECASE):
                    return ThreatLevel.SAFE, 0.9

            # 疑わしいパターンチェック
            suspicious_count = 0
            for pattern in self.suspicious_patterns:
                if re.match(pattern, domain, re.IGNORECASE):
                    suspicious_count += 1

            if suspicious_count > 0:
                threat_level = ThreatLevel.HIGH
                confidence = min(0.8, 0.3 + (suspicious_count * 0.2))

            # ドメイン長チェック
            if len(domain) > 50:
                threat_level = ThreatLevel.MEDIUM
                confidence = max(confidence, 0.6)

            # 数字とハイフンの比率チェック
            num_digits = sum(c.isdigit() for c in domain)
            num_hyphens = domain.count('-')
            total_chars = len(domain)

            if total_chars > 0:
                digit_ratio = num_digits / total_chars
                hyphen_ratio = num_hyphens / total_chars

                if digit_ratio > 0.3 or hyphen_ratio > 0.2:
                    threat_level = ThreatLevel.MEDIUM
                    confidence = max(confidence, 0.7)

            return threat_level, confidence

        except Exception as e:
            logger.error(f"Pattern analysis error: {str(e)}")
            return ThreatLevel.MEDIUM, 0.5

    def _calculate_final_threat_level(self, domain_info: DomainInfo) -> DomainInfo:
        """最終的な脅威レベルの計算"""
        try:
            factors = []

            # Whois情報による判定
            if domain_info.whois_data:
                whois_data = domain_info.whois_data

                # 作成日が最近すぎる場合は要注意
                if whois_data.get('creation_date'):
                    try:
                        creation_date = datetime.fromisoformat(whois_data['creation_date'].replace('Z', '+00:00'))
                        days_old = (datetime.utcnow() - creation_date).days

                        if days_old < 30:
                            factors.append(('new_domain', 0.7, ThreatLevel.HIGH))
                        elif days_old < 365:
                            factors.append(('recent_domain', 0.5, ThreatLevel.MEDIUM))
                    except:
                        pass

                # 組織情報がない場合
                if not whois_data.get('org') and not whois_data.get('registrar'):
                    factors.append(('no_org_info', 0.4, ThreatLevel.MEDIUM))

            # SSL情報による判定
            if domain_info.ssl_info:
                if not domain_info.ssl_info.get('ssl_available', False):
                    factors.append(('no_ssl', 0.6, ThreatLevel.HIGH))

            # 総合判定
            if factors:
                avg_confidence = sum(f[1] for f in factors) / len(factors)
                max_threat = max(f[2] for f in factors)

                domain_info.confidence_score = min(1.0, max(domain_info.confidence_score, avg_confidence))

                # より高い脅威レベルを採用
                if max_threat.value > domain_info.threat_level.value:
                    domain_info.threat_level = max_threat

            return domain_info

        except Exception as e:
            logger.error(f"Final threat calculation error: {str(e)}")
            return domain_info

    async def get_whitelist_domains(self, skip: int = 0, limit: int = 100) -> List[WhitelistDomain]:
        """ホワイトリストドメインの取得"""
        try:
            return self.db.query(WhitelistDomain).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error fetching whitelist domains: {str(e)}")
            return []

    async def add_to_whitelist(self, domain: str, added_by: str) -> WhitelistDomain:
        """ドメインをホワイトリストに追加"""
        try:
            # 既存チェック
            existing = self.db.query(WhitelistDomain).filter(
                WhitelistDomain.domain == domain
            ).first()

            if existing:
                raise ValueError(f"Domain {domain} is already in whitelist")

            whitelist_entry = WhitelistDomain(
                domain=domain,
                added_by=added_by,
                added_at=datetime.utcnow()
            )

            self.db.add(whitelist_entry)
            self.db.commit()
            self.db.refresh(whitelist_entry)

            return whitelist_entry

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding domain to whitelist: {str(e)}")
            raise

    async def remove_from_whitelist(self, domain_id: str) -> bool:
        """ホワイトリストからドメインを削除"""
        try:
            domain_entry = self.db.query(WhitelistDomain).filter(
                WhitelistDomain.id == domain_id
            ).first()

            if not domain_entry:
                return False

            self.db.delete(domain_entry)
            self.db.commit()

            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error removing domain from whitelist: {str(e)}")
            raise


def get_domain_classifier(db: Session = None) -> DomainClassifier:
    """DomainClassifier インスタンスの取得"""
    if db is None:
        db = next(get_db())
    return DomainClassifier(db)