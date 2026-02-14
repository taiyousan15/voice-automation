"""OpenRouter LLM Client - Claude Haiku via OpenRouter API"""
import os
import time
from typing import Optional
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
        max_retries: int = 2
    ) -> Optional[str]:
        """
        Generate podcast script from news article using Claude Haiku

        Args:
            article_text: News article text
            theme: Article theme for context
            max_retries: Maximum retry attempts

        Returns:
            Generated podcast script or None on failure
        """
        prompt = self._build_script_prompt(article_text, theme)

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

    def _build_script_prompt(self, article_text: str, theme: str) -> str:
        """Build the prompt for podcast script generation"""
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
