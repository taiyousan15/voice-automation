#!/usr/bin/env python3
"""Main pipeline execution script - Complete automation workflow"""
import asyncio
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from loguru import logger

from src.orchestrator import PipelineOrchestrator, PipelineConfig
from src.publishers.rss_generator import RSSGenerator

# Load environment
load_dotenv()

# Configure logger
logger.remove()
logger.add(
    sys.stderr,
    format="<level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
    level="INFO",
)


async def main(args):
    """
    Execute complete podcast automation pipeline

    Pipeline flow:
    1. Collect articles from NewsData.io (multi-theme)
    2. Deduplicate articles
    3. Calculate trust scores
    4. Generate scripts with Groq LLM
    5. Generate RSS feed
    6. Save outputs to files
    7. Generate dashboard summary
    """
    logger.info("\n" + "=" * 70)
    logger.info("🚀 PODCAST AUTOMATION PIPELINE STARTED")
    logger.info("=" * 70)

    start_time = datetime.now()

    try:
        # Parse configuration
        config = PipelineConfig(
            themes=args.themes.split(",") if args.themes else ["technology", "business", "health"],
            max_articles_per_theme=args.max_articles,
            articles_per_episode=args.articles_per_episode,
            max_workers=args.workers,
            timeout_seconds=args.timeout,
            dry_run=args.dry_run,
        )

        logger.info(f"Configuration:")
        logger.info(f"  Themes: {config.themes}")
        logger.info(f"  Max articles per theme: {config.max_articles_per_theme}")
        logger.info(f"  Articles per episode: {config.articles_per_episode}")
        logger.info(f"  Max workers: {config.max_workers}")
        logger.info(f"  Dry run: {config.dry_run}")

        # Step 1: Run orchestrator
        logger.info("\n" + "=" * 70)
        logger.info("STEP 1: Running orchestrator...")
        logger.info("=" * 70)

        orchestrator = PipelineOrchestrator(config)
        report = await orchestrator.run()

        logger.info(f"✓ Orchestrator completed: {report['total_episodes']} episodes")

        if args.dry_run:
            logger.info("✓ DRY RUN - No files saved")
            return report

        # Step 2: Save episodes to files
        logger.info("\n" + "=" * 70)
        logger.info("STEP 2: Saving episodes...")
        logger.info("=" * 70)

        output_dir = Path(args.output_dir) if args.output_dir else Path(__file__).parent.parent / "episodes"
        saved_files = orchestrator.save_results(output_dir)

        for key, path in saved_files.items():
            logger.info(f"✓ Saved: {path}")

        # Step 3: Generate RSS feed
        logger.info("\n" + "=" * 70)
        logger.info("STEP 3: Generating RSS feed...")
        logger.info("=" * 70)

        rss_gen = RSSGenerator(
            title="ポッドキャスト自動配信",
            description="AI自動生成のニュースポッドキャスト",
            link="https://github.com/yourusername/podcast-automation",
        )

        # Prepare episodes for RSS
        rss_episodes = []
        for result in orchestrator.results:
            if result.status == "success":
                rss_episodes.append(
                    {
                        "theme": result.theme,
                        "script": result.script,
                        "articles": [
                            {
                                "title": a.get("title"),
                                "source": a.get("source_name"),
                                "trust_score": a.get("trust_score", 0),
                            }
                            for a in result.articles
                        ],
                        "processing_time": result.processing_time,
                    }
                )

        if rss_episodes:
            feed_path = output_dir / "feed.xml"
            rss_gen.save_feed(rss_episodes, feed_path)

            # Validate feed
            if RSSGenerator.validate_feed(feed_path.read_text()):
                logger.info(f"✓ RSS feed generated: {feed_path}")
            else:
                logger.warning("⚠ RSS feed validation warning (may still be usable)")
        else:
            logger.warning("⚠ No successful episodes - RSS feed not generated")

        # Step 4: Generate dashboard summary
        logger.info("\n" + "=" * 70)
        logger.info("STEP 4: Generating dashboard summary...")
        logger.info("=" * 70)

        dashboard = {
            "generated_at": datetime.now().isoformat(),
            "total_time": (datetime.now() - start_time).total_seconds(),
            "total_episodes": report["total_episodes"],
            "successful_episodes": report["successful_episodes"],
            "failed_episodes": report["failed_episodes"],
            "episodes": report["episodes"],
            "files": {k: str(v) for k, v in saved_files.items()},
            "rss_feed": str(feed_path) if rss_episodes else None,
        }

        dashboard_path = output_dir / "dashboard.json"
        with open(dashboard_path, "w", encoding="utf-8") as f:
            json.dump(dashboard, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ Dashboard saved: {dashboard_path}")

        # Step 5: Final report
        logger.info("\n" + "=" * 70)
        logger.info("✅ PIPELINE EXECUTION COMPLETED")
        logger.info("=" * 70)
        logger.info(f"Total time: {dashboard['total_time']:.2f}s")
        logger.info(f"Episodes created: {dashboard['successful_episodes']}/{dashboard['total_episodes']}")
        logger.info(f"Output directory: {output_dir}")

        if rss_episodes:
            logger.info(f"RSS feed: {feed_path}")

        return dashboard

    except Exception as e:
        logger.error(f"✗ Pipeline failed: {e}")
        import traceback

        traceback.print_exc()
        return {"status": "failed", "error": str(e)}


def main_sync():
    """Sync wrapper for async main"""
    parser = argparse.ArgumentParser(description="Podcast Automation Pipeline")
    parser.add_argument(
        "--themes",
        default="technology,business,health",
        help="Comma-separated themes (default: technology,business,health)",
    )
    parser.add_argument(
        "--max-articles",
        type=int,
        default=3,
        help="Max articles per theme (default: 3)",
    )
    parser.add_argument(
        "--articles-per-episode",
        type=int,
        default=3,
        help="Articles per episode (default: 3)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Max concurrent workers (default: 3)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds (default: 300)",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory (default: ./episodes)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - no files saved",
    )

    args = parser.parse_args()

    result = asyncio.run(main(args))
    sys.exit(0 if result.get("status") != "failed" else 1)


if __name__ == "__main__":
    main_sync()
