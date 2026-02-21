"""
OCRCollector のユニットテスト（Ollama版）
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.collectors.ocr_collector import (
    OCRCollector,
    SUPPORTED_TYPES,
    SUPPORTED_IMAGE_TYPES,
    DEFAULT_MODEL,
    DEFAULT_OLLAMA_BASE_URL,
    FALLBACK_MODELS,
)


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


def _make_png(tmp_path: Path, name: str = "test.png") -> Path:
    p = tmp_path / name
    p.write_bytes(PNG_BYTES)
    return p


def _mock_response(text: str, total_tokens: int = 10) -> MagicMock:
    usage = MagicMock()
    usage.total_tokens = total_tokens
    msg = MagicMock()
    msg.content = text
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    resp.usage = usage
    return resp


class TestOCRCollectorInit:
    @patch("src.collectors.ocr_collector.OpenAI")
    def test_default_model_is_qwen35_cloud(self, mock_openai, monkeypatch):
        monkeypatch.delenv("QWEN_OCR_MODEL", raising=False)
        collector = OCRCollector()
        assert collector.model == "qwen3.5:397b-cloud"

    @patch("src.collectors.ocr_collector.OpenAI")
    def test_default_base_url_is_ollama(self, mock_openai, monkeypatch):
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        collector = OCRCollector()
        assert "11434" in collector.base_url

    @patch("src.collectors.ocr_collector.OpenAI")
    def test_default_api_key_is_ollama(self, mock_openai, monkeypatch):
        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        collector = OCRCollector()
        assert collector.api_key == "ollama"

    @patch("src.collectors.ocr_collector.OpenAI")
    def test_env_model_override(self, mock_openai, monkeypatch):
        monkeypatch.setenv("QWEN_OCR_MODEL", "qwen3-vl:32b")
        collector = OCRCollector()
        assert collector.model == "qwen3-vl:32b"

    @patch("src.collectors.ocr_collector.OpenAI")
    def test_explicit_params_override_env(self, mock_openai):
        collector = OCRCollector(
            model="qwen3-vl:8b",
            base_url="http://custom:11434/v1",
            api_key="my-key",
        )
        assert collector.model == "qwen3-vl:8b"
        assert collector.base_url == "http://custom:11434/v1"
        assert collector.api_key == "my-key"

    @patch("src.collectors.ocr_collector.OpenAI")
    def test_no_api_key_required(self, mock_openai, monkeypatch):
        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        collector = OCRCollector()
        assert collector.api_key == "ollama"


class TestConstants:
    def test_default_model_value(self):
        assert DEFAULT_MODEL == "qwen3.5:397b-cloud"

    def test_default_base_url_value(self):
        assert "11434" in DEFAULT_OLLAMA_BASE_URL

    def test_fallback_models_contains_local(self):
        assert "qwen3-vl:32b" in FALLBACK_MODELS
        assert "qwen3-vl:8b" in FALLBACK_MODELS


class TestSupportedTypes:
    def test_image_types_contains_expected(self):
        assert ".png" in SUPPORTED_IMAGE_TYPES
        assert ".jpg" in SUPPORTED_IMAGE_TYPES
        assert ".jpeg" in SUPPORTED_IMAGE_TYPES
        assert ".webp" in SUPPORTED_IMAGE_TYPES
        assert ".gif" in SUPPORTED_IMAGE_TYPES

    def test_pdf_in_supported_types(self):
        assert ".pdf" in SUPPORTED_TYPES

    def test_unsupported_not_included(self):
        assert ".txt" not in SUPPORTED_TYPES
        assert ".docx" not in SUPPORTED_TYPES


class TestIsAvailable:
    @pytest.fixture
    def collector(self):
        with patch("src.collectors.ocr_collector.OpenAI"):
            return OCRCollector()

    def test_returns_true_when_ollama_running(self, collector):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("src.collectors.ocr_collector.httpx.get", return_value=mock_resp):
            assert collector.is_available() is True

    def test_returns_false_when_ollama_not_running(self, collector):
        with patch(
            "src.collectors.ocr_collector.httpx.get",
            side_effect=Exception("Connection refused"),
        ):
            assert collector.is_available() is False

    def test_returns_false_on_non_200(self, collector):
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        with patch("src.collectors.ocr_collector.httpx.get", return_value=mock_resp):
            assert collector.is_available() is False


class TestResolveModel:
    @pytest.fixture
    def collector(self):
        with patch("src.collectors.ocr_collector.OpenAI"):
            return OCRCollector()

    def _mock_tags(self, models):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": [{"name": m} for m in models]}
        return mock_resp

    def test_returns_configured_model_when_available(self, collector):
        mock_resp = self._mock_tags(["qwen3.5:397b-cloud"])
        with patch("src.collectors.ocr_collector.httpx.get", return_value=mock_resp):
            result = collector.resolve_model()
        assert result == "qwen3.5:397b-cloud"

    def test_falls_back_to_32b_when_cloud_missing(self, collector):
        mock_resp = self._mock_tags(["qwen3-vl:32b"])
        with patch("src.collectors.ocr_collector.httpx.get", return_value=mock_resp):
            result = collector.resolve_model()
        assert result == "qwen3-vl:32b"

    def test_falls_back_to_8b_when_only_8b_available(self, collector):
        mock_resp = self._mock_tags(["qwen3-vl:8b"])
        with patch("src.collectors.ocr_collector.httpx.get", return_value=mock_resp):
            result = collector.resolve_model()
        assert result == "qwen3-vl:8b"

    def test_returns_configured_model_on_api_error(self, collector):
        with patch(
            "src.collectors.ocr_collector.httpx.get",
            side_effect=Exception("Timeout"),
        ):
            result = collector.resolve_model()
        assert result == collector.model


class TestExtractText:
    @pytest.fixture
    def collector(self):
        with patch("src.collectors.ocr_collector.OpenAI"):
            return OCRCollector()

    def test_file_not_found_returns_none(self, collector):
        result = collector.extract_text("/nonexistent/path/image.png")
        assert result is None

    def test_unsupported_format_returns_none(self, collector, tmp_path):
        txt_file = tmp_path / "doc.txt"
        txt_file.write_text("hello")
        result = collector.extract_text(str(txt_file))
        assert result is None

    def test_encode_failure_returns_none(self, collector, tmp_path):
        png = _make_png(tmp_path)
        with patch.object(collector, "_encode_image", return_value=None):
            result = collector.extract_text(str(png))
        assert result is None

    def test_successful_extraction(self, collector, tmp_path):
        png = _make_png(tmp_path)
        mock_resp = _mock_response("抽出されたテキスト")
        collector.client.chat.completions.create = MagicMock(return_value=mock_resp)
        result = collector.extract_text(str(png))
        assert result == "抽出されたテキスト"

    def test_api_error_returns_none(self, collector, tmp_path):
        png = _make_png(tmp_path)
        collector.client.chat.completions.create = MagicMock(
            side_effect=Exception("API Error")
        )
        result = collector.extract_text(str(png))
        assert result is None


class TestExtractStructured:
    @pytest.fixture
    def collector(self):
        with patch("src.collectors.ocr_collector.OpenAI"):
            return OCRCollector()

    def test_json_response_parsed_correctly(self, collector, tmp_path):
        png = _make_png(tmp_path)
        payload = {"title": "T", "body": "B", "tables": [], "numbers": [], "source": ""}
        with patch.object(collector, "extract_text", return_value=json.dumps(payload)):
            result = collector.extract_structured(str(png))
        assert result == payload

    def test_markdown_wrapped_json_parsed(self, collector, tmp_path):
        png = _make_png(tmp_path)
        payload = {"title": "MD", "body": "text", "tables": [], "numbers": [], "source": ""}
        wrapped = f"```json\n{json.dumps(payload)}\n```"
        with patch.object(collector, "extract_text", return_value=wrapped):
            result = collector.extract_structured(str(png))
        assert result == payload

    def test_fallback_on_invalid_json(self, collector, tmp_path):
        png = _make_png(tmp_path)
        with patch.object(collector, "extract_text", return_value="not valid json"):
            result = collector.extract_structured(str(png))
        assert result is not None
        assert result["body"] == "not valid json"
        assert result["tables"] == []

    def test_returns_none_when_extract_text_fails(self, collector, tmp_path):
        png = _make_png(tmp_path)
        with patch.object(collector, "extract_text", return_value=None):
            result = collector.extract_structured(str(png))
        assert result is None


class TestBatchExtract:
    @pytest.fixture
    def collector(self):
        with patch("src.collectors.ocr_collector.OpenAI"):
            return OCRCollector()

    def test_processes_all_files(self, collector, tmp_path):
        paths = [str(_make_png(tmp_path, f"img{i}.png")) for i in range(3)]
        texts = ["text0", "text1", None]
        with patch.object(collector, "extract_text", side_effect=texts):
            results = collector.batch_extract(paths)
        assert len(results) == 3
        assert results[0] == {"path": paths[0], "text": "text0", "success": True}
        assert results[2] == {"path": paths[2], "text": "", "success": False}


class TestDefaultPrompt:
    def test_japanese_prompt_contains_expected_keyword(self):
        prompt = OCRCollector._default_prompt("ja")
        assert "テキスト" in prompt

    def test_english_prompt_returned_for_non_ja(self):
        prompt = OCRCollector._default_prompt("en")
        assert "Extract all text" in prompt

    def test_default_language_is_japanese(self):
        prompt = OCRCollector._default_prompt()
        assert "テキスト" in prompt
