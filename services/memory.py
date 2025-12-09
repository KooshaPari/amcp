"""User-Scoped Memory Service for SmartCP.

Provides persistent memory management scoped to users via UserContext.
Replaces session-based memory with user-based memory that persists
across requests and sessions.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from smartcp.infrastructure.state.adapter import StateAdapter
from smartcp.services.models import UserContext

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    """Types of memory storage."""

    # Short-term working memory (cleared on session end)
    WORKING = "working"
    # Long-term persistent memory (persists across sessions)
    PERSISTENT = "persistent"
    # Context memory for conversation history
    CONTEXT = "context"
    # Variable storage for code execution
    VARIABLE = "variable"
    # File references and metadata
    FILE = "file"
    # Learning patterns and preferences
    LEARNING = "learning"


class MemoryItem(BaseModel):
    """A memory item with metadata."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    key: str = Field(..., description="Memory key")
    value: Any = Field(..., description="Memory value")
    memory_type: MemoryType = Field(default=MemoryType.WORKING)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = Field(None, description="Expiration time")
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)


@dataclass
class MemoryStats:
    """Statistics about memory usage."""

    total_items: int = 0
    working_items: int = 0
    persistent_items: int = 0
    context_items: int = 0
    variable_items: int = 0
    file_items: int = 0
    learning_items: int = 0


class UserScopedMemory:
    """User-scoped memory service.

    Provides memory operations isolated by UserContext, replacing
    the session-based memory with persistent user memory.

    Memory is organized by type:
    - WORKING: Temporary working memory (auto-expires)
    - PERSISTENT: Long-term user memory
    - CONTEXT: Conversation context
    - VARIABLE: Code execution variables
    - FILE: File references
    - LEARNING: User learning patterns

    Usage:
        memory = UserScopedMemory(state_adapter)

        # Store a value
        await memory.set(user_ctx, "my_key", {"data": "value"})

        # Retrieve a value
        value = await memory.get(user_ctx, "my_key")

        # Store with type
        await memory.set(user_ctx, "counter", 42, memory_type=MemoryType.VARIABLE)

        # List keys by type
        keys = await memory.list_keys(user_ctx, memory_type=MemoryType.VARIABLE)
    """

    # Key prefixes for different memory types
    _PREFIXES = {
        MemoryType.WORKING: "mem:work:",
        MemoryType.PERSISTENT: "mem:persist:",
        MemoryType.CONTEXT: "mem:ctx:",
        MemoryType.VARIABLE: "mem:var:",
        MemoryType.FILE: "mem:file:",
        MemoryType.LEARNING: "mem:learn:",
    }

    # Default TTL for working memory (1 hour)
    DEFAULT_WORKING_TTL = 3600

    def __init__(self, state_adapter: StateAdapter):
        """Initialize memory service.

        Args:
            state_adapter: State adapter for persistence
        """
        self.state = state_adapter

    def _make_key(self, key: str, memory_type: MemoryType) -> str:
        """Create a prefixed key for storage.

        Args:
            key: User-provided key
            memory_type: Type of memory

        Returns:
            Prefixed key for storage
        """
        prefix = self._PREFIXES.get(memory_type, "mem:")
        return f"{prefix}{key}"

    def _extract_key(self, storage_key: str, memory_type: MemoryType) -> str:
        """Extract user key from storage key.

        Args:
            storage_key: Full storage key with prefix
            memory_type: Type of memory

        Returns:
            User-provided key without prefix
        """
        prefix = self._PREFIXES.get(memory_type, "mem:")
        if storage_key.startswith(prefix):
            return storage_key[len(prefix):]
        return storage_key

    async def get(
        self,
        user_ctx: UserContext,
        key: str,
        memory_type: MemoryType = MemoryType.WORKING,
        default: Any = None,
    ) -> Any:
        """Get a memory value.

        Args:
            user_ctx: User context for scoping
            key: Memory key
            memory_type: Type of memory
            default: Default value if not found

        Returns:
            Memory value or default
        """
        storage_key = self._make_key(key, memory_type)
        item_data = await self.state.get(user_ctx, storage_key, default=None)

        if item_data is None:
            return default

        # If stored as MemoryItem, extract value
        if isinstance(item_data, dict) and "value" in item_data:
            return item_data["value"]

        return item_data

    async def get_item(
        self,
        user_ctx: UserContext,
        key: str,
        memory_type: MemoryType = MemoryType.WORKING,
    ) -> Optional[MemoryItem]:
        """Get a full memory item with metadata.

        Args:
            user_ctx: User context for scoping
            key: Memory key
            memory_type: Type of memory

        Returns:
            MemoryItem or None if not found
        """
        storage_key = self._make_key(key, memory_type)
        item_data = await self.state.get(user_ctx, storage_key, default=None)

        if item_data is None:
            return None

        if isinstance(item_data, dict) and "id" in item_data:
            return MemoryItem(**item_data)

        # Legacy format - wrap in MemoryItem
        return MemoryItem(
            key=key,
            value=item_data,
            memory_type=memory_type,
        )

    async def set(
        self,
        user_ctx: UserContext,
        key: str,
        value: Any,
        memory_type: MemoryType = MemoryType.WORKING,
        ttl: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> MemoryItem:
        """Set a memory value.

        Args:
            user_ctx: User context for scoping
            key: Memory key
            value: Value to store
            memory_type: Type of memory
            ttl: Time-to-live in seconds (default depends on type)
            metadata: Optional metadata

        Returns:
            Created/updated MemoryItem
        """
        storage_key = self._make_key(key, memory_type)

        # Calculate TTL
        if ttl is None and memory_type == MemoryType.WORKING:
            ttl = self.DEFAULT_WORKING_TTL

        # Create memory item
        now = datetime.now(timezone.utc)
        item = MemoryItem(
            key=key,
            value=value,
            memory_type=memory_type,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )

        if ttl:
            item.expires_at = now + __import__("datetime").timedelta(seconds=ttl)

        # Store as dict for JSON serialization
        await self.state.set(user_ctx, storage_key, item.model_dump(mode="json"), ttl=ttl)

        logger.debug(
            "Memory value set",
            extra={
                "user_id": user_ctx.user_id,
                "key": key,
                "memory_type": memory_type.value,
                "ttl": ttl,
                "request_id": user_ctx.request_id,
            },
        )

        return item

    async def delete(
        self,
        user_ctx: UserContext,
        key: str,
        memory_type: MemoryType = MemoryType.WORKING,
    ) -> bool:
        """Delete a memory value.

        Args:
            user_ctx: User context for scoping
            key: Memory key
            memory_type: Type of memory

        Returns:
            True if deleted, False if not found
        """
        storage_key = self._make_key(key, memory_type)
        return await self.state.delete(user_ctx, storage_key)

    async def exists(
        self,
        user_ctx: UserContext,
        key: str,
        memory_type: MemoryType = MemoryType.WORKING,
    ) -> bool:
        """Check if a memory key exists.

        Args:
            user_ctx: User context for scoping
            key: Memory key
            memory_type: Type of memory

        Returns:
            True if exists
        """
        storage_key = self._make_key(key, memory_type)
        return await self.state.exists(user_ctx, storage_key)

    async def list_keys(
        self,
        user_ctx: UserContext,
        memory_type: Optional[MemoryType] = None,
    ) -> list[str]:
        """List memory keys.

        Args:
            user_ctx: User context for scoping
            memory_type: Filter by type (None for all)

        Returns:
            List of user-facing keys (without prefix)
        """
        if memory_type:
            prefix = self._PREFIXES.get(memory_type, "mem:")
            storage_keys = await self.state.list_keys(user_ctx, prefix=prefix)
            return [self._extract_key(k, memory_type) for k in storage_keys]
        else:
            # List all memory keys
            all_keys = await self.state.list_keys(user_ctx, prefix="mem:")
            result = []
            for storage_key in all_keys:
                for mem_type, prefix in self._PREFIXES.items():
                    if storage_key.startswith(prefix):
                        result.append(self._extract_key(storage_key, mem_type))
                        break
            return result

    async def clear(
        self,
        user_ctx: UserContext,
        memory_type: Optional[MemoryType] = None,
    ) -> int:
        """Clear memory.

        Args:
            user_ctx: User context for scoping
            memory_type: Type to clear (None for all)

        Returns:
            Number of keys cleared
        """
        if memory_type:
            prefix = self._PREFIXES.get(memory_type, "mem:")
            count = await self.state.clear(user_ctx, prefix=prefix)
        else:
            count = await self.state.clear(user_ctx, prefix="mem:")

        logger.info(
            "Memory cleared",
            extra={
                "user_id": user_ctx.user_id,
                "memory_type": memory_type.value if memory_type else "all",
                "count": count,
                "request_id": user_ctx.request_id,
            },
        )

        return count

    async def get_stats(self, user_ctx: UserContext) -> MemoryStats:
        """Get memory statistics.

        Args:
            user_ctx: User context for scoping

        Returns:
            MemoryStats with counts per type
        """
        stats = MemoryStats()

        for mem_type in MemoryType:
            keys = await self.list_keys(user_ctx, memory_type=mem_type)
            count = len(keys)
            stats.total_items += count

            if mem_type == MemoryType.WORKING:
                stats.working_items = count
            elif mem_type == MemoryType.PERSISTENT:
                stats.persistent_items = count
            elif mem_type == MemoryType.CONTEXT:
                stats.context_items = count
            elif mem_type == MemoryType.VARIABLE:
                stats.variable_items = count
            elif mem_type == MemoryType.FILE:
                stats.file_items = count
            elif mem_type == MemoryType.LEARNING:
                stats.learning_items = count

        return stats

    # =========================================================================
    # Convenience Methods for Specific Memory Types
    # =========================================================================

    async def set_variable(
        self,
        user_ctx: UserContext,
        name: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> MemoryItem:
        """Store a code execution variable.

        Args:
            user_ctx: User context
            name: Variable name
            value: Variable value
            ttl: Optional TTL

        Returns:
            Created MemoryItem
        """
        return await self.set(
            user_ctx,
            key=name,
            value=value,
            memory_type=MemoryType.VARIABLE,
            ttl=ttl,
            metadata={"type": type(value).__name__},
        )

    async def get_variable(
        self,
        user_ctx: UserContext,
        name: str,
        default: Any = None,
    ) -> Any:
        """Get a code execution variable.

        Args:
            user_ctx: User context
            name: Variable name
            default: Default value

        Returns:
            Variable value or default
        """
        return await self.get(user_ctx, name, MemoryType.VARIABLE, default)

    async def get_variables(self, user_ctx: UserContext) -> dict[str, Any]:
        """Get all variables as a dictionary.

        Args:
            user_ctx: User context

        Returns:
            Dictionary of variable name -> value
        """
        keys = await self.list_keys(user_ctx, MemoryType.VARIABLE)
        result = {}
        for key in keys:
            result[key] = await self.get_variable(user_ctx, key)
        return result

    async def store_context(
        self,
        user_ctx: UserContext,
        key: str,
        context_data: dict[str, Any],
    ) -> MemoryItem:
        """Store conversation context.

        Args:
            user_ctx: User context
            key: Context key (e.g., "conversation_history")
            context_data: Context data

        Returns:
            Created MemoryItem
        """
        return await self.set(
            user_ctx,
            key=key,
            value=context_data,
            memory_type=MemoryType.CONTEXT,
        )

    async def get_context(
        self,
        user_ctx: UserContext,
        key: str,
    ) -> Optional[dict[str, Any]]:
        """Get conversation context.

        Args:
            user_ctx: User context
            key: Context key

        Returns:
            Context data or None
        """
        return await self.get(user_ctx, key, MemoryType.CONTEXT)

    async def store_file_reference(
        self,
        user_ctx: UserContext,
        file_id: str,
        file_info: dict[str, Any],
    ) -> MemoryItem:
        """Store a file reference.

        Args:
            user_ctx: User context
            file_id: File identifier
            file_info: File metadata (name, path, size, etc.)

        Returns:
            Created MemoryItem
        """
        return await self.set(
            user_ctx,
            key=file_id,
            value=file_info,
            memory_type=MemoryType.FILE,
            metadata={"file_name": file_info.get("name", "")},
        )

    async def get_file_reference(
        self,
        user_ctx: UserContext,
        file_id: str,
    ) -> Optional[dict[str, Any]]:
        """Get a file reference.

        Args:
            user_ctx: User context
            file_id: File identifier

        Returns:
            File info or None
        """
        return await self.get(user_ctx, file_id, MemoryType.FILE)

    async def store_learning(
        self,
        user_ctx: UserContext,
        pattern_key: str,
        pattern_data: dict[str, Any],
    ) -> MemoryItem:
        """Store a learning pattern.

        Args:
            user_ctx: User context
            pattern_key: Pattern identifier
            pattern_data: Pattern data

        Returns:
            Created MemoryItem
        """
        return await self.set(
            user_ctx,
            key=pattern_key,
            value=pattern_data,
            memory_type=MemoryType.LEARNING,
        )

    async def get_learning(
        self,
        user_ctx: UserContext,
        pattern_key: str,
    ) -> Optional[dict[str, Any]]:
        """Get a learning pattern.

        Args:
            user_ctx: User context
            pattern_key: Pattern identifier

        Returns:
            Pattern data or None
        """
        return await self.get(user_ctx, pattern_key, MemoryType.LEARNING)


def create_memory_service(
    state_adapter: Optional[StateAdapter] = None,
) -> UserScopedMemory:
    """Factory function to create a memory service.

    Args:
        state_adapter: State adapter (created if not provided)

    Returns:
        Configured UserScopedMemory instance
    """
    if state_adapter is None:
        from smartcp.infrastructure.state import create_state_adapter
        state_adapter = create_state_adapter()

    return UserScopedMemory(state_adapter)
