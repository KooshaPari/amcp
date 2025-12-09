"""State Management MCP Tools for SmartCP.

Provides low-level state access tools for advanced use cases.
Most users should prefer the memory tools which provide
higher-level abstractions.
"""

import logging
from typing import Any, Optional

from auth.context import get_request_context
from smartcp.infrastructure.state.adapter import StateAdapter

logger = logging.getLogger(__name__)


def register_state_tools(mcp: Any, state: StateAdapter) -> None:
    """Register state tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        state: StateAdapter for persistence
    """

    @mcp.tool()
    async def state_get(
        key: str,
        default: Any = None,
    ) -> dict[str, Any]:
        """Get a raw state value.

        Low-level state access. For most use cases, prefer store_memory
        and retrieve_memory which provide better organization.

        Args:
            key: State key
            default: Default value if not found

        Returns:
            Dictionary with:
            - found: Whether the key was found
            - key: The state key
            - value: The stored value (or default)
        """
        user_ctx = get_request_context()
        if user_ctx is None:
            return {"found": False, "error": "Authentication required"}

        value = await state.get(user_ctx, key, default=None)

        return {
            "found": value is not None,
            "key": key,
            "value": value if value is not None else default,
        }

    @mcp.tool()
    async def state_set(
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> dict[str, Any]:
        """Set a raw state value.

        Low-level state access. For most use cases, prefer store_memory
        which provides better organization by memory type.

        Args:
            key: State key
            value: Value to store (must be JSON-serializable)
            ttl: Optional time-to-live in seconds

        Returns:
            Dictionary with:
            - success: Whether the operation succeeded
            - key: The state key
        """
        user_ctx = get_request_context()
        if user_ctx is None:
            return {"success": False, "error": "Authentication required"}

        try:
            await state.set(user_ctx, key, value, ttl=ttl)
            return {"success": True, "key": key}
        except Exception as e:
            logger.error(
                "Failed to set state",
                extra={
                    "user_id": user_ctx.user_id,
                    "key": key,
                    "error": str(e),
                    "request_id": user_ctx.request_id,
                },
            )
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def state_delete(key: str) -> dict[str, Any]:
        """Delete a raw state value.

        Args:
            key: State key to delete

        Returns:
            Dictionary with:
            - success: Whether the key was deleted
            - key: The state key
        """
        user_ctx = get_request_context()
        if user_ctx is None:
            return {"success": False, "error": "Authentication required"}

        deleted = await state.delete(user_ctx, key)
        return {"success": deleted, "key": key}

    @mcp.tool()
    async def state_exists(key: str) -> dict[str, Any]:
        """Check if a state key exists.

        Args:
            key: State key to check

        Returns:
            Dictionary with:
            - exists: Whether the key exists
            - key: The state key
        """
        user_ctx = get_request_context()
        if user_ctx is None:
            return {"exists": False, "error": "Authentication required"}

        exists = await state.exists(user_ctx, key)
        return {"exists": exists, "key": key}

    @mcp.tool()
    async def state_list_keys(
        prefix: Optional[str] = None,
    ) -> dict[str, Any]:
        """List all state keys.

        Args:
            prefix: Optional prefix filter

        Returns:
            Dictionary with:
            - keys: List of matching keys
            - count: Number of keys
            - prefix: The prefix filter applied
        """
        user_ctx = get_request_context()
        if user_ctx is None:
            return {"keys": [], "count": 0, "error": "Authentication required"}

        keys = await state.list_keys(user_ctx, prefix=prefix)

        return {
            "keys": keys,
            "count": len(keys),
            "prefix": prefix,
        }

    @mcp.tool()
    async def state_clear(
        prefix: Optional[str] = None,
    ) -> dict[str, Any]:
        """Clear state keys.

        WARNING: This will delete all matching state. Use with caution.

        Args:
            prefix: Optional prefix to limit deletion (None clears all)

        Returns:
            Dictionary with:
            - success: Whether the operation succeeded
            - count: Number of keys cleared
            - prefix: The prefix filter applied
        """
        user_ctx = get_request_context()
        if user_ctx is None:
            return {"success": False, "count": 0, "error": "Authentication required"}

        count = await state.clear(user_ctx, prefix=prefix)

        logger.info(
            "State cleared",
            extra={
                "user_id": user_ctx.user_id,
                "prefix": prefix,
                "count": count,
                "request_id": user_ctx.request_id,
            },
        )

        return {
            "success": True,
            "count": count,
            "prefix": prefix,
        }

    logger.info("Registered state tools with MCP server")
