#!/usr/bin/env python3
"""Test Groq LLM client - Script generation test"""
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from loguru import logger
from src.generators.groq_client import GroqClient

# Load environment
load_dotenv()

# Configure logger
logger.remove()
logger.add(sys.stderr, format="<level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>", level="INFO")


def test_groq_script_generation():
    """Test Groq script generation with sample article"""
    logger.info("Starting Groq LLM test...")

    # Sample article for testing
    sample_article = """
    【AI新ロボット登場】東京のテック企業が新型AIロボットを発表

    東京のテック企業が本日、最新のAIロボット「RoboX-5000」を発表しました。
    このロボットは、従来のロボットよりも30%高速で、消費電力を50%削減し、
    自然言語処理により、日本語でのコマンドを99.5%の精度で理解できます。

    開発チームは、このロボットがオフィス、工場、病院など様々な場所で活躍することを期待しており、
    2026年Q2からの販売を予定しています。価格は200万円からとなります。

    アナリストは「このロボットは業界に革新をもたらす可能性が高い」とコメントしています。
    """

    try:
        # Initialize Groq client
        logger.info("Initializing Groq client...")
        client = GroqClient()

        # Generate script
        logger.info("Generating podcast script...")
        start_time = time.time()

        script = client.generate_podcast_script(
            article_text=sample_article.strip(),
            theme="technology",
            max_retries=2
        )

        elapsed_time = time.time() - start_time

        if script:
            logger.info(f"✓ Script generated successfully in {elapsed_time:.2f}s")
            logger.info(f"Generated script length: {len(script)} characters")
            logger.info(f"\n{'='*60}")
            logger.info("GENERATED PODCAST SCRIPT:")
            logger.info(f"{'='*60}\n")
            print(script)
            logger.info(f"\n{'='*60}")
            logger.info(f"Generation time: {elapsed_time:.2f}s (Target: < 10s) {'✓' if elapsed_time < 10 else '✗'}")
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
    success = test_groq_script_generation()
    sys.exit(0 if success else 1)
