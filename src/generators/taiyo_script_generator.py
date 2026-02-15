"""Taiyo Style Script Generator - Phase 3 Integration

REQ-004: taiyo-style-headline for title generation
REQ-005: taiyo-style-vsl + taiyo-rewriter for script generation
REQ-009: taiyo-analyzer for quality scoring (70+ points)
"""
import asyncio
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger


class TaiyoScriptGenerator:
    """
    Taiyo Style Marketing Script Generator
    
    Pipeline:
    1. taiyo-style-headline: Generate attractive title (60 chars max)
    2. taiyo-style-vsl: Generate VSL structure script
    3. taiyo-rewriter: Refine script to 1,200-2,000 chars
    4. taiyo-analyzer: Validate quality score (70+ points)
    """
    
    def __init__(self):
        """Initialize Taiyo script generator"""
        self.project_root = Path(__file__).parent.parent.parent
        self.skills_dir = Path.home() / "taisun_agent" / ".claude" / "skills"
        
        # Check if skills exist
        self.skills_available = self._check_skills_availability()
        
        if self.skills_available:
            logger.info("✓ Taiyo skills available")
        else:
            logger.warning("⚠ Taiyo skills not found - using fallback mode")
    
    def _check_skills_availability(self) -> bool:
        """Check if taiyo skills are available"""
        required_skills = [
            "taiyo-style-headline",
            "taiyo-style-vsl",
            "taiyo-rewriter",
            "taiyo-analyzer"
        ]
        
        for skill in required_skills:
            skill_path = self.skills_dir / skill
            if not skill_path.exists():
                logger.debug(f"Skill not found: {skill}")
                return False
        
        return True
    
    async def generate_title(
        self,
        keywords: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate attractive title using taiyo-style-headline
        
        REQ-004: Title generation with click-through rate prediction
        
        Args:
            keywords: Expanded keywords from research
            context: Research context and collected information
        
        Returns:
            Title with metadata
        """
        try:
            if not self.skills_available:
                # Fallback: Generate simple title
                return self._generate_fallback_title(keywords, context)
            
            # Prepare input for taiyo-style-headline
            headline_input = {
                "keywords": keywords[:10],  # Top 10 keywords
                "context": context.get("summary", ""),
                "target_length": 60
            }
            
            # Execute skill via subprocess (simulation for now)
            logger.info("Generating title with taiyo-style-headline...")
            
            # TODO: Implement actual skill execution
            # For now, use fallback
            return self._generate_fallback_title(keywords, context)
            
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return self._generate_fallback_title(keywords, context)
    
    def _generate_fallback_title(
        self,
        keywords: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback title without skill execution"""
        # Simple title generation
        main_keyword = keywords[0] if keywords else "最新ニュース"
        
        title_templates = [
            f"{main_keyword}の最新動向と活用法",
            f"今話題の{main_keyword}を徹底解説",
            f"{main_keyword}で変わる未来",
            f"知っておきたい{main_keyword}の基礎",
            f"{main_keyword}の賢い使い方"
        ]
        
        # Select first template (can be randomized)
        title = title_templates[0][:60]  # Max 60 chars
        
        return {
            "title": title,
            "length": len(title),
            "click_rate_score": 65,  # Simulated score
            "status": "fallback"
        }
    
    async def generate_script(
        self,
        title: str,
        keywords: List[str],
        articles: List[Dict[str, Any]],
        target_length: int = 1500
    ) -> Dict[str, Any]:
        """
        Generate marketing script using taiyo-style-vsl + taiyo-rewriter
        
        REQ-005: 1,200-2,000 chars VSL script with marketing elements
        
        Args:
            title: Generated title
            keywords: Expanded keywords
            articles: Collected article data
            target_length: Target character count (default: 1500)
        
        Returns:
            Script with metadata
        """
        try:
            if not self.skills_available:
                return self._generate_fallback_script(
                    title, keywords, articles, target_length
                )
            
            logger.info("Generating VSL script with taiyo-style-vsl...")
            
            # Step 1: VSL structure generation
            vsl_input = {
                "title": title,
                "keywords": keywords[:20],
                "articles": articles[:5],  # Top 5 articles
                "structure": "15_chapter"  # VSL 15-chapter structure
            }
            
            # TODO: Execute taiyo-style-vsl skill
            
            # Step 2: Rewrite and refine
            logger.info("Refining script with taiyo-rewriter...")
            
            # TODO: Execute taiyo-rewriter skill
            
            # For now, use fallback
            return self._generate_fallback_script(
                title, keywords, articles, target_length
            )
            
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return self._generate_fallback_script(
                title, keywords, articles, target_length
            )
    
    def _generate_fallback_script(
        self,
        title: str,
        keywords: List[str],
        articles: List[Dict[str, Any]],
        target_length: int
    ) -> Dict[str, Any]:
        """Generate fallback script without skill execution"""
        # Build simple script from articles
        script_parts = []
        
        # Opening
        script_parts.append(f"こんにちは。今日は「{title}」についてお話しします。")
        
        # Main content from articles
        for article in articles[:3]:
            snippet = article.get("description", "")[:200]
            if snippet:
                script_parts.append(snippet)
        
        # Closing
        script_parts.append("以上、本日のニュースをお届けしました。")
        
        script = "\n\n".join(script_parts)
        
        # Adjust length
        if len(script) > target_length:
            script = script[:target_length - 10] + "...続きます。"
        elif len(script) < 1200:
            # Pad if too short
            script += "\n\nさらに詳しい情報は、各ニュースソースをご確認ください。"
        
        return {
            "script": script,
            "length": len(script),
            "status": "fallback",
            "taiyo_score": 50  # Low score for fallback
        }
    
    async def validate_quality(
        self,
        script: str
    ) -> Dict[str, Any]:
        """
        Validate script quality using taiyo-analyzer
        
        REQ-009: Taiyo score >= 70 points
        
        Args:
            script: Generated script text
        
        Returns:
            Quality validation result
        """
        try:
            if not self.skills_available:
                return {
                    "score": 50,
                    "passed": False,
                    "status": "fallback",
                    "recommendation": "Install taiyo-analyzer for accurate scoring"
                }
            
            logger.info("Validating script quality with taiyo-analyzer...")
            
            # TODO: Execute taiyo-analyzer skill
            
            # For now, return simulated result
            return {
                "score": 50,
                "passed": False,
                "status": "simulation"
            }
            
        except Exception as e:
            logger.error(f"Error validating quality: {e}")
            return {
                "score": 0,
                "passed": False,
                "error": str(e)
            }
    
    async def generate_complete_episode(
        self,
        theme: str,
        keywords: List[str],
        articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Full pipeline: Title → Script → Quality validation
        
        Pipeline:
        1. Generate title (taiyo-style-headline)
        2. Generate script (taiyo-style-vsl + taiyo-rewriter)
        3. Validate quality (taiyo-analyzer)
        4. Retry if quality < 70 (max 2 times)
        
        Args:
            theme: Main theme keyword
            keywords: Expanded keywords
            articles: Collected articles
        
        Returns:
            Complete episode data
        """
        try:
            logger.info(f"=== Generating Taiyo-style episode for: {theme} ===")
            
            # Step 1: Generate title
            title_result = await self.generate_title(
                keywords=keywords,
                context={"theme": theme, "articles": articles}
            )
            title = title_result["title"]
            logger.info(f"✓ Title: {title}")
            
            # Step 2: Generate script (with retry)
            max_retries = 2
            for attempt in range(max_retries + 1):
                script_result = await self.generate_script(
                    title=title,
                    keywords=keywords,
                    articles=articles,
                    target_length=1500
                )
                
                script = script_result["script"]
                logger.info(f"✓ Script generated: {len(script)} chars")
                
                # Step 3: Validate quality
                quality_result = await self.validate_quality(script)
                taiyo_score = quality_result.get("score", 0)
                
                logger.info(f"✓ Taiyo score: {taiyo_score} points")
                
                # Check if quality is acceptable
                if taiyo_score >= 70 or attempt == max_retries:
                    break
                
                logger.warning(f"⚠ Score too low, retrying... (attempt {attempt + 1}/{max_retries})")
            
            return {
                "theme": theme,
                "title": title,
                "script": script,
                "length": len(script),
                "taiyo_score": taiyo_score,
                "passed_quality": taiyo_score >= 70,
                "status": "completed",
                "attempts": attempt + 1
            }
            
        except Exception as e:
            logger.error(f"Error generating complete episode: {e}")
            return {
                "theme": theme,
                "status": "failed",
                "error": str(e)
            }
