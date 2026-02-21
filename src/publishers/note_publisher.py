"""note.com article template generator for podcast episodes"""
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger


class NotePublisher:
    """Generate note.com article templates from podcast episodes.

    note.com has no public API for audio posting, so this generates
    a Markdown template that can be manually pasted into note's editor.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or "https://note.com"
        self.logger = logger

    def generate_template(
        self,
        episode_title: str,
        description: str,
        audio_url: str,
        rss_url: str,
        theme: str,
        pub_date: Optional[str] = None,
    ) -> str:
        """Generate a Markdown article template for note.com.

        Args:
            episode_title: Title of the podcast episode
            description: Episode description / script excerpt
            audio_url: Public URL to the MP3 file
            rss_url: RSS feed URL for subscription
            theme: Episode theme/category
            pub_date: Publication date (ISO format), defaults to now

        Returns:
            Markdown-formatted article template string
        """
        date_str = pub_date or datetime.now().strftime("%Y-%m-%d")
        preview = (description[:300] + "...") if len(description) > 300 else description

        return (
            f"# {episode_title}\n\n"
            f"**{date_str}** | テーマ: {theme}\n\n"
            f"---\n\n"
            f"## 今回のエピソード\n\n"
            f"{preview}\n\n"
            f"## 音声を聴く\n\n"
            f"[MP3ファイルはこちら]({audio_url})\n\n"
            f"## ポッドキャストを購読\n\n"
            f"RSSフィードで購読: {rss_url}\n\n"
            f"---\n\n"
            f"*この記事はAIポッドキャスト自動配信システムにより生成されました。*\n"
        )

    def save_template(self, template: str, output_path: Path) -> Path:
        """Save template to a Markdown file.

        Args:
            template: Markdown template string
            output_path: Destination file path

        Returns:
            Path to the saved file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(template, encoding="utf-8")
        self.logger.info(f"note.com template saved: {output_path}")
        return output_path
