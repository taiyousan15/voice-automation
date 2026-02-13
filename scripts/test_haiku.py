#!/usr/bin/env python3
"""Test Claude Haiku via OpenRouter - Fallback LLM test"""
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from loguru import logger
from src.generators.openrouter_client import OpenRouterClient

# Load environment
load_dotenv()

# Configure logger
logger.remove()
logger.add(sys.stderr, format="<level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>", level="INFO")


def test_claude_haiku_script_generation():
    """Test Claude Haiku script generation with sample article"""
    logger.info("Starting Claude Haiku (OpenRouter) test...")

    # Sample article for testing
    sample_article = """
    【脱炭素技術】日本が新型太陽電池技術を開発

    日本の研究機関が、従来の太陽電池よりも変換効率が45%高い新型太陽電池を開発しました。
    この技術は、将来のクリーンエネルギー社会において重要な役割を果たすと期待されています。

    新しい太陽電池は、薄膜技術を用いており、軽く、曲げることもできます。
    建物の屋根だけでなく、車や衣類にも組み込むことが可能となり、
    より多くの場所で太陽光発電ができるようになります。

    研究チームは2027年の実用化を目指しており、
    世界中の企業からの問い合わせが殺到しているとのことです。
    """

    try:
        # Initialize OpenRouter client
        logger.info("Initializing Claude Haiku client (OpenRouter)...")
        client = OpenRouterClient()

        # Generate script
        logger.info("Generating podcast script...")
        start_time = time.time()

        script = client.generate_podcast_script(
            article_text=sample_article.strip(),
            theme="environment",
            max_retries=2
        )

        elapsed_time = time.time() - start_time

        if script:
            logger.info(f"✓ Script generated successfully in {elapsed_time:.2f}s")
            logger.info(f"Generated script length: {len(script)} characters")
            logger.info(f"\n{'='*60}")
            logger.info("GENERATED PODCAST SCRIPT (Claude Haiku):")
            logger.info(f"{'='*60}\n")
            print(script)
            logger.info(f"\n{'='*60}")
            logger.info(f"Generation time: {elapsed_time:.2f}s (Target: < 30s) {'✓' if elapsed_time < 30 else '✗'}")
            return True
        else:
            logger.error("✗ Failed to generate script")
            return False

    except Exception as e:
        logger.error(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_claude_haiku_script_generation()
    sys.exit(0 if success else 1)
