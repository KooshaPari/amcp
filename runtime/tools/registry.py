"""Tool registry for managing available tools."""

import logging
from typing import Any

from smartcp.runtime.tools.types import ToolDefinition
from smartcp.runtime.types import UserContext

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing tools available in the runtime."""

    def __init__(self):
        """Initialize tool registry."""
        self._tools: dict[str, ToolDefinition] = {}
        self._user_tools: dict[str, dict[str, ToolDefinition]] = {}  # user_id -> {name -> tool}
        logger.info("ToolRegistry initialized")

    def register(
        self,
        name: str,
        description: str,
        func: Any,
        user_ctx: UserContext | None = None,
    ) -> None:
        """Register a tool.

        Args:
            name: Tool name
            description: Tool description
            func: Async function implementing the tool
            user_ctx: Optional user context for user-scoped tools
        """
        tool = ToolDefinition(
            name=name,
            description=description,
            func=func,
            user_ctx=user_ctx,
        )

        if user_ctx:
            # User-scoped tool
            if user_ctx.user_id not in self._user_tools:
                self._user_tools[user_ctx.user_id] = {}
            self._user_tools[user_ctx.user_id][name] = tool
            logger.info(f"Registered user tool: {name} for user {user_ctx.user_id}")
        else:
            # Global tool
            self._tools[name] = tool
            logger.info(f"Registered global tool: {name}")

    def get_tools(self, user_ctx: UserContext | None = None) -> list[ToolDefinition]:
        """Get all tools available for a user.

        Args:
            user_ctx: User context (optional)

        Returns:
            List of tool definitions
        """
        tools = list(self._tools.values())

        # Add user-specific tools
        if user_ctx and user_ctx.user_id in self._user_tools:
            tools.extend(self._user_tools[user_ctx.user_id].values())

        return tools

    def get_tool(self, name: str, user_ctx: UserContext | None = None) -> ToolDefinition | None:
        """Get a specific tool by name.

        Args:
            name: Tool name
            user_ctx: User context (optional)

        Returns:
            Tool definition or None if not found
        """
        # Check user-specific tools first
        if user_ctx and user_ctx.user_id in self._user_tools:
            if name in self._user_tools[user_ctx.user_id]:
                return self._user_tools[user_ctx.user_id][name]

        # Check global tools
        return self._tools.get(name)

    def unregister(self, name: str, user_ctx: UserContext | None = None) -> bool:
        """Unregister a tool.

        Args:
            name: Tool name
            user_ctx: Optional user context for user-scoped tools

        Returns:
            True if tool was removed, False if not found
        """
        if user_ctx and user_ctx.user_id in self._user_tools:
            if name in self._user_tools[user_ctx.user_id]:
                del self._user_tools[user_ctx.user_id][name]
                logger.info(f"Unregistered user tool: {name}")
                return True

        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered global tool: {name}")
            return True

        return False
