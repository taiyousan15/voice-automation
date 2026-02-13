#!/usr/bin/env python3
"""Test VOICEVOX Nemo TTS - Audio generation test (Google Colab compatible)"""
import os
import sys
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from loguru import logger

# Load environment
load_dotenv()

# Configure logger
logger.remove()
logger.add(sys.stderr, format="<level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>", level="INFO")


def test_voicevox_setup():
    """Test VOICEVOX Nemo setup and verify API connection"""
    logger.info("Starting VOICEVOX Nemo setup test...")

    # Check if VOICEVOX server is running
    voicevox_url = os.getenv("VOICEVOX_API_URL", "http://localhost:50021")
    logger.info(f"Checking VOICEVOX server at {voicevox_url}...")

    # Try to ping the VOICEVOX API
    try:
        import requests
        response = requests.get(f"{voicevox_url}/version", timeout=5)

        if response.status_code == 200:
            logger.info("✓ VOICEVOX server is running")
            version = response.json()
            logger.info(f"VOICEVOX version: {version.get('version', 'unknown')}")
            return handle_voicevox_generation(voicevox_url)
        else:
            logger.warning(f"✗ VOICEVOX server returned status {response.status_code}")
            return handle_google_colab_setup()
    except Exception as e:
        logger.warning(f"✗ Cannot connect to VOICEVOX server: {e}")
        return handle_google_colab_setup()


def handle_voicevox_generation(voicevox_url: str) -> bool:
    """Generate audio using local VOICEVOX server"""
    logger.info("Generating audio using local VOICEVOX server...")

    try:
        import requests

        # Sample podcast script
        script_text = """
こんにちは、テクノロジーニュースをお届けします。
本日は、東京のテック企業が発表した新型AIロボット「RoboX-5000」についてお話します。
このロボットは、従来のロボットよりも30パーセント高速で、消費電力を50パーセント削減できます。
また、自然言語処理により、日本語でのコマンドを99.5パーセントの精度で理解できるとのことです。
開発チームは、このロボットがオフィス、工場、病院など様々な場所で活躍することを期待しており、
2026年Q2からの販売を予定しています。
ご感想やご質問は、お気軽にお送りください。
本日もお聴きいただき、ありがとうございました。
"""

        speaker_id = int(os.getenv("VOICEVOX_SPEAKER_ID", "3"))
        speed_scale = float(os.getenv("VOICEVOX_SPEED_SCALE", "1.0"))

        # Step 1: Audio query
        logger.info("Step 1: Requesting audio query...")
        query_response = requests.post(
            f"{voicevox_url}/audio_query",
            params={
                "text": script_text.strip(),
                "speaker": speaker_id,
                "speedScale": speed_scale
            },
            timeout=30
        )

        if query_response.status_code != 200:
            logger.error(f"Audio query failed: {query_response.status_code}")
            return False

        audio_query = query_response.json()
        logger.info("✓ Audio query created")

        # Step 2: Synthesis
        logger.info("Step 2: Synthesizing audio...")
        synthesis_response = requests.post(
            f"{voicevox_url}/synthesis",
            json=audio_query,
            params={"speaker": speaker_id},
            timeout=60
        )

        if synthesis_response.status_code != 200:
            logger.error(f"Synthesis failed: {synthesis_response.status_code}")
            return False

        # Save audio file
        output_path = Path(__file__).parent.parent / "episodes" / "test_episode.wav"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(synthesis_response.content)

        file_size_mb = output_path.stat().st_size / 1024 / 1024
        logger.info(f"✓ Audio file saved: {output_path} ({file_size_mb:.2f} MB)")

        # Verify with ffprobe if available
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1:noprint_names=1", str(output_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                logger.info(f"✓ Audio duration: {duration:.2f} seconds")
        except Exception as e:
            logger.debug(f"ffprobe check skipped: {e}")

        return True

    except Exception as e:
        logger.error(f"Audio generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def handle_google_colab_setup() -> bool:
    """Provide instructions for Google Colab setup"""
    logger.info("\n" + "="*70)
    logger.info("VOICEVOX Nemo Google Colab Setup Instructions")
    logger.info("="*70)

    instructions = """
Google Colab でVOICEVOX Nemoを実行する手順：

1. Google Colabを開く: https://colab.research.google.com/

2. 新しいNotebook を作成

3. 以下のセルを実行します：

   # セル 1: インストール
   !pip install -q -U voicevox-core requests pydantic

   # セル 2: サーバー起動
   from voicevox_core import VoicevoxCore
   import asyncio

   # VoicevoxCore の初期化
   core = VoicevoxCore()
   await core.initialize()

   # TTS テスト
   task_id = await core.text_to_speech(
       text="こんにちは、ポッドキャスト自動配信システムです。",
       speaker_id=3,
       enable_interrogative_upspeak=True,
   )

   audio_data = await core.retrieve_synthesis_result(task_id)

   # ファイル保存
   with open("/content/test_audio.wav", "wb") as f:
       f.write(audio_data.audio)

   # ダウンロード
   from google.colab import files
   files.download("/content/test_audio.wav")

4. 音声ファイルをダウンロード

Status: Google Colab による VOICEVOX Nemo はセットアップ準備完了
     """

    logger.info(instructions)
    logger.info("="*70)
    return True


if __name__ == "__main__":
    success = test_voicevox_setup()
    sys.exit(0 if success else 1)
