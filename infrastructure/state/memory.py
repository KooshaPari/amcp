"""In-memory state adapter for testing."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from smartcp.infrastructure.state.adapter import StateAdapter
from smartcp.models.schemas import UserContext


class InMemoryStateAdapter(StateAdapter):
    """In-memory state adapter for testing.

    Stores state in a dictionary, scoped by user_id.
    Not suitable for production use.
    """

    def __init__(self):
        self._store: dict[str, dict[str, tuple[Any, Optional[datetime]]]] = {}

    def _get_user_store(self, user_id: str) -> dict[str, tuple[Any, Optional[datetime]]]:
        """Get or create user's state store."""
        if user_id not in self._store:
            self._store[user_id] = {}
        return self._store[user_id]

    async def get(
        self,
        user_ctx: UserContext,
        key: str,
        default: Any = None,
    ) -> Any:
        store = self._get_user_store(user_ctx.user_id)
        if key not in store:
            return default

        value, expires_at = store[key]
        if expires_at and expires_at < datetime.now(timezone.utc):
            del store[key]
            return default

        return value

    async def set(
        self,
        user_ctx: UserContext,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        store = self._get_user_store(user_ctx.user_id)
        expires_at = None
        if ttl:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        store[key] = (value, expires_at)

    async def delete(
        self,
        user_ctx: UserContext,
        key: str,
    ) -> bool:
        store = self._get_user_store(user_ctx.user_id)
        if key in store:
            del store[key]
            return True
        return False

    async def exists(
        self,
        user_ctx: UserContext,
        key: str,
    ) -> bool:
        value = await self.get(user_ctx, key, default=None)
        return value is not None

    async def list_keys(
        self,
        user_ctx: UserContext,
        prefix: Optional[str] = None,
    ) -> list[str]:
        store = self._get_user_store(user_ctx.user_id)
        now = datetime.now(timezone.utc)
        keys = []

        for key, (_, expires_at) in store.items():
            if expires_at and expires_at < now:
                continue
            if prefix and not key.startswith(prefix):
                continue
            keys.append(key)

        return sorted(keys)

    async def clear(
        self,
        user_ctx: UserContext,
        prefix: Optional[str] = None,
    ) -> int:
        store = self._get_user_store(user_ctx.user_id)

        if prefix:
            keys_to_delete = [k for k in store if k.startswith(prefix)]
            for key in keys_to_delete:
                del store[key]
            return len(keys_to_delete)
        else:
            count = len(store)
            store.clear()
            return count

    async def get_many(
        self,
        user_ctx: UserContext,
        keys: list[str],
    ) -> dict[str, Any]:
        """Get multiple state values at once."""
        result = {}
        for key in keys:
            value = await self.get(user_ctx, key)
            if value is not None:
                result[key] = value
        return result

    async def set_many(
        self,
        user_ctx: UserContext,
        items: dict[str, Any],
        ttl: Optional[int] = None,
    ) -> None:
        """Set multiple state values at once."""
        for key, value in items.items():
            await self.set(user_ctx, key, value, ttl=ttl)

    async def increment(
        self,
        user_ctx: UserContext,
        key: str,
        amount: int = 1,
    ) -> int:
        """Increment a numeric state value."""
        from smartcp.infrastructure.state.errors import StateError

        current = await self.get(user_ctx, key, default=0)

        if not isinstance(current, (int, float)):
            raise StateError(f"Cannot increment non-numeric value for key '{key}'")

        new_value = current + amount
        await self.set(user_ctx, key, new_value)

        return new_value
