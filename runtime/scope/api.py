"""Scope API for agent namespace."""

import logging
from typing import Any

from smartcp.runtime.scope.manager import ScopeManager
from smartcp.runtime.scope.types import ScopeLevel
from smartcp.runtime.types import UserContext

logger = logging.getLogger(__name__)


class ScopeLevelAccessor:
    """Accessor for a single scope level."""

    def __init__(
        self,
        level: ScopeLevel,
        manager: ScopeManager,
        user_ctx: UserContext,
    ):
        """Initialize scope level accessor.

        Args:
            level: Scope level
            manager: Scope manager
            user_ctx: User context
        """
        self._level = level
        self._manager = manager
        self._user_ctx = user_ctx

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from scope."""
        return await self._manager.get(self._level, key, self._user_ctx, default)

    async def set(self, key: str, value: Any) -> None:
        """Set value in scope."""
        await self._manager.set(self._level, key, value, self._user_ctx)

    async def delete(self, key: str) -> bool:
        """Delete value from scope."""
        return await self._manager.delete(self._level, key, self._user_ctx)

    async def keys(self) -> list[str]:
        """List keys in scope."""
        return await self._manager.keys(self._level, self._user_ctx)


class ScopeAPI:
    """Scope API injected into agent namespace."""

    def __init__(
        self,
        manager: ScopeManager,
        user_ctx: UserContext,
    ):
        """Initialize scope API.

        Args:
            manager: Scope manager
            user_ctx: User context
        """
        self._manager = manager
        self._user_ctx = user_ctx

        # Create level-specific accessors
        self.block = ScopeLevelAccessor(ScopeLevel.BLOCK, manager, user_ctx)
        self.iteration = ScopeLevelAccessor(ScopeLevel.ITERATION, manager, user_ctx)
        self.tool_call = ScopeLevelAccessor(ScopeLevel.TOOL_CALL, manager, user_ctx)
        self.prompt_chain = ScopeLevelAccessor(ScopeLevel.PROMPT_CHAIN, manager, user_ctx)
        self.session = ScopeLevelAccessor(ScopeLevel.SESSION, manager, user_ctx)
        self.phase = ScopeLevelAccessor(ScopeLevel.PHASE, manager, user_ctx)
        self.project = ScopeLevelAccessor(ScopeLevel.PROJECT, manager, user_ctx)
        self.workspace = ScopeLevelAccessor(ScopeLevel.WORKSPACE, manager, user_ctx)
        self.organization = ScopeLevelAccessor(ScopeLevel.ORGANIZATION, manager, user_ctx)
        self.global_ = ScopeLevelAccessor(ScopeLevel.GLOBAL, manager, user_ctx)
        self.permanent = ScopeLevelAccessor(ScopeLevel.PERMANENT, manager, user_ctx)

    async def promote(self, key: str, from_level: str, to_level: str) -> bool:
        """Promote a value to a higher scope.

        Args:
            key: Variable key
            from_level: Source scope level
            to_level: Target scope level

        Returns:
            True if promoted successfully
        """
        from_enum = ScopeLevel.from_string(from_level)
        to_enum = ScopeLevel.from_string(to_level)
        return await self._manager.promote(key, from_enum, to_enum, self._user_ctx)

    async def demote(self, key: str, from_level: str, to_level: str) -> bool:
        """Demote a value to a lower scope.

        Args:
            key: Variable key
            from_level: Source scope level
            to_level: Target scope level

        Returns:
            True if demoted successfully
        """
        from_enum = ScopeLevel.from_string(from_level)
        to_enum = ScopeLevel.from_string(to_level)
        return await self._manager.demote(key, from_enum, to_enum, self._user_ctx)
