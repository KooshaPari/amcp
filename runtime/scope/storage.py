"""Scope storage backends.

Supports multiple storage backends:
- Redis (hot/fast storage)
- Supabase (cold/persistent storage)
- In-memory (fallback/development)
"""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from smartcp.runtime.scope.types import ScopeLevel
    from smartcp.runtime.types import UserContext

logger = logging.getLogger(__name__)


class ScopeStorage(ABC):
    """Abstract base class for scope storage backends."""

    @classmethod
    def create(cls, backend: str = "memory", **kwargs) -> "ScopeStorage":
        """Create storage backend instance.

        Args:
            backend: Backend type ("memory", "redis", "supabase")
            **kwargs: Backend-specific configuration

        Returns:
            ScopeStorage instance
        """
        return create_storage(backend, **kwargs)

    @abstractmethod
    async def get(
        self,
        level: "ScopeLevel",
        key: str,
        user_ctx: "UserContext",
        default: Any = None,
    ) -> Any:
        """Get value from storage.

        Args:
            level: Scope level
            key: Variable key
            user_ctx: User context
            default: Default value if not found

        Returns:
            Stored value or default
        """
        pass

    @abstractmethod
    async def set(
        self,
        level: "ScopeLevel",
        key: str,
        value: Any,
        user_ctx: "UserContext",
    ) -> None:
        """Set value in storage.

        Args:
            level: Scope level
            key: Variable key
            value: Value to store
            user_ctx: User context
        """
        pass

    @abstractmethod
    async def delete(
        self,
        level: "ScopeLevel",
        key: str,
        user_ctx: "UserContext",
    ) -> bool:
        """Delete value from storage.

        Args:
            level: Scope level
            key: Variable key
            user_ctx: User context

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def keys(
        self,
        level: "ScopeLevel",
        user_ctx: "UserContext",
    ) -> list[str]:
        """List keys in scope level.

        Args:
            level: Scope level
            user_ctx: User context

        Returns:
            List of keys
        """
        pass


class InMemoryStorage(ScopeStorage):
    """In-memory storage backend (fallback/development)."""

    def __init__(self):
        """Initialize in-memory storage."""
        self._store: dict[str, Any] = {}

    def _make_key(self, level: "ScopeLevel", key: str, user_ctx: "UserContext") -> str:
        """Create storage key from scope level and user context."""
        parts = [level.value, user_ctx.user_id]
        if user_ctx.workspace_id:
            parts.append(f"ws:{user_ctx.workspace_id}")
        parts.append(key)
        return ":".join(parts)

    async def get(
        self,
        level: "ScopeLevel",
        key: str,
        user_ctx: "UserContext",
        default: Any = None,
    ) -> Any:
        """Get value from memory."""
        storage_key = self._make_key(level, key, user_ctx)
        return self._store.get(storage_key, default)

    async def set(
        self,
        level: "ScopeLevel",
        key: str,
        value: Any,
        user_ctx: "UserContext",
    ) -> None:
        """Set value in memory."""
        storage_key = self._make_key(level, key, user_ctx)
        self._store[storage_key] = value

    async def delete(
        self,
        level: "ScopeLevel",
        key: str,
        user_ctx: "UserContext",
    ) -> bool:
        """Delete value from memory."""
        storage_key = self._make_key(level, key, user_ctx)
        if storage_key in self._store:
            del self._store[storage_key]
            return True
        return False

    async def keys(
        self,
        level: "ScopeLevel",
        user_ctx: "UserContext",
    ) -> list[str]:
        """List keys in scope level."""
        prefix = f"{level.value}:{user_ctx.user_id}:"
        if user_ctx.workspace_id:
            prefix += f"ws:{user_ctx.workspace_id}:"

        keys = []
        for storage_key in self._store.keys():
            if storage_key.startswith(prefix):
                # Extract the actual key name
                key_part = storage_key[len(prefix):]
                keys.append(key_part)

        return keys


class RedisStorage(ScopeStorage):
    """Redis storage backend (hot/fast storage)."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize Redis storage.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self._client: Any = None

    async def _get_client(self):
        """Get or create Redis client."""
        if self._client is None:
            try:
                import redis.asyncio as redis

                self._client = redis.from_url(self.redis_url, decode_responses=True)
            except ImportError:
                raise ImportError(
                    "redis package required for RedisStorage. Install with: pip install redis"
                )
        return self._client

    def _make_key(self, level: "ScopeLevel", key: str, user_ctx: "UserContext") -> str:
        """Create storage key from scope level and user context."""
        parts = [level.value, user_ctx.user_id]
        if user_ctx.workspace_id:
            parts.append(f"ws:{user_ctx.workspace_id}")
        parts.append(key)
        return ":".join(parts)

    async def get(
        self,
        level: "ScopeLevel",
        key: str,
        user_ctx: "UserContext",
        default: Any = None,
    ) -> Any:
        """Get value from Redis."""
        try:
            client = await self._get_client()
            import json

            storage_key = self._make_key(level, key, user_ctx)
            value = await client.get(storage_key)
            if value is None:
                return default
            return json.loads(value)
        except Exception as e:
            logger.warning(f"Redis get failed: {e}", extra={"key": key})
            return default

    async def set(
        self,
        level: "ScopeLevel",
        key: str,
        value: Any,
        user_ctx: "UserContext",
    ) -> None:
        """Set value in Redis."""
        try:
            client = await self._get_client()
            import json

            storage_key = self._make_key(level, key, user_ctx)
            serialized = json.dumps(value)
            await client.set(storage_key, serialized)
        except Exception as e:
            logger.warning(f"Redis set failed: {e}", extra={"key": key})

    async def delete(
        self,
        level: "ScopeLevel",
        key: str,
        user_ctx: "UserContext",
    ) -> bool:
        """Delete value from Redis."""
        try:
            client = await self._get_client()
            storage_key = self._make_key(level, key, user_ctx)
            result = await client.delete(storage_key)
            return result > 0
        except Exception as e:
            logger.warning(f"Redis delete failed: {e}", extra={"key": key})
            return False

    async def keys(
        self,
        level: "ScopeLevel",
        user_ctx: "UserContext",
    ) -> list[str]:
        """List keys in scope level."""
        try:
            client = await self._get_client()
            pattern = f"{level.value}:{user_ctx.user_id}:*"
            if user_ctx.workspace_id:
                pattern = f"{level.value}:{user_ctx.user_id}:ws:{user_ctx.workspace_id}:*"

            storage_keys = [k async for k in client.scan_iter(match=pattern)]
            # Extract actual key names
            prefix = f"{level.value}:{user_ctx.user_id}:"
            if user_ctx.workspace_id:
                prefix += f"ws:{user_ctx.workspace_id}:"

            return [k[len(prefix):] for k in storage_keys]
        except Exception as e:
            logger.warning(f"Redis keys failed: {e}", extra={"level": level.value})
            return []


class SupabaseStorage(ScopeStorage):
    """Supabase storage backend (cold/persistent storage)."""

    def __init__(self, supabase_url: str, supabase_key: str, table: str = "scope_storage"):
        """Initialize Supabase storage.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service key
            table: Table name for scope storage
        """
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.table = table
        self._client: Any = None

    async def _get_client(self):
        """Get or create Supabase client."""
        if self._client is None:
            try:
                from supabase import create_client

                self._client = create_client(self.supabase_url, self.supabase_key)
            except ImportError:
                raise ImportError(
                    "supabase package required for SupabaseStorage. Install with: pip install supabase"
                )
        return self._client

    def _make_key(self, level: "ScopeLevel", key: str, user_ctx: "UserContext") -> str:
        """Create storage key from scope level and user context."""
        parts = [level.value, user_ctx.user_id]
        if user_ctx.workspace_id:
            parts.append(f"ws:{user_ctx.workspace_id}")
        parts.append(key)
        return ":".join(parts)

    async def get(
        self,
        level: "ScopeLevel",
        key: str,
        user_ctx: "UserContext",
        default: Any = None,
    ) -> Any:
        """Get value from Supabase."""
        try:
            client = await self._get_client()
            import json

            storage_key = self._make_key(level, key, user_ctx)
            result = client.table(self.table).select("value").eq("key", storage_key).execute()
            if result.data:
                return json.loads(result.data[0]["value"])
            return default
        except Exception as e:
            logger.warning(f"Supabase get failed: {e}", extra={"key": key})
            return default

    async def set(
        self,
        level: "ScopeLevel",
        key: str,
        value: Any,
        user_ctx: "UserContext",
    ) -> None:
        """Set value in Supabase."""
        try:
            client = await self._get_client()
            import json
            from datetime import datetime

            storage_key = self._make_key(level, key, user_ctx)
            data = {
                "key": storage_key,
                "value": json.dumps(value),
                "level": level.value,
                "user_id": user_ctx.user_id,
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Upsert
            client.table(self.table).upsert(data).execute()
        except Exception as e:
            logger.warning(f"Supabase set failed: {e}", extra={"key": key})

    async def delete(
        self,
        level: "ScopeLevel",
        key: str,
        user_ctx: "UserContext",
    ) -> bool:
        """Delete value from Supabase."""
        try:
            client = await self._get_client()
            storage_key = self._make_key(level, key, user_ctx)
            result = client.table(self.table).delete().eq("key", storage_key).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.warning(f"Supabase delete failed: {e}", extra={"key": key})
            return False

    async def keys(
        self,
        level: "ScopeLevel",
        user_ctx: "UserContext",
    ) -> list[str]:
        """List keys in scope level."""
        try:
            client = await self._get_client()
            result = (
                client.table(self.table)
                .select("key")
                .eq("level", level.value)
                .eq("user_id", user_ctx.user_id)
                .execute()
            )

            prefix = f"{level.value}:{user_ctx.user_id}:"
            if user_ctx.workspace_id:
                prefix += f"ws:{user_ctx.workspace_id}:"

            keys = []
            for row in result.data:
                storage_key = row["key"]
                if storage_key.startswith(prefix):
                    keys.append(storage_key[len(prefix):])

            return keys
        except Exception as e:
            logger.warning(f"Supabase keys failed: {e}", extra={"level": level.value})
            return []


def create_storage(
    backend: str = "memory",
    **kwargs,
) -> ScopeStorage:
    """Create storage backend instance.

    Args:
        backend: Backend type ("memory", "redis", "supabase")
        **kwargs: Backend-specific configuration

    Returns:
        ScopeStorage instance
    """
    if backend == "memory":
        return InMemoryStorage()
    elif backend == "redis":
        return RedisStorage(kwargs.get("redis_url", "redis://localhost:6379"))
    elif backend == "supabase":
        return SupabaseStorage(
            supabase_url=kwargs["supabase_url"],
            supabase_key=kwargs["supabase_key"],
            table=kwargs.get("table", "scope_storage"),
        )
    else:
        raise ValueError(f"Unknown storage backend: {backend}")
