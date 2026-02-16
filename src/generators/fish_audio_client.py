"""
Fish Audio TTS Client
=====================

Fish Audio API を使用した高品質日本語音声合成クライアント。

主な機能:
- Text-to-Speech 生成（MP3直接出力）
- 音声メタデータ取得（duration, size）
- エラーハンドリングとリトライ

API仕様:
- Base URL: https://api.fish.audio/v1
- 認証: Bearer Token
- 出力形式: MP3（FFmpeg不要）
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess
import json

import aiohttp
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class FishAudioClient:
    """Fish Audio API クライアント"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_id: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        初期化

        Args:
            api_key: Fish Audio API Key (default: 環境変数 FISH_AUDIO_API_KEY)
            voice_id: Voice ID (default: 環境変数 FISH_AUDIO_VOICE_ID)
            base_url: API Base URL (default: 環境変数 FISH_AUDIO_BASE_URL)
            timeout: タイムアウト秒数 (default: 60)
        """
        self.api_key = api_key or os.getenv("FISH_AUDIO_API_KEY")
        self.voice_id = voice_id or os.getenv("FISH_AUDIO_VOICE_ID")
        self.base_url = (base_url or os.getenv("FISH_AUDIO_BASE_URL", "https://api.fish.audio/v1")).rstrip("/")
        self.timeout = timeout or int(os.getenv("FISH_AUDIO_TIMEOUT_SECONDS", "60"))

        if not self.api_key:
            raise ValueError("FISH_AUDIO_API_KEY が設定されていません")
        if not self.voice_id:
            raise ValueError("FISH_AUDIO_VOICE_ID が設定されていません")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"Fish Audio Client initialized (Voice ID: {self.voice_id[:8]}...)")

    async def test_connection(self) -> bool:
        """
        API 接続テスト（短いテキストで TTS リクエストを送信）

        Returns:
            bool: 接続成功時 True
        """
        try:
            async with aiohttp.ClientSession() as session:
                # 短いテキストで TTS リクエストを送信して接続確認
                url = f"{self.base_url}/tts"
                payload = {
                    "text": "テスト",
                    "reference_id": self.voice_id,
                    "format": "mp3",
                }

                async with session.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as response:
                    if response.status == 200:
                        logger.info("✓ Fish Audio API 接続成功")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"✗ Fish Audio API 接続失敗: HTTP {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"✗ Fish Audio API 接続エラー: {e}")
            return False

    async def generate_audio(
        self,
        text: str,
        output_filename: Optional[str] = None,
        max_retries: int = 2,
        backoff_factor: float = 2.0,
    ) -> Optional[Path]:
        """
        テキストから音声を生成（指数バックオフリトライ付き）

        Args:
            text: 音声化するテキスト
            output_filename: 出力ファイル名（拡張子なし）
            max_retries: 最大リトライ回数
            backoff_factor: バックオフ係数（秒）

        Returns:
            Path: 生成された MP3 ファイルのパス（失敗時 None）
        """
        if not text or not text.strip():
            logger.error("✗ テキストが空です")
            return None

        # 出力ディレクトリ作成
        output_dir = Path("episodes")
        output_dir.mkdir(exist_ok=True)

        # ファイル名生成
        if output_filename:
            output_path = output_dir / f"{output_filename}.mp3"
        else:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"fish_audio_{timestamp}.mp3"

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self.base_url}/tts"
                    payload = {
                        "text": text,
                        "reference_id": self.voice_id,
                        "format": "mp3",
                        "normalize": True,
                        "latency": "normal",
                    }

                    if attempt > 0:
                        logger.info(f"Fish Audio TTS リトライ {attempt}/{max_retries} ({len(text)} 文字)")
                    else:
                        logger.info(f"Fish Audio TTS リクエスト送信 ({len(text)} 文字)")

                    async with session.post(
                        url,
                        headers=self.headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"✗ TTS 生成失敗: HTTP {response.status} - {error_text}")
                            last_error = f"HTTP {response.status}"
                            if attempt < max_retries:
                                wait_time = backoff_factor * (2 ** attempt)
                                logger.info(f"  {wait_time:.1f}秒後にリトライ...")
                                await asyncio.sleep(wait_time)
                                continue
                            return None

                        audio_data = await response.read()
                        output_path.write_bytes(audio_data)

                        file_size_mb = len(audio_data) / (1024 * 1024)
                        logger.info(f"✓ 音声生成完了: {output_path.name} ({file_size_mb:.2f} MB)")

                        return output_path

            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                last_error = str(e) if str(e) else type(e).__name__
                logger.warning(f"✗ TTS エラー (attempt {attempt + 1}/{max_retries + 1}): {last_error}")
                if attempt < max_retries:
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.info(f"  {wait_time:.1f}秒後にリトライ...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"✗ 最大リトライ回数超過: {last_error}")
                    return None
            except Exception as e:
                logger.error(f"✗ 音声生成エラー: {e}")
                return None

        return None

    def get_audio_duration(self, audio_file: Path) -> Optional[str]:
        """
        MP3 ファイルの再生時間を取得（HH:MM:SS 形式）

        Args:
            audio_file: MP3 ファイルパス

        Returns:
            str: 再生時間（例: "00:05:23"）、失敗時 None
        """
        if not audio_file.exists():
            logger.error(f"✗ ファイルが存在しません: {audio_file}")
            return None

        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "json",
                    str(audio_file),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            data = json.loads(result.stdout)
            duration_seconds = float(data["format"]["duration"])

            # HH:MM:SS 形式に変換
            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            seconds = int(duration_seconds % 60)

            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            logger.debug(f"音声時間: {duration_str}")

            return duration_str

        except subprocess.CalledProcessError as e:
            logger.error(f"✗ ffprobe エラー: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"✗ 再生時間取得エラー: {e}")
            return None

    async def generate_podcast_audio(
        self,
        text: str,
        output_filename: str,
    ) -> Optional[Dict[str, Any]]:
        """
        ポッドキャスト用音声生成（メタデータ付き）

        Args:
            text: 音声化するテキスト
            output_filename: 出力ファイル名（拡張子なし）

        Returns:
            dict: 音声ファイル情報（file_path, duration, size_bytes）
                  失敗時 None
        """
        # 音声生成
        audio_file = await self.generate_audio(text, output_filename)
        if not audio_file:
            return None

        # メタデータ取得
        duration = self.get_audio_duration(audio_file)
        file_size = audio_file.stat().st_size

        return {
            "file_path": audio_file,
            "duration": duration,
            "size_bytes": file_size,
            "format": "mp3",
        }


async def main():
    """テスト実行"""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    client = FishAudioClient()

    # 接続テスト
    print("\n=== Fish Audio API 接続テスト ===")
    success = await client.test_connection()
    if not success:
        print("✗ 接続失敗")
        sys.exit(1)

    # 短いテキストで音声生成テスト
    test_text = "こんにちは。Fish Audio による音声合成のテストです。"
    print(f"\n=== 音声生成テスト ===")
    print(f"テキスト: {test_text}")

    result = await client.generate_podcast_audio(
        text=test_text,
        output_filename="fish_audio_test",
    )

    if result:
        print(f"\n✓ 成功")
        print(f"  ファイル: {result['file_path']}")
        print(f"  再生時間: {result['duration']}")
        print(f"  サイズ: {result['size_bytes'] / 1024:.2f} KB")
    else:
        print("\n✗ 失敗")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
