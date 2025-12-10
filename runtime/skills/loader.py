"""Skill loader for loading and saving skills."""

import logging
from pathlib import Path
from typing import Any

from smartcp.runtime.types import UserContext

logger = logging.getLogger(__name__)


class SkillLoader:
    """Loads and saves skills (SKILL.md files)."""

    def __init__(self, skills_dir: str | None = None):
        """Initialize skill loader.

        Args:
            skills_dir: Directory for skills storage
        """
        self.skills_dir = Path(skills_dir) if skills_dir else Path.home() / ".smartcp" / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"SkillLoader initialized with directory: {self.skills_dir}")

    async def load(self, skill_name: str, user_ctx: UserContext | None = None) -> dict[str, Any]:
        """Load a skill by name.

        Args:
            skill_name: Skill name
            user_ctx: Optional user context for user-scoped skills

        Returns:
            Skill content and metadata
        """
        skill_path = self._get_skill_path(skill_name, user_ctx)

        if not skill_path.exists():
            return {
                "status": "not_found",
                "skill": skill_name,
            }

        try:
            content = skill_path.read_text()
            return {
                "status": "loaded",
                "skill": skill_name,
                "content": content,
            }
        except Exception as e:
            logger.error(f"Failed to load skill {skill_name}: {e}")
            return {
                "status": "error",
                "skill": skill_name,
                "error": str(e),
            }

    async def save(
        self,
        name: str,
        content: str,
        user_ctx: UserContext | None = None,
    ) -> dict[str, Any]:
        """Save a new skill.

        Args:
            name: Skill name
            content: Skill content (SKILL.md format)
            user_ctx: Optional user context for user-scoped skills

        Returns:
            Save result
        """
        skill_path = self._get_skill_path(name, user_ctx)

        try:
            skill_path.write_text(content)
            logger.info(f"Saved skill: {name}")
            return {
                "status": "saved",
                "skill": name,
            }
        except Exception as e:
            logger.error(f"Failed to save skill {name}: {e}")
            return {
                "status": "error",
                "skill": name,
                "error": str(e),
            }

    async def list(self, user_ctx: UserContext | None = None) -> list[str]:
        """List available skills.

        Args:
            user_ctx: Optional user context for user-scoped skills

        Returns:
            List of skill names
        """
        skills_path = self._get_skills_base_path(user_ctx)

        if not skills_path.exists():
            return []

        skills = []
        if skills_path.exists():
            for skill_file in skills_path.glob("*.md"):
                if skill_file.name.startswith("SKILL_"):
                    skill_name = skill_file.stem.replace("SKILL_", "")
                    skills.append(skill_name)

        return skills

    def _get_skills_base_path(self, user_ctx: UserContext | None = None) -> Path:
        """Get base path for skills."""
        if user_ctx:
            return self.skills_dir / user_ctx.user_id
        return self.skills_dir

    def _get_skill_path(self, skill_name: str, user_ctx: UserContext | None = None) -> Path:
        """Get path for a specific skill."""
        base = self._get_skills_base_path(user_ctx)
        return base / f"SKILL_{skill_name}.md"
