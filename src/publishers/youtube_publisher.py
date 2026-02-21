"""YouTube publisher for podcast episodes - video creation and upload"""
import base64
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.oauth2.service_account import Credentials
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


YOUTUBE_API_SERVICE = "youtube"
YOUTUBE_API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubePublisher:
    """Create videos from audio and upload to YouTube via Data API v3."""

    def __init__(
        self,
        credentials_json: Optional[str] = None,
        channel_id: Optional[str] = None,
        playlist_id: Optional[str] = None,
    ):
        self.logger = logger

        creds_b64 = credentials_json or os.getenv("YOUTUBE_CREDENTIALS_JSON", "")
        self.channel_id = channel_id or os.getenv("YOUTUBE_CHANNEL_ID", "")
        self.playlist_id = playlist_id or os.getenv("YOUTUBE_PLAYLIST_ID", "")

        if not creds_b64 or not self.channel_id:
            raise ValueError("YouTube credentials or channel ID not configured")

        if not GOOGLE_API_AVAILABLE:
            raise ImportError(
                "google-api-python-client and google-auth are required: "
                "pip install google-api-python-client google-auth"
            )

        creds_data = json.loads(base64.b64decode(creds_b64))
        credentials = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
        self.youtube = build(YOUTUBE_API_SERVICE, YOUTUBE_API_VERSION, credentials=credentials)

    def create_video_from_audio(
        self,
        audio_path: Path,
        thumbnail_path: Optional[Path] = None,
        output_path: Optional[Path] = None,
    ) -> Optional[Path]:
        """Create a still-image video from audio using FFmpeg.

        Args:
            audio_path: Path to the MP3 audio file
            thumbnail_path: Path to a PNG/JPG thumbnail image
            output_path: Destination video path (defaults to temp file)

        Returns:
            Path to the created MP4 file, or None on failure
        """
        if output_path is None:
            output_path = Path(tempfile.mktemp(suffix=".mp4"))

        # Use provided thumbnail or generate a black frame
        if thumbnail_path and thumbnail_path.exists():
            image_input = str(thumbnail_path)
        else:
            image_input = self._create_default_thumbnail()

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", image_input,
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(output_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                self.logger.error(f"FFmpeg failed: {result.stderr[:500]}")
                return None

            self.logger.info(f"Video created: {output_path}")
            return output_path

        except subprocess.TimeoutExpired:
            self.logger.error("FFmpeg timed out (300s)")
            return None
        except FileNotFoundError:
            self.logger.error("FFmpeg not found. Install with: apt-get install ffmpeg")
            return None

    def upload_video(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        privacy_status: str = "public",
    ) -> Optional[Dict]:
        """Upload a video to YouTube via resumable upload.

        Args:
            video_path: Path to the MP4 file
            title: Video title
            description: Video description
            tags: List of tags/keywords
            privacy_status: "public", "unlisted", or "private"

        Returns:
            API response dict with video ID, or None on failure
        """
        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": (tags or [])[:500],
                "categoryId": "22",  # People & Blogs
                "defaultLanguage": "ja",
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True,
            chunksize=10 * 1024 * 1024,
        )

        try:
            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
            )

            response = None
            while response is None:
                _, response = request.next_chunk()

            video_id = response.get("id")
            self.logger.info(f"Video uploaded: https://youtu.be/{video_id}")
            return response

        except Exception as e:
            self.logger.error(f"YouTube upload failed: {e}")
            return None

    def add_to_playlist(self, video_id: str, playlist_id: Optional[str] = None) -> bool:
        """Add an uploaded video to a playlist.

        Args:
            video_id: YouTube video ID
            playlist_id: Playlist ID (defaults to configured playlist)

        Returns:
            True if added successfully
        """
        pid = playlist_id or self.playlist_id
        if not pid:
            self.logger.debug("No playlist ID configured, skipping")
            return False

        body = {
            "snippet": {
                "playlistId": pid,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id,
                },
            }
        }

        try:
            self.youtube.playlistItems().insert(
                part="snippet",
                body=body,
            ).execute()
            self.logger.info(f"Added video {video_id} to playlist {pid}")
            return True
        except Exception as e:
            self.logger.warning(f"Failed to add to playlist: {e}")
            return False

    def publish_episode(
        self,
        audio_path: Path,
        title: str,
        description: str,
        thumbnail_path: Optional[Path] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        """Full pipeline: create video from audio and upload to YouTube.

        Args:
            audio_path: Path to the MP3 file
            title: Episode title
            description: Episode description
            thumbnail_path: Optional thumbnail image
            tags: Optional tags list

        Returns:
            Upload response dict, or None on failure
        """
        video_path = self.create_video_from_audio(audio_path, thumbnail_path)
        if not video_path:
            return None

        try:
            response = self.upload_video(video_path, title, description, tags)
            if response:
                video_id = response.get("id")
                if video_id and self.playlist_id:
                    self.add_to_playlist(video_id)
            return response
        finally:
            # Clean up temp video file
            if video_path.exists() and "/tmp" in str(video_path):
                video_path.unlink(missing_ok=True)

    @staticmethod
    def _create_default_thumbnail() -> str:
        """Create a simple black 1920x1080 thumbnail for FFmpeg."""
        tmp = tempfile.mktemp(suffix=".png")
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=c=black:s=1920x1080:d=1",
            "-frames:v", "1",
            tmp,
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)
        return tmp
