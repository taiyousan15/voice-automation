"""Groq LLM Client - Llama 3.3 70B for fast script generation"""
import os
import time
from typing import Optional
from groq import Groq, APIError, APIConnectionError, RateLimitError
from loguru import logger


class GroqClient:
    """Groq API client for Llama 3.3 70B model"""

    def __init__(self):
        """Initialize Groq client"""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")

        self.client = Groq(api_key=api_key)
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.timeout = int(os.getenv("GROQ_TIMEOUT_SECONDS", "15"))

        logger.info(f"Groq client initialized - Model: {self.model}")

    def generate_podcast_script(
        self,
        article_text: str,
        theme: str = "general",
        max_retries: int = 2
    ) -> Optional[str]:
        """
        Generate podcast script from news article using Groq Llama

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
                logger.debug(f"Generating script via Groq (attempt {attempt + 1}/{max_retries + 1})")
                start_time = time.time()

                message = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=1500,
                    top_p=0.9
                )

                script = message.choices[0].message.content
                elapsed = time.time() - start_time
                logger.info(f"Groq script generated in {elapsed:.2f}s ({len(script)} chars)")
                return script

            except RateLimitError as e:
                logger.warning(f"Groq rate limit: {e}")
                if attempt < max_retries:
                    wait_time = 3 * (attempt + 1)
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error("Max retries exceeded - Groq rate limit")
                    return None

            except APIConnectionError as e:
                logger.error(f"Groq connection error: {e}")
                if attempt < max_retries:
                    logger.info("Retrying in 3s...")
                    time.sleep(3)
                else:
                    return None

            except APIError as e:
                logger.error(f"Groq API error: {e}")
                return None

        return None

    def _build_script_prompt(self, article_text: str, theme: str) -> str:
        """Build the prompt for podcast script generation"""
        return f"""以下のニュース記事をポッドキャスト台本に変換してください。
対象テーマ: {theme}
目標時間: 約5分間の音声放送

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
