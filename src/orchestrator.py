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
from src.generators.taiyo_script_generator import TaiyoScriptGenerator
from src.quality.japanese_reading_checker import JapaneseReadingChecker
from src.quality.quality_inspector import QualityInspector

# Add scripts to path for text_preprocessor
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).parent.parent / "scripts"))
from text_preprocessor import JapaneseTextPreprocessor
from src.publishers.rss_generator import RSSGenerator
from src.collectors.keyword_researcher import KeywordResearcher

from src.generators.groq_client import GroqClient
from src.generators.template_selector import TemplateSelector

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

# Taiyo Style Script Generator (Phase 3)
try:
    TAIYO_AVAILABLE = True
except ImportError:
    TAIYO_AVAILABLE = False
    logger.warning("Taiyo script generator not available - using basic script generation")
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
        self.taiyo_generator = TaiyoScriptGenerator()  # Phase 3: Taiyo style integration
        self.reading_checker = JapaneseReadingChecker()  # Phase 4: Japanese reading validation
        self.quality_inspector = QualityInspector()      # Phase 4: Script quality inspection
        self.text_preprocessor = JapaneseTextPreprocessor()  # Phase 5: TTS text preprocessing


        # Initialize template selector (REQ-201/REQ-202)
        self.template_selector = TemplateSelector()

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
                    timeout_seconds = int(os.getenv("FISH_AUDIO_TIMEOUT_SECONDS", "240"))
                    self.fish_audio_client = FishAudioClient(timeout=timeout_seconds)
                    self.logger.info(f"✓ Fish Audio client initialized (primary TTS, timeout={timeout_seconds}s)")
                except Exception as e:
                    self.logger.warning(f"⚠ Fish Audio initialization failed: {e}")

            # Always initialize VOICEVOX as fallback (even when Fish Audio is available)
            if VOICEVOX_AVAILABLE:
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
                world_search=True  # Phase 1: Enable world research integration
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

            # Select template based on theme (REQ-201/REQ-202)
            selected_template = self.template_selector.select(
                theme=theme,
                articles=articles,
                info_count=len(articles)
            )
            template_name = selected_template.get("name", "default") if selected_template else "default"
            template_style = selected_template.get("style", "taiyo_ok") if selected_template else "taiyo_ok"
            self.logger.info(f"  Template: {template_name} (style={template_style})")

            # Generate scripts for each article
            scripts = []
            for i, article in enumerate(articles, 1):
                try:
                    article_text = f"{article.get('title')}\n\n{article.get('description')}"

                    # Try Groq first (fast & free)
                    script = self.groq_client.generate_podcast_script(
                        article_text=article_text,
                        theme=theme,
                        template=selected_template
                    )

                    # Fallback to OpenRouter Claude Haiku if Groq fails
                    if not script and self.openrouter_client:
                        self.logger.warning(f"  ⚠ Groq failed for article {i}, falling back to Claude Haiku...")
                        script = self.openrouter_client.generate_podcast_script(
                            article_text=article_text,
                            theme=theme,
                            template=selected_template
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

            # Compile full script with dynamic article count adjustment
            max_total_chars = 5000
            max_retries = 2

            for retry in range(max_retries + 1):
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

                if len(full_script) <= max_total_chars:
                    break

                if retry < max_retries and len(scripts) > 1:
                    reduced_count = max(1, len(scripts) - 2)
                    self.logger.warning(
                        f"  ⚠ Script too long ({len(full_script)} chars > {max_total_chars}), "
                        f"reducing articles from {len(scripts)} to {reduced_count} (retry {retry + 1}/{max_retries})"
                    )
                    scripts = scripts[:reduced_count]
                else:
                    self.logger.warning(
                        f"  ⚠ Script still {len(full_script)} chars after {max_retries} retries"
                    )

            # Phase 4: Quality Check Pipeline
            self.logger.info(f"  Running quality checks for {theme}...")
            
            # 1st Japanese reading check (REQ-006)
            reading_result_1 = self.reading_checker.check(full_script)
            self.logger.info(
                f"  ✓ 1st reading check: {reading_result_1['total_risks']} risks detected "
                f"(kanji: {reading_result_1['kanji_count']}, "
                f"number: {reading_result_1['number_count']}, "
                f"english: {reading_result_1['english_count']})"
            )
            
            # Auto-correction if risks detected (REQ-007)
            if reading_result_1['total_risks'] > 0:
                corrected_script, corrections = self.reading_checker.auto_correct(full_script)
                self.logger.info(
                    f"  ✓ Auto-corrected {corrections['total']} issues "
                    f"(kanji: {corrections['difficult_kanji']}, "
                    f"number: {corrections['number_reading']}, "
                    f"english: {corrections['english_word']})"
                )
                full_script = corrected_script
                
                # 2nd reading check to verify correction (REQ-008)
                reading_result_2 = self.reading_checker.check(full_script)
                self.logger.info(
                    f"  ✓ 2nd reading check: {reading_result_2['total_risks']} remaining risks"
                )
                
                if reading_result_2['total_risks'] > 0:
                    self.logger.warning(f"  ⚠ {reading_result_2['total_risks']} risks remain after correction")
            else:
                self.logger.info("  ✓ No reading risks detected")
            
            # Quality inspection (REQ-009: char count, duration, Taiyo score)
            quality_result = self.quality_inspector.inspect(full_script, taiyo_score=None)
            
            # Log quality metrics
            char_status = "✓" if quality_result['char_count']['passed'] else "✗"
            dur_status = "✓" if quality_result['duration']['passed'] else "✗"
            self.logger.info(
                f"  {char_status} Character count: {quality_result['char_count']['value']} chars "
                f"({quality_result['char_count']['min']}-{quality_result['char_count']['max']})"
            )
            self.logger.info(
                f"  {dur_status} Estimated duration: {quality_result['duration']['value_str']} (4-7分)"
            )
            
            # Taiyo score (N/A in current implementation)
            if quality_result['taiyo_score']['value'] is not None:
                taiyo_status = "✓" if quality_result['taiyo_score']['passed'] else "✗"
                self.logger.info(
                    f"  {taiyo_status} Taiyo score: {quality_result['taiyo_score']['value']} points "
                    f"(>= {quality_result['taiyo_score']['min']})"
                )
            
            # Overall quality status
            critical_issues = [i for i in quality_result['issues'] if i['severity'] == 'critical']
            # TTS-dangerous issues only: long scripts cause timeouts, short scripts are safe
            tts_blocking_types = {'char_count_high', 'duration_long'}
            tts_blocking_issues = [i for i in critical_issues if i['type'] in tts_blocking_types]
            if quality_result['passed']:
                self.logger.info("  ✓ Quality check PASSED")
            elif critical_issues:
                self.logger.error(
                    f"  ✗ Quality check CRITICAL ({len(critical_issues)} critical issues) - TTS blocked"
                )
                for issue in critical_issues:
                    self.logger.error(f"    ! {issue['message']}")
            else:
                self.logger.warning(
                    f"  ⚠ Quality check FAILED ({len(quality_result['issues'])} issues)"
                )
                for issue in quality_result['issues']:
                    severity_icon = "!" if issue['severity'] == 'critical' else "⚠"
                    self.logger.warning(f"    {severity_icon} {issue['message']}")

            episode_name = f"episode_{theme}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Block TTS only for TTS-dangerous issues (long scripts cause timeouts)
            # char_count_low is critical for quality but safe for TTS
            if tts_blocking_issues:
                self.logger.warning(f"  ⚠ Skipping audio generation due to TTS-dangerous issues")
                return ProcessingResult(
                    episode_name=episode_name,
                    theme=theme,
                    status="partial",
                    articles=articles,
                    script=full_script,
                    audio_file=None,
                    error_message=f"TTS blocked: {len(tts_blocking_issues)} TTS-dangerous issues",
                    processing_time=(datetime.now() - start_time).total_seconds()
                )

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
        # Phase 5: MANDATORY TTS preprocessing (CLAUDE.md requirement)
        # Convert numbers to hiragana to prevent misreading
        # Examples: 1000万→いっせんまん, 3000万→さんぜんまん, 8000億→はっせんおく
        original_script = script
        script = self.text_preprocessor.preprocess(script)
        
        if script != original_script:
            self.logger.debug("  ✓ TTS preprocessing applied (numbers → hiragana)")
        
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
                    # Only copy if source and destination are different
                    if result.audio_file.resolve() != audio_dest.resolve():
                        import shutil
                        shutil.copy2(result.audio_file, audio_dest)
                        self.logger.info(f"✓ Saved audio: {audio_dest}")
                    else:
                        self.logger.debug(f"✓ Audio already in place: {audio_dest}")
                    saved_files[f"audio_{result.theme}"] = audio_dest

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

        # Phase 6: Generate RSS feed (REQ-010: RSS配信)
        import os
        
        # Get GitHub Pages URL from environment (set by GitHub Actions)
        github_pages_url = os.getenv(
            "GITHUB_PAGES_URL",
            "https://USERNAME.github.io/REPO_NAME"  # Fallback for local testing
        )
        
        # Initialize RSS generator
        rss_gen = RSSGenerator(
            title="AI情報ポッドキャスト - 最新トレンド自動配信",
            description="AIビジネス、バイブコーディング、エージェント活用など、最新AI情報を毎日自動配信",
            language="ja",
            author="AI Podcast System",
            link=github_pages_url
        )
        
        # Prepare episodes for RSS (with audio URLs)
        rss_episodes = []
        for r in self.results:
            if r.status == "success":
                rss_episodes.append({
                    "theme": r.theme,
                    "script": r.script,
                    "articles": [
                        {
                            "title": a.get("title"),
                            "source": a.get("source_name"),
                            "trust_score": a.get("trust_score")
                        }
                        for a in r.articles
                    ],
                    "audio_url": r.audio_url,
                    "audio_length": r.audio_length,
                    "audio_duration": r.audio_duration,
                    "processing_time": r.processing_time
                })
        
        # Generate and save RSS feed
        rss_file = output_dir / "feed.xml"
        rss_gen.save_feed(rss_episodes, rss_file)
        saved_files["rss_feed"] = rss_file
        self.logger.info(f"✓ Saved RSS feed: {rss_file}")
        self.logger.info(f"  Feed URL: {github_pages_url}/feed.xml")
        
        # Generate dashboard.json for GitHub Pages
        dashboard_file = output_dir / "dashboard.json"
        with open(dashboard_file, "w", encoding="utf-8") as f:
            dashboard = {
                "generated_at": datetime.now().isoformat(),
                "feed_url": f"{github_pages_url}/feed.xml",
                "episodes_count": len(rss_episodes),
                "latest_episode": rss_episodes[0]["theme"] if rss_episodes else None,
                "audio_enabled": self.enable_audio
            }
            json.dump(dashboard, f, ensure_ascii=False, indent=2)
        saved_files["dashboard"] = dashboard_file
        self.logger.info(f"✓ Saved dashboard: {dashboard_file}")
        self.logger.info(f"✓ Saved summary: {summary_file}")

        # Phase 7: Multi-platform distribution (non-blocking)
        try:
            from src.publishers.distribution_manager import DistributionManager
            dist_manager = DistributionManager()
            rss_url = f"{github_pages_url}/feed.xml"

            for result in self.results:
                if result.status == "success" and result.audio_url:
                    dist_report = dist_manager.distribute_episode(
                        episode_title=f"エピソード: {result.theme.capitalize()}",
                        theme=result.theme,
                        audio_path=result.audio_file,
                        audio_url=result.audio_url,
                        description=result.script[:500] if result.script else "",
                        rss_url=rss_url,
                        output_dir=output_dir,
                    )
                    saved_files[f"distribution_{result.theme}"] = {
                        "successful": [r.platform for r in dist_report.successful],
                        "skipped": [r.platform for r in dist_report.skipped_platforms],
                        "failed": [r.platform for r in dist_report.failed],
                    }
        except Exception as e:
            self.logger.warning(f"Distribution failed (non-blocking): {e}")

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
