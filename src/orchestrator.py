"""Main pipeline orchestrator - Complete automation workflow"""
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from loguru import logger

from src.collectors.newsdata_client import NewsDataClient
from src.utils.deduplication import DeduplicationEngine
from src.utils.trust_score import TrustScoreEngine
from src.generators.groq_client import GroqClient


@dataclass
class PipelineConfig:
    """Pipeline configuration"""
    themes: List[str] = None
    max_articles_per_theme: int = 3
    articles_per_episode: int = 3
    max_workers: int = 3
    timeout_seconds: int = 300
    dry_run: bool = False

    def __post_init__(self):
        if self.themes is None:
            self.themes = ["technology", "business", "health"]


@dataclass
class ProcessingResult:
    """Processing result"""
    episode_name: str
    theme: str
    status: str  # "success", "partial", "failed"
    articles: List[Dict[str, Any]]
    script: Optional[str] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0


class PipelineOrchestrator:
    """Main orchestrator for end-to-end pipeline"""

    def __init__(self, config: PipelineConfig = None):
        """Initialize orchestrator"""
        self.config = config or PipelineConfig()
        self.logger = logger
        self.results: List[ProcessingResult] = []

        # Initialize components
        self.newsdata_client = NewsDataClient()
        self.dedup_engine = DeduplicationEngine()
        self.trust_engine = TrustScoreEngine()
        self.groq_client = GroqClient()

        self.logger.info(f"Pipeline orchestrator initialized - Themes: {self.config.themes}")

    async def run(self) -> Dict[str, Any]:
        """Run complete pipeline"""
        self.logger.info("\n" + "="*70)
        self.logger.info("STARTING END-TO-END PIPELINE")
        self.logger.info("="*70)

        start_time = datetime.now()

        try:
            # Step 1: Collect articles
            self.logger.info("\nSTEP 1: Collecting articles from all themes...")
            all_articles = await self._collect_articles()

            if not all_articles:
                self.logger.error("✗ No articles collected")
                return self._generate_report(start_time, success=False)

            # Step 2: Generate episodes
            self.logger.info("\nSTEP 2: Generating episodes...")
            tasks = []
            for theme, articles in all_articles.items():
                task = self._generate_episode_async(theme, articles)
                tasks.append(task)

            # Run tasks concurrently with semaphore
            semaphore = asyncio.Semaphore(self.config.max_workers)

            async def bounded_task(task):
                async with semaphore:
                    return await task

            episode_results = await asyncio.gather(*[bounded_task(t) for t in tasks], return_exceptions=True)

            # Handle results
            for result in episode_results:
                if isinstance(result, Exception):
                    self.logger.error(f"✗ Episode generation failed: {result}")
                else:
                    self.results.append(result)

            # Step 3: Generate report
            self.logger.info("\nSTEP 3: Generating report...")
            report = self._generate_report(start_time, success=len(self.results) > 0)

            return report

        except Exception as e:
            self.logger.error(f"✗ Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            return self._generate_report(start_time, success=False)

    async def _collect_articles(self) -> Dict[str, List[Dict[str, Any]]]:
        """Collect articles from all themes"""
        all_articles = {}

        for theme in self.config.themes:
            try:
                self.logger.info(f"\nCollecting articles for theme: {theme}")

                # Fetch articles
                articles = self.newsdata_client.search_news(
                    query=theme,
                    language="ja",
                    max_results=self.config.max_articles_per_theme + 2
                )

                if not articles:
                    self.logger.warning(f"  ⚠ No articles found for {theme}")
                    continue

                # Deduplicate
                unique_articles = self.dedup_engine.filter_duplicates(articles)

                # Score
                scored_articles = []
                min_trust = float(os.getenv("MIN_TRUST_SCORE", "0.6"))
                for article in unique_articles:
                    score = self.trust_engine.calculate_score(article)
                    article["trust_score"] = score
                    scored_articles.append(article)

                # Filter by trust score
                filtered = self.trust_engine.filter_by_trust_score(
                    scored_articles,
                    min_score=min_trust
                )

                if filtered:
                    all_articles[theme] = filtered[:self.config.articles_per_episode]
                    self.logger.info(f"  ✓ {len(all_articles[theme])} articles for {theme}")
                else:
                    self.logger.warning(f"  ⚠ No articles passed trust score for {theme}")

            except Exception as e:
                self.logger.error(f"✗ Error collecting articles for {theme}: {e}")
                continue

        return all_articles

    async def _generate_episode_async(self, theme: str, articles: List[Dict[str, Any]]) -> ProcessingResult:
        """Generate episode for theme (async wrapper)"""
        start_time = datetime.now()

        try:
            # Generate intro
            intro = f"""こんにちは、ポッドキャスト自動配信システムへようこそ。
本日は、【{theme}】に関する最新ニュースをお届けします。
それでは、今週のハイライトをご紹介します。

---
"""

            # Generate scripts for each article
            scripts = []
            for i, article in enumerate(articles, 1):
                try:
                    article_text = f"{article.get('title')}\n\n{article.get('description')}"

                    script = self.groq_client.generate_podcast_script(
                        article_text=article_text,
                        theme=theme
                    )

                    if script:
                        scripts.append({
                            "index": i,
                            "title": article.get("title"),
                            "source": article.get("source_name"),
                            "trust_score": article.get("trust_score", 0),
                            "script": script
                        })
                        self.logger.debug(f"  ✓ Script {i} generated for {theme}")
                    else:
                        self.logger.warning(f"  ⚠ Failed to generate script {i} for {theme}")

                except Exception as e:
                    self.logger.error(f"✗ Error generating script {i}: {e}")
                    continue

            if not scripts:
                return ProcessingResult(
                    episode_name=f"episode_{theme}_{datetime.now().strftime('%Y%m%d')}",
                    theme=theme,
                    status="failed",
                    articles=articles,
                    error_message="No scripts generated",
                    processing_time=(datetime.now() - start_time).total_seconds()
                )

            # Compile full script
            full_script = intro
            for script_item in scripts:
                full_script += f"\n【セクション {script_item['index']}: {script_item['source']}】\n"
                full_script += f"信頼度スコア: {script_item['trust_score']:.1f}/10\n\n"
                full_script += script_item["script"]
                full_script += "\n\n"

            outro = """---

本日のエピソードをお聴きいただき、ありがとうございました。
次回のエピソードもお楽しみに。

それでは、また来週お会いしましょう。さようなら。"""

            full_script += outro

            episode_name = f"episode_{theme}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            result = ProcessingResult(
                episode_name=episode_name,
                theme=theme,
                status="success",
                articles=articles,
                script=full_script,
                processing_time=(datetime.now() - start_time).total_seconds()
            )

            self.logger.info(f"✓ Episode generated for {theme} in {result.processing_time:.2f}s")
            return result

        except Exception as e:
            self.logger.error(f"✗ Error generating episode for {theme}: {e}")
            return ProcessingResult(
                episode_name=f"episode_{theme}_{datetime.now().strftime('%Y%m%d')}",
                theme=theme,
                status="failed",
                articles=articles,
                error_message=str(e),
                processing_time=(datetime.now() - start_time).total_seconds()
            )

    def _generate_report(self, start_time: datetime, success: bool) -> Dict[str, Any]:
        """Generate execution report"""
        elapsed = (datetime.now() - start_time).total_seconds()

        report = {
            "timestamp": datetime.now().isoformat(),
            "status": "success" if success else "failed",
            "total_episodes": len(self.results),
            "successful_episodes": sum(1 for r in self.results if r.status == "success"),
            "failed_episodes": sum(1 for r in self.results if r.status == "failed"),
            "total_processing_time": elapsed,
            "episodes": [
                {
                    "name": r.episode_name,
                    "theme": r.theme,
                    "status": r.status,
                    "articles_count": len(r.articles),
                    "script_length": len(r.script) if r.script else 0,
                    "processing_time": r.processing_time,
                    "error": r.error_message
                }
                for r in self.results
            ]
        }

        self.logger.info("\n" + "="*70)
        self.logger.info("PIPELINE EXECUTION REPORT")
        self.logger.info("="*70)
        self.logger.info(f"Total Episodes: {report['total_episodes']}")
        self.logger.info(f"Successful: {report['successful_episodes']}")
        self.logger.info(f"Failed: {report['failed_episodes']}")
        self.logger.info(f"Total Time: {elapsed:.2f}s")
        self.logger.info("="*70)

        return report

    def save_results(self, output_dir: Path = None) -> Dict[str, Path]:
        """Save pipeline results to files"""
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "pipeline_output"

        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = {}

        # Save each episode
        for result in self.results:
            if result.status == "success" and result.script:
                episode_file = output_dir / f"{result.episode_name}.txt"
                with open(episode_file, "w", encoding="utf-8") as f:
                    f.write(result.script)
                saved_files[f"episode_{result.theme}"] = episode_file
                self.logger.info(f"✓ Saved: {episode_file}")

        # Save summary
        summary_file = output_dir / "summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            summary = {
                "generated_at": datetime.now().isoformat(),
                "total_episodes": len(self.results),
                "episodes": [
                    {
                        "name": r.episode_name,
                        "theme": r.theme,
                        "status": r.status,
                        "articles": [
                            {
                                "title": a.get("title"),
                                "source": a.get("source_name"),
                                "trust_score": a.get("trust_score")
                            }
                            for a in r.articles
                        ]
                    }
                    for r in self.results
                ]
            }
            json.dump(summary, f, ensure_ascii=False, indent=2)

        saved_files["summary"] = summary_file
        self.logger.info(f"✓ Saved summary: {summary_file}")

        return saved_files
