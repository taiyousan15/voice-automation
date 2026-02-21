"""X (Twitter) publisher for podcast episode announcements"""
import os
import time
from typing import Dict, List, Optional

from loguru import logger

try:
    from requests_oauthlib import OAuth1Session
    OAUTHLIB_AVAILABLE = True
except ImportError:
    OAUTHLIB_AVAILABLE = False


TWEETS_ENDPOINT = "https://api.twitter.com/2/tweets"
TWEET_MAX_LENGTH = 280
URL_DISPLAY_LENGTH = 23  # X counts all URLs as 23 chars


class XPublisher:
    """Post episode announcements to X (Twitter) via API v2."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("TWITTER_API_KEY", "")
        self.api_secret = api_secret or os.getenv("TWITTER_API_SECRET", "")
        self.access_token = access_token or os.getenv("TWITTER_ACCESS_TOKEN", "")
        self.access_token_secret = access_token_secret or os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
        self.logger = logger

        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            raise ValueError("Twitter API credentials not configured")

        if not OAUTHLIB_AVAILABLE:
            raise ImportError("requests-oauthlib is required: pip install requests-oauthlib")

    def _build_tweet_text(
        self,
        episode_title: str,
        theme: str,
        audio_url: str,
        hashtags: Optional[List[str]] = None,
    ) -> str:
        """Build tweet text within 280-char limit.

        Args:
            episode_title: Episode title
            theme: Episode theme
            audio_url: Public URL to the episode
            hashtags: Optional list of hashtags (without #)

        Returns:
            Tweet text string within character limit
        """
        tags = hashtags or [theme, "ポッドキャスト", "AI"]
        hashtag_str = " ".join(f"#{t}" for t in tags)

        body = f"新エピソード公開\n{episode_title}\n\n{audio_url}\n\n{hashtag_str}"

        # Calculate effective length (URLs count as 23 chars)
        effective_len = len(body) - len(audio_url) + URL_DISPLAY_LENGTH

        if effective_len > TWEET_MAX_LENGTH:
            overflow = effective_len - TWEET_MAX_LENGTH
            max_title_len = max(10, len(episode_title) - overflow - 3)
            truncated_title = episode_title[:max_title_len] + "..."
            body = f"新エピソード公開\n{truncated_title}\n\n{audio_url}\n\n{hashtag_str}"

        return body

    def post_episode_tweet(
        self,
        episode_title: str,
        theme: str,
        audio_url: str,
        hashtags: Optional[List[str]] = None,
        max_retries: int = 3,
    ) -> Optional[Dict]:
        """Post an episode announcement tweet.

        Args:
            episode_title: Episode title
            theme: Episode theme
            audio_url: Public URL to the episode
            hashtags: Optional hashtag list
            max_retries: Max retry attempts for rate limits

        Returns:
            API response dict on success, None on failure
        """
        tweet_text = self._build_tweet_text(episode_title, theme, audio_url, hashtags)

        session = OAuth1Session(
            self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret,
        )

        for attempt in range(max_retries):
            response = session.post(TWEETS_ENDPOINT, json={"text": tweet_text})

            if response.status_code == 201:
                data = response.json()
                self.logger.info(f"Tweet posted: {data.get('data', {}).get('id', 'unknown')}")
                return data

            if response.status_code == 429:
                wait = min(2 ** attempt * 5, 60)
                self.logger.warning(f"Rate limited, waiting {wait}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait)
                continue

            self.logger.error(f"Tweet failed ({response.status_code}): {response.text}")
            return None

        self.logger.error(f"Tweet failed after {max_retries} retries (rate limited)")
        return None
