"""Skills API for agent namespace."""

import logging
from typing import Any

from smartcp.runtime.skills.loader import SkillLoader
from smartcp.runtime.types import UserContext

logger = logging.getLogger(__name__)


class SkillsAPI:
    """Skills API injected into agent namespace."""

    def __init__(
        self,
        loader: SkillLoader,
        user_ctx: UserContext,
    ):
        """Initialize skills API.

        Args:
            loader: Skill loader
            user_ctx: User context
        """
        self._loader = loader
        self._user_ctx = user_ctx

    async def load(self, skill_name: str) -> dict[str, Any]:
        """Load a skill by name."""
        return await self._loader.load(skill_name, self._user_ctx)

    async def save(self, name: str, content: str) -> dict[str, Any]:
        """Save a new skill."""
        return await self._loader.save(name, content, self._user_ctx)

    async def list(self) -> list[str]:
        """List available skills."""
        return await self._loader.list(self._user_ctx)
