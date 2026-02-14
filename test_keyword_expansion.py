#!/usr/bin/env python3
"""Test keyword expansion and research integration"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.collectors.keyword_researcher import KeywordResearcher
from loguru import logger

async def main():
    logger.info("=== Testing Keyword Expansion ===")
    
    # Initialize researcher
    researcher = KeywordResearcher()
    
    # Test themes
    themes = ["AIビジネスモデル", "バイブコーディング", "エージェント活用"]
    
    # Run integrated research
    results = await researcher.integrated_research(
        themes=themes,
        expand_keywords=True,
        world_search=False  # Disable world search for now
    )
    
    # Display results
    logger.info(f"\n=== Results ===")
    logger.info(f"Themes: {results['themes']}")
    logger.info(f"Expanded keywords count: {len(results.get('expanded_keywords', {}))}")
    logger.info(f"Suggested queries count: {len(results.get('suggested_queries', []))}")
    
    if results.get('suggested_queries'):
        logger.info(f"\nTop 10 suggested queries:")
        for i, query in enumerate(results['suggested_queries'][:10], 1):
            logger.info(f"  {i}. {query}")
    
    # Extract newsworthy topics
    topics = researcher.extract_newsworthy_topics(results)
    logger.info(f"\nNewsworthy topics for NewsData.io: {len(topics)}")
    for i, topic in enumerate(topics[:5], 1):
        logger.info(f"  {i}. {topic}")
    
    logger.info("\n✅ Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
