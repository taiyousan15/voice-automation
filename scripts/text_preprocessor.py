"""Japanese Text Preprocessor for TTS - v2

数字→ひらがな変換により、Fish Audio TTSの誤読を防ぐ
"""
import re


class JapaneseTextPreprocessor:
    """Japanese text preprocessing for TTS accuracy"""
    
    def __init__(self):
        pass
    
    def preprocess(self, text: str) -> str:
        """Preprocess Japanese text for TTS"""
        text = self._convert_numbers(text)
        return text
    
    def _convert_numbers(self, text: str) -> str:
        """Convert numbers to Japanese hiragana readings"""
        # Pattern: 数字 + 単位（万/億/兆）
        pattern = r'(\d+)(万|億|兆)'
        
        def replace_number(match):
            number_str = match.group(1)
            unit = match.group(2)
            num = int(number_str)
            
            # Convert to reading
            reading = self._num_to_ja(num)
            
            # Add unit
            unit_map = {'万': 'まん', '億': 'おく', '兆': 'ちょう'}
            
            # Special: 1兆 → いっちょう
            if num == 1 and unit == '兆':
                return 'いっちょう'
            
            return reading + unit_map[unit]
        
        text = re.sub(pattern, replace_number, text)
        
        # Standalone large numbers (1000+)
        pattern_standalone = r'\b(\d{4,})\b'
        text = re.sub(pattern_standalone, lambda m: self._num_to_ja(int(m.group(1))), text)
        
        return text
    
    def _num_to_ja(self, num: int) -> str:
        """Convert integer to Japanese reading"""
        if num == 0:
            return 'ゼロ'
        
        parts = []
        
        # 兆
        if num >= 1_000_000_000_000:
            cho = num // 1_000_000_000_000
            if cho == 1:
                parts.append('いっ')  # 1兆 → いっちょう
            else:
                parts.append(self._1to9999(cho))
            parts.append('ちょう')
            num %= 1_000_000_000_000
        
        # 億
        if num >= 100_000_000:
            oku = num // 100_000_000
            parts.append(self._1to9999(oku) + 'おく')
            num %= 100_000_000
        
        # 万
        if num >= 10_000:
            man = num // 10_000
            parts.append(self._1to9999(man) + 'まん')
            num %= 10_000
        
        # 1-9999
        if num > 0:
            parts.append(self._1to9999(num))
        
        return ''.join(parts)
    
    def _1to9999(self, num: int) -> str:
        """Convert 1-9999 to Japanese reading with 促音/撥音 rules"""
        if num == 0:
            return ''
        
        parts = []
        digits = ['', 'いち', 'に', 'さん', 'よん', 'ご', 'ろく', 'なな', 'はち', 'きゅう']
        
        # 千の位
        sen = num // 1000
        if sen > 0:
            if sen == 1:
                parts.append('いっせん')
            elif sen == 3:
                parts.append('さんぜん')
            elif sen == 8:
                parts.append('はっせん')
            else:
                parts.append(digits[sen] + 'せん')
            num %= 1000
        
        # 百の位
        hyaku = num // 100
        if hyaku > 0:
            if hyaku == 1:
                parts.append('ひゃく')
            elif hyaku == 3:
                parts.append('さんびゃく')
            elif hyaku == 6:
                parts.append('ろっぴゃく')
            elif hyaku == 8:
                parts.append('はっぴゃく')
            else:
                parts.append(digits[hyaku] + 'ひゃく')
            num %= 100
        
        # 十の位
        ju = num // 10
        if ju > 0:
            if ju == 1:
                parts.append('じゅう')
            else:
                parts.append(digits[ju] + 'じゅう')
            num %= 10
        
        # 一の位
        if num > 0:
            parts.append(digits[num])
        
        return ''.join(parts)


def preprocess_for_tts(text: str) -> str:
    """Convenience function"""
    preprocessor = JapaneseTextPreprocessor()
    return preprocessor.preprocess(text)


if __name__ == "__main__":
    preprocessor = JapaneseTextPreprocessor()
    
    tests = [
        ("1000万", "いっせんまん"),
        ("3000万", "さんぜんまん"),
        ("8000億", "はっせんおく"),
        ("1億", "いちおく"),
        ("1兆", "いっちょう"),
        ("300万", "さんびゃくまん"),
        ("600万", "ろっぴゃくまん"),
        ("800万", "はっぴゃくまん"),
    ]
    
    print("=== Number Reading Tests ===\n")
    passed = 0
    for inp, exp in tests:
        res = preprocessor.preprocess(inp)
        ok = res == exp
        if ok:
            passed += 1
        print(f"{'✓' if ok else '✗'} {inp:12s} → {res:20s} (expected: {exp})")
    
    print(f"\n{passed}/{len(tests)} tests passed")
