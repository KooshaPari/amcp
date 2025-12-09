"""Memory MCP Tools for SmartCP.

Provides MCP tools for user-scoped memory operations including
working memory, persistent memory, and context management.
"""

import logging
from typing import Any, Optional

from auth.context import get_request_context
from services.memory import MemoryType, UserScopedMemory

logger = logging.getLogger(__name__)


def register_memory_tools(mcp: Any, memory: UserScopedMemory) -> None:
    """Register memory tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        memory: UserScopedMemory service
    """

    @mcp.tool()
    async def store_memory(
        key: str,
        value: Any,
        memory_type: str = "working",
        ttl: Optional[int] = None,
    ) -> dict[str, Any]:
        """Store a value in user memory.

        Memory is isolated per user and persists across requests.
        Different memory types have different lifetimes:

        - working: Temporary storage (auto-expires after 1 hour by default)
        - persistent: Long-term storage (never expires)
        - context: Conversation context storage

        Args:
            key: Memory key (unique within memory type)
            value: Value to store (must be JSON-serializable)
            memory_type: Type of memory ("working", "persistent", or "context")
            ttl: Optional time-to-live in seconds (overrides default)

        Returns:
            Dictionary with:
            - success: Whether the operation succeeded
            - key: The memory key
            - memory_type: The memory type used
            - expires_at: Expiration timestamp if TTL set

        Examples:
            # Store temporary working memory
            store_memory(key="current_task", value={"step": 1})

            # Store persistent preference
            store_memory(key="theme", value="dark", memory_type="persistent")

            # Store with custom TTL (5 minutes)
            store_memory(key="cache", value=data, ttl=300)
        """
        user_ctx = get_request_context()
        if user_ctx is None:
            return {"success": False, "error": "Authentication required"}

        try:
            mem_type = MemoryType(memory_type)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid memory_type: {memory_type}. "
                f"Must be one of: working, persistent, context",
            }

        try:
            item = await memory.set(
                user_ctx,
                key=key,
                value=value,
                memory_type=mem_type,
                ttl=ttl,
            )

            return {
                "success": True,
                "key": key,
                "memory_type": memory_type,
                "expires_at": item.expires_at.isoformat() if item.expires_at else None,
            }

        except Exception as e:
            logger.error(
                "Failed to store memory",
                extra={
                    "user_id": user_ctx.user_id,
                    "key": key,
                    "error": str(e),
                    "request_id": user_ctx.request_id,
                },
            )
            return {"success": False, "error": f"Failed to store: {e}"}

    @mcp.tool()
    async def retrieve_memory(
        key: str,
        memory_type: str = "working",
    ) -> dict[str, Any]:
        """Retrieve a value from user memory.

        Args:
            key: Memory key to retrieve
            memory_type: Type of memory to search ("working", "persistent", or "context")

        Returns:
            Dictionary with:
            - found: Whether the key was found
            - key: The memory key
            - value: The stored value (if found)
            - memory_type: The memory type searched

        Examples:
            # Retrieve working memory
            retrieve_memory(key="current_task")
            # Result: {"found": True, "key": "current_task", "value": {"step": 1}}

            # Retrieve persistent setting
            retrieve_memory(key="theme", memory_type="persistent")
        """
        user_ctx = get_request_context()
        if user_ctx is None:
            return {"found": False, "error": "Authentication required"}

        try:
            mem_type = MemoryType(memory_type)
        except ValueError:
            return {"found": False, "error": f"Invalid memory_type: {memory_type}"}

        value = await memory.get(user_ctx, key, mem_type)

        return {
            "found": value is not None,
            "key": key,
            "value": value,
            "memory_type": memory_type,
        }

    @mcp.tool()
    async def delete_memory(
        key: str,
        memory_type: str = "working",
    ) -> dict[str, Any]:
        """Delete a value from user memory.

        Args:
            key: Memory key to delete
            memory_type: Type of memory ("working", "persistent", or "context")

        Returns:
            Dictionary with:
            - success: Whether the key was deleted
            - key: The memory key
        """
        user_ctx = get_request_context()
        if user_ctx is None:
            return {"success": False, "error": "Authentication required"}

        try:
            mem_type = MemoryType(memory_type)
        except ValueError:
            return {"success": False, "error": f"Invalid memory_type: {memory_type}"}

        deleted = await memory.delete(user_ctx, key, mem_type)

        return {
            "success": deleted,
            "key": key,
            "memory_type": memory_type,
        }

    @mcp.tool()
    async def list_memory_keys(
        memory_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """List all memory keys for the user.

        Args:
            memory_type: Optional filter by type (None for all types)

        Returns:
            Dictionary with:
            - keys: List of memory keys
            - count: Number of keys
            - memory_type: The type filter applied (or "all")
        """
        user_ctx = get_request_context()
        if user_ctx is None:
            return {"keys": [], "count": 0, "error": "Authentication required"}

        mem_type = None
        if memory_type:
            try:
                mem_type = MemoryType(memory_type)
            except ValueError:
                return {"keys": [], "count": 0, "error": f"Invalid memory_type: {memory_type}"}

        keys = await memory.list_keys(user_ctx, memory_type=mem_type)

        return {
            "keys": keys,
            "count": len(keys),
            "memory_type": memory_type or "all",
        }

    @mcp.tool()
    async def clear_memory(
        memory_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """Clear user memory.

        WARNING: This will delete all memory of the specified type.
        Use with caution.

        Args:
            memory_type: Type to clear (None to clear all memory)

        Returns:
            Dictionary with:
            - success: Whether the operation succeeded
            - count: Number of keys cleared
            - memory_type: The type cleared (or "all")
        """
        user_ctx = get_request_context()
        if user_ctx is None:
            return {"success": False, "count": 0, "error": "Authentication required"}

        mem_type = None
        if memory_type:
            try:
                mem_type = MemoryType(memory_type)
            except ValueError:
                return {"success": False, "count": 0, "error": f"Invalid memory_type: {memory_type}"}

        count = await memory.clear(user_ctx, memory_type=mem_type)

        logger.info(
            "Memory cleared",
            extra={
                "user_id": user_ctx.user_id,
                "memory_type": memory_type or "all",
                "count": count,
                "request_id": user_ctx.request_id,
            },
        )

        return {
            "success": True,
            "count": count,
            "memory_type": memory_type or "all",
        }

    @mcp.tool()
    async def get_memory_stats() -> dict[str, Any]:
        """Get memory usage statistics.

        Returns:
            Dictionary with counts per memory type:
            - total_items: Total number of stored items
            - working_items: Working memory items
            - persistent_items: Persistent memory items
            - context_items: Context items
            - variable_items: Execution variables
            - file_items: File references
            - learning_items: Learning patterns
        """
        user_ctx = get_request_context()
        if user_ctx is None:
            return {"error": "Authentication required"}

        stats = await memory.get_stats(user_ctx)

        return {
            "total_items": stats.total_items,
            "working_items": stats.working_items,
            "persistent_items": stats.persistent_items,
            "context_items": stats.context_items,
            "variable_items": stats.variable_items,
            "file_items": stats.file_items,
            "learning_items": stats.learning_items,
        }

    logger.info("Registered memory tools with MCP server")
