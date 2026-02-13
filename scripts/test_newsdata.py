#!/usr/bin/env python3
"""Test NewsData.io API integration - Data collection test"""
import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from loguru import logger
from src.collectors.newsdata_client import NewsDataClient
from src.utils.deduplication import DeduplicationEngine
from src.utils.trust_score import TrustScoreEngine

# Load environment
load_dotenv()

# Configure logger
logger.remove()
logger.add(sys.stderr, format="<level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>", level="INFO")


def test_newsdata_integration():
    """Test NewsData.io API integration"""
    logger.info("Starting NewsData.io API integration test...")

    try:
        # Initialize components
        logger.info("Initializing clients...")
        client = NewsDataClient()
        dedup_engine = DeduplicationEngine()
        trust_engine = TrustScoreEngine()

        # Test 1: Search for articles
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Searching for articles...")
        logger.info("="*60)

        articles = client.search_news(
            query="AI technology",
            language="ja",
            max_results=5
        )

        if not articles:
            logger.error("✗ Failed to fetch articles")
            return False

        logger.info(f"✓ Found {len(articles)} articles")

        # Test 2: Deduplication
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Deduplication...")
        logger.info("="*60)

        unique_articles = dedup_engine.filter_duplicates(articles)
        logger.info(f"✓ Unique articles: {len(unique_articles)} / {len(articles)}")

        # Test 3: Trust scoring
        logger.info("\n" + "="*60)
        logger.info("TEST 3: Trust scoring...")
        logger.info("="*60)

        scored_articles = []
        for article in unique_articles:
            score = trust_engine.calculate_score(article)
            article["trust_score"] = score
            scored_articles.append(article)
            logger.debug(f"  [{score:.1f}] {article.get('title', 'N/A')[:60]}...")

        logger.info(f"✓ Calculated trust scores for {len(scored_articles)} articles")

        # Test 4: Filtering by trust score
        logger.info("\n" + "="*60)
        logger.info("TEST 4: Filtering by trust score (min: 0.6)...")
        logger.info("="*60)

        min_trust_score = float(os.getenv("MIN_TRUST_SCORE", "0.6"))
        filtered_articles = trust_engine.filter_by_trust_score(
            scored_articles,
            min_score=min_trust_score
        )

        logger.info(f"✓ Filtered to {len(filtered_articles)} articles with trust score >= {min_trust_score}")

        # Display results
        logger.info("\n" + "="*60)
        logger.info("SAMPLE ARTICLES:")
        logger.info("="*60)

        for i, article in enumerate(filtered_articles[:3], 1):
            logger.info(f"\n{i}. {article.get('title')}")
            logger.info(f"   Source: {article.get('source_name')}")
            logger.info(f"   Trust Score: {article.get('trust_score', 0):.1f}/10")
            logger.info(f"   Description: {article.get('description', 'N/A')[:100]}...")

        # Save results
        output_path = Path(__file__).parent.parent / "data" / "test_articles.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "total_fetched": len(articles),
                "unique": len(unique_articles),
                "passed_trust_score": len(filtered_articles),
                "articles": filtered_articles[:5]  # Save top 5
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"\n✓ Results saved to: {output_path}")

        # Summary
        logger.info("\n" + "="*60)
        logger.info("SUMMARY:")
        logger.info("="*60)
        logger.info(f"✓ Articles fetched: {len(articles)}")
        logger.info(f"✓ Unique articles: {len(unique_articles)}")
        logger.info(f"✓ High-trust articles (>= {min_trust_score}): {len(filtered_articles)}")
        logger.info(f"✓ Deduplication stats: {dedup_engine.get_stats()}")

        return True

    except Exception as e:
        logger.error(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_newsdata_integration()
    sys.exit(0 if success else 1)
