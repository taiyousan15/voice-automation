"""Quality Inspector for Script Validation

REQ-009: 品質検品
- 文字数チェック（1,200-2,000字）
- 読み上げ時間チェック（4-7分）
- 太陽スコアチェック（70点以上）
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from loguru import logger


class QualityInspector:
    """
    Script quality inspector
    
    Validates:
    - Character count (1,200-2,000)
    - Estimated reading time (4-7 minutes)
    - Taiyo score (>= 70 points)
    """
    
    # Constants
    MIN_CHARS = 1200
    MAX_CHARS = 2000
    CRITICAL_MAX_CHARS = 5000  # TTS ブロック閾値
    MIN_DURATION_SEC = 4 * 60  # 4 minutes
    MAX_DURATION_SEC = 7 * 60  # 7 minutes
    CRITICAL_MAX_DURATION_SEC = 16 * 60  # 16 minutes - TTS ブロック閾値
    MIN_TAIYO_SCORE = 70
    
    # Reading speed: ~300 chars/min for Japanese TTS
    CHARS_PER_MINUTE = 300
    
    def __init__(self):
        """Initialize quality inspector"""
        pass
    
    def inspect(
        self,
        script: str,
        taiyo_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive quality inspection
        
        Args:
            script: Script text to inspect
            taiyo_score: Optional Taiyo score (if available)
        
        Returns:
            Inspection result
        """
        result = {
            'passed': True,
            'char_count': {
                'value': 0,
                'passed': False,
                'min': self.MIN_CHARS,
                'max': self.MAX_CHARS
            },
            'duration': {
                'value_sec': 0,
                'value_str': '',
                'passed': False,
                'min_sec': self.MIN_DURATION_SEC,
                'max_sec': self.MAX_DURATION_SEC
            },
            'taiyo_score': {
                'value': taiyo_score,
                'passed': False if taiyo_score is not None else None,
                'min': self.MIN_TAIYO_SCORE
            },
            'issues': []
        }
        
        # 1. Character count check (REQ-009: AT-020)
        char_count = len(script)
        result['char_count']['value'] = char_count
        
        if self.MIN_CHARS <= char_count <= self.MAX_CHARS:
            result['char_count']['passed'] = True
        else:
            result['char_count']['passed'] = False
            result['passed'] = False
            
            if char_count < self.MIN_CHARS:
                result['issues'].append({
                    'type': 'char_count_low',
                    'message': f'Script too short: {char_count} chars (min: {self.MIN_CHARS})',
                    'severity': 'critical'
                })
            elif char_count > self.CRITICAL_MAX_CHARS:
                result['issues'].append({
                    'type': 'char_count_high',
                    'message': f'Script critically long: {char_count} chars (critical: {self.CRITICAL_MAX_CHARS})',
                    'severity': 'critical'
                })
            else:
                result['issues'].append({
                    'type': 'char_count_high',
                    'message': f'Script too long: {char_count} chars (max: {self.MAX_CHARS})',
                    'severity': 'warning'
                })
        
        # 2. Duration check (REQ-009: AT-021)
        duration_sec = (char_count / self.CHARS_PER_MINUTE) * 60
        duration_min = duration_sec / 60
        
        result['duration']['value_sec'] = int(duration_sec)
        result['duration']['value_str'] = f"{int(duration_min)}分{int(duration_sec % 60)}秒"
        
        if self.MIN_DURATION_SEC <= duration_sec <= self.MAX_DURATION_SEC:
            result['duration']['passed'] = True
        else:
            result['duration']['passed'] = False
            result['passed'] = False
            
            if duration_sec < self.MIN_DURATION_SEC:
                result['issues'].append({
                    'type': 'duration_short',
                    'message': f'Estimated duration too short: {result["duration"]["value_str"]} (min: 4分)',
                    'severity': 'warning'
                })
            elif duration_sec > self.CRITICAL_MAX_DURATION_SEC:
                result['issues'].append({
                    'type': 'duration_long',
                    'message': f'Estimated duration critically long: {result["duration"]["value_str"]} (critical: 16分)',
                    'severity': 'critical'
                })
            else:
                result['issues'].append({
                    'type': 'duration_long',
                    'message': f'Estimated duration too long: {result["duration"]["value_str"]} (max: 7分)',
                    'severity': 'warning'
                })
        
        # 3. Taiyo score check (REQ-009: AT-022)
        if taiyo_score is not None:
            if taiyo_score >= self.MIN_TAIYO_SCORE:
                result['taiyo_score']['passed'] = True
            else:
                result['taiyo_score']['passed'] = False
                result['passed'] = False
                
                result['issues'].append({
                    'type': 'taiyo_score_low',
                    'message': f'Taiyo score too low: {taiyo_score} points (min: {self.MIN_TAIYO_SCORE})',
                    'severity': 'critical'
                })
        
        return result
    
    def generate_report(self, result: Dict[str, Any]) -> str:
        """
        Generate human-readable inspection report
        
        Args:
            result: Inspection result from inspect()
        
        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=== Quality Inspection Report ===")
        lines.append("")
        
        # Overall status
        status = "✓ PASSED" if result['passed'] else "✗ FAILED"
        lines.append(f"Overall: {status}")
        lines.append("")
        
        # Character count
        char = result['char_count']
        char_status = "✓" if char['passed'] else "✗"
        lines.append(f"{char_status} Character count: {char['value']} ({char['min']}-{char['max']})")
        
        # Duration
        dur = result['duration']
        dur_status = "✓" if dur['passed'] else "✗"
        lines.append(f"{dur_status} Duration: {dur['value_str']} (4-7分)")
        
        # Taiyo score
        taiyo = result['taiyo_score']
        if taiyo['value'] is not None:
            taiyo_status = "✓" if taiyo['passed'] else "✗"
            lines.append(f"{taiyo_status} Taiyo score: {taiyo['value']} points (>= {taiyo['min']})")
        else:
            lines.append("- Taiyo score: N/A")
        
        # Issues
        if result['issues']:
            lines.append("")
            lines.append("Issues:")
            for issue in result['issues']:
                severity_icon = "!" if issue['severity'] == 'critical' else "⚠"
                lines.append(f"  {severity_icon} {issue['message']}")
        
        lines.append("")
        lines.append("="*40)
        
        return "\n".join(lines)


if __name__ == "__main__":
    # Test cases
    inspector = QualityInspector()
    
    print("=== Quality Inspector Test ===\n")
    
    # Test 1: Perfect script
    test_script_good = "あ" * 1500  # 1500 chars
    result1 = inspector.inspect(test_script_good, taiyo_score=75)
    print("Test 1: Ideal script (1500 chars, score 75)")
    print(inspector.generate_report(result1))
    
    # Test 2: Too short
    test_script_short = "あ" * 800  # 800 chars
    result2 = inspector.inspect(test_script_short, taiyo_score=80)
    print("\nTest 2: Too short (800 chars)")
    print(inspector.generate_report(result2))
    
    # Test 3: Low Taiyo score
    test_script_low = "あ" * 1400
    result3 = inspector.inspect(test_script_low, taiyo_score=65)
    print("\nTest 3: Low Taiyo score (65 points)")
    print(inspector.generate_report(result3))
