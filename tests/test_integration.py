"""Integration tests for podcast automation pipeline"""
import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from src.orchestrator import PipelineOrchestrator, PipelineConfig, ProcessingResult
from src.publishers.rss_generator import RSSGenerator
from src.collectors.newsdata_client import NewsDataClient
from src.utils.deduplication import DeduplicationEngine
from src.utils.trust_score import TrustScoreEngine


class TestPipelineIntegration:
    """Integration tests for complete pipeline"""

    @pytest.fixture
    def config(self):
        """Create test configuration"""
        return PipelineConfig(
            themes=["technology"],
            max_articles_per_theme=2,
            articles_per_episode=2,
            max_workers=1,
            timeout_seconds=60,
            dry_run=False,
        )

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, config):
        """Test orchestrator initializes correctly"""
        with patch.dict('os.environ', {'NEWSDATA_API_KEY': 'test_key', 'GROQ_API_KEY': 'test_key'}):
            orchestrator = PipelineOrchestrator(config)
            assert orchestrator.config is not None
            assert len(orchestrator.config.themes) == 1
            assert orchestrator.config.themes[0] == "technology"
            assert orchestrator.results == []

    @pytest.mark.asyncio
    async def test_generate_episode(self, config):
        """Test episode generation"""
        with patch.dict('os.environ', {'NEWSDATA_API_KEY': 'test_key', 'GROQ_API_KEY': 'test_key'}):
            orchestrator = PipelineOrchestrator(config)

            # Create mock articles
            mock_articles = [
                {
                    "title": "テストニュース1",
                    "description": "テスト説明1",
                    "source_name": "Test Source",
                    "trust_score": 7.5,
                },
                {
                    "title": "テストニュース2",
                    "description": "テスト説明2",
                    "source_name": "Test Source",
                    "trust_score": 8.0,
                },
            ]

            result = await orchestrator._generate_episode_async("technology", mock_articles)

            assert isinstance(result, ProcessingResult)
            assert result.theme == "technology"
            assert result.status in ["success", "failed"]
            if result.status == "success":
                assert result.script is not None
                assert len(result.script) > 0

    def test_rss_feed_generation(self):
        """Test RSS feed generation"""
        rss_gen = RSSGenerator()

        episodes = [
            {
                "theme": "technology",
                "script": "これはテスト台本です。",
                "articles": [
                    {
                        "title": "テスト記事",
                        "source": "Test",
                        "trust_score": 8.0,
                    }
                ],
                "processing_time": 1.5,
            }
        ]

        feed = rss_gen.generate_feed(episodes)

        assert feed is not None
        assert "<?xml" in feed
        assert "<rss" in feed
        assert "<title>" in feed
        assert "<item>" in feed
        assert "</rss>" in feed
        assert RSSGenerator.validate_feed(feed)

    def test_rss_feed_escaping(self):
        """Test RSS XML escaping"""
        rss_gen = RSSGenerator()

        episodes = [
            {
                "theme": "tech & science",
                "script": "Test script with ampersand",
                "articles": [
                    {
                        "title": "Title with special chars",
                        "source": "Source & Co.",
                        "trust_score": 7.5,
                    }
                ],
                "processing_time": 1.0,
            }
        ]

        feed = rss_gen.generate_feed(episodes)
        # Should have escaped ampersand
        assert "&amp;" in feed

    def test_deduplication_engine(self):
        """Test article deduplication"""
        dedup = DeduplicationEngine()

        articles = [
            {
                "title": "Article 1",
                "link": "https://example.com/1",
                "description": "Description 1",
            },
            {
                "title": "Article 2",
                "link": "https://example.com/2",
                "description": "Description 2",
            },
            {
                "title": "Article 1 Duplicate",
                "link": "https://example.com/1",
                "description": "Description 1",
            },
        ]

        unique = dedup.filter_duplicates(articles)
        assert len(unique) == 2
        assert unique[0]["title"] == "Article 1"
        assert unique[1]["title"] == "Article 2"

    def test_trust_scoring(self):
        """Test trust score calculation"""
        trust_engine = TrustScoreEngine()

        articles = [
            {
                "title": "NHK News",
                "source_name": "NHK",
                "description": "Important news",
            },
            {
                "title": "Unknown Source",
                "source_name": "Unknown News",
                "description": "Some news",
            },
        ]

        scored = []
        for article in articles:
            score = trust_engine.calculate_score(article)
            article["trust_score"] = score
            scored.append(article)

        # NHK should have higher trust score
        assert scored[0]["trust_score"] > scored[1]["trust_score"]

    def test_trust_score_filtering(self):
        """Test trust score filtering"""
        trust_engine = TrustScoreEngine()

        articles = [
            {
                "title": "Article 1",
                "source_name": "NHK",
                "description": "Important",
                "trust_score": 9.0,
            },
            {
                "title": "Article 2",
                "source_name": "Unknown",
                "description": "Maybe",
                "trust_score": 4.0,
            },
            {
                "title": "Article 3",
                "source_name": "Asahi",
                "description": "News",
                "trust_score": 8.0,
            },
        ]

        filtered = trust_engine.filter_by_trust_score(articles, min_score=0.7)
        assert len(filtered) == 2
        assert all(a["trust_score"] >= 0.7 for a in filtered)

    def test_processing_result_dataclass(self):
        """Test ProcessingResult creation"""
        result = ProcessingResult(
            episode_name="test_episode",
            theme="technology",
            status="success",
            articles=[{"title": "Test"}],
            script="Test script",
            processing_time=1.5,
        )

        assert result.episode_name == "test_episode"
        assert result.theme == "technology"
        assert result.status == "success"
        assert len(result.articles) == 1
        assert result.script == "Test script"
        assert result.processing_time == 1.5
        assert result.error_message is None

    def test_rss_feed_save(self, tmp_path):
        """Test saving RSS feed to file"""
        rss_gen = RSSGenerator()

        episodes = [
            {
                "theme": "test",
                "script": "Test script",
                "articles": [],
                "processing_time": 1.0,
            }
        ]

        feed_path = tmp_path / "test_feed.xml"
        saved_path = rss_gen.save_feed(episodes, feed_path)

        assert saved_path.exists()
        content = saved_path.read_text()
        assert "<?xml" in content
        assert "<rss" in content

    @pytest.mark.asyncio
    async def test_complete_pipeline_flow(self, tmp_path):
        """Test complete pipeline flow"""
        config = PipelineConfig(
            themes=["technology"],
            max_articles_per_theme=1,
            articles_per_episode=1,
            max_workers=1,
            timeout_seconds=30,
            dry_run=False,
        )

        orchestrator = PipelineOrchestrator(config)

        # Run pipeline
        report = await orchestrator.run()

        assert "status" in report or "total_episodes" in report
        assert isinstance(report, dict)

        # Test result saving
        saved_files = orchestrator.save_results(tmp_path)
        assert "summary" in saved_files


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_episodes_rss(self):
        """Test RSS generation with empty episodes"""
        rss_gen = RSSGenerator()
        feed = rss_gen.generate_feed([])

        assert "<?xml" in feed
        assert "<rss" in feed
        assert RSSGenerator.validate_feed(feed)

    def test_special_characters_in_articles(self):
        """Test handling of special characters"""
        rss_gen = RSSGenerator()

        episodes = [
            {
                "theme": "テーマ",
                "script": "日本語の台本",
                "articles": [
                    {
                        "title": "日本語 & 特殊文字 < > \" '",
                        "source": "ソース",
                        "trust_score": 8.5,
                    }
                ],
                "processing_time": 1.0,
            }
        ]

        feed = rss_gen.generate_feed(episodes)
        assert RSSGenerator.validate_feed(feed)

    def test_very_long_script(self):
        """Test handling of very long scripts"""
        rss_gen = RSSGenerator()

        long_script = "これは長い台本です。" * 100

        episodes = [
            {
                "theme": "test",
                "script": long_script,
                "articles": [],
                "processing_time": 1.0,
            }
        ]

        feed = rss_gen.generate_feed(episodes)
        assert len(feed) > len(long_script)
        assert RSSGenerator.validate_feed(feed)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
