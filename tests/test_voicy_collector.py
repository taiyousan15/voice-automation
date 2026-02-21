"""
VoicyCollector ユニットテスト

vmw.api.voicy.jp（読み取り専用内部API）のモックテスト。
実際の HTTP リクエストは一切行わない。
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.collectors.voicy_collector import (
    BASE_URL,
    DEFAULT_LIMIT,
    DEFAULT_TIMEOUT,
    PUBLIC_TYPE_PUBLIC,
    VoicyCollector,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_resp(status_code: int = 200, json_data: object = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    return resp


def _make_collector() -> tuple[VoicyCollector, MagicMock]:
    """httpx.Client をモックして VoicyCollector を返す。"""
    with patch("src.collectors.voicy_collector.httpx.Client") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        collector = VoicyCollector()
    return collector, mock_client


# ---------------------------------------------------------------------------
# TestInit
# ---------------------------------------------------------------------------

class TestInit:
    def test_default_base_url(self):
        with patch("src.collectors.voicy_collector.httpx.Client"):
            c = VoicyCollector()
        assert c.base_url == BASE_URL.rstrip("/")

    def test_custom_base_url(self):
        with patch("src.collectors.voicy_collector.httpx.Client"):
            c = VoicyCollector(base_url="https://custom.example.com/")
        assert c.base_url == "https://custom.example.com"  # trailing slash stripped

    def test_default_timeout(self):
        with patch("src.collectors.voicy_collector.httpx.Client"):
            c = VoicyCollector()
        assert c.timeout == DEFAULT_TIMEOUT

    def test_custom_timeout(self):
        with patch("src.collectors.voicy_collector.httpx.Client"):
            c = VoicyCollector(timeout=30)
        assert c.timeout == 30


# ---------------------------------------------------------------------------
# TestConstants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_base_url_is_voicy(self):
        assert "voicy" in BASE_URL

    def test_default_limit(self):
        assert DEFAULT_LIMIT == 20

    def test_public_type(self):
        assert PUBLIC_TYPE_PUBLIC == 3


# ---------------------------------------------------------------------------
# TestGetChannelEpisodes
# ---------------------------------------------------------------------------

class TestGetChannelEpisodes:
    def test_returns_episodes_from_programs_key(self):
        collector, mock_client = _make_collector()
        episodes = [{"voice_id": 1, "title": "EP1"}, {"voice_id": 2, "title": "EP2"}]
        mock_client.get.return_value = _make_resp(json_data={"programs": episodes})

        result = collector.get_channel_episodes(channel_id=100)

        assert result == episodes
        assert len(result) == 2

    def test_returns_episodes_from_voice_data_key(self):
        collector, mock_client = _make_collector()
        episodes = [{"voice_id": 3, "title": "EP3"}]
        mock_client.get.return_value = _make_resp(json_data={"voice_data": episodes})

        result = collector.get_channel_episodes(channel_id=100)

        assert result == episodes

    def test_returns_empty_list_when_no_key(self):
        collector, mock_client = _make_collector()
        mock_client.get.return_value = _make_resp(json_data={})

        result = collector.get_channel_episodes(channel_id=100)

        assert result == []

    def test_returns_none_on_non_200(self):
        collector, mock_client = _make_collector()
        mock_client.get.return_value = _make_resp(status_code=404)

        result = collector.get_channel_episodes(channel_id=999)

        assert result is None

    def test_returns_none_on_timeout(self):
        import httpx
        collector, mock_client = _make_collector()
        mock_client.get.side_effect = httpx.TimeoutException("timeout")

        result = collector.get_channel_episodes(channel_id=100)

        assert result is None

    def test_passes_correct_params(self):
        collector, mock_client = _make_collector()
        mock_client.get.return_value = _make_resp(json_data={"programs": []})

        collector.get_channel_episodes(channel_id=42, limit=10, public_type=3)

        call_kwargs = mock_client.get.call_args
        params = call_kwargs[1]["params"] if "params" in call_kwargs[1] else call_kwargs[0][1]
        assert params["channel_id"] == 42
        assert params["limit"] == 10
        assert params["public_type"] == 3


# ---------------------------------------------------------------------------
# TestGetEpisodeDetail
# ---------------------------------------------------------------------------

class TestGetEpisodeDetail:
    def test_returns_detail_dict(self):
        collector, mock_client = _make_collector()
        detail = {"VoiceFile": "https://cdn.example.com/ep1.mp3", "title": "EP1"}
        mock_client.get.return_value = _make_resp(json_data=detail)

        result = collector.get_episode_detail(channel_id=100, voice_id=1)

        assert result == detail

    def test_returns_voice_data_if_nested(self):
        collector, mock_client = _make_collector()
        inner = {"VoiceFile": "https://cdn.example.com/ep1.mp3"}
        mock_client.get.return_value = _make_resp(json_data={"voice_data": inner})

        result = collector.get_episode_detail(channel_id=100, voice_id=1)

        assert result == inner

    def test_returns_none_on_error(self):
        collector, mock_client = _make_collector()
        mock_client.get.return_value = _make_resp(status_code=500)

        result = collector.get_episode_detail(channel_id=100, voice_id=1)

        assert result is None

    def test_passes_correct_params(self):
        collector, mock_client = _make_collector()
        mock_client.get.return_value = _make_resp(json_data={})

        collector.get_episode_detail(channel_id=55, voice_id=77)

        call_kwargs = mock_client.get.call_args
        params = call_kwargs[1]["params"] if "params" in call_kwargs[1] else call_kwargs[0][1]
        assert params["channel_id"] == 55
        assert params["pid"] == 77


# ---------------------------------------------------------------------------
# TestGetMp3Url
# ---------------------------------------------------------------------------

class TestGetMp3Url:
    def test_extracts_voice_file_key(self):
        collector, mock_client = _make_collector()
        mp3_url = "https://cdn.example.com/audio.mp3"
        mock_client.get.return_value = _make_resp(
            json_data={"VoiceFile": mp3_url, "title": "EP1"}
        )

        result = collector.get_mp3_url(channel_id=10, voice_id=1)

        assert result == mp3_url

    def test_extracts_from_list_response(self):
        collector, mock_client = _make_collector()
        mp3_url = "https://cdn.example.com/ep2.mp3"
        mock_client.get.return_value = _make_resp(
            json_data=[{"VoiceFile": mp3_url, "title": "EP2"}]
        )

        result = collector.get_mp3_url(channel_id=10, voice_id=2)

        assert result == mp3_url

    def test_extracts_from_nested_voice_data_list(self):
        collector, mock_client = _make_collector()
        mp3_url = "https://cdn.example.com/ep3.mp3"
        mock_client.get.return_value = _make_resp(
            json_data={"voice_data": [{"VoiceFile": mp3_url}]}
        )

        result = collector.get_mp3_url(channel_id=10, voice_id=3)

        assert result == mp3_url

    def test_returns_none_when_no_mp3_key(self):
        collector, mock_client = _make_collector()
        mock_client.get.return_value = _make_resp(json_data={"title": "No Audio"})

        result = collector.get_mp3_url(channel_id=10, voice_id=4)

        assert result is None

    def test_returns_none_on_detail_failure(self):
        collector, mock_client = _make_collector()
        mock_client.get.return_value = _make_resp(status_code=404)

        result = collector.get_mp3_url(channel_id=10, voice_id=999)

        assert result is None

    def test_ignores_non_http_mp3_value(self):
        collector, mock_client = _make_collector()
        mock_client.get.return_value = _make_resp(
            json_data={"VoiceFile": "not-a-url"}
        )

        result = collector.get_mp3_url(channel_id=10, voice_id=5)

        assert result is None

    def test_fallback_keys_voice_file_lowercase(self):
        collector, mock_client = _make_collector()
        mp3_url = "https://cdn.example.com/lower.mp3"
        mock_client.get.return_value = _make_resp(
            json_data={"voice_file": mp3_url}
        )

        result = collector.get_mp3_url(channel_id=10, voice_id=6)

        assert result == mp3_url


# ---------------------------------------------------------------------------
# TestSearchChannels
# ---------------------------------------------------------------------------

class TestSearchChannels:
    def test_returns_channels_list(self):
        collector, mock_client = _make_collector()
        channels = [{"channel_id": 1, "name": "Tech Talk"}]
        mock_client.get.return_value = _make_resp(json_data={"channels": channels})

        result = collector.search_channels("技術")

        assert result == channels

    def test_returns_results_key(self):
        collector, mock_client = _make_collector()
        channels = [{"channel_id": 2}]
        mock_client.get.return_value = _make_resp(json_data={"results": channels})

        result = collector.search_channels("AI")

        assert result == channels

    def test_returns_empty_list_on_no_key(self):
        collector, mock_client = _make_collector()
        mock_client.get.return_value = _make_resp(json_data={})

        result = collector.search_channels("xyz")

        assert result == []

    def test_returns_none_on_error(self):
        collector, mock_client = _make_collector()
        mock_client.get.return_value = _make_resp(status_code=503)

        result = collector.search_channels("error")

        assert result is None


# ---------------------------------------------------------------------------
# TestIsAvailable
# ---------------------------------------------------------------------------

class TestIsAvailable:
    def test_returns_true_on_200(self):
        collector, mock_client = _make_collector()
        mock_client.get.return_value = _make_resp(status_code=200)

        assert collector.is_available() is True

    def test_returns_true_on_404(self):
        """404 も 5xx 未満なので疎通OK とみなす。"""
        collector, mock_client = _make_collector()
        mock_client.get.return_value = _make_resp(status_code=404)

        assert collector.is_available() is True

    def test_returns_false_on_500(self):
        collector, mock_client = _make_collector()
        mock_client.get.return_value = _make_resp(status_code=500)

        assert collector.is_available() is False

    def test_returns_false_on_exception(self):
        collector, mock_client = _make_collector()
        mock_client.get.side_effect = Exception("connection refused")

        assert collector.is_available() is False


# ---------------------------------------------------------------------------
# TestContextManager
# ---------------------------------------------------------------------------

class TestContextManager:
    def test_close_called_on_exit(self):
        collector, mock_client = _make_collector()

        with collector:
            pass

        mock_client.close.assert_called_once()

    def test_returns_self_on_enter(self):
        collector, _ = _make_collector()

        result = collector.__enter__()

        assert result is collector


# ---------------------------------------------------------------------------
# TestInternalGet
# ---------------------------------------------------------------------------

class TestInternalGet:
    def test_returns_none_on_json_error(self):
        collector, mock_client = _make_collector()
        resp = _make_resp(status_code=200)
        resp.json.side_effect = ValueError("bad json")
        mock_client.get.return_value = resp

        result = collector._get("https://example.com/test")

        assert result is None

    def test_returns_none_on_request_error(self):
        import httpx
        collector, mock_client = _make_collector()
        mock_client.get.side_effect = httpx.RequestError("connection error")

        result = collector._get("https://example.com/test")

        assert result is None

    def test_passes_params_to_client(self):
        collector, mock_client = _make_collector()
        mock_client.get.return_value = _make_resp(json_data={"ok": True})

        collector._get("https://example.com/api", {"foo": "bar"})

        mock_client.get.assert_called_once_with(
            "https://example.com/api", params={"foo": "bar"}
        )
