"""
Voicy Content Collector - 競合分析用コンテンツリーダー

vmw.api.voicy.jp（内部API・読み取り専用）を使用してVoicyの公開コンテンツを取得する。
投稿・アップロード機能なし。競合分析・トレンドリサーチ専用。
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from loguru import logger


BASE_URL = "https://vmw.api.voicy.jp"
DEFAULT_LIMIT = 20
DEFAULT_TIMEOUT = 15
PUBLIC_TYPE_PUBLIC = 3  # 公開エピソードのみ


class VoicyCollector:
    """Voicy内部API（vmw.api.voicy.jp）を使った読み取り専用コレクター。

    競合分析・トレンドリサーチ目的で使用する。
    投稿・アップロードAPIは存在しないため、本クラスは取得専用。
    """

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(
            timeout=self.timeout,
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (compatible; VoicyCollector/1.0)",
            },
        )
        logger.info(f"VoicyCollector initialized (base_url={self.base_url})")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_channel_episodes(
        self,
        channel_id: int,
        limit: int = DEFAULT_LIMIT,
        public_type: int = PUBLIC_TYPE_PUBLIC,
    ) -> Optional[List[Dict[str, Any]]]:
        """チャンネルのエピソード一覧を取得する。

        Args:
            channel_id: VoicyチャンネルID（例: 12345）
            limit: 取得件数（最大50程度）
            public_type: 公開タイプ（3=公開エピソードのみ）

        Returns:
            エピソードのリスト。失敗時は None。
            各要素は {"voice_id", "title", "published_at", ...} を含む。
        """
        url = f"{self.base_url}/program_list/all"
        params = {
            "channel_id": channel_id,
            "limit": limit,
            "public_type": public_type,
        }
        data = self._get(url, params)
        if data is None:
            return None

        episodes = data.get("programs") or data.get("voice_data") or []
        logger.info(
            f"Channel {channel_id}: fetched {len(episodes)} episodes"
        )
        return episodes

    def get_episode_detail(
        self,
        channel_id: int,
        voice_id: int,
    ) -> Optional[Dict[str, Any]]:
        """エピソード詳細（MP3 URLを含む）を取得する。

        Args:
            channel_id: VoicyチャンネルID
            voice_id: エピソードID（VoiceID）

        Returns:
            エピソード詳細辞書。失敗時は None。
            ``VoiceFile`` フィールドに MP3 URL が含まれる。
        """
        url = f"{self.base_url}/articles_list"
        params = {
            "channel_id": channel_id,
            "pid": voice_id,
        }
        data = self._get(url, params)
        if data is None:
            return None

        # レスポンス構造が入れ子になる場合を吸収
        if isinstance(data, list):
            detail = data
        elif isinstance(data, dict):
            detail = data.get("voice_data") or data
        else:
            detail = data
        logger.debug(
            f"Episode detail fetched: channel={channel_id}, voice={voice_id}"
        )
        return detail

    def get_mp3_url(
        self,
        channel_id: int,
        voice_id: int,
    ) -> Optional[str]:
        """エピソードのMP3 URLを取得する。

        Args:
            channel_id: VoicyチャンネルID
            voice_id: エピソードID

        Returns:
            MP3の直接URL文字列。取得失敗・URLなしの場合は None。
        """
        detail = self.get_episode_detail(channel_id, voice_id)
        if detail is None:
            return None

        # 単一エピソード or エピソードリストの両形式を処理
        if isinstance(detail, list):
            items = detail
        elif isinstance(detail, dict):
            # {"voice_data": [...]} or {"VoiceFile": "..."}
            if "voice_data" in detail and isinstance(detail["voice_data"], list):
                items = detail["voice_data"]
            else:
                items = [detail]
        else:
            logger.warning(f"Unexpected detail type: {type(detail)}")
            return None

        for item in items:
            if not isinstance(item, dict):
                continue
            # VoiceFile フィールドを優先探索
            for key in ("VoiceFile", "voice_file", "mp3_url", "audio_url"):
                mp3 = item.get(key)
                if mp3 and isinstance(mp3, str) and mp3.startswith("http"):
                    logger.info(
                        f"MP3 URL found: channel={channel_id}, voice={voice_id}"
                    )
                    return mp3

        logger.warning(
            f"No MP3 URL found: channel={channel_id}, voice={voice_id}"
        )
        return None

    def get_channel_info(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """チャンネル情報を取得する（存在確認・メタデータ用）。

        Args:
            channel_id: VoicyチャンネルID

        Returns:
            チャンネル情報辞書。失敗時は None。
        """
        url = f"{self.base_url}/channel/info"
        params = {"channel_id": channel_id}
        data = self._get(url, params)
        if data is None:
            return None
        logger.debug(f"Channel info fetched: channel={channel_id}")
        return data

    def search_channels(
        self,
        keyword: str,
        limit: int = DEFAULT_LIMIT,
    ) -> Optional[List[Dict[str, Any]]]:
        """キーワードでチャンネルを検索する（競合分析用）。

        Args:
            keyword: 検索キーワード
            limit: 取得件数

        Returns:
            チャンネルリスト。失敗時は None。
        """
        url = f"{self.base_url}/channel/search"
        params = {"keyword": keyword, "limit": limit}
        data = self._get(url, params)
        if data is None:
            return None

        channels = (
            data.get("channels")
            or data.get("channel_list")
            or data.get("results")
            or []
        )
        logger.info(
            f"Search '{keyword}': found {len(channels)} channels"
        )
        return channels

    def is_available(self) -> bool:
        """APIが疎通可能かチェックする。

        Returns:
            True=疎通OK / False=疎通不可
        """
        try:
            resp = self._client.get(self.base_url, timeout=5)
            available = resp.status_code < 500
            logger.debug(f"VoicyAPI availability: {available} (status={resp.status_code})")
            return available
        except Exception as exc:
            logger.debug(f"VoicyAPI unavailable: {exc}")
            return False

    def close(self) -> None:
        """HTTP クライアントを閉じる。"""
        self._client.close()

    def __enter__(self) -> "VoicyCollector":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """GET リクエストを実行し JSON を返す。エラー時は None。"""
        try:
            resp = self._client.get(url, params=params)
        except httpx.TimeoutException:
            logger.error(f"Timeout: GET {url} params={params}")
            return None
        except httpx.RequestError as exc:
            logger.error(f"Request error: {exc}")
            return None

        if resp.status_code != 200:
            logger.warning(
                f"Non-200 response: {resp.status_code} GET {url}"
            )
            return None

        try:
            return resp.json()
        except Exception as exc:
            logger.error(f"JSON decode error: {exc}")
            return None
