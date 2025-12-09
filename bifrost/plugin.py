"""SmartCP Bifrost Plugin.

Provides plugin registration and lifecycle management for
SmartCP tools within the Bifrost gateway.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

from smartcp.bifrost.registry import (
    SMARTCP_TOOLS,
    ToolRegistry,
    ToolSchema,
    ParameterSchema,
)
from smartcp.infrastructure.bifrost import BifrostClient

logger = logging.getLogger(__name__)


@dataclass
class PluginConfig:
    """Configuration for SmartCP Bifrost plugin."""

    bifrost_url: str = "ws://localhost:4000/graphql"
    bifrost_api_key: str = ""
    smartcp_endpoint: str = "http://localhost:8001"
    auto_register: bool = True
    register_timeout: float = 30.0
    health_check_interval: float = 60.0
    tags: list[str] | None = None


@dataclass
class RegistrationResult:
    """Result of tool registration."""

    tool_name: str
    success: bool
    error: str | None = None


class SmartCPBifrostPlugin:
    """SmartCP plugin for Bifrost gateway integration.

    Handles:
    - Tool registration with Bifrost
    - Health monitoring
    - Event subscription
    - Lifecycle management
    """

    def __init__(
        self,
        config: PluginConfig | None = None,
        registry: ToolRegistry | None = None,
    ) -> None:
        """Initialize the plugin.

        Args:
            config: Plugin configuration
            registry: Tool registry (defaults to SMARTCP_TOOLS)
        """
        self.config = config or PluginConfig()
        self.registry = registry or SMARTCP_TOOLS
        self._client: BifrostClient | None = None
        self._registered_tools: set[str] = set()
        self._health_task: asyncio.Task | None = None
        self._running = False

    @property
    def client(self) -> BifrostClient:
        """Get or create Bifrost client."""
        if self._client is None:
            self._client = BifrostClient(
                url=self.config.bifrost_url,
                api_key=self.config.bifrost_api_key,
                timeout=self.config.register_timeout,
            )
        return self._client

    async def start(self) -> None:
        """Start the plugin.

        Connects to Bifrost and registers all tools.
        """
        if self._running:
            logger.warning("Plugin already running")
            return

        logger.info("Starting SmartCP Bifrost plugin")

        # Connect to Bifrost
        await self.client.connect()
        self._running = True

        # Auto-register tools if configured
        if self.config.auto_register:
            await self.register_all_tools()

        # Start health check task
        self._health_task = asyncio.create_task(self._health_check_loop())

        logger.info("SmartCP Bifrost plugin started")

    async def stop(self) -> None:
        """Stop the plugin.

        Disconnects from Bifrost and cleans up resources.
        """
        if not self._running:
            return

        logger.info("Stopping SmartCP Bifrost plugin")

        self._running = False

        # Cancel health check task
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
            self._health_task = None

        # Disconnect client
        if self._client:
            await self._client.disconnect()
            self._client = None

        self._registered_tools.clear()

        logger.info("SmartCP Bifrost plugin stopped")

    async def __aenter__(self) -> "SmartCPBifrostPlugin":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()

    async def register_tool(self, tool: ToolSchema) -> RegistrationResult:
        """Register a single tool with Bifrost.

        Args:
            tool: Tool schema to register

        Returns:
            Registration result
        """
        if not self._running:
            return RegistrationResult(
                tool_name=tool.name,
                success=False,
                error="Plugin not running",
            )

        try:
            # Build parameters for Bifrost
            parameters = tool.to_json_schema()

            # Add SmartCP-specific metadata
            tags = list(tool.tags)
            if self.config.tags:
                tags.extend(self.config.tags)
            tags.append("smartcp")

            # Register with Bifrost
            success = await self.client.register_tool(
                name=tool.name,
                description=tool.description,
                parameters=parameters,
                category=tool.category,
                tags=tags,
            )

            if success:
                self._registered_tools.add(tool.name)
                logger.info(f"Registered tool with Bifrost: {tool.name}")
            else:
                logger.warning(f"Failed to register tool with Bifrost: {tool.name}")

            return RegistrationResult(
                tool_name=tool.name,
                success=success,
            )

        except Exception as e:
            logger.error(f"Error registering tool {tool.name}: {e}")
            return RegistrationResult(
                tool_name=tool.name,
                success=False,
                error=str(e),
            )

    async def register_all_tools(self) -> list[RegistrationResult]:
        """Register all tools from the registry with Bifrost.

        Returns:
            List of registration results
        """
        logger.info(f"Registering {len(self.registry.all())} tools with Bifrost")

        results = []
        for tool in self.registry.all():
            result = await self.register_tool(tool)
            results.append(result)

        # Log summary
        success_count = sum(1 for r in results if r.success)
        failed_count = len(results) - success_count

        logger.info(
            f"Tool registration complete: {success_count} succeeded, {failed_count} failed"
        )

        return results

    async def register_category(self, category: str) -> list[RegistrationResult]:
        """Register all tools in a category.

        Args:
            category: Category to register (e.g., "execution", "memory", "state")

        Returns:
            List of registration results
        """
        tools = self.registry.by_category(category)
        logger.info(f"Registering {len(tools)} tools in category '{category}'")

        results = []
        for tool in tools:
            result = await self.register_tool(tool)
            results.append(result)

        return results

    async def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool from Bifrost.

        Note: This requires Bifrost to support tool unregistration.

        Args:
            tool_name: Name of tool to unregister

        Returns:
            True if successful
        """
        # Bifrost client doesn't have unregister method yet
        # This is a placeholder for future implementation
        logger.warning(
            f"Tool unregistration not implemented: {tool_name}"
        )
        self._registered_tools.discard(tool_name)
        return True

    def is_registered(self, tool_name: str) -> bool:
        """Check if a tool is registered.

        Args:
            tool_name: Tool name to check

        Returns:
            True if registered
        """
        return tool_name in self._registered_tools

    @property
    def registered_tools(self) -> set[str]:
        """Get set of registered tool names."""
        return self._registered_tools.copy()

    async def _health_check_loop(self) -> None:
        """Background task for health checking."""
        while self._running:
            try:
                await asyncio.sleep(self.config.health_check_interval)

                if not self._running:
                    break

                # Simple health check - query a tool
                try:
                    await self.client.query_tools(limit=1)
                    logger.debug("Bifrost health check passed")
                except Exception as e:
                    logger.warning(f"Bifrost health check failed: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def get_routing_decision(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get routing decision from Bifrost.

        Args:
            prompt: User prompt to route
            context: Optional context

        Returns:
            Routing decision with selected_tool, confidence, reasoning
        """
        if not self._running:
            raise RuntimeError("Plugin not running")

        decision = await self.client.route_request(prompt, context)
        return {
            "selected_tool": decision.selected_tool,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "alternatives": decision.alternatives,
        }

    async def execute_via_bifrost(
        self,
        tool_name: str,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a tool via Bifrost.

        Args:
            tool_name: Tool to execute
            input_data: Tool input parameters

        Returns:
            Execution result
        """
        if not self._running:
            raise RuntimeError("Plugin not running")

        return await self.client.execute_tool(tool_name, input_data)


def create_bifrost_plugin(
    bifrost_url: str | None = None,
    bifrost_api_key: str | None = None,
    smartcp_endpoint: str | None = None,
    auto_register: bool = True,
    registry: ToolRegistry | None = None,
) -> SmartCPBifrostPlugin:
    """Factory function to create a SmartCP Bifrost plugin.

    Args:
        bifrost_url: Bifrost GraphQL URL
        bifrost_api_key: API key for Bifrost
        smartcp_endpoint: SmartCP server endpoint
        auto_register: Auto-register tools on start
        registry: Optional custom tool registry

    Returns:
        Configured SmartCPBifrostPlugin instance
    """
    import os

    config = PluginConfig(
        bifrost_url=bifrost_url or os.getenv(
            "BIFROST_URL", "ws://localhost:4000/graphql"
        ),
        bifrost_api_key=bifrost_api_key or os.getenv("BIFROST_API_KEY", ""),
        smartcp_endpoint=smartcp_endpoint or os.getenv(
            "SMARTCP_ENDPOINT", "http://localhost:8001"
        ),
        auto_register=auto_register,
    )

    return SmartCPBifrostPlugin(config=config, registry=registry)


# Re-export for convenience
__all__ = [
    "SmartCPBifrostPlugin",
    "PluginConfig",
    "RegistrationResult",
    "ToolSchema",
    "ParameterSchema",
    "create_bifrost_plugin",
]
