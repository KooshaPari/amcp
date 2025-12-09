"""Abstract state adapter interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional

from smartcp.models.schemas import UserContext


class StateAdapter(ABC):
    """Abstract base class for state adapters.

    Defines the interface for user-scoped state management.
    All implementations must ensure proper user isolation.
    """

    @abstractmethod
    async def get(
        self,
        user_ctx: UserContext,
        key: str,
        default: Any = None,
    ) -> Any:
        """Get a state value for the user.

        Args:
            user_ctx: User context for scoping
            key: State key
            default: Default value if key not found

        Returns:
            State value or default
        """
        ...

    @abstractmethod
    async def set(
        self,
        user_ctx: UserContext,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set a state value for the user.

        Args:
            user_ctx: User context for scoping
            key: State key
            value: Value to store (must be JSON-serializable)
            ttl: Optional time-to-live in seconds
        """
        ...

    @abstractmethod
    async def delete(
        self,
        user_ctx: UserContext,
        key: str,
    ) -> bool:
        """Delete a state key.

        Args:
            user_ctx: User context for scoping
            key: State key to delete

        Returns:
            True if key was deleted, False if not found
        """
        ...

    @abstractmethod
    async def exists(
        self,
        user_ctx: UserContext,
        key: str,
    ) -> bool:
        """Check if a state key exists.

        Args:
            user_ctx: User context for scoping
            key: State key to check

        Returns:
            True if key exists
        """
        ...

    @abstractmethod
    async def list_keys(
        self,
        user_ctx: UserContext,
        prefix: Optional[str] = None,
    ) -> list[str]:
        """List all state keys for the user.

        Args:
            user_ctx: User context for scoping
            prefix: Optional key prefix filter

        Returns:
            List of matching keys
        """
        ...

    @abstractmethod
    async def clear(
        self,
        user_ctx: UserContext,
        prefix: Optional[str] = None,
    ) -> int:
        """Clear all state for the user.

        Args:
            user_ctx: User context for scoping
            prefix: Optional key prefix to limit deletion

        Returns:
            Number of keys deleted
        """
        ...
