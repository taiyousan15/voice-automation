"""RSS feed generator for podcast episodes"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import quote


class RSSGenerator:
    """Generate RSS 2.0 feed for podcast episodes"""

    def __init__(
        self,
        title: str = "ポッドキャスト自動配信",
        description: str = "AI自動生成のポッドキャストエピソード",
        language: str = "ja-jp",
        author: str = "Podcast Automation System",
        link: str = "https://example.com",
    ):
        """Initialize RSS generator"""
        self.title = title
        self.description = description
        self.language = language
        self.author = author
        self.link = link

    def generate_feed(self, episodes: List[Dict[str, Any]]) -> str:
        """
        Generate RSS 2.0 feed from episodes

        Args:
            episodes: List of episode dicts with theme, scripts, articles

        Returns:
            RSS 2.0 XML string
        """
        items = []
        for i, episode in enumerate(episodes, 1):
            theme = episode.get("theme", "episode")
            script = episode.get("script", "")
            articles = episode.get("articles", [])
            processing_time = episode.get("processing_time", 0)

            # Build description with article list
            description = self._build_description(articles, script)

            # Create item
            item = self._create_item(
                title=f"エピソード {i}: {theme.capitalize()}",
                description=description,
                theme=theme,
                index=i,
                pub_date=datetime.now().isoformat(),
                guid=f"episode_{theme}_{i}_{int(datetime.now().timestamp())}",
            )

            items.append(item)

        # Build RSS
        feed = self._build_rss("".join(items))
        return feed

    def _build_description(self, articles: List[Dict], script: str) -> str:
        """Build episode description with article references"""
        parts = []

        # Add script preview
        if script:
            preview = (script[:200] + "...") if len(script) > 200 else script
            parts.append(f"<![CDATA[{preview}]]>")

        # Add article list
        if articles:
            parts.append("\n\n記事一覧:")
            for article in articles:
                title = article.get("title", "")
                source = article.get("source", "")
                trust_score = article.get("trust_score", 0)
                parts.append(
                    f"  • {title} (出典: {source}, 信頼度: {trust_score:.1f}/10)"
                )

        return "\n".join(parts)

    def _create_item(
        self,
        title: str,
        description: str,
        theme: str,
        index: int,
        pub_date: str,
        guid: str,
    ) -> str:
        """Create RSS item XML"""
        return f"""    <item>
        <title>{self._escape_xml(title)}</title>
        <description>{description}</description>
        <category>{theme}</category>
        <pubDate>{pub_date}</pubDate>
        <guid isPermaLink="false">{guid}</guid>
        <link>{self.link}/episodes/{quote(theme)}/{index}</link>
    </item>
"""

    def _build_rss(self, items_xml: str) -> str:
        """Build complete RSS 2.0 feed"""
        now = datetime.now().isoformat()
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
    <channel>
        <title>{self._escape_xml(self.title)}</title>
        <link>{self.link}</link>
        <description>{self._escape_xml(self.description)}</description>
        <language>{self.language}</language>
        <managingEditor>{self.author}</managingEditor>
        <lastBuildDate>{now}</lastBuildDate>
        <generator>Podcast Automation System</generator>
{items_xml}    </channel>
</rss>
"""

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters"""
        if not text:
            return ""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    def save_feed(self, episodes: List[Dict[str, Any]], output_path: Path) -> Path:
        """
        Save RSS feed to file

        Args:
            episodes: List of episodes
            output_path: Path to save feed.xml

        Returns:
            Path to saved feed file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        feed = self.generate_feed(episodes)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(feed)

        return output_path

    @staticmethod
    def validate_feed(feed_xml: str) -> bool:
        """
        Validate RSS 2.0 feed structure (basic check)

        Args:
            feed_xml: RSS feed XML string

        Returns:
            True if feed has required elements
        """
        required_tags = ["<rss", "<channel>", "<title>", "</rss>"]
        return all(tag in feed_xml for tag in required_tags)
