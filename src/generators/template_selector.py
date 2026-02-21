"""Template Selector - Genre-aware podcast template selection (REQ-201/REQ-202)"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger


# Theme-to-genre mapping (English themes → Japanese genres)
THEME_GENRE_MAP = {
    "technology": ["AIマーケティング", "AIビジネス"],
    "ai": ["AIマーケティング", "AIビジネス"],
    "business": ["ビジネスモデル", "コンテンツビジネス"],
    "startup": ["ビジネスモデル", "逆転劇"],
    "marketing": ["SNSマーケティング", "Webマーケティング", "音声マーケティング"],
    "copywriting": ["広告", "コピーライティング"],
    "advertising": ["広告", "コピーライティング"],
    "psychology": ["心理/行動経済学"],
    "investment": ["株式投資", "暗号通貨"],
    "crypto": ["暗号通貨"],
    "finance": ["株式投資", "FIRE/お金"],
    "economy": ["経済学", "経済評論"],
    "money": ["FIRE/お金"],
    "fire": ["FIRE/お金"],
    "philosophy": ["哲学"],
    "spiritual": ["スピリチュアル"],
    "mental": ["メンタル"],
    "coaching": ["メンタル/コーチング"],
    "health": ["メンタル", "スピリチュアル"],
    "content": ["コンテンツビジネス", "DRM"],
    "launch": ["プロダクトローンチ"],
    "drm": ["DRM"],
    "sns": ["SNSマーケティング"],
    "audio": ["音声マーケティング"],
    "reversal": ["逆転劇"],
}


class TemplateSelector:
    """Select optimal podcast template based on theme and content"""

    def __init__(self, templates_path: Optional[Path] = None):
        """Initialize with templates JSON file

        Args:
            templates_path: Path to podcast_templates.json.
                           Defaults to templates/podcast_templates.json
        """
        if templates_path is None:
            templates_path = Path(__file__).parent.parent.parent / "templates" / "podcast_templates.json"

        self.templates_path = templates_path
        self.templates = self._load_templates()
        self._recent_selections: List[str] = []

        logger.info(f"TemplateSelector initialized with {len(self.templates)} templates")

    def _load_templates(self) -> List[Dict]:
        """Load templates from JSON file"""
        if not self.templates_path.exists():
            logger.warning(f"Templates file not found: {self.templates_path}")
            return []

        with open(self.templates_path, "r", encoding="utf-8") as f:
            templates = json.load(f)

        logger.debug(f"Loaded {len(templates)} templates from {self.templates_path}")
        return templates

    def select(self, theme: str, articles: Optional[List[Dict]] = None, info_count: int = 0) -> Dict:
        """Select best template for given theme and content

        Algorithm (REQ-202):
            score = (topic_match * 0.4) + (info_count_fit * 0.3) + (recency_bonus * 0.3)

        Args:
            theme: Content theme (English keyword)
            articles: List of article dicts (optional)
            info_count: Number of articles/info items

        Returns:
            Best matching template dict
        """
        if not self.templates:
            logger.warning("No templates loaded, returning empty dict")
            return {}

        if articles and info_count == 0:
            info_count = len(articles)

        best_template = None
        best_score = -1.0

        for template in self.templates:
            topic_score = self._topic_match_score(template, theme)
            fit_score = self._info_count_fit_score(template, info_count)
            recency = self._recency_bonus(template)

            total_score = (topic_score * 0.4) + (fit_score * 0.3) + (recency * 0.3)

            logger.debug(
                f"  {template['template_id']}: "
                f"topic={topic_score:.2f} fit={fit_score:.2f} recency={recency:.2f} "
                f"total={total_score:.2f}"
            )

            if total_score > best_score:
                best_score = total_score
                best_template = template

        # Track selection for recency bonus
        if best_template:
            self._recent_selections.append(best_template["template_id"])
            if len(self._recent_selections) > 10:
                self._recent_selections = self._recent_selections[-10:]

            logger.info(
                f"Selected template: {best_template['template_id']} "
                f"({best_template['name']}) for theme '{theme}' "
                f"(score={best_score:.2f}, style={best_template['style']})"
            )

        return best_template or self.templates[0]

    def _topic_match_score(self, template: Dict, theme: str) -> float:
        """Calculate topic match score between template and theme

        Args:
            template: Template dict with 'genres' and 'category'
            theme: Theme keyword (English)

        Returns:
            Score from 0.0 to 1.0
        """
        theme_lower = theme.lower().strip()
        template_genres = set(template.get("genres", []))
        template_category = template.get("category", "")

        # Map English theme to Japanese genres
        mapped_genres = set()
        for key, genres in THEME_GENRE_MAP.items():
            if key in theme_lower:
                mapped_genres.update(genres)

        if not mapped_genres:
            # Fallback: check if theme appears in template category or genres
            for genre in template_genres:
                if theme_lower in genre.lower():
                    return 0.8
            if theme_lower in template_category.lower():
                return 0.6
            return 0.1

        # Calculate overlap between mapped genres and template genres
        overlap = mapped_genres & template_genres
        if overlap:
            return min(1.0, len(overlap) / len(mapped_genres))

        # Check category match
        for genre in mapped_genres:
            if genre in template_category:
                return 0.5

        return 0.1

    def _info_count_fit_score(self, template: Dict, info_count: int) -> float:
        """Calculate how well the template fits the number of articles

        Templates with more sections work better with more articles.

        Args:
            template: Template dict with 'sections'
            info_count: Number of articles

        Returns:
            Score from 0.0 to 1.0
        """
        sections = template.get("sections", [])
        section_count = len(sections)

        if info_count == 0:
            return 0.5

        # Ideal: info_count roughly matches section_count
        ratio = min(info_count, section_count) / max(info_count, section_count)
        return max(0.2, ratio)

    def _recency_bonus(self, template: Dict) -> float:
        """Calculate recency bonus (prefer templates not recently used)

        Args:
            template: Template dict with 'template_id'

        Returns:
            Score from 0.0 to 1.0
        """
        template_id = template.get("template_id", "")

        if not self._recent_selections:
            return 1.0

        if template_id in self._recent_selections:
            # Penalize recently used templates
            last_index = len(self._recent_selections) - 1 - self._recent_selections[::-1].index(template_id)
            distance = len(self._recent_selections) - last_index
            return min(1.0, distance / 5.0)

        return 1.0

    def get_ng_status(self, template: Dict) -> str:
        """Get the NG/style status of a template

        Args:
            template: Template dict

        Returns:
            'fact_strict', 'caution', or 'taiyo_ok'
        """
        return template.get("style", "taiyo_ok")
