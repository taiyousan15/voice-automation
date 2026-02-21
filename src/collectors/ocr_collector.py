"""
OCR Collector - Qwen3.5-397B-A17B via Ollama
=============================================

画像・PDF からテキストを抽出する OCR コレクター。
Ollama 経由で Qwen3.5-397B-A17B の Vision 機能を使用。

デフォルト: qwen3.5:397b-cloud（Ollama Cloud）
フォールバック: qwen3-vl:32b（完全ローカル）

対応形式: PNG, JPG, JPEG, WebP, GIF, PDF(1ページ目)
"""

import os
import base64
import mimetypes
from pathlib import Path
from typing import Optional, List, Dict, Any

import httpx
from openai import OpenAI
from loguru import logger


# 対応画像形式
SUPPORTED_IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
SUPPORTED_TYPES = SUPPORTED_IMAGE_TYPES | {".pdf"}

# Ollama デフォルト設定
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen3.5:397b-cloud"
FALLBACK_MODELS = ["qwen3-vl:32b", "qwen3-vl:8b"]


class OCRCollector:
    """Qwen3.5-397B-A17B Vision を使用した OCR コレクター（Ollama版）"""

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        初期化

        Args:
            model: モデル名 (default: QWEN_OCR_MODEL env or qwen3.5:397b-cloud)
            base_url: Ollama API Base URL (default: http://localhost:11434/v1)
            api_key: API Key (Ollamaではダミー値でOK)
        """
        self.model = model or os.getenv("QWEN_OCR_MODEL", DEFAULT_MODEL)
        self.base_url = base_url or os.getenv(
            "OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL
        )
        self.api_key = api_key or os.getenv("OLLAMA_API_KEY", "ollama")
        self.max_tokens = int(os.getenv("QWEN_OCR_MAX_TOKENS", "4096"))

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        logger.info(
            f"OCR Collector initialized - Model: {self.model}, "
            f"Base URL: {self.base_url}"
        )

    def is_available(self) -> bool:
        """Ollamaサーバーへの接続確認"""
        ollama_url = self.base_url.replace("/v1", "")
        try:
            resp = httpx.get(f"{ollama_url}/api/tags", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

    def resolve_model(self) -> str:
        """利用可能なモデルを自動検出（設定モデル → フォールバック順）"""
        ollama_url = self.base_url.replace("/v1", "")
        try:
            resp = httpx.get(f"{ollama_url}/api/tags", timeout=5.0)
            if resp.status_code != 200:
                return self.model
            installed = {
                m["name"].split(":")[0] + ":" + m["name"].split(":")[-1]
                for m in resp.json().get("models", [])
            }
            # name形式が "qwen3.5:397b-cloud" or "qwen3-vl:32b" etc.
            installed_base = {m["name"] for m in resp.json().get("models", [])}
            candidates = [self.model] + FALLBACK_MODELS
            for candidate in candidates:
                if candidate in installed_base:
                    if candidate != self.model:
                        logger.info(
                            f"モデル切替: {self.model} → {candidate}"
                        )
                        self.model = candidate
                    return candidate
        except Exception as e:
            logger.warning(f"モデル検出失敗: {e}")
        return self.model

    def extract_text(
        self,
        image_path: str,
        prompt: Optional[str] = None,
        language: str = "ja",
    ) -> Optional[str]:
        """
        画像からテキストを抽出

        Args:
            image_path: 画像ファイルパス
            prompt: カスタムプロンプト（省略時はデフォルトOCRプロンプト）
            language: 抽出言語 (default: ja)

        Returns:
            抽出されたテキスト（失敗時 None）
        """
        path = Path(image_path)
        if not path.exists():
            logger.error(f"ファイルが見つかりません: {image_path}")
            return None

        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_TYPES:
            logger.error(
                f"非対応形式: {suffix} (対応: {', '.join(SUPPORTED_TYPES)})"
            )
            return None

        image_data = self._encode_image(path)
        if not image_data:
            return None

        ocr_prompt = prompt or self._default_prompt(language)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": ocr_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{image_data['mime']};base64,{image_data['base64']}"
                                },
                            },
                        ],
                    }
                ],
            )

            text = response.choices[0].message.content
            tokens_used = getattr(response.usage, "total_tokens", 0)
            logger.info(
                f"OCR完了: {path.name} → {len(text)}文字 ({tokens_used} tokens)"
            )
            return text

        except Exception as e:
            logger.error(f"OCR失敗: {path.name} - {e}")
            return None

    def extract_text_from_url(
        self,
        image_url: str,
        prompt: Optional[str] = None,
        language: str = "ja",
    ) -> Optional[str]:
        """
        URL画像からテキストを抽出

        Args:
            image_url: 画像URL
            prompt: カスタムプロンプト
            language: 抽出言語

        Returns:
            抽出されたテキスト（失敗時 None）
        """
        ocr_prompt = prompt or self._default_prompt(language)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": ocr_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url},
                            },
                        ],
                    }
                ],
            )

            text = response.choices[0].message.content
            logger.info(f"OCR完了(URL): {len(text)}文字")
            return text

        except Exception as e:
            logger.error(f"OCR失敗(URL): {e}")
            return None

    def extract_structured(
        self,
        image_path: str,
        language: str = "ja",
    ) -> Optional[Dict[str, Any]]:
        """
        画像から構造化データを抽出（表・チャート対応）

        Args:
            image_path: 画像ファイルパス
            language: 抽出言語

        Returns:
            構造化データ dict（title, body, tables, numbers）
        """
        prompt = """この画像の内容を構造化して抽出してください。

以下のJSON形式で出力してください：
{
  "title": "文書タイトル（あれば）",
  "body": "本文テキスト全文",
  "tables": [{"header": ["列1", "列2"], "rows": [["値1", "値2"]]}],
  "numbers": [{"label": "項目名", "value": "数値", "unit": "単位"}],
  "source": "出典情報（あれば）"
}

テキストは正確に、数値は単位付きで抽出してください。"""

        raw = self.extract_text(image_path, prompt=prompt, language=language)
        if not raw:
            return None

        import json

        try:
            # JSON部分を抽出（マークダウンコードブロック対応）
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("構造化解析失敗、プレーンテキストとして返却")
            return {"title": "", "body": raw, "tables": [], "numbers": [], "source": ""}

    def batch_extract(
        self,
        image_paths: List[str],
        prompt: Optional[str] = None,
        language: str = "ja",
    ) -> List[Dict[str, Any]]:
        """
        複数画像を一括OCR

        Args:
            image_paths: 画像パスのリスト
            prompt: カスタムプロンプト
            language: 抽出言語

        Returns:
            結果リスト [{path, text, success}]
        """
        results = []
        for img_path in image_paths:
            text = self.extract_text(img_path, prompt=prompt, language=language)
            results.append({
                "path": img_path,
                "text": text or "",
                "success": text is not None,
            })
        return results

    def _encode_image(self, path: Path) -> Optional[Dict[str, str]]:
        """画像をbase64エンコード"""
        try:
            mime_type = mimetypes.guess_type(str(path))[0]
            if not mime_type:
                suffix_to_mime = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".webp": "image/webp",
                    ".gif": "image/gif",
                    ".pdf": "application/pdf",
                }
                mime_type = suffix_to_mime.get(path.suffix.lower(), "image/png")

            with open(path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")

            return {"base64": encoded, "mime": mime_type}

        except Exception as e:
            logger.error(f"画像エンコード失敗: {path} - {e}")
            return None

    @staticmethod
    def _default_prompt(language: str = "ja") -> str:
        """デフォルトOCRプロンプト"""
        if language == "ja":
            return (
                "この画像に含まれるテキストを全て正確に抽出してください。"
                "レイアウトや改行を可能な限り保持し、"
                "表がある場合はMarkdown表形式で出力してください。"
                "数値・固有名詞は特に正確に読み取ってください。"
            )
        return (
            "Extract all text from this image accurately. "
            "Preserve layout and line breaks where possible. "
            "Format tables as Markdown tables."
        )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.collectors.ocr_collector <image_path>")
        print("  Ollama が起動していることを確認してください")
        print("  モデル: ollama pull qwen3.5:397b-cloud")
        sys.exit(1)

    from dotenv import load_dotenv
    load_dotenv()

    collector = OCRCollector()

    if not collector.is_available():
        print("エラー: Ollamaに接続できません（ollama serve を実行してください）")
        sys.exit(1)

    resolved = collector.resolve_model()
    print(f"使用モデル: {resolved}")

    result = collector.extract_text(sys.argv[1])

    if result:
        print(f"\n=== OCR結果 ({len(result)}文字) ===\n")
        print(result)
    else:
        print("OCR失敗")
        sys.exit(1)
