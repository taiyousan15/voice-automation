"""Groq LLM Client - Llama 3.3 70B for fast script generation"""
import os
import time
from typing import Optional, Dict
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
        max_retries: int = 2,
        template: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Generate podcast script from news article using Groq Llama

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
