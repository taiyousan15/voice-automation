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
                    max_tokens=1500,  # 1記事あたり最大1,500トークン ≈ 600字
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

【CRITICAL制約】出力は400-600文字厳守。これは1記事分のセクションです。400文字未満や600文字超過は禁止。

【ニュース記事】
{article_text}

【出力形式】
以下の構成で台本を作成してください（合計400-600文字）：

1. **トピック紹介（20秒・80文字）**
   - 何のニュースかを簡潔に紹介

2. **ニュース解説（1分・350文字）**
   - 記事の要点を分かりやすく説明
   - 専門用語は避ける
   - 事実に基づいた内容

3. **まとめ（20秒・70文字）**
   - 要約とリスナーへの一言

【スタイル】
- 話し言葉で自然なリズム
- 難しい言葉は避け、わかりやすく
- 日本語として正確で読み間違いのない表記
- 冗長な表現は排除し、簡潔に"""
