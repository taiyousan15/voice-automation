"""OpenRouter LLM Client - Claude Haiku via OpenRouter API"""
import os
import time
from typing import Optional, Dict
from anthropic import Anthropic, APIError, APIConnectionError, RateLimitError
from loguru import logger


class OpenRouterClient:
    """OpenRouter API client for Claude models via Anthropic SDK"""

    def __init__(self):
        """Initialize OpenRouter client with Anthropic SDK"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        base_url = os.getenv("ANTHROPIC_BASE_URL", "https://openrouter.ai/api/v1")

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        self.client = Anthropic(api_key=api_key, base_url=base_url)
        self.model = os.getenv("CLAUDE_MODEL", "anthropic/claude-3-5-haiku")
        self.max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", "4000"))
        self.timeout = int(os.getenv("CLAUDE_TIMEOUT_SECONDS", "30"))

        logger.info(f"OpenRouter client initialized - Model: {self.model}")

    def generate_podcast_script(
        self,
        article_text: str,
        theme: str = "general",
        max_retries: int = 2,
        template: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Generate podcast script from news article using Claude Haiku

        Args:
            article_text: News article text
            theme: Article theme for context
            max_retries: Maximum retry attempts
            template: Optional template dict for genre-aware generation

        Returns:
            Generated podcast script or None on failure
        """
        prompt = self._build_script_prompt(article_text, theme, template=template)

        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Generating script (attempt {attempt + 1}/{max_retries + 1})")

                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )

                script = message.content[0].text
                logger.info(f"Script generated successfully ({len(script)} chars)")
                return script

            except RateLimitError as e:
                logger.warning(f"Rate limit exceeded: {e}")
                if attempt < max_retries:
                    wait_time = 5 * (attempt + 1)  # Exponential backoff
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error("Max retries exceeded - Rate limit")
                    return None

            except APIConnectionError as e:
                logger.error(f"Connection error: {e}")
                if attempt < max_retries:
                    logger.info(f"Retrying in 5s...")
                    time.sleep(5)
                else:
                    return None

            except APIError as e:
                logger.error(f"API error: {e}")
                return None

        return None

    def _build_script_prompt(self, article_text: str, theme: str, template: Optional[Dict] = None) -> str:
        """Build the prompt for podcast script generation

        Args:
            article_text: News article text
            theme: Article theme
            template: Optional template dict for genre-aware generation
        """
        if template:
            return self._build_template_prompt(article_text, theme, template)

        return f"""以下のニュース記事をポッドキャスト台本に変換してください。
対象テーマ: {theme}
目標時間: 約4-7分間の音声放送（日本語のみ）

【ニュース記事】
{article_text}

【出力形式】
以下の4セクションで構成した台本を、自然な日本語で作成してください：

1. **導入（30秒）**
   - リスナーへのあいさつと本日のトピック紹介
   - 軽い口調で親しみやすく

2. **ニュース解説（2分）**
   - 記事の要点を分かりやすく説明
   - 専門用語は簡潔に解説
   - 事実に基づいた内容

3. **インサイト・考察（1分30秒）**
   - ニュースの背景や意味
   - 社会への影響や意義
   - 個人的見解もOK（「個人的には」と前置きして）

4. **閉じ（30秒）**
   - 簡潔な要約
   - リスナーへのメッセージ
   - 次回エピソードへの予告

【スタイル】
- 話し言葉で自然なリズム
- 難しい言葉は避け、わかりやすく
- 適度な間を設けて読みやすく
- 日本語として正確で読み間違いのない表記"""

    def _build_template_prompt(self, article_text: str, theme: str, template: Dict) -> str:
        """Build prompt using template sections and style"""
        sections = template.get("sections", [])
        total_chars = sum(s.get("target_chars", 200) for s in sections)
        style = template.get("style", "taiyo_ok")
        ng_keywords = template.get("ng_keywords", [])
        prompt_injection = template.get("prompt_injection", "")

        # Build sections description
        section_lines = []
        for i, section in enumerate(sections, 1):
            section_lines.append(
                f"{i}. **{section['name']}（{section['target_chars']}文字）**\n"
                f"   - {section['role']}"
            )
        sections_text = "\n\n".join(section_lines)

        # Style constraints
        style_text = "- 話し言葉で自然なリズム\n- 日本語として正確で読み間違いのない表記"
        if style == "fact_strict":
            style_text += "\n- 【CRITICAL】事実のみ記載。誇大表現・断定的判断は禁止"
            style_text += "\n- 「〜と言われています」「〜というデータがあります」のように根拠を示す"
        elif style == "caution":
            style_text += "\n- 【CRITICAL】断定表現を回避。「個人の体験として」「一つの考え方として」と前置き"
            style_text += "\n- 医療効果の断定は禁止"

        # NG keywords
        ng_text = ""
        if ng_keywords:
            ng_text = f"\n\n【NGワード（使用禁止）】\n{', '.join(ng_keywords)}"

        return f"""{prompt_injection}

以下のニュース記事をポッドキャスト台本に変換してください。
対象テーマ: {theme}
テンプレート: {template.get('name', 'default')}

【CRITICAL制約】出力は{total_chars}文字前後を目標。{ng_text}

【ニュース記事】
{article_text}

【出力形式】
以下の構成で台本を作成してください（合計約{total_chars}文字）：

{sections_text}

【スタイル】
{style_text}
- 冗長な表現は排除し、簡潔に"""
