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
from src.collectors.keyword_researcher import KeywordResearcher

from src.generators.groq_client import GroqClient

# LLM Fallback: OpenRouter Claude Haiku
try:
    from src.generators.openrouter_client import OpenRouterClient
    OPENROUTER_AVAILABLE = True
except ImportError:
    OPENROUTER_AVAILABLE = False
    logger.warning("OpenRouter client not available - LLM fallback disabled")

# TTS Clients (Fish Audio優先、VOICEVOXフォールバック)
try:
    from src.generators.fish_audio_client import FishAudioClient
    FISH_AUDIO_AVAILABLE = True
except ImportError:
    FISH_AUDIO_AVAILABLE = False
    logger.warning("Fish Audio client not available - falling back to VOICEVOX")

try:
    from src.generators.voicevox_client import VOICEVOXClient
    VOICEVOX_AVAILABLE = True
except ImportError:
    VOICEVOX_AVAILABLE = False
    logger.warning("VOICEVOX client not available - audio generation will be skipped")


@dataclass
class PipelineConfig:
    """Pipeline configuration"""
    themes: List[str] = None
    max_articles_per_theme: int = 7  # 4-7分のコンテンツ確保
    articles_per_episode: int = 7
    max_workers: int = 3
    timeout_seconds: int = 300
    dry_run: bool = False

    def __post_init__(self):
        if self.themes is None:
            self.themes = ["technology", "business", "health"]


@dataclass
class ProcessingResult:
    """Processing result with optional audio generation"""
    episode_name: str
    theme: str
    status: str  # "success", "partial", "failed"
    articles: List[Dict[str, Any]]
    script: Optional[str] = None
    audio_file: Optional[Path] = None  # Path to generated MP3
    audio_url: Optional[str] = None  # Public URL for RSS enclosure
    audio_length: Optional[int] = None  # File size in bytes
    audio_duration: Optional[str] = None  # Duration in HH:MM:SS format
    error_message: Optional[str] = None
    processing_time: float = 0.0


class PipelineOrchestrator:
    """Main orchestrator for end-to-end pipeline"""

    def __init__(self, config: PipelineConfig = None, enable_audio: bool = True):
        """Initialize orchestrator

        Args:
            config: Pipeline configuration
            enable_audio: Enable audio generation (Fish Audio or VOICEVOX)
        """
        self.config = config or PipelineConfig()
        self.logger = logger
        self.results: List[ProcessingResult] = []
        self.enable_audio = enable_audio and (FISH_AUDIO_AVAILABLE or VOICEVOX_AVAILABLE)

        # Initialize components
        self.newsdata_client = NewsDataClient()
        self.dedup_engine = DeduplicationEngine()
        self.trust_engine = TrustScoreEngine()
        self.keyword_researcher = KeywordResearcher()


        # Initialize LLM clients (Groq優先、OpenRouter Claude Haikuフォールバック)
        self.groq_client = GroqClient()
        self.openrouter_client = None

        if OPENROUTER_AVAILABLE:
            try:
                self.openrouter_client = OpenRouterClient()
                self.logger.info("✓ OpenRouter Claude client initialized (LLM fallback)")
            except Exception as e:
                self.logger.warning(f"⚠ OpenRouter initialization failed: {e}")

        # Initialize TTS clients (Fish Audio優先、VOICEVOXフォールバック)
        self.fish_audio_client = None
        self.voicevox_client = None

        if self.enable_audio:
            # Try Fish Audio first (premium quality)
            if FISH_AUDIO_AVAILABLE:
                try:
                    self.fish_audio_client = FishAudioClient()
                    self.logger.info("✓ Fish Audio client initialized (primary TTS)")
                except Exception as e:
                    self.logger.warning(f"⚠ Fish Audio initialization failed: {e}")

            # Try VOICEVOX as fallback
            if VOICEVOX_AVAILABLE and not self.fish_audio_client:
                try:
                    self.voicevox_client = VOICEVOXClient()
                    self.logger.info("✓ VOICEVOX client initialized (fallback TTS)")
                except Exception as e:
                    self.logger.warning(f"⚠ VOICEVOX initialization failed: {e}")

            # Disable audio if neither TTS is available
            if not self.fish_audio_client and not self.voicevox_client:
                self.enable_audio = False
                self.logger.warning("⚠ No TTS engine available - audio generation disabled")

        self.logger.info(f"Pipeline orchestrator initialized - Themes: {self.config.themes}")
        self.logger.info(f"Audio generation: {'enabled' if self.enable_audio else 'disabled'}")

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
        """Collect articles from all themes with keyword expansion"""
        all_articles = {}
        
        # Step 1: Keyword expansion and world research
        self.logger.info("=== Keyword Expansion & Research ===")
        try:
            research_results = await self.keyword_researcher.integrated_research(
                themes=self.config.themes,
                expand_keywords=True,
                world_search=False  # Set to True to enable full world research
            )
            
            # Extract newsworthy topics for NewsData.io
            expanded_queries = self.keyword_researcher.extract_newsworthy_topics(research_results)
            self.logger.info(f"✓ Expanded to {len(expanded_queries)} search queries")
        except Exception as e:
            self.logger.warning(f"⚠ Keyword expansion failed: {e}, using original themes")
            expanded_queries = self.config.themes

        # Step 2: Collect articles using expanded queries
        for theme in expanded_queries[:10]:  # Limit to top 10 to avoid quota
            try:
                self.logger.info(f"\nCollecting articles for: {theme}")

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

                    # Try Groq first (fast & free)
                    script = self.groq_client.generate_podcast_script(
                        article_text=article_text,
                        theme=theme
                    )

                    # Fallback to OpenRouter Claude Haiku if Groq fails
                    if not script and self.openrouter_client:
                        self.logger.warning(f"  ⚠ Groq failed for article {i}, falling back to Claude Haiku...")
                        script = self.openrouter_client.generate_podcast_script(
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

            # Generate audio if enabled
            audio_file = None
            audio_url = None
            audio_length = None
            audio_duration = None

            if self.enable_audio and (self.fish_audio_client or self.voicevox_client):
                try:
                    self.logger.info(f"  Generating audio for {theme}...")
                    audio_result = await self._generate_audio(episode_name, full_script)
                    if audio_result:
                        audio_file = audio_result["file"]
                        audio_url = audio_result["url"]
                        audio_length = audio_result["length"]
                        audio_duration = audio_result["duration"]
                        self.logger.info(f"  ✓ Audio generated: {audio_file.name}")
                except Exception as e:
                    self.logger.warning(f"  ⚠ Audio generation failed: {e}")

            result = ProcessingResult(
                episode_name=episode_name,
                theme=theme,
                status="success",
                articles=articles,
                script=full_script,
                audio_file=audio_file,
                audio_url=audio_url,
                audio_length=audio_length,
                audio_duration=audio_duration,
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

    async def _generate_audio(self, episode_name: str, script: str) -> Optional[Dict[str, Any]]:
        """
        Generate audio from script using Fish Audio (primary) or VOICEVOX (fallback)

        Args:
            episode_name: Episode identifier
            script: Full episode script

        Returns:
            Dict with audio metadata (file, url, length, duration) or None if failed
        """
        if not self.fish_audio_client and not self.voicevox_client:
            return None

        audio_result = None
        tts_engine = None

        # Try Fish Audio first (premium quality)
        if self.fish_audio_client:
            try:
                self.logger.info("  Using Fish Audio TTS...")
                audio_result = await self.fish_audio_client.generate_podcast_audio(
                    text=script,
                    output_filename=episode_name  # Fish Audio adds .mp3 extension
                )
                tts_engine = "Fish Audio"
            except Exception as e:
                self.logger.warning(f"  ⚠ Fish Audio failed: {e}, falling back to VOICEVOX...")

        # Fallback to VOICEVOX if Fish Audio failed or unavailable
        if not audio_result and self.voicevox_client:
            try:
                self.logger.info("  Using VOICEVOX TTS...")
                voicevox_file = await self.voicevox_client.generate_podcast_audio(
                    text=script,
                    output_filename=f"{episode_name}.mp3"
                )
                if voicevox_file and voicevox_file.exists():
                    # Convert VOICEVOX Path to dict format
                    audio_result = {
                        "file_path": voicevox_file,
                        "duration": self.voicevox_client.get_audio_duration(voicevox_file),
                        "size_bytes": voicevox_file.stat().st_size,
                        "format": "mp3"
                    }
                    tts_engine = "VOICEVOX"
            except Exception as e:
                self.logger.error(f"  ✗ VOICEVOX also failed: {e}")
                return None

        # Validate result
        if not audio_result:
            self.logger.error("  ✗ Audio file generation failed")
            return None

        try:
            # Extract file path from result (Fish Audio returns dict, VOICEVOX converted to dict)
            audio_file = audio_result.get("file_path")
            if not audio_file or not audio_file.exists():
                self.logger.error("  ✗ Audio file not found")
                return None

            # Get metadata from result
            audio_length = audio_result.get("size_bytes", audio_file.stat().st_size)
            audio_duration = audio_result.get("duration", 0)

            # Generate GitHub Pages URL
            base_url = os.getenv("GITHUB_PAGES_URL", "https://taiyousan15.github.io/voice-automation")
            audio_url = f"{base_url}/podcast/{audio_file.name}"

            self.logger.info(f"  ✓ Audio generated using {tts_engine}")
            return {
                "file": audio_file,
                "url": audio_url,
                "length": audio_length,
                "duration": audio_duration,
                "engine": tts_engine
            }

        except Exception as e:
            self.logger.error(f"Audio metadata extraction error: {e}")
            return None

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
        """Save pipeline results to files (scripts, audio, summary)"""
        # Convert string to Path if needed
        if isinstance(output_dir, str):
            output_dir = Path(output_dir)

        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "pipeline_output"

        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = {}

        # Save each episode
        for result in self.results:
            if result.status == "success":
                # Save script
                if result.script:
                    episode_file = output_dir / f"{result.episode_name}.txt"
                    with open(episode_file, "w", encoding="utf-8") as f:
                        f.write(result.script)
                    saved_files[f"episode_{result.theme}"] = episode_file
                    self.logger.info(f"✓ Saved script: {episode_file}")

                # Copy audio file if it exists
                if result.audio_file and result.audio_file.exists():
                    audio_dest = output_dir / result.audio_file.name
                    import shutil
                    shutil.copy2(result.audio_file, audio_dest)
                    saved_files[f"audio_{result.theme}"] = audio_dest
                    self.logger.info(f"✓ Saved audio: {audio_dest}")

        # Save summary with audio metadata
        summary_file = output_dir / "summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            summary = {
                "generated_at": datetime.now().isoformat(),
                "total_episodes": len(self.results),
                "audio_enabled": self.enable_audio,
                "episodes": [
                    {
                        "name": r.episode_name,
                        "theme": r.theme,
                        "status": r.status,
                        "audio_url": r.audio_url,
                        "audio_length": r.audio_length,
                        "audio_duration": r.audio_duration,
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


async def main():
    """Main entry point for podcast automation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Podcast Automation System")
    parser.add_argument(
        "--themes",
        nargs="+",
        help="Themes to generate podcasts for"
    )
    parser.add_argument(
        "--enable-audio",
        action="store_true",
        help="Enable audio generation (Fish Audio or VOICEVOX)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="episodes",
        help="Output directory for episodes"
    )
    
    args = parser.parse_args()
    
    # Load config.yaml if it exists
    config_file = Path("config.yaml")
    themes = args.themes
    
    if not themes and config_file.exists():
        import yaml
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
            themes = config_data.get("themes", [])
            logger.info(f"Loaded {len(themes)} themes from config.yaml")
    
    if not themes:
        logger.error("No themes specified. Use --themes or create config.yaml")
        return
    
    # Create pipeline config
    pipeline_config = PipelineConfig(themes=themes)
    
    # Create orchestrator
    orchestrator = PipelineOrchestrator(
        config=pipeline_config,
        enable_audio=args.enable_audio
    )
    
    # Run pipeline
    logger.info("=== Starting Podcast Automation Pipeline ===")
    logger.info(f"Themes: {', '.join(themes)}")
    logger.info(f"Audio: {'Enabled' if args.enable_audio else 'Disabled'}")
    
    report = await orchestrator.run()
    
    # Save results
    saved_files = orchestrator.save_results(output_dir=args.output_dir)
    
    # Print summary
    logger.info("\n=== Pipeline Complete ===")
    logger.info(f"Total episodes: {report['total_episodes']}")
    logger.info(f"Successful: {report['successful_episodes']}")
    logger.info(f"Failed: {report['failed_episodes']}")
    
    for key, file_path in saved_files.items():
        logger.info(f"  - {key}: {file_path}")


if __name__ == "__main__":
    asyncio.run(main())
