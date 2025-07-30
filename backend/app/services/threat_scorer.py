"""
ABDSシステム - 脅威度スコアリングサービス
ドメイン信頼度、AI分析結果、その他要因を統合した脅威度評価
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ThreatScorer:
    """脅威度スコアリングクラス"""

    def __init__(self):
        # 重み付け設定
        self.weights = {
            'domain_trust': 0.40,      # ドメイン信頼度: 40%
            'ai_analysis': 0.40,       # AI分析結果: 40%
            'other_factors': 0.20      # その他の要因: 20%
        }

        # ドメイン信頼度の重み
        self.domain_weights = {
            'domain_age': 0.30,        # ドメイン年齢
            'ssl_certificate': 0.25,   # SSL証明書
            'whois_info': 0.20,        # WHOIS情報
            'dns_records': 0.15,       # DNS記録
            'reputation': 0.10         # ドメイン評判
        }

        # AI分析の重み
        self.ai_weights = {
            'abuse_detection': 0.35,   # 悪用検出
            'copyright_risk': 0.30,    # 著作権リスク
            'commercial_use': 0.20,    # 商用利用
            'content_quality': 0.15    # コンテンツ品質
        }

        # その他要因の重み
        self.other_weights = {
            'search_ranking': 0.30,    # 検索順位
            'content_similarity': 0.25, # コンテンツ類似度
            'update_frequency': 0.20,  # 更新頻度
            'traffic_data': 0.15,      # トラフィックデータ
            'social_signals': 0.10     # ソーシャルシグナル
        }

    def calculate_score(
        self,
        domain_data: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        search_data: Dict[str, Any],
        content_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        総合脅威度スコアを計算

        Args:
            domain_data: ドメイン関連データ
            ai_analysis: AI分析結果
            search_data: 検索関連データ
            content_data: コンテンツデータ

        Returns:
            Dict: 脅威度評価結果
        """
        try:
            # 各カテゴリのスコア計算
            domain_score = self._calculate_domain_score(domain_data)
            ai_score = self._calculate_ai_score(ai_analysis)
            other_score = self._calculate_other_score(search_data, content_data)

            # 重み付き総合スコア
            total_score = (
                domain_score * self.weights['domain_trust'] +
                ai_score * self.weights['ai_analysis'] +
                other_score * self.weights['other_factors']
            )

            # スコア正規化（0-100）
            normalized_score = max(0, min(100, total_score))

            # 脅威レベル決定
            threat_level = self._determine_threat_level(normalized_score)

            # 詳細結果
            result = {
                'overall_score': round(normalized_score, 2),
                'threat_level': threat_level,
                'confidence': self._calculate_confidence(domain_data, ai_analysis),
                'components': {
                    'domain_trust': {
                        'score': round(domain_score, 2),
                        'weight': self.weights['domain_trust'],
                        'contribution': round(domain_score * self.weights['domain_trust'], 2)
                    },
                    'ai_analysis': {
                        'score': round(ai_score, 2),
                        'weight': self.weights['ai_analysis'],
                        'contribution': round(ai_score * self.weights['ai_analysis'], 2)
                    },
                    'other_factors': {
                        'score': round(other_score, 2),
                        'weight': self.weights['other_factors'],
                        'contribution': round(other_score * self.weights['other_factors'], 2)
                    }
                },
                'risk_factors': self._identify_risk_factors(
                    domain_data, ai_analysis, search_data, content_data
                ),
                'recommendations': self._generate_recommendations(normalized_score, threat_level),
                'calculated_at': datetime.utcnow().isoformat()
            }

            logger.info(f"Threat score calculated: {normalized_score} ({threat_level})")
            return result

        except Exception as e:
            logger.error(f"Threat score calculation failed: {e}")
            return self._create_error_result(str(e))

    def _calculate_domain_score(self, domain_data: Dict[str, Any]) -> float:
        """ドメイン信頼度スコアを計算"""
        score = 0.0

        # ドメイン年齢評価
        domain_age_score = self._score_domain_age(
            domain_data.get('creation_date'),
            domain_data.get('expiration_date')
        )
        score += domain_age_score * self.domain_weights['domain_age']

        # SSL証明書評価
        ssl_score = self._score_ssl_certificate(domain_data.get('ssl_info', {}))
        score += ssl_score * self.domain_weights['ssl_certificate']

        # WHOIS情報評価
        whois_score = self._score_whois_info(domain_data.get('whois_info', {}))
        score += whois_score * self.domain_weights['whois_info']

        # DNS記録評価
        dns_score = self._score_dns_records(domain_data.get('dns_records', {}))
        score += dns_score * self.domain_weights['dns_records']

        # ドメイン評判評価
        reputation_score = self._score_domain_reputation(domain_data.get('reputation', {}))
        score += reputation_score * self.domain_weights['reputation']

        return min(100, max(0, score))

    def _calculate_ai_score(self, ai_analysis: Dict[str, Any]) -> float:
        """AI分析スコアを計算"""
        score = 0.0

        # 悪用検出評価
        abuse_score = self._score_abuse_detection(ai_analysis.get('abuse_detection', {}))
        score += abuse_score * self.ai_weights['abuse_detection']

        # 著作権リスク評価
        copyright_score = self._score_copyright_risk(ai_analysis.get('copyright_infringement', {}))
        score += copyright_score * self.ai_weights['copyright_risk']

        # 商用利用評価
        commercial_score = self._score_commercial_use(ai_analysis.get('commercial_use', {}))
        score += commercial_score * self.ai_weights['commercial_use']

        # コンテンツ品質評価
        quality_score = self._score_content_quality(ai_analysis.get('content_modification', {}))
        score += quality_score * self.ai_weights['content_quality']

        return min(100, max(0, score))

    def _calculate_other_score(self, search_data: Dict[str, Any], content_data: Dict[str, Any]) -> float:
        """その他要因スコアを計算"""
        score = 0.0

        # 検索順位評価
        ranking_score = self._score_search_ranking(search_data.get('ranking', 0))
        score += ranking_score * self.other_weights['search_ranking']

        # コンテンツ類似度評価
        similarity_score = self._score_content_similarity(content_data.get('similarity_score', 0))
        score += similarity_score * self.other_weights['content_similarity']

        # 更新頻度評価
        update_score = self._score_update_frequency(content_data.get('last_updated'))
        score += update_score * self.other_weights['update_frequency']

        # トラフィックデータ評価
        traffic_score = self._score_traffic_data(search_data.get('traffic_estimate', {}))
        score += traffic_score * self.other_weights['traffic_data']

        # ソーシャルシグナル評価
        social_score = self._score_social_signals(content_data.get('social_data', {}))
        score += social_score * self.other_weights['social_signals']

        return min(100, max(0, score))

    def _score_domain_age(self, creation_date: Optional[str], expiration_date: Optional[str]) -> float:
        """ドメイン年齢スコア（古いほど信頼度高）"""
        if not creation_date:
            return 50.0  # 不明な場合は中間値

        try:
            if isinstance(creation_date, str):
                creation = datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
            else:
                creation = creation_date

            age_days = (datetime.utcnow() - creation.replace(tzinfo=None)).days

            # 年齢による信頼度スコア
            if age_days > 365 * 5:  # 5年以上
                return 10.0  # 低リスク
            elif age_days > 365 * 2:  # 2年以上
                return 20.0
            elif age_days > 365:  # 1年以上
                return 40.0
            elif age_days > 180:  # 6ヶ月以上
                return 60.0
            elif age_days > 30:  # 1ヶ月以上
                return 80.0
            else:  # 新しいドメイン
                return 90.0  # 高リスク

        except Exception:
            return 50.0

    def _score_ssl_certificate(self, ssl_info: Dict[str, Any]) -> float:
        """SSL証明書スコア"""
        if not ssl_info:
            return 70.0  # SSL情報なしは中リスク

        has_ssl = ssl_info.get('has_ssl', False)
        is_valid = ssl_info.get('is_valid', False)
        issuer = ssl_info.get('issuer', '').lower()

        if not has_ssl:
            return 80.0  # SSL なしは高リスク

        if not is_valid:
            return 75.0  # 無効なSSLは高リスク

        # 証明書発行者による評価
        trusted_issuers = ['let\'s encrypt', 'digicert', 'symantec', 'comodo', 'godaddy']
        if any(trusted in issuer for trusted in trusted_issuers):
            return 10.0  # 信頼できる発行者
        else:
            return 30.0  # その他の発行者

    def _score_whois_info(self, whois_info: Dict[str, Any]) -> float:
        """WHOIS情報スコア"""
        if not whois_info:
            return 60.0

        score = 50.0

        # 登録者情報の完全性
        registrant = whois_info.get('registrant', {})
        if registrant.get('organization'):
            score -= 10.0  # 組織名があると信頼度up
        if registrant.get('country'):
            score -= 5.0

        # プライバシー保護
        if whois_info.get('privacy_protected', False):
            score += 15.0  # プライバシー保護は若干リスク

        # 登録期間
        expiry = whois_info.get('expiration_date')
        if expiry:
            try:
                if isinstance(expiry, str):
                    exp_date = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
                else:
                    exp_date = expiry

                days_to_expiry = (exp_date.replace(tzinfo=None) - datetime.utcnow()).days
                if days_to_expiry > 365:
                    score -= 10.0  # 長期登録は信頼度up
                elif days_to_expiry < 30:
                    score += 20.0  # 期限切れ間近はリスク

            except Exception:
                pass

        return max(0, min(100, score))

    def _score_dns_records(self, dns_records: Dict[str, Any]) -> float:
        """DNS記録スコア"""
        if not dns_records:
            return 50.0

        score = 50.0

        # MXレコード（メールサーバー）
        if dns_records.get('mx_records'):
            score -= 10.0

        # SPF/DKIM/DMARC（メール認証）
        txt_records = dns_records.get('txt_records', [])
        if any('spf' in record.lower() for record in txt_records):
            score -= 5.0
        if any('dkim' in record.lower() for record in txt_records):
            score -= 5.0

        # CDNやセキュリティサービス
        cname_records = dns_records.get('cname_records', [])
        security_providers = ['cloudflare', 'akamai', 'fastly', 'amazon']
        if any(provider in str(cname_records).lower() for provider in security_providers):
            score -= 15.0

        return max(0, min(100, score))

    def _score_domain_reputation(self, reputation: Dict[str, Any]) -> float:
        """ドメイン評判スコア"""
        if not reputation:
            return 50.0

        # 既知の悪質ドメインチェック
        if reputation.get('is_malicious', False):
            return 100.0

        # セキュリティベンダーの評価
        vendor_scores = reputation.get('vendor_assessments', {})
        if vendor_scores:
            avg_score = sum(vendor_scores.values()) / len(vendor_scores)
            return avg_score

        return 50.0

    def _score_abuse_detection(self, abuse_data: Dict[str, Any]) -> float:
        """悪用検出スコア"""
        if not abuse_data:
            return 50.0

        risk_level = abuse_data.get('risk_level', '').lower()
        confidence = abuse_data.get('confidence', 0.5)

        # リスクレベルベースのスコア
        if '高' in risk_level or 'high' in risk_level:
            base_score = 90.0
        elif '中' in risk_level or 'medium' in risk_level:
            base_score = 60.0
        else:
            base_score = 20.0

        # 信頼度による調整
        adjusted_score = base_score * confidence + 50.0 * (1 - confidence)

        return min(100, max(0, adjusted_score))

    def _score_copyright_risk(self, copyright_data: Dict[str, Any]) -> float:
        """著作権リスクスコア"""
        if not copyright_data:
            return 30.0

        probability = copyright_data.get('probability', '').lower()
        confidence = copyright_data.get('confidence', 0.5)

        if '高' in probability or 'high' in probability:
            base_score = 85.0
        elif '中' in probability or 'medium' in probability:
            base_score = 55.0
        else:
            base_score = 15.0

        return base_score * confidence + 30.0 * (1 - confidence)

    def _score_commercial_use(self, commercial_data: Dict[str, Any]) -> float:
        """商用利用スコア"""
        if not commercial_data:
            return 30.0

        status = commercial_data.get('status', '').lower()

        if '無許可' in status or 'unauthorized' in status:
            return 70.0
        elif '商用' in status or 'commercial' in status:
            return 50.0
        else:
            return 20.0

    def _score_content_quality(self, modification_data: Dict[str, Any]) -> float:
        """コンテンツ品質スコア"""
        if not modification_data:
            return 30.0

        level = modification_data.get('level', '').lower()

        if '大幅' in level or 'major' in level:
            return 70.0
        elif '軽微' in level or 'minor' in level:
            return 40.0
        else:
            return 20.0

    def _score_search_ranking(self, ranking: int) -> float:
        """検索順位スコア（上位ほど信頼度高）"""
        if ranking <= 0:
            return 50.0

        if ranking <= 3:
            return 10.0  # トップ3は信頼度高
        elif ranking <= 10:
            return 25.0
        elif ranking <= 20:
            return 40.0
        elif ranking <= 50:
            return 60.0
        else:
            return 80.0  # 低順位は要注意

    def _score_content_similarity(self, similarity: float) -> float:
        """コンテンツ類似度スコア"""
        if similarity >= 0.9:
            return 20.0  # 高い類似度は信頼度高
        elif similarity >= 0.7:
            return 35.0
        elif similarity >= 0.5:
            return 50.0
        elif similarity >= 0.3:
            return 70.0
        else:
            return 85.0  # 低い類似度は要注意

    def _score_update_frequency(self, last_updated: Optional[str]) -> float:
        """更新頻度スコア"""
        if not last_updated:
            return 60.0

        try:
            if isinstance(last_updated, str):
                updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            else:
                updated = last_updated

            days_since_update = (datetime.utcnow() - updated.replace(tzinfo=None)).days

            if days_since_update <= 7:
                return 30.0  # 最近更新
            elif days_since_update <= 30:
                return 40.0
            elif days_since_update <= 90:
                return 55.0
            elif days_since_update <= 365:
                return 70.0
            else:
                return 85.0  # 長期間未更新

        except Exception:
            return 60.0

    def _score_traffic_data(self, traffic_data: Dict[str, Any]) -> float:
        """トラフィックデータスコア"""
        if not traffic_data:
            return 50.0

        # Alexaランクやトラフィック推定
        alexa_rank = traffic_data.get('alexa_rank', 0)
        if alexa_rank > 0:
            if alexa_rank <= 10000:
                return 10.0  # 人気サイト
            elif alexa_rank <= 100000:
                return 25.0
            elif alexa_rank <= 1000000:
                return 40.0
            else:
                return 60.0

        return 50.0

    def _score_social_signals(self, social_data: Dict[str, Any]) -> float:
        """ソーシャルシグナルスコア"""
        if not social_data:
            return 50.0

        # SNSでのシェア数
        total_shares = sum([
            social_data.get('facebook_shares', 0),
            social_data.get('twitter_shares', 0),
            social_data.get('linkedin_shares', 0)
        ])

        if total_shares > 1000:
            return 20.0
        elif total_shares > 100:
            return 35.0
        elif total_shares > 10:
            return 50.0
        else:
            return 70.0

    def _determine_threat_level(self, score: float) -> str:
        """スコアから脅威レベルを決定"""
        if score >= 80:
            return 'HIGH'
        elif score >= 60:
            return 'MEDIUM'
        elif score >= 40:
            return 'LOW'
        else:
            return 'SAFE'

    def _calculate_confidence(self, domain_data: Dict, ai_analysis: Dict) -> float:
        """評価の信頼度を計算"""
        confidence_factors = []

        # ドメインデータの完全性
        if domain_data.get('whois_info'):
            confidence_factors.append(0.9)
        if domain_data.get('ssl_info'):
            confidence_factors.append(0.8)

        # AI分析の信頼度
        for analysis in ai_analysis.values():
            if isinstance(analysis, dict) and 'confidence' in analysis:
                confidence_factors.append(analysis['confidence'])

        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        else:
            return 0.5

    def _identify_risk_factors(self, domain_data: Dict, ai_analysis: Dict,
                            search_data: Dict, content_data: Dict) -> List[str]:
        """リスク要因を特定"""
        risk_factors = []

        # ドメイン関連
        if domain_data.get('creation_date'):
            try:
                creation = datetime.fromisoformat(domain_data['creation_date'].replace('Z', '+00:00'))
                if (datetime.utcnow() - creation.replace(tzinfo=None)).days < 30:
                    risk_factors.append('新規ドメイン（30日以内）')
            except:
                pass

        ssl_info = domain_data.get('ssl_info', {})
        if not ssl_info.get('has_ssl'):
            risk_factors.append('SSL証明書なし')

        # AI分析関連
        abuse = ai_analysis.get('abuse_detection', {})
        if 'high' in str(abuse.get('risk_level', '')).lower():
            risk_factors.append('高い悪用リスク')

        copyright = ai_analysis.get('copyright_infringement', {})
        if 'high' in str(copyright.get('probability', '')).lower():
            risk_factors.append('著作権侵害の可能性')

        # その他
        ranking = search_data.get('ranking', 0)
        if ranking > 50:
            risk_factors.append('検索順位が低い')

        similarity = content_data.get('similarity_score', 1.0)
        if similarity < 0.3:
            risk_factors.append('コンテンツ類似度が低い')

        return risk_factors

    def _generate_recommendations(self, score: float, threat_level: str) -> List[str]:
        """推奨アクションを生成"""
        recommendations = []

        if threat_level == 'HIGH':
            recommendations.extend([
                '即座に詳細調査を実施してください',
                '著作権侵害の可能性があります',
                '法的措置を検討してください'
            ])
        elif threat_level == 'MEDIUM':
            recommendations.extend([
                '追加の確認を推奨します',
                'ドメイン所有者に連絡を検討してください',
                '継続的な監視を設定してください'
            ])
        elif threat_level == 'LOW':
            recommendations.extend([
                '定期的な監視で十分です',
                '必要に応じて追加調査を検討してください'
            ])
        else:
            recommendations.append('現時点では特別な対応は不要です')

        return recommendations

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """エラー時のデフォルト結果を作成"""
        return {
            'overall_score': 50.0,
            'threat_level': 'UNKNOWN',
            'confidence': 0.0,
            'error': error_message,
            'components': {},
            'risk_factors': ['評価エラーが発生しました'],
            'recommendations': ['手動での詳細確認を推奨します'],
            'calculated_at': datetime.utcnow().isoformat()
        }


# インスタンス取得用のファクトリ関数
def get_threat_scorer() -> ThreatScorer:
    """ThreatScorerインスタンスを取得"""
    return ThreatScorer()