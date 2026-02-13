"""Article deduplication system"""
import hashlib
from typing import List, Dict, Any, Set
from loguru import logger


class DeduplicationEngine:
    """Deduplication engine for news articles"""

    def __init__(self):
        """Initialize deduplication engine"""
        self.seen_hashes: Set[str] = set()
        self.seen_urls: Set[str] = set()
        logger.info("Deduplication engine initialized")

    def get_url_hash(self, url: str) -> str:
        """Generate MD5 hash of URL"""
        return hashlib.md5(url.encode()).hexdigest()

    def get_content_hash(self, content: str) -> str:
        """Generate MD5 hash of content (title + description)"""
        # Normalize content
        normalized = content.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()

    def is_duplicate(self, article: Dict[str, Any]) -> bool:
        """
        Check if article is duplicate based on URL and content

        Args:
            article: Article dict with 'link', 'title', 'description'

        Returns:
            True if duplicate, False otherwise
        """
        url = article.get("link", "")
        title = article.get("title", "")
        description = article.get("description", "")

        # Check URL
        if url:
            url_hash = self.get_url_hash(url)
            if url_hash in self.seen_hashes:
                logger.debug(f"Duplicate URL detected: {url}")
                return True
            self.seen_hashes.add(url_hash)
            self.seen_urls.add(url)

        # Check content similarity
        if title and description:
            content = f"{title} {description}"
            content_hash = self.get_content_hash(content)
            if content_hash in self.seen_hashes:
                logger.debug(f"Duplicate content detected: {title[:50]}...")
                return True
            self.seen_hashes.add(content_hash)

        return False

    def filter_duplicates(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out duplicate articles

        Args:
            articles: List of articles

        Returns:
            List of unique articles
        """
        unique_articles = []
        duplicate_count = 0

        for article in articles:
            if not self.is_duplicate(article):
                unique_articles.append(article)
            else:
                duplicate_count += 1

        logger.info(f"Filtered articles: {len(unique_articles)} unique, {duplicate_count} duplicates removed")
        return unique_articles

    def clear_cache(self):
        """Clear deduplication cache"""
        self.seen_hashes.clear()
        self.seen_urls.clear()
        logger.info("Deduplication cache cleared")

    def get_stats(self) -> Dict[str, int]:
        """Get deduplication statistics"""
        return {
            "total_hashes": len(self.seen_hashes),
            "total_urls": len(self.seen_urls)
        }
