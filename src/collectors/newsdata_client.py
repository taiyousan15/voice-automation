"""NewsData.io API Client - News article collection"""
import os
import time
from typing import Optional, List, Dict, Any
import requests
from datetime import datetime, timedelta
from loguru import logger


class NewsDataClient:
    """NewsData.io API client for collecting news articles"""

    def __init__(self):
        """Initialize NewsData.io client"""
        api_key = os.getenv("NEWSDATA_API_KEY")
        if not api_key:
            raise ValueError("NEWSDATA_API_KEY environment variable is required")

        self.api_key = api_key
        self.base_url = "https://newsdata.io/api/1"
        self.languages = os.getenv("NEWSDATA_LANGUAGES", "ja").split(",")
        self.country = os.getenv("NEWSDATA_COUNTRY", "jp")
        self.search_limit = int(os.getenv("NEWSDATA_SEARCH_LIMIT", "10"))
        self.timeout = 30

        logger.info(f"NewsData.io client initialized - Languages: {self.languages}")

    def search_news(
        self,
        query: str,
        language: str = "ja",
        category: Optional[str] = None,
        max_results: int = 10,
        sort_by: str = "publishedAt"
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Search for news articles

        Args:
            query: Search query (e.g., "AI", "Technology")
            language: Language code (e.g., "ja", "en")
            category: Category filter (optional)
            max_results: Maximum number of results
            sort_by: Sort order ("publishedAt", "popularity", "rank")

        Returns:
            List of articles or None on failure
        """
        try:
            params = {
                "apikey": self.api_key,
                "q": query,
                "language": language,
                "size": min(max_results, self.search_limit)
                # Note: sortby parameter is not supported in /news endpoint
            }

            if category:
                params["category"] = category

            if self.country:
                params["country"] = self.country

            logger.debug(f"Searching articles: query='{query}', language='{language}'")
            response = requests.get(
                f"{self.base_url}/news",
                params=params,
                timeout=self.timeout
            )

            if response.status_code != 200:
                logger.error(f"NewsData.io API error: {response.status_code} - {response.text}")
                return None

            data = response.json()

            if data.get("status") != "success":
                logger.error(f"API returned status: {data.get('status')} - {data.get('message')}")
                return None

            articles = data.get("results", [])
            logger.info(f"✓ Found {len(articles)} articles for query: {query}")
            return self._normalize_articles(articles)

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error searching articles: {e}")
            return None

    def get_trending_topics(self, language: str = "ja") -> Optional[List[Dict[str, Any]]]:
        """Get trending news topics"""
        try:
            # Try to fetch trending articles by searching for recent news
            trending_queries = ["今日のニュース", "最新ニュース", "速報"]

            all_articles = []
            for query in trending_queries[:1]:  # Limit to avoid quota issues
                articles = self.search_news(
                    query=query,
                    language=language,
                    max_results=5
                )
                if articles:
                    all_articles.extend(articles)

            # Remove duplicates by source
            unique_articles = []
            seen_links = set()
            for article in all_articles:
                link = article.get("link")
                if link not in seen_links:
                    unique_articles.append(article)
                    seen_links.add(link)

            return unique_articles

        except Exception as e:
            logger.error(f"Error fetching trending topics: {e}")
            return None

    def _normalize_articles(self, raw_articles: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize articles to standard format"""
        normalized = []
        for article in raw_articles:
            normalized.append({
                "title": article.get("title", ""),
                "description": article.get("description", "") or article.get("content", ""),
                "content": article.get("content", article.get("description", "")),
                "source": article.get("source_id", ""),
                "source_name": article.get("source_name", article.get("source_id", "")),
                "link": article.get("link", ""),
                "image": article.get("image_url", ""),
                "published_at": article.get("pubDate", ""),
                "country": article.get("country", [self.country]),
                "category": article.get("category", []),
                "language": article.get("language", ""),
                "original_data": article
            })
        return normalized

    def get_articles_by_category(
        self,
        category: str,
        language: str = "ja",
        max_results: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """Get articles by category"""
        try:
            params = {
                "apikey": self.api_key,
                "category": category,
                "language": language,
                "country": self.country,
                "size": min(max_results, self.search_limit)
                # Note: sortby parameter is not supported in /news endpoint
            }

            logger.debug(f"Fetching articles by category: {category}")
            response = requests.get(
                f"{self.base_url}/news",
                params=params,
                timeout=self.timeout
            )

            if response.status_code != 200:
                logger.error(f"API error: {response.status_code}")
                return None

            data = response.json()
            if data.get("status") != "success":
                logger.error(f"API status: {data.get('status')}")
                return None

            articles = data.get("results", [])
            logger.info(f"✓ Found {len(articles)} articles in category: {category}")
            return self._normalize_articles(articles)

        except Exception as e:
            logger.error(f"Error fetching category articles: {e}")
            return None
