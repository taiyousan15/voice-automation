"""VOICEVOX Nemo TTS client for podcast audio generation"""
import asyncio
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import httpx
from loguru import logger


class VOICEVOXClient:
    """VOICEVOX Nemo TTS client for generating podcast audio"""

    def __init__(
        self,
        api_url: Optional[str] = None,
        speaker_id: int = 0,
        output_dir: Optional[Path] = None,
    ):
        """Initialize VOICEVOX client

        Args:
            api_url: VOICEVOX API base URL (default: http://localhost:50021)
            speaker_id: Speaker ID for voice selection (default: 0)
            output_dir: Output directory for generated audio files
        """
        self.api_url = api_url or os.getenv(
            "VOICEVOX_API_URL", "http://localhost:50021"
        )
        self.speaker_id = speaker_id
        self.output_dir = output_dir or Path(__file__).parent.parent.parent / "episodes"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"VOICEVOX client initialized - API: {self.api_url}, Speaker: {self.speaker_id}")

    async def test_connection(self) -> bool:
        """Test VOICEVOX API connection

        Returns:
            True if API is reachable, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.api_url}/speakers")
                if response.status_code == 200:
                    logger.info("✓ VOICEVOX API connection successful")
                    return True
                else:
                    logger.error(f"✗ VOICEVOX API returned {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"✗ VOICEVOX API connection failed: {e}")
            return False

    async def generate_audio(self, text: str) -> Optional[Path]:
        """Generate WAV audio from text using VOICEVOX API

        Args:
            text: Text to convert to speech

        Returns:
            Path to generated WAV file, or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Step 1: Create audio query
                logger.debug(f"Creating audio query for {len(text)} characters...")
                query_response = await client.post(
                    f"{self.api_url}/audio_query",
                    params={"text": text, "speaker": self.speaker_id},
                )
                query_response.raise_for_status()
                audio_query = query_response.json()

                # Step 2: Synthesize audio
                logger.debug("Synthesizing audio...")
                synthesis_response = await client.post(
                    f"{self.api_url}/synthesis",
                    params={"speaker": self.speaker_id},
                    json=audio_query,
                )
                synthesis_response.raise_for_status()

                # Step 3: Save WAV file
                wav_file = self.output_dir / f"temp_{os.getpid()}.wav"
                with open(wav_file, "wb") as f:
                    f.write(synthesis_response.content)

                logger.info(f"✓ Audio generated: {wav_file}")
                return wav_file

        except httpx.HTTPStatusError as e:
            logger.error(f"✗ VOICEVOX API error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"✗ Audio generation failed: {e}")
            return None

    def convert_to_mp3(self, wav_file: Path, output_filename: str) -> Optional[Path]:
        """Convert WAV to MP3 using FFmpeg

        Args:
            wav_file: Path to WAV file
            output_filename: Desired MP3 filename (e.g., "episode_1.mp3")

        Returns:
            Path to generated MP3 file, or None if failed
        """
        try:
            mp3_file = self.output_dir / output_filename

            # Check ffmpeg availability
            result = subprocess.run(
                ["which", "ffmpeg"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                logger.error("✗ ffmpeg not found - install with: brew install ffmpeg")
                return None

            # Convert WAV to MP3 (128kbps for podcasts)
            logger.debug(f"Converting {wav_file} to MP3...")
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i", str(wav_file),
                    "-b:a", "128k",
                    "-y",  # Overwrite without asking
                    str(mp3_file),
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"✗ FFmpeg conversion failed: {result.stderr}")
                return None

            # Clean up WAV file
            wav_file.unlink()
            logger.info(f"✓ MP3 generated: {mp3_file}")
            return mp3_file

        except Exception as e:
            logger.error(f"✗ MP3 conversion failed: {e}")
            return None

    def get_audio_duration(self, audio_file: Path) -> Optional[str]:
        """Get audio duration in HH:MM:SS format using ffprobe

        Args:
            audio_file: Path to audio file

        Returns:
            Duration string (HH:MM:SS), or None if failed
        """
        try:
            # Check ffprobe availability
            result = subprocess.run(
                ["which", "ffprobe"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                logger.error("✗ ffprobe not found - install with: brew install ffmpeg")
                return None

            # Get duration using ffprobe
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(audio_file),
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"✗ ffprobe failed: {result.stderr}")
                return None

            # Convert seconds to HH:MM:SS
            total_seconds = float(result.stdout.strip())
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)

            duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            logger.debug(f"Audio duration: {duration}")
            return duration

        except Exception as e:
            logger.error(f"✗ Duration extraction failed: {e}")
            return None

    async def generate_podcast_audio(
        self,
        text: str,
        output_filename: str,
    ) -> Optional[Path]:
        """Generate podcast audio (end-to-end workflow)

        Args:
            text: Text to convert to speech
            output_filename: Desired MP3 filename (e.g., "episode_technology_20260214.mp3")

        Returns:
            Path to generated MP3 file, or None if failed
        """
        try:
            logger.info(f"Starting podcast audio generation: {output_filename}")

            # Step 1: Generate WAV
            wav_file = await self.generate_audio(text)
            if not wav_file or not wav_file.exists():
                logger.error("✗ WAV generation failed")
                return None

            # Step 2: Convert to MP3
            mp3_file = self.convert_to_mp3(wav_file, output_filename)
            if not mp3_file or not mp3_file.exists():
                logger.error("✗ MP3 conversion failed")
                return None

            logger.info(f"✓ Podcast audio generated: {mp3_file}")
            return mp3_file

        except Exception as e:
            logger.error(f"✗ Podcast audio generation failed: {e}")
            return None


# Test/Debug execution
if __name__ == "__main__":
    import sys

    async def test_voicevox():
        """Test VOICEVOX client"""
        client = VOICEVOXClient()

        # Test 1: Connection check
        print("\\n" + "=" * 70)
        print("TEST 1: VOICEVOX API Connection")
        print("=" * 70)
        is_connected = await client.test_connection()
        if not is_connected:
            print("\\n⚠ VOICEVOX API is not running or not accessible")
            print("Please start VOICEVOX Nemo server or use Google Colab")
            print("See: scripts/test_voicevox.py for setup instructions")
            return

        # Test 2: Short audio generation
        print("\\n" + "=" * 70)
        print("TEST 2: Short Audio Generation")
        print("=" * 70)
        test_text = "こんにちは。VOICEVOX Nemo のテストです。"
        audio_file = await client.generate_podcast_audio(
            text=test_text,
            output_filename="test_voicevox.mp3",
        )

        if audio_file and audio_file.exists():
            print(f"\\n✓ Audio generated: {audio_file}")
            print(f"  File size: {audio_file.stat().st_size:,} bytes")

            duration = client.get_audio_duration(audio_file)
            if duration:
                print(f"  Duration: {duration}")
        else:
            print("\\n✗ Audio generation failed")

        print("\\n" + "=" * 70)
        print("VOICEVOX Client Test Complete")
        print("=" * 70)

    # Run test
    asyncio.run(test_voicevox())
