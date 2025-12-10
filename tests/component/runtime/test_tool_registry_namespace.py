"""Component tests for ToolRegistry + NamespaceBuilder integration."""

import pytest

from smartcp.runtime.namespace import NamespaceBuilder
from smartcp.runtime.tools.registry import ToolRegistry
from smartcp.runtime.types import NamespaceConfig, UserContext


class TestToolRegistryNamespaceIntegration:
    """Component tests for ToolRegistry and NamespaceBuilder."""

    @pytest.fixture
    def registry(self):
        """Create a tool registry."""
        registry = ToolRegistry()

        async def tool1(param: str) -> dict:
            return {"result": f"tool1: {param}"}

        async def tool2(x: int, y: int) -> dict:
            return {"result": x + y}

        registry.register("tool1", "Tool 1", tool1)
        registry.register("tool2", "Tool 2", tool2)
        return registry

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user")

    @pytest.mark.asyncio
    async def test_tools_in_namespace(self, registry, user_ctx):
        """Test that registered tools appear in namespace."""
        config = NamespaceConfig(include_tools=True)
        builder = NamespaceBuilder(config, user_ctx, registry)

        namespace = await builder.build()

        assert "tool1" in namespace
        assert "tool2" in namespace

        # Test calling tools
        result1 = await namespace["tool1"]("test")
        assert result1["result"] == "tool1: test"

        result2 = await namespace["tool2"](5, 3)
        assert result2["result"] == 8

    @pytest.mark.asyncio
    async def test_user_scoped_tools(self, registry, user_ctx):
        """Test user-scoped tools in namespace."""
        user1 = UserContext(user_id="user1")
        user2 = UserContext(user_id="user2")

        async def user_tool() -> dict:
            return {"user": "specific"}

        registry.register("user_tool", "User tool", user_tool, user1)

        # Build namespace for user1
        config = NamespaceConfig(include_tools=True)
        builder1 = NamespaceBuilder(config, user1, registry)
        namespace1 = await builder1.build()

        assert "user_tool" in namespace1

        # Build namespace for user2 (should not have user_tool)
        builder2 = NamespaceBuilder(config, user2, registry)
        namespace2 = await builder2.build()

        assert "user_tool" not in namespace2
