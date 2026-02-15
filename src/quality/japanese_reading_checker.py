"""Japanese Reading Checker for TTS Quality

REQ-006: 日本語読み方チェック（1回目）- 難読漢字検出
REQ-008: 日本語読み方チェック（2回目）- 残存リスク確認
"""
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add scripts to path for text_preprocessor import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from text_preprocessor import JapaneseTextPreprocessor
from loguru import logger


class JapaneseReadingChecker:
    """
    Check Japanese text for potential TTS reading errors
    
    Detects:
    - 難読漢字 (difficult kanji)
    - 数字読みリスク (number reading risks)
    - 英単語読みリスク (English word reading risks)
    """
    
    # 難読漢字リスト（TTS誤読リスクが高いもの）
    DIFFICULT_KANJI = {
        '脆弱': 'ぜいじゃく',
        '汎用': 'はんよう',
        '依存': 'いぞん',
        '顕著': 'けんちょ',
        '踏襲': 'とうしゅう',
        '遵守': 'じゅんしゅ',
        '醸成': 'じょうせい',
        '相殺': 'そうさい',
        '堅牢': 'けんろう',
        '冗長': 'じょうちょう',
        '貼付': 'ちょうふ',
        '割愛': 'かつあい',
        '漏洩': 'ろうえい',
        '施策': 'しさく',
        '措置': 'そち',
        '疾病': 'しっぺい',
        '直轄': 'ちょっかつ',
        '早急': 'さっきゅう',
        '凡例': 'はんれい',
        '逐次': 'ちくじ',
    }
    
    def __init__(self):
        """Initialize reading checker"""
        self.preprocessor = JapaneseTextPreprocessor()
    
    def check(self, text: str) -> Dict[str, Any]:
        """
        Check text for reading risks
        
        Args:
            text: Japanese text to check
        
        Returns:
            Check result with detected risks
        """
        risks = []
        
        # 1. Check difficult kanji
        kanji_risks = self._check_difficult_kanji(text)
        risks.extend(kanji_risks)
        
        # 2. Check number reading
        number_risks = self._check_number_reading(text)
        risks.extend(number_risks)
        
        # 3. Check English words
        english_risks = self._check_english_words(text)
        risks.extend(english_risks)
        
        return {
            'total_risks': len(risks),
            'risks': risks,
            'passed': len(risks) == 0,
            'kanji_count': len(kanji_risks),
            'number_count': len(number_risks),
            'english_count': len(english_risks)
        }
    
    def _check_difficult_kanji(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect difficult kanji that may be misread by TTS
        
        REQ-006: AT-012
        """
        risks = []
        
        for kanji, reading in self.DIFFICULT_KANJI.items():
            if kanji in text:
                # Find all positions
                positions = [m.start() for m in re.finditer(re.escape(kanji), text)]
                
                for pos in positions:
                    risks.append({
                        'type': 'difficult_kanji',
                        'text': kanji,
                        'position': pos,
                        'correct_reading': reading,
                        'risk_level': 'high',
                        'suggestion': f'{kanji} → {reading}'
                    })
        
        return risks
    
    def _check_number_reading(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect numbers that may be misread
        
        REQ-006: AT-013
        Examples:
        - 1000万 (いっせんまん)
        - 3000万 (さんぜんまん)
        - 8000億 (はっせんおく)
        """
        risks = []
        
        # Pattern: 数字 + 単位
        patterns = [
            (r'(\d+)(万|億|兆)', 'medium'),
            (r'\b(\d{4,})\b', 'low')  # Standalone large numbers
        ]
        
        for pattern, risk_level in patterns:
            for match in re.finditer(pattern, text):
                original = match.group(0)
                
                # Get correct reading using preprocessor
                correct = self.preprocessor.preprocess(original)
                
                # Only flag if conversion changed the text
                if correct != original:
                    risks.append({
                        'type': 'number_reading',
                        'text': original,
                        'position': match.start(),
                        'correct_reading': correct,
                        'risk_level': risk_level,
                        'suggestion': f'{original} → {correct}'
                    })
        
        return risks
    
    def _check_english_words(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect English words that should have katakana pronunciation
        
        REQ-006: AT-014
        """
        risks = []
        
        # Common English/acronym patterns
        english_pattern = r'\b[A-Z]{2,}\b'  # API, AWS, VSL, etc.
        
        # Known katakana mappings
        katakana_map = {
            'API': 'エーピーアイ',
            'AWS': 'エーダブリューエス',
            'AI': 'エーアイ',
            'VSL': 'ブイエスエル',
            'TTS': 'ティーティーエス',
            'RSS': 'アールエスエス',
            'URL': 'ユーアールエル',
            'HTML': 'エイチティーエムエル',
            'CSS': 'シーエスエス',
            'JSON': 'ジェイソン',
            'XML': 'エックスエムエル',
            'HTTP': 'エイチティーティーピー',
            'HTTPS': 'エイチティーティーピーエス',
            'SDK': 'エスディーケー',
            'CLI': 'シーエルアイ',
            'UI': 'ユーアイ',
            'UX': 'ユーエックス',
        }
        
        for match in re.finditer(english_pattern, text):
            word = match.group(0)
            
            # Get katakana if known
            katakana = katakana_map.get(word, f'({word})')  # Fallback to parentheses
            
            risks.append({
                'type': 'english_word',
                'text': word,
                'position': match.start(),
                'correct_reading': katakana,
                'risk_level': 'medium',
                'suggestion': f'{word}（{katakana}）'
            })
        
        return risks
    
    def auto_correct(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Automatically correct detected reading risks
        
        REQ-007: 自動修正
        
        Returns:
            (corrected_text, correction_report)
        """
        corrections = {
            'difficult_kanji': 0,
            'number_reading': 0,
            'english_word': 0,
            'total': 0
        }
        
        # 1. Replace difficult kanji with hiragana
        for kanji, reading in self.DIFFICULT_KANJI.items():
            if kanji in text:
                text = text.replace(kanji, reading)
                corrections['difficult_kanji'] += 1
        
        # 2. Convert numbers to hiragana
        original_text = text
        text = self.preprocessor.preprocess(text)
        if text != original_text:
            # Count number replacements
            corrections['number_reading'] = len(re.findall(r'\d+[万億兆]', original_text))
        
        # 3. Add katakana to English words
        katakana_map = {
            'API': 'エーピーアイ',
            'AWS': 'エーダブリューエス',
            'AI': 'エーアイ',
            'VSL': 'ブイエスエル',
            'TTS': 'ティーティーエス',
            'RSS': 'アールエスエス',
        }
        
        for word, katakana in katakana_map.items():
            pattern = r'\b' + word + r'\b'
            if re.search(pattern, text):
                text = re.sub(pattern, f'{word}（{katakana}）', text)
                corrections['english_word'] += 1
        
        corrections['total'] = sum([
            corrections['difficult_kanji'],
            corrections['number_reading'],
            corrections['english_word']
        ])
        
        return text, corrections


if __name__ == "__main__":
    # Test cases
    checker = JapaneseReadingChecker()
    
    test_text = """
    本システムは脆弱性対策として1000万件のデータを処理し、
    API経由で3000万ユーザーに配信します。
    """
    
    print("=== Japanese Reading Checker Test ===\n")
    print(f"Original text:\n{test_text}\n")
    
    # Check risks
    result = checker.check(test_text)
    print(f"Total risks detected: {result['total_risks']}")
    print(f"  - Difficult kanji: {result['kanji_count']}")
    print(f"  - Number reading: {result['number_count']}")
    print(f"  - English words: {result['english_count']}")
    print(f"\nPassed: {result['passed']}\n")
    
    # Show risks
    print("Detected risks:")
    for risk in result['risks']:
        print(f"  [{risk['type']}] {risk['suggestion']}")
    
    # Auto-correct
    corrected, corrections = checker.auto_correct(test_text)
    print(f"\n=== Auto-corrected ({corrections['total']} changes) ===")
    print(corrected)
    
    # Re-check
    result2 = checker.check(corrected)
    print(f"\nRe-check after correction:")
    print(f"  Remaining risks: {result2['total_risks']}")
    print(f"  Passed: {result2['passed']}")
