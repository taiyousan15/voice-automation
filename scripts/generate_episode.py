#!/usr/bin/env python3
"""End-to-end episode generation script - News → Script → Ready for TTS"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from loguru import logger
from src.collectors.newsdata_client import NewsDataClient
from src.utils.deduplication import DeduplicationEngine
from src.utils.trust_score import TrustScoreEngine
from src.generators.groq_client import GroqClient

# Load environment
load_dotenv()

# Configure logger
logger.remove()
logger.add(sys.stderr, format="<level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>", level="INFO")


def generate_episode(theme: str = "technology", max_articles: int = 3):
    """
    Generate podcast episode with script

    Args:
        theme: Article theme (e.g., "technology", "business", "health")
        max_articles: Maximum number of articles to include
    """
    logger.info(f"Starting episode generation for theme: {theme}")

    try:
        # 1. Collect news articles
        logger.info("\n" + "="*60)
        logger.info("STEP 1: Collecting articles...")
        logger.info("="*60)

        client = NewsDataClient()
        articles = client.search_news(
            query=theme,
            language="ja",
            max_results=max_articles + 2  # Get extra to handle filtering
        )

        if not articles:
            logger.error("✗ No articles found")
            return None

        logger.info(f"✓ Fetched {len(articles)} articles")

        # 2. Deduplication
        logger.info("\n" + "="*60)
        logger.info("STEP 2: Deduplicating...")
        logger.info("="*60)

        dedup_engine = DeduplicationEngine()
        unique_articles = dedup_engine.filter_duplicates(articles)
        logger.info(f"✓ {len(unique_articles)} unique articles")

        # 3. Trust scoring
        logger.info("\n" + "="*60)
        logger.info("STEP 3: Calculating trust scores...")
        logger.info("="*60)

        trust_engine = TrustScoreEngine()
        min_trust = float(os.getenv("MIN_TRUST_SCORE", "0.6"))
        filtered_articles = trust_engine.filter_by_trust_score(unique_articles, min_score=min_trust)

        if not filtered_articles:
            logger.error("✗ No articles passed trust score threshold")
            return None

        logger.info(f"✓ {len(filtered_articles)} articles passed trust check")

        # Use only top N articles
        selected_articles = filtered_articles[:max_articles]

        # 4. Generate scripts
        logger.info("\n" + "="*60)
        logger.info("STEP 4: Generating scripts...")
        logger.info("="*60)

        groq_client = GroqClient()
        scripts = []

        for i, article in enumerate(selected_articles, 1):
            logger.info(f"\nGenerating script {i}/{len(selected_articles)}...")
            logger.info(f"Title: {article.get('title')[:60]}...")

            # Combine title and description for script generation
            article_text = f"{article.get('title')}\n\n{article.get('description')}"

            script = groq_client.generate_podcast_script(
                article_text=article_text,
                theme=theme
            )

            if script:
                scripts.append({
                    "article_index": i,
                    "article_title": article.get("title"),
                    "article_source": article.get("source_name"),
                    "trust_score": article.get("trust_score", 0),
                    "script": script
                })
                logger.info(f"✓ Script generated ({len(script)} chars)")
            else:
                logger.warning(f"⚠ Failed to generate script for article {i}")

        if not scripts:
            logger.error("✗ No scripts generated")
            return None

        # 5. Compile episode
        logger.info("\n" + "="*60)
        logger.info("STEP 5: Compiling episode...")
        logger.info("="*60)

        # Create intro and outro
        intro = """こんにちは、ポッドキャスト自動配信システムへようこそ。
本日は、最新のニュースを台本にしてお届けいたします。
それでは、今週のハイライトをご紹介します。

---
"""

        outro = """---

本日のエピソードをお聴きいただき、ありがとうございました。
今週も、興味深いニュースをお配りできたと思います。
次回のエピソードもお楽しみに。

それでは、また来週お会いしましょう。さようなら。"""

        # Combine all scripts
        full_script = intro
        for i, script_item in enumerate(scripts, 1):
            full_script += f"\n【セクション {i}: {script_item['article_source']}】\n"
            full_script += f"信頼度スコア: {script_item['trust_score']:.1f}/10\n\n"
            full_script += script_item["script"]
            full_script += "\n\n"

        full_script += outro

        # 6. Save episode
        logger.info("\n" + "="*60)
        logger.info("STEP 6: Saving episode...")
        logger.info("="*60)

        episode_data = {
            "generated_at": datetime.now().isoformat(),
            "theme": theme,
            "article_count": len(scripts),
            "total_script_length": len(full_script),
            "articles": [
                {
                    "title": s["article_title"],
                    "source": s["article_source"],
                    "trust_score": s["trust_score"]
                }
                for s in scripts
            ],
            "full_script": full_script
        }

        # Save to file
        output_dir = Path(__file__).parent.parent / "episodes"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        episode_path = output_dir / f"episode_{theme}_{timestamp}.json"

        with open(episode_path, "w", encoding="utf-8") as f:
            json.dump(episode_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ Episode saved to: {episode_path}")

        # 7. Display summary
        logger.info("\n" + "="*60)
        logger.info("EPISODE SUMMARY:")
        logger.info("="*60)
        logger.info(f"Theme: {theme}")
        logger.info(f"Total articles: {len(scripts)}")
        logger.info(f"Full script length: {len(full_script)} characters")
        logger.info(f"Estimated reading time: ~{len(full_script) // 300} minutes")

        logger.info("\n" + "="*60)
        logger.info("FULL SCRIPT PREVIEW:")
        logger.info("="*60)
        print(full_script[:500] + "...\n[Script truncated for display]")

        return episode_path

    except Exception as e:
        logger.error(f"✗ Episode generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    theme = sys.argv[1] if len(sys.argv) > 1 else "technology"
    max_articles = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    result = generate_episode(theme=theme, max_articles=max_articles)
    sys.exit(0 if result else 1)
