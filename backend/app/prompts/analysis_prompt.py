"""
ABDSシステム - AI分析用プロンプトテンプレート
Gemini APIを使用したコンテンツ分析のためのプロンプト設計
"""

from typing import Dict, List, Optional
from datetime import datetime

# =================================
# 基本分析プロンプト
# =================================

CONTENT_ANALYSIS_PROMPT = """
あなたは著作権侵害とコンテンツ悪用を検出する専門のAI分析システムです。
提供されたWebページのコンテンツと画像の情報を基に、以下の観点から詳細に分析してください。

# 分析対象情報
## Webページコンテンツ
{html_content}

## 画像コンテキスト情報
{image_context}

# 分析項目と判定基準

## 1. コンテンツ悪用判定 (abuse_detection)
- **高リスク**: 明らかな詐欺、フィッシング、マルウェア配布の兆候
- **中リスク**: 怪しいリンク、不審な要求、信頼性に疑問
- **低リスク**: 軽微な問題や注意が必要な要素
- **安全**: 問題となる要素が見つからない

## 2. 著作権侵害の可能性 (copyright_infringement)
- **高確率**: 無断使用が明確、著作権表示の改変・削除
- **中確率**: 出典不明、ライセンス情報なし、疑わしい使用
- **低確率**: 適切な引用の可能性、フェアユースの範囲内
- **問題なし**: 正当な使用、適切な権利処理

## 3. 商用利用の有無 (commercial_use)
- **明確な商用利用**: 販売、広告、営利目的での使用が明らか
- **疑わしい商用利用**: 商用の可能性があるが確証がない
- **非商用利用**: 個人使用、教育目的、非営利での使用
- **判定不可**: 情報不足で判定できない

## 4. レビューサイトでの無断転載 (unauthorized_repost)
- **明確な無断転載**: 元コンテンツからの完全コピー
- **疑わしい転載**: 類似性が高いが確証がない
- **適切な引用**: 正当な引用・参照の範囲内
- **オリジナル**: 独自コンテンツと判断

## 5. 改変の有無 (content_modification)
- **大幅改変**: 元コンテンツから大きく変更されている
- **部分改変**: 一部が変更・追加されている
- **軽微改変**: わずかな変更のみ
- **無改変**: オリジナルのまま使用

# 回答形式
以下のJSON形式で回答してください：

```json
{{
  "analysis_result": {{
    "abuse_detection": {{
      "risk_level": "高リスク|中リスク|低リスク|安全",
      "confidence": 0.0-1.0,
      "evidence": ["具体的な根拠1", "具体的な根拠2"],
      "details": "詳細な説明"
    }},
    "copyright_infringement": {{
      "probability": "高確率|中確率|低確率|問題なし",
      "confidence": 0.0-1.0,
      "evidence": ["具体的な根拠1", "具体的な根拠2"],
      "details": "詳細な説明"
    }},
    "commercial_use": {{
      "status": "明確な商用利用|疑わしい商用利用|非商用利用|判定不可",
      "confidence": 0.0-1.0,
      "evidence": ["具体的な根拠1", "具体的な根拠2"],
      "details": "詳細な説明"
    }},
    "unauthorized_repost": {{
      "status": "明確な無断転載|疑わしい転載|適切な引用|オリジナル",
      "confidence": 0.0-1.0,
      "evidence": ["具体的な根拠1", "具体的な根拠2"],
      "details": "詳細な説明"
    }},
    "content_modification": {{
      "level": "大幅改変|部分改変|軽微改変|無改変",
      "confidence": 0.0-1.0,
      "evidence": ["具体的な根拠1", "具体的な根拠2"],
      "details": "詳細な説明"
    }}
  }},
  "overall_assessment": {{
    "threat_level": "高|中|低|なし",
    "risk_score": 0-100,
    "summary": "総合的な分析結果のサマリー",
    "recommendations": ["推奨アクション1", "推奨アクション2"]
  }},
  "metadata": {{
    "analyzed_at": "{timestamp}",
    "analysis_version": "1.0",
    "confidence_score": 0.0-1.0
  }}
}}
```

分析は客観的かつ詳細に行い、明確な根拠を示してください。
不明な点がある場合は、その旨を明記し、推測と事実を区別してください。
"""

# =================================
# 専門分析プロンプト
# =================================

IMAGE_CONTEXT_PROMPT = """
画像コンテキスト分析：
- ファイル名: {filename}
- アップロード日時: {upload_date}
- 画像メタデータ: {metadata}
- 検出された類似画像: {similar_images}

この情報を基に、画像の使用状況と権利関係を分析してください。
"""

ABUSE_DETECTION_PROMPT = """
悪用検出に特化した分析を実行してください：

検出項目:
1. フィッシング・詐欺サイトの特徴
2. マルウェア配布の兆候
3. 個人情報の不正収集
4. 偽ブランド・なりすまし
5. 違法コンテンツの配布

特に以下の要素に注意：
- URL構造の異常性
- SSL証明書の問題
- 不自然な日本語
- 緊急性を煽る文言
- 個人情報入力フォーム
"""

COPYRIGHT_ANALYSIS_PROMPT = """
著作権侵害分析に特化した検証を実行してください：

検証項目:
1. 著作権表示の有無と適切性
2. ライセンス情報の記載
3. 出典・引用の明記
4. 改変・加工の痕跡
5. 商用利用の兆候

日本の著作権法に基づいて判定し、以下を特に注意：
- 著作権者の明示
- 利用許諾の有無
- フェアユースの適用可能性
- 引用の適切性
"""

COMMERCIAL_USE_PROMPT = """
商用利用検出に特化した分析を実行してください：

検出項目:
1. 商品・サービスの販売
2. 広告・宣伝活動
3. アフィリエイトリンク
4. 企業サイトでの使用
5. 収益化の仕組み

営利目的での使用を示す要素：
- 価格表示
- 購入ボタン
- 広告バナー
- 企業情報
- 利益誘導
"""

UNAUTHORIZED_REPOST_PROMPT = """
無断転載検出に特化した分析を実行してください：

検証項目:
1. 元コンテンツとの一致度
2. 出典の明記状況
3. 許可の有無
4. 改変・編集の程度
5. クレジット表示

レビューサイト特有の問題：
- 他サイトからのコピー
- 画像の無断使用
- レビュー内容の盗用
- 著作者情報の削除
"""

MODIFICATION_DETECTION_PROMPT = """
改変検出に特化した分析を実行してください：

検出項目:
1. 画像の加工・編集
2. テキストの改変
3. 透かしの除去
4. クレジットの削除
5. 内容の変更

改変の程度判定：
- 元コンテンツからの変更点
- 改変の意図と目的
- 著作権に与える影響
- 同一性保持権の侵害
"""

# =================================
# プロンプトビルダークラス
# =================================

class AnalysisPromptBuilder:
    """分析用プロンプトを動的に構築するクラス"""

    def __init__(self):
        self.base_prompt = CONTENT_ANALYSIS_PROMPT
        self.specialized_prompts = {
            'abuse': ABUSE_DETECTION_PROMPT,
            'copyright': COPYRIGHT_ANALYSIS_PROMPT,
            'commercial': COMMERCIAL_USE_PROMPT,
            'repost': UNAUTHORIZED_REPOST_PROMPT,
            'modification': MODIFICATION_DETECTION_PROMPT
        }

    def build_comprehensive_prompt(
        self,
        html_content: str,
        image_context: Dict,
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """包括的な分析プロンプトを構築"""

        # 画像コンテキストの構築
        image_context_text = self._build_image_context(image_context)

        # 基本プロンプト
        prompt = self.base_prompt.format(
            html_content=self._truncate_content(html_content, 8000),
            image_context=image_context_text,
            timestamp=datetime.utcnow().isoformat()
        )

        # 特化分析の追加
        if focus_areas:
            prompt += "\n\n# 特化分析\n"
            for area in focus_areas:
                if area in self.specialized_prompts:
                    prompt += f"\n## {area.upper()}分析\n"
                    prompt += self.specialized_prompts[area]

        return prompt

    def build_focused_prompt(
        self,
        analysis_type: str,
        html_content: str,
        image_context: Dict
    ) -> str:
        """特定分析に特化したプロンプトを構築"""

        if analysis_type not in self.specialized_prompts:
            raise ValueError(f"Unknown analysis type: {analysis_type}")

        image_context_text = self._build_image_context(image_context)

        base_info = f"""
# 分析対象情報
## Webページコンテンツ
{self._truncate_content(html_content, 10000)}

## 画像コンテキスト情報
{image_context_text}

# 分析日時
{datetime.utcnow().isoformat()}
"""

        return base_info + "\n\n" + self.specialized_prompts[analysis_type]

    def _build_image_context(self, image_context: Dict) -> str:
        """画像コンテキスト情報を構築"""
        context_parts = []

        if image_context.get('filename'):
            context_parts.append(f"ファイル名: {image_context['filename']}")

        if image_context.get('upload_date'):
            context_parts.append(f"アップロード日時: {image_context['upload_date']}")

        if image_context.get('metadata'):
            metadata = image_context['metadata']
            context_parts.append(f"画像メタデータ: {metadata}")

        if image_context.get('similar_images'):
            similar_count = len(image_context['similar_images'])
            context_parts.append(f"類似画像検出数: {similar_count}件")

            # 上位3件の類似画像情報
            for i, img in enumerate(image_context['similar_images'][:3]):
                context_parts.append(
                    f"類似画像{i+1}: {img.get('url', 'N/A')} "
                    f"(類似度: {img.get('similarity_score', 0):.2f})"
                )

        if image_context.get('search_results'):
            results_count = len(image_context['search_results'])
            context_parts.append(f"検索結果数: {results_count}件")

        return "\n".join(context_parts) if context_parts else "画像コンテキスト情報なし"

    def _truncate_content(self, content: str, max_length: int) -> str:
        """コンテンツを指定長で切り詰め"""
        if len(content) <= max_length:
            return content

        truncated = content[:max_length]
        # 単語の途中で切れないように調整
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:
            truncated = truncated[:last_space]

        return truncated + "\n\n[... コンテンツが切り詰められました ...]"

# =================================
# プロンプトテンプレート設定
# =================================

# 分析レベル別プロンプト
ANALYSIS_LEVELS = {
    'basic': {
        'focus_areas': ['abuse', 'copyright'],
        'detail_level': 'standard'
    },
    'comprehensive': {
        'focus_areas': ['abuse', 'copyright', 'commercial', 'repost', 'modification'],
        'detail_level': 'detailed'
    },
    'copyright_focused': {
        'focus_areas': ['copyright', 'modification'],
        'detail_level': 'detailed'
    },
    'abuse_focused': {
        'focus_areas': ['abuse', 'commercial'],
        'detail_level': 'detailed'
    }
}