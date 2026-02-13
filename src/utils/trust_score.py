"""Trust scoring system for news articles"""
from typing import Dict, Any
from loguru import logger


class TrustScoreEngine:
    """Trust score calculation for news articles"""

    # Trusted Japanese news sources
    TRUSTED_SOURCES = {
        "nhk": 9,
        "asahi": 8,
        "yomiuri": 8,
        "nikkei": 8,
        "mainichi": 8,
        "tokyo": 7,
        "bbc": 9,
        "reuters": 8,
        "ap": 8,
        "ft": 8,
        "economist": 7
    }

    def __init__(self):
        """Initialize trust score engine"""
        logger.info("Trust score engine initialized")

    def calculate_score(self, article: Dict[str, Any]) -> float:
        """
        Calculate trust score for article (0-10)

        Args:
            article: Article with source_name, title, description, etc.

        Returns:
            Trust score (0-10)
        """
        score = 5.0  # Base score

        # 1. Source credibility (0-4 points)
        source_score = self._get_source_score(article.get("source_name", "").lower())
        score += source_score

        # 2. Content quality (0-2 points)
        content_score = self._get_content_quality_score(
            article.get("title", ""),
            article.get("description", "")
        )
        score += content_score

        # 3. Recency bonus (-1 to +1 points)
        recency_score = self._get_recency_score(article.get("published_at", ""))
        score += recency_score

        # Clamp to 0-10
        final_score = max(0.0, min(10.0, score))
        return round(final_score, 1)

    def _get_source_score(self, source_name: str) -> float:
        """Calculate source credibility score (0-4 points)"""
        source_lower = source_name.lower()

        # Check trusted sources
        for trusted, score in self.TRUSTED_SOURCES.items():
            if trusted in source_lower:
                # Normalized to 4 points max
                return (score / 10) * 4

        # Check for common patterns
        if any(pattern in source_lower for pattern in ["news", "times", "press", "agency"]):
            return 2.0  # Generic news outlet

        if any(pattern in source_lower for pattern in ["blog", "personal", "user"]):
            return 0.5  # Low credibility

        return 1.0  # Default medium credibility

    def _get_content_quality_score(self, title: str, description: str) -> float:
        """Calculate content quality score (0-2 points)"""
        score = 0.0

        # Check title quality
        if title and len(title) > 20 and len(title) < 200:
            score += 0.5

        # Check description length and completeness
        if description:
            if len(description) > 100:
                score += 1.0
            elif len(description) > 50:
                score += 0.5

        return min(2.0, score)

    def _get_recency_score(self, published_at: str) -> float:
        """Calculate recency bonus/penalty (-1 to +1 points)"""
        try:
            from datetime import datetime
            import pytz

            if not published_at:
                return 0.0

            # Parse published date
            # Handle ISO format: 2025-02-12T10:30:00Z
            published_at = published_at.replace("Z", "+00:00")

            try:
                published_date = datetime.fromisoformat(published_at)
            except:
                # Fallback parsing
                published_date = datetime.strptime(published_at[:10], "%Y-%m-%d")

            # Get current time
            now = datetime.now(pytz.UTC) if published_date.tzinfo else datetime.now()

            # Calculate age in hours
            if published_date.tzinfo and now.tzinfo:
                age_hours = (now - published_date).total_seconds() / 3600
            else:
                age_hours = (now - published_date.replace(tzinfo=None)).total_seconds() / 3600

            # Score based on recency
            if age_hours < 24:
                return 1.0  # Recent articles get bonus
            elif age_hours < 7 * 24:
                return 0.5
            elif age_hours < 30 * 24:
                return 0.0
            else:
                return -0.5  # Older articles get penalty

        except Exception as e:
            logger.debug(f"Error calculating recency score: {e}")
            return 0.0

    def filter_by_trust_score(
        self,
        articles: list,
        min_score: float = 0.6
    ) -> list:
        """
        Filter articles by minimum trust score

        Args:
            articles: List of articles
            min_score: Minimum trust score (0-1 scale normalized)

        Returns:
            Filtered articles with scores
        """
        filtered = []

        for article in articles:
            score = self.calculate_score(article)
            # Normalize from 0-10 to 0-1
            normalized_score = score / 10

            if normalized_score >= min_score:
                article["trust_score"] = score
                article["trust_score_normalized"] = normalized_score
                filtered.append(article)

        logger.info(f"Filtered {len(articles)} articles → {len(filtered)} passed trust score > {min_score}")
        return filtered
