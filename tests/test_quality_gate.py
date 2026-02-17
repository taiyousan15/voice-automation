"""Tests for quality gate and TTS blocking logic"""
import pytest
from src.quality.quality_inspector import QualityInspector


class TestQualityInspectorThresholds:
    """Test CRITICAL thresholds added for TTS stabilization"""

    @pytest.fixture
    def inspector(self):
        return QualityInspector()

    def test_normal_script_passes(self, inspector):
        """1,200-2,000 chars should pass all checks"""
        script = "あ" * 1500
        result = inspector.inspect(script)
        assert result['passed'] is True
        assert result['char_count']['passed'] is True
        assert len(result['issues']) == 0

    def test_short_script_critical(self, inspector):
        """< 1,200 chars should be critical (char_count_low)"""
        script = "あ" * 800
        result = inspector.inspect(script)
        assert result['passed'] is False
        issues = [i for i in result['issues'] if i['type'] == 'char_count_low']
        assert len(issues) == 1
        assert issues[0]['severity'] == 'critical'

    def test_long_script_warning(self, inspector):
        """2,001-5,000 chars should be warning (not critical)"""
        script = "あ" * 3000
        result = inspector.inspect(script)
        assert result['passed'] is False
        issues = [i for i in result['issues'] if i['type'] == 'char_count_high']
        assert len(issues) == 1
        assert issues[0]['severity'] == 'warning'

    def test_critically_long_script(self, inspector):
        """> 5,000 chars should be critical (char_count_high)"""
        script = "あ" * 6000
        result = inspector.inspect(script)
        assert result['passed'] is False
        issues = [i for i in result['issues'] if i['type'] == 'char_count_high']
        assert len(issues) == 1
        assert issues[0]['severity'] == 'critical'

    def test_critical_max_chars_boundary(self, inspector):
        """Exactly 5,000 chars should be warning, 5,001 should be critical"""
        # At boundary (5000) - warning
        script_at = "あ" * 5000
        result_at = inspector.inspect(script_at)
        high_issues = [i for i in result_at['issues'] if i['type'] == 'char_count_high']
        assert len(high_issues) == 1
        assert high_issues[0]['severity'] == 'warning'

        # Over boundary (5001) - critical
        script_over = "あ" * 5001
        result_over = inspector.inspect(script_over)
        high_issues_over = [i for i in result_over['issues'] if i['type'] == 'char_count_high']
        assert len(high_issues_over) == 1
        assert high_issues_over[0]['severity'] == 'critical'

    def test_duration_warning(self, inspector):
        """Duration > 7min but <= 16min should be warning"""
        # 2,500 chars / 300 cpm = 8.3 min -> warning
        script = "あ" * 2500
        result = inspector.inspect(script)
        dur_issues = [i for i in result['issues'] if i['type'] == 'duration_long']
        assert len(dur_issues) == 1
        assert dur_issues[0]['severity'] == 'warning'

    def test_duration_critical(self, inspector):
        """Duration > 16min should be critical"""
        # 5,000 chars / 300 cpm = 16.67 min -> critical
        script = "あ" * 5000
        result = inspector.inspect(script)
        dur_issues = [i for i in result['issues'] if i['type'] == 'duration_long']
        assert len(dur_issues) == 1
        assert dur_issues[0]['severity'] == 'critical'

    def test_taiyo_score_pass(self, inspector):
        """Taiyo score >= 70 should pass"""
        script = "あ" * 1500
        result = inspector.inspect(script, taiyo_score=75)
        assert result['taiyo_score']['passed'] is True

    def test_taiyo_score_fail(self, inspector):
        """Taiyo score < 70 should be critical"""
        script = "あ" * 1500
        result = inspector.inspect(script, taiyo_score=65)
        assert result['taiyo_score']['passed'] is False
        issues = [i for i in result['issues'] if i['type'] == 'taiyo_score_low']
        assert len(issues) == 1
        assert issues[0]['severity'] == 'critical'


class TestTTSBlockingLogic:
    """Test that TTS blocking only triggers for TTS-dangerous issues"""

    def _get_tts_blocking_issues(self, quality_result):
        """Replicate orchestrator's TTS blocking logic"""
        tts_blocking_types = {'char_count_high', 'duration_long'}
        critical_issues = [i for i in quality_result['issues'] if i['severity'] == 'critical']
        return [i for i in critical_issues if i['type'] in tts_blocking_types]

    def test_short_script_does_not_block_tts(self):
        """char_count_low (critical) should NOT block TTS"""
        inspector = QualityInspector()
        script = "あ" * 800  # Too short
        result = inspector.inspect(script)

        tts_issues = self._get_tts_blocking_issues(result)
        assert len(tts_issues) == 0, "Short scripts should not block TTS"

    def test_warning_long_script_does_not_block_tts(self):
        """char_count_high (warning) should NOT block TTS"""
        inspector = QualityInspector()
        script = "あ" * 3000  # Long but not critical
        result = inspector.inspect(script)

        tts_issues = self._get_tts_blocking_issues(result)
        assert len(tts_issues) == 0, "Warning-level long scripts should not block TTS"

    def test_critical_long_script_blocks_tts(self):
        """char_count_high (critical, > 5000) SHOULD block TTS"""
        inspector = QualityInspector()
        script = "あ" * 6000  # Critically long
        result = inspector.inspect(script)

        tts_issues = self._get_tts_blocking_issues(result)
        assert len(tts_issues) >= 1, "Critically long scripts should block TTS"
        assert any(i['type'] == 'char_count_high' for i in tts_issues)

    def test_critical_duration_blocks_tts(self):
        """duration_long (critical, > 16min) SHOULD block TTS"""
        inspector = QualityInspector()
        script = "あ" * 5500  # > 16min duration
        result = inspector.inspect(script)

        tts_issues = self._get_tts_blocking_issues(result)
        assert any(i['type'] == 'duration_long' for i in tts_issues)

    def test_low_taiyo_score_does_not_block_tts(self):
        """taiyo_score_low (critical) should NOT block TTS"""
        inspector = QualityInspector()
        script = "あ" * 1500  # Good length
        result = inspector.inspect(script, taiyo_score=50)

        tts_issues = self._get_tts_blocking_issues(result)
        assert len(tts_issues) == 0, "Low taiyo score should not block TTS"

    def test_normal_script_no_tts_block(self):
        """Normal script should have no TTS blocking issues"""
        inspector = QualityInspector()
        script = "あ" * 1500
        result = inspector.inspect(script, taiyo_score=80)

        tts_issues = self._get_tts_blocking_issues(result)
        assert len(tts_issues) == 0


class TestQualityReport:
    """Test quality report generation"""

    def test_report_contains_all_sections(self):
        inspector = QualityInspector()
        script = "あ" * 1500
        result = inspector.inspect(script, taiyo_score=75)
        report = inspector.generate_report(result)

        assert "Quality Inspection Report" in report
        assert "PASSED" in report
        assert "Character count" in report
        assert "Duration" in report
        assert "Taiyo score" in report

    def test_report_shows_issues(self):
        inspector = QualityInspector()
        script = "あ" * 800  # Too short
        result = inspector.inspect(script)
        report = inspector.generate_report(result)

        assert "FAILED" in report
        assert "Issues:" in report
        assert "too short" in report
