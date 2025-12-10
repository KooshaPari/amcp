"""Scope manager for 11-level scope hierarchy."""

import logging
from typing import Any

from smartcp.runtime.scope.storage import ScopeStorage
from smartcp.runtime.scope.types import ScopeLevel
from smartcp.runtime.types import UserContext

logger = logging.getLogger(__name__)


class ScopeManager:
    """Manages 11-level scope hierarchy for variable storage."""

    def __init__(self, storage_backend: str = "memory"):
        """Initialize scope manager.

        Args:
            storage_backend: Storage backend type ("memory", "redis", "supabase")
        """
        self.storage = ScopeStorage.create(storage_backend)
        logger.info(f"ScopeManager initialized with {storage_backend} backend")

    async def get(
        self,
        level: ScopeLevel | str,
        key: str,
        user_ctx: UserContext,
        default: Any = None,
    ) -> Any:
        """Get value from scope.

        Args:
            level: Scope level
            key: Variable key
            user_ctx: User context
            default: Default value if not found

        Returns:
            Stored value or default
        """
        level_enum = ScopeLevel(level) if isinstance(level, str) else level
        return await self.storage.get(level_enum, key, user_ctx, default)

    async def set(
        self,
        level: ScopeLevel | str,
        key: str,
        value: Any,
        user_ctx: UserContext,
    ) -> None:
        """Set value in scope.

        Args:
            level: Scope level
            key: Variable key
            value: Value to store
            user_ctx: User context
        """
        level_enum = ScopeLevel(level) if isinstance(level, str) else level
        await self.storage.set(level_enum, key, value, user_ctx)

    async def delete(
        self,
        level: ScopeLevel | str,
        key: str,
        user_ctx: UserContext,
    ) -> bool:
        """Delete value from scope.

        Args:
            level: Scope level
            key: Variable key
            user_ctx: User context

        Returns:
            True if deleted, False if not found
        """
        level_enum = ScopeLevel(level) if isinstance(level, str) else level
        return await self.storage.delete(level_enum, key, user_ctx)

    async def keys(
        self,
        level: ScopeLevel | str,
        user_ctx: UserContext,
    ) -> list[str]:
        """List all keys in a scope level.

        Args:
            level: Scope level
            user_ctx: User context

        Returns:
            List of keys
        """
        level_enum = ScopeLevel(level) if isinstance(level, str) else level
        return await self.storage.keys(level_enum, user_ctx)

    async def promote(
        self,
        key: str,
        from_level: ScopeLevel | str,
        to_level: ScopeLevel | str,
        user_ctx: UserContext,
    ) -> bool:
        """Promote a value to a higher scope level.

        Args:
            key: Variable key
            from_level: Source scope level
            to_level: Target scope level
            user_ctx: User context

        Returns:
            True if promoted, False if source value not found
        """
        value = await self.get(from_level, key, user_ctx)
        if value is None:
            return False

        await self.set(to_level, key, value, user_ctx)
        await self.delete(from_level, key, user_ctx)
        return True

    async def demote(
        self,
        key: str,
        from_level: ScopeLevel | str,
        to_level: ScopeLevel | str,
        user_ctx: UserContext,
    ) -> bool:
        """Demote a value to a lower scope level.

        Args:
            key: Variable key
            from_level: Source scope level
            to_level: Target scope level
            user_ctx: User context

        Returns:
            True if demoted, False if source value not found
        """
        value = await self.get(from_level, key, user_ctx)
        if value is None:
            return False

        await self.set(to_level, key, value, user_ctx)
        await self.delete(from_level, key, user_ctx)
        return True
