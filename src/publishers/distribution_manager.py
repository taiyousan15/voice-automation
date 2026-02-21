"""Distribution manager - orchestrates publishing across platforms"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger


@dataclass(frozen=True)
class DistributionResult:
    """Result from a single platform distribution attempt."""
    platform: str
    success: bool
    url: Optional[str] = None
    error: Optional[str] = None
    skipped: bool = False


@dataclass(frozen=True)
class DistributionReport:
    """Aggregated report across all platforms."""
    results: tuple = field(default_factory=tuple)

    @property
    def successful(self) -> List[DistributionResult]:
        return [r for r in self.results if r.success]

    @property
    def failed(self) -> List[DistributionResult]:
        return [r for r in self.results if not r.success and not r.skipped]

    @property
    def skipped_platforms(self) -> List[DistributionResult]:
        return [r for r in self.results if r.skipped]


class DistributionManager:
    """Distribute episodes across configured platforms.

    Each platform is independent - one failure does not block others.
    Missing credentials cause a platform to be skipped, not to fail.
    """

    def __init__(self):
        self.logger = logger
        self._note_publisher = None
        self._x_publisher = None
        self._youtube_publisher = None

        # Lazy-init each publisher; missing credentials = skip
        try:
            from src.publishers.note_publisher import NotePublisher
            self._note_publisher = NotePublisher()
        except Exception as e:
            self.logger.debug(f"note.com publisher not available: {e}")

        try:
            from src.publishers.x_publisher import XPublisher
            self._x_publisher = XPublisher()
        except Exception as e:
            self.logger.debug(f"X/Twitter publisher not available: {e}")

        try:
            from src.publishers.youtube_publisher import YouTubePublisher
            self._youtube_publisher = YouTubePublisher()
        except Exception as e:
            self.logger.debug(f"YouTube publisher not available: {e}")

    def distribute_episode(
        self,
        episode_title: str,
        theme: str,
        audio_path: Optional[Path] = None,
        audio_url: Optional[str] = None,
        description: str = "",
        rss_url: str = "",
        output_dir: Optional[Path] = None,
    ) -> DistributionReport:
        """Distribute an episode to all configured platforms.

        Args:
            episode_title: Episode title
            theme: Episode theme/category
            audio_path: Local path to the MP3 file
            audio_url: Public URL to the MP3 file
            description: Episode description text
            rss_url: RSS feed URL
            output_dir: Directory for generated templates

        Returns:
            DistributionReport with per-platform results
        """
        results = []

        results.append(self._distribute_note(
            episode_title, description, audio_url or "", rss_url, theme, output_dir,
        ))
        results.append(self._distribute_x(episode_title, theme, audio_url or ""))
        results.append(self._distribute_youtube(
            audio_path, episode_title, description, theme,
        ))

        report = DistributionReport(results=tuple(results))

        self.logger.info(
            f"Distribution complete: {len(report.successful)} succeeded, "
            f"{len(report.failed)} failed, {len(report.skipped_platforms)} skipped"
        )
        return report

    def _distribute_note(
        self, title: str, description: str, audio_url: str,
        rss_url: str, theme: str, output_dir: Optional[Path],
    ) -> DistributionResult:
        if not self._note_publisher:
            return DistributionResult(platform="note.com", success=False, skipped=True)
        try:
            template = self._note_publisher.generate_template(
                episode_title=title, description=description,
                audio_url=audio_url, rss_url=rss_url, theme=theme,
            )
            out_dir = output_dir or Path("episodes")
            safe_theme = theme.replace("/", "_").replace(" ", "_")
            path = out_dir / f"note_template_{safe_theme}.md"
            self._note_publisher.save_template(template, path)
            return DistributionResult(platform="note.com", success=True, url=str(path))
        except Exception as e:
            self.logger.warning(f"note.com distribution failed: {e}")
            return DistributionResult(platform="note.com", success=False, error=str(e))

    def _distribute_x(self, title: str, theme: str, audio_url: str) -> DistributionResult:
        if not self._x_publisher:
            return DistributionResult(platform="X/Twitter", success=False, skipped=True)
        try:
            response = self._x_publisher.post_episode_tweet(
                episode_title=title, theme=theme, audio_url=audio_url,
            )
            if response:
                tweet_id = response.get("data", {}).get("id", "")
                url = f"https://x.com/i/status/{tweet_id}" if tweet_id else None
                return DistributionResult(platform="X/Twitter", success=True, url=url)
            return DistributionResult(platform="X/Twitter", success=False, error="No response")
        except Exception as e:
            self.logger.warning(f"X/Twitter distribution failed: {e}")
            return DistributionResult(platform="X/Twitter", success=False, error=str(e))

    def _distribute_youtube(
        self, audio_path: Optional[Path], title: str, description: str, theme: str,
    ) -> DistributionResult:
        if not self._youtube_publisher:
            return DistributionResult(platform="YouTube", success=False, skipped=True)
        if not audio_path or not Path(audio_path).exists():
            return DistributionResult(
                platform="YouTube", success=False, skipped=True,
                error="No audio file available",
            )
        try:
            response = self._youtube_publisher.publish_episode(
                audio_path=audio_path, title=title,
                description=description, tags=[theme, "ポッドキャスト", "AI"],
            )
            if response:
                video_id = response.get("id", "")
                url = f"https://youtu.be/{video_id}" if video_id else None
                return DistributionResult(platform="YouTube", success=True, url=url)
            return DistributionResult(platform="YouTube", success=False, error="Upload failed")
        except Exception as e:
            self.logger.warning(f"YouTube distribution failed: {e}")
            return DistributionResult(platform="YouTube", success=False, error=str(e))
