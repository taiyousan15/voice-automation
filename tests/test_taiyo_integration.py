"""Test Taiyo Style Script Generator - Phase 3"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from generators.taiyo_script_generator import TaiyoScriptGenerator


async def test_taiyo_pipeline():
    """Test complete Taiyo pipeline"""
    generator = TaiyoScriptGenerator()
    
    print("=== Testing Taiyo Style Script Generation (Phase 3) ===\n")
    
    # Sample data
    theme = "Claude Code"
    keywords = [
        "Claude Code とは",
        "Claude Code 使い方",
        "Claude Code おすすめ",
        "Claude Code 比較",
        "Claude Code API"
    ]
    
    articles = [
        {
            "title": "Claude Code発表、開発者向けAIツール",
            "description": "Anthropic社が新しい開発者向けツールClaude Codeを発表。VS Code統合により、コーディング効率が向上。"
        },
        {
            "title": "Claude Codeの実力は？ GPT-4 Turboと比較",
            "description": "最新のAIコーディングアシスタントを徹底比較。Claude Codeの強みと弱みを解説。"
        }
    ]
    
    # Test complete pipeline
    print(f"Theme: {theme}")
    print(f"Keywords: {len(keywords)}")
    print(f"Articles: {len(articles)}\n")
    
    result = await generator.generate_complete_episode(
        theme=theme,
        keywords=keywords,
        articles=articles
    )
    
    # Display results
    print("\n=== Generation Results ===")
    print(f"Status: {result.get('status')}")
    print(f"Title: {result.get('title')}")
    print(f"Script length: {result.get('length')} chars")
    print(f"Taiyo score: {result.get('taiyo_score')} points")
    print(f"Quality passed: {result.get('passed_quality')}")
    print(f"Attempts: {result.get('attempts')}")
    
    # Show script preview
    script = result.get('script', '')
    if script:
        print("\n=== Script Preview (first 300 chars) ===")
        print(script[:300] + "..." if len(script) > 300 else script)
    
    # Check requirements
    print("\n=== Requirements Validation ===")
    
    # REQ-004: Title length <= 60 chars
    title_len = len(result.get('title', ''))
    print(f"REQ-004 (Title <= 60 chars): {title_len} chars - {'PASS' if title_len <= 60 else 'FAIL'}")
    
    # REQ-005: Script 1,200-2,000 chars
    script_len = result.get('length', 0)
    in_range = 1200 <= script_len <= 2000
    print(f"REQ-005 (1,200-2,000 chars): {script_len} chars - {'PASS' if in_range else 'FAIL'}")
    
    # REQ-009: Taiyo score >= 70
    score = result.get('taiyo_score', 0)
    print(f"REQ-009 (Taiyo score >= 70): {score} points - {'PASS' if score >= 70 else 'FAIL'}")
    
    print("\n" + "="*60)
    print("NOTE: This is fallback mode. Install taiyo skills for full functionality.")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_taiyo_pipeline())
