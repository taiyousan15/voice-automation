"""Tests for publisher modules and distribution manager"""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.publishers.note_publisher import NotePublisher
from src.publishers.x_publisher import XPublisher, TWEET_MAX_LENGTH, URL_DISPLAY_LENGTH


# ===== NotePublisher Tests =====

class TestNotePublisher:
    def test_generate_template_contains_required_sections(self):
        publisher = NotePublisher()
        template = publisher.generate_template(
            episode_title="テストエピソード",
            description="テスト説明文",
            audio_url="https://example.com/audio.mp3",
            rss_url="https://example.com/feed.xml",
            theme="technology",
        )
        assert "テストエピソード" in template
        assert "https://example.com/audio.mp3" in template
        assert "https://example.com/feed.xml" in template
        assert "technology" in template

    def test_generate_template_truncates_long_description(self):
        publisher = NotePublisher()
        long_desc = "あ" * 500
        template = publisher.generate_template(
            episode_title="長い説明テスト",
            description=long_desc,
            audio_url="https://example.com/audio.mp3",
            rss_url="https://example.com/feed.xml",
            theme="test",
        )
        assert "..." in template
        assert "あ" * 301 not in template

    def test_save_template_creates_file(self, tmp_path):
        publisher = NotePublisher()
        template = "# Test Template\n\nContent here."
        out_path = tmp_path / "subdir" / "note_template.md"

        result = publisher.save_template(template, out_path)

        assert result == out_path
        assert out_path.exists()
        assert out_path.read_text(encoding="utf-8") == template


# ===== XPublisher Tests =====

class TestXPublisher:
    @patch.dict("os.environ", {
        "TWITTER_API_KEY": "key",
        "TWITTER_API_SECRET": "secret",
        "TWITTER_ACCESS_TOKEN": "token",
        "TWITTER_ACCESS_TOKEN_SECRET": "token_secret",
    })
    @patch("src.publishers.x_publisher.OAUTHLIB_AVAILABLE", True)
    def test_build_tweet_text_within_limit(self):
        publisher = XPublisher()
        text = publisher._build_tweet_text(
            episode_title="短いタイトル",
            theme="tech",
            audio_url="https://example.com/ep.mp3",
        )
        effective_len = len(text) - len("https://example.com/ep.mp3") + URL_DISPLAY_LENGTH
        assert effective_len <= TWEET_MAX_LENGTH

    @patch.dict("os.environ", {
        "TWITTER_API_KEY": "key",
        "TWITTER_API_SECRET": "secret",
        "TWITTER_ACCESS_TOKEN": "token",
        "TWITTER_ACCESS_TOKEN_SECRET": "token_secret",
    })
    @patch("src.publishers.x_publisher.OAUTHLIB_AVAILABLE", True)
    def test_build_tweet_truncates_long_title(self):
        publisher = XPublisher()
        long_title = "非常に長いエピソードタイトル" * 20
        text = publisher._build_tweet_text(
            episode_title=long_title,
            theme="tech",
            audio_url="https://example.com/ep.mp3",
        )
        effective_len = len(text) - len("https://example.com/ep.mp3") + URL_DISPLAY_LENGTH
        assert effective_len <= TWEET_MAX_LENGTH
        assert "..." in text

    @patch.dict("os.environ", {
        "TWITTER_API_KEY": "key",
        "TWITTER_API_SECRET": "secret",
        "TWITTER_ACCESS_TOKEN": "token",
        "TWITTER_ACCESS_TOKEN_SECRET": "token_secret",
    })
    @patch("src.publishers.x_publisher.OAUTHLIB_AVAILABLE", True)
    @patch("src.publishers.x_publisher.OAuth1Session")
    def test_post_episode_tweet_success(self, mock_session_cls):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"data": {"id": "12345"}}
        mock_session.post.return_value = mock_response
        mock_session_cls.return_value = mock_session

        publisher = XPublisher()
        result = publisher.post_episode_tweet(
            episode_title="テスト", theme="tech",
            audio_url="https://example.com/ep.mp3",
        )
        assert result is not None
        assert result["data"]["id"] == "12345"

    @patch.dict("os.environ", {
        "TWITTER_API_KEY": "key",
        "TWITTER_API_SECRET": "secret",
        "TWITTER_ACCESS_TOKEN": "token",
        "TWITTER_ACCESS_TOKEN_SECRET": "token_secret",
    })
    @patch("src.publishers.x_publisher.OAUTHLIB_AVAILABLE", True)
    @patch("src.publishers.x_publisher.OAuth1Session")
    def test_post_episode_tweet_failure(self, mock_session_cls):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_session.post.return_value = mock_response
        mock_session_cls.return_value = mock_session

        publisher = XPublisher()
        result = publisher.post_episode_tweet(
            episode_title="テスト", theme="tech",
            audio_url="https://example.com/ep.mp3",
        )
        assert result is None


# ===== YouTubePublisher Tests =====

class TestYouTubePublisher:
    @patch("src.publishers.youtube_publisher.GOOGLE_API_AVAILABLE", True)
    @patch("src.publishers.youtube_publisher.build")
    @patch("src.publishers.youtube_publisher.Credentials")
    def test_create_video_from_audio_calls_ffmpeg(self, mock_creds, mock_build, tmp_path):
        import base64
        creds_json = base64.b64encode(json.dumps({"type": "service_account"}).encode()).decode()

        with patch.dict("os.environ", {
            "YOUTUBE_CREDENTIALS_JSON": creds_json,
            "YOUTUBE_CHANNEL_ID": "UC_test",
        }):
            mock_creds.from_service_account_info.return_value = MagicMock()
            publisher = __import__(
                "src.publishers.youtube_publisher", fromlist=["YouTubePublisher"]
            ).YouTubePublisher()

        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"\x00" * 100)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = publisher.create_video_from_audio(audio_file)

        assert mock_run.called
        cmd_args = mock_run.call_args[0][0]
        assert cmd_args[0] == "ffmpeg"
        assert "-shortest" in cmd_args

    @patch("src.publishers.youtube_publisher.GOOGLE_API_AVAILABLE", True)
    @patch("src.publishers.youtube_publisher.build")
    @patch("src.publishers.youtube_publisher.Credentials")
    def test_create_video_ffmpeg_not_found(self, mock_creds, mock_build, tmp_path):
        import base64
        creds_json = base64.b64encode(json.dumps({"type": "service_account"}).encode()).decode()

        with patch.dict("os.environ", {
            "YOUTUBE_CREDENTIALS_JSON": creds_json,
            "YOUTUBE_CHANNEL_ID": "UC_test",
        }):
            mock_creds.from_service_account_info.return_value = MagicMock()
            publisher = __import__(
                "src.publishers.youtube_publisher", fromlist=["YouTubePublisher"]
            ).YouTubePublisher()

        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"\x00" * 100)
        # Provide a thumbnail so _create_default_thumbnail is not called
        thumb = tmp_path / "thumb.png"
        thumb.write_bytes(b"\x00" * 10)

        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = publisher.create_video_from_audio(audio_file, thumbnail_path=thumb)

        assert result is None

    @patch("src.publishers.youtube_publisher.GOOGLE_API_AVAILABLE", True)
    @patch("src.publishers.youtube_publisher.build")
    @patch("src.publishers.youtube_publisher.Credentials")
    @patch("src.publishers.youtube_publisher.MediaFileUpload")
    def test_upload_video_success(self, mock_media, mock_creds, mock_build, tmp_path):
        import base64
        creds_json = base64.b64encode(json.dumps({"type": "service_account"}).encode()).decode()

        mock_youtube = MagicMock()
        mock_insert = MagicMock()
        mock_insert.next_chunk.return_value = (None, {"id": "vid_123"})
        mock_youtube.videos.return_value.insert.return_value = mock_insert
        mock_build.return_value = mock_youtube

        with patch.dict("os.environ", {
            "YOUTUBE_CREDENTIALS_JSON": creds_json,
            "YOUTUBE_CHANNEL_ID": "UC_test",
        }):
            mock_creds.from_service_account_info.return_value = MagicMock()
            publisher = __import__(
                "src.publishers.youtube_publisher", fromlist=["YouTubePublisher"]
            ).YouTubePublisher()

        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"\x00" * 100)

        result = publisher.upload_video(video_file, "Title", "Description")
        assert result is not None
        assert result["id"] == "vid_123"


# ===== DistributionManager Tests =====

class TestDistributionManager:
    @patch("src.publishers.distribution_manager.DistributionManager.__init__", return_value=None)
    def test_skips_unconfigured_platforms(self, mock_init):
        from src.publishers.distribution_manager import DistributionManager
        manager = DistributionManager()
        manager.logger = MagicMock()
        manager._note_publisher = None
        manager._x_publisher = None
        manager._youtube_publisher = None

        report = manager.distribute_episode(
            episode_title="テスト", theme="tech",
            audio_url="https://example.com/ep.mp3",
        )
        assert len(report.skipped_platforms) == 3
        assert len(report.failed) == 0

    @patch("src.publishers.distribution_manager.DistributionManager.__init__", return_value=None)
    def test_independent_platform_execution(self, mock_init):
        from src.publishers.distribution_manager import DistributionManager
        manager = DistributionManager()
        manager.logger = MagicMock()

        # note succeeds, x fails, youtube skipped
        mock_note = MagicMock()
        mock_note.generate_template.return_value = "# Template"
        mock_note.save_template.return_value = Path("/tmp/note.md")
        manager._note_publisher = mock_note

        mock_x = MagicMock()
        mock_x.post_episode_tweet.side_effect = Exception("API Error")
        manager._x_publisher = mock_x

        manager._youtube_publisher = None

        report = manager.distribute_episode(
            episode_title="テスト", theme="tech",
            audio_url="https://example.com/ep.mp3",
            output_dir=Path("/tmp"),
        )
        assert len(report.successful) == 1
        assert report.successful[0].platform == "note.com"
        assert len(report.failed) == 1
        assert report.failed[0].platform == "X/Twitter"
        assert len(report.skipped_platforms) == 1

    @patch("src.publishers.distribution_manager.DistributionManager.__init__", return_value=None)
    def test_distribution_report_properties(self, mock_init):
        from src.publishers.distribution_manager import DistributionManager, DistributionResult
        manager = DistributionManager()
        manager.logger = MagicMock()
        manager._note_publisher = None
        manager._x_publisher = None
        manager._youtube_publisher = None

        report = manager.distribute_episode(
            episode_title="テスト", theme="tech",
        )
        assert len(report.results) == 3
        assert all(r.skipped for r in report.results)
