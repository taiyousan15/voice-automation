"""Test KeywordResearcher with 50+ keyword generation"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from collectors.keyword_researcher import KeywordResearcher


async def test_keyword_expansion():
    """Test REQ-003: 50+ keyword generation"""
    researcher = KeywordResearcher()
    
    # Test with single theme
    seed_keywords = ["AI Agent"]
    
    print("=== Testing Keyword Expansion (REQ-003) ===")
    print(f"Seed keyword: {seed_keywords[0]}\n")
    
    # Expand keywords
    expanded = await researcher.expand_keywords(seed_keywords)
    
    # Check results
    for seed, data in expanded.items():
        keywords = data.get("keywords", [])
        print(f"✓ Seed: {seed}")
        print(f"✓ Generated keywords: {len(keywords)}")
        print(f"✓ REQ-003 (50+ keywords): {'PASS' if len(keywords) >= 50 else 'FAIL'}")
        
        # Show keyword types breakdown
        types = {}
        for kw in keywords:
            kw_type = kw.get("type", "unknown")
            types[kw_type] = types.get(kw_type, 0) + 1
        
        print("\nKeyword breakdown by type:")
        for kw_type, count in types.items():
            print(f"  - {kw_type}: {count}")
        
        # Show high buying intent keywords
        high_intent = [kw for kw in keywords if kw.get("buying_intent", 0) >= 0.7]
        print(f"\nHigh buying intent keywords: {len(high_intent)}")
        print("Sample high-intent keywords:")
        for kw in high_intent[:5]:
            print(f"  - {kw['keyword']} (intent: {kw['buying_intent']})")


async def test_integrated_research():
    """Test integrated research pipeline"""
    researcher = KeywordResearcher()
    
    print("\n\n=== Testing Integrated Research Pipeline ===")
    
    themes = ["Claude Code"]
    
    results = await researcher.integrated_research(
        themes=themes,
        expand_keywords=True,
        world_search=True
    )
    
    print(f"✓ Themes: {results.get('themes')}")
    print(f"✓ Suggested queries: {len(results.get('suggested_queries', []))}")
    print(f"✓ World research keywords: {len(results.get('world_research', {}))}")
    
    # Show suggested queries
    print("\nSuggested queries (top 10):")
    for i, query in enumerate(results.get('suggested_queries', [])[:10], 1):
        print(f"  {i}. {query}")


if __name__ == "__main__":
    asyncio.run(test_keyword_expansion())
    asyncio.run(test_integrated_research())
