"""Namespace builder for agent runtime execution.

Builds the execution namespace with tools, APIs, and utilities.
"""

import logging
from typing import Any, Callable

from smartcp.runtime.tools.registry import ToolRegistry
from smartcp.runtime.types import NamespaceConfig, UserContext

logger = logging.getLogger(__name__)


class NamespaceBuilder:
    """Builds execution namespace for agent code.

    Injects MCP tools, scope API, and other utilities into the
    execution namespace so agent code can call them directly.
    """

    def __init__(
        self,
        config: NamespaceConfig,
        user_ctx: UserContext,
        tool_registry: ToolRegistry | None = None,
    ):
        """Initialize namespace builder.

        Args:
            config: Namespace configuration
            user_ctx: User context for scoped operations
            tool_registry: Optional tool registry (creates new if not provided)
        """
        self.config = config
        self.user_ctx = user_ctx
        self.tool_registry = tool_registry or ToolRegistry()

    async def build(self) -> dict[str, Any]:
        """Build execution namespace.

        Returns:
            Dictionary of names available in execution context
        """
        namespace: dict[str, Any] = {}

        # Phase 1: Basic namespace (tools will be added in Phase 3)
        if self.config.include_tools:
            # Placeholder for tool registry (Phase 3)
            namespace.update(await self._build_tools())

        # Phase 2: Scope API (will be implemented in Phase 2)
        if self.config.include_scope:
            namespace["scope"] = await self._build_scope_api()

        # MCP management
        if self.config.include_mcp:
            namespace["mcp"] = await self._build_mcp_api()

        # Skills
        if self.config.include_skills:
            namespace["skills"] = await self._build_skills_api()

        # Background tasks
        if self.config.include_background:
            namespace["bg"] = await self._build_background_api()
            namespace["events"] = await self._build_events_api()
            namespace["agents"] = await self._build_agents_api()

        # Tool definition decorator
        if self.config.include_tools:
            namespace["tool"] = await self._build_tool_decorator()

        return namespace

    async def _build_tools(self) -> dict[str, Any]:
        """Build tool namespace.

        Returns:
            Dictionary of callable tools
        """
        tools = self.tool_registry.get_tools(self.user_ctx)

        # Wrap tools as callable functions
        namespace = {}
        for tool in tools:
            namespace[tool.name] = self._wrap_tool(tool)

        return namespace

    def _wrap_tool(self, tool: Any) -> Any:
        """Wrap tool function for namespace injection.

        Args:
            tool: ToolDefinition

        Returns:
            Wrapped callable function
        """
        async def wrapped(*args, **kwargs):
            """Wrapped tool function."""
            return await tool.func(*args, **kwargs)

        return wrapped

    async def _build_scope_api(self) -> Any:
        """Build scope API.

        Returns:
            Scope API object
        """
        from smartcp.runtime.scope import ScopeAPI, ScopeManager

        # Create scope manager (using in-memory storage by default)
        # In production, this would be configured from settings
        scope_manager = ScopeManager(storage_backend="memory")
        return ScopeAPI(scope_manager, self.user_ctx)

    async def _build_mcp_api(self) -> Any:
        """Build MCP management API.

        Returns:
            MCP API object
        """
        from smartcp.runtime.mcp import MCPAPI, MCPServerManager

        manager = MCPServerManager()
        return MCPAPI(manager, self.user_ctx)

    async def _build_skills_api(self) -> Any:
        """Build skills API.

        Returns:
            Skills API object
        """
        from smartcp.runtime.skills import SkillLoader, SkillsAPI

        loader = SkillLoader()
        return SkillsAPI(loader, self.user_ctx)

    async def _build_background_api(self) -> Callable:
        """Build background task API.

        Returns:
            bg() function for background tasks
        """
        from smartcp.runtime.events import NATSEventBus, create_background_task_api

        event_bus = NATSEventBus()
        return create_background_task_api(event_bus, self.user_ctx)

    async def _build_events_api(self) -> Any:
        """Build events API.

        Returns:
            Events API object
        """
        from smartcp.runtime.events import EventsAPI, NATSEventBus

        event_bus = NATSEventBus()
        return EventsAPI(event_bus, self.user_ctx)

    async def _build_agents_api(self) -> Any:
        """Build agents API.

        Returns:
            Agents API object
        """
        from smartcp.runtime.events import AgentsAPI, NATSEventBus

        event_bus = NATSEventBus()
        return AgentsAPI(event_bus, self.user_ctx)

    async def _build_tool_decorator(self) -> Callable:
        """Build @tool decorator.

        Returns:
            tool decorator function
        """
        from smartcp.runtime.tools.decorator import create_tool_decorator

        return create_tool_decorator(self.tool_registry, self.user_ctx)


# Placeholder APIs for phases not yet implemented






