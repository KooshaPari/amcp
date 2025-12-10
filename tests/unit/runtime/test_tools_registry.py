"""Unit tests for ToolRegistry."""

import pytest

from smartcp.runtime.tools.registry import ToolRegistry
from smartcp.runtime.tools.types import ToolDefinition
from smartcp.runtime.types import UserContext


class TestToolRegistry:
    """Unit tests for ToolRegistry."""

    @pytest.fixture
    def registry(self):
        """Create a tool registry."""
        return ToolRegistry()

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user", workspace_id="ws-123")

    @pytest.fixture
    def sample_tool_func(self):
        """Create a sample tool function."""
        async def tool_func(param: str) -> dict:
            """Sample tool."""
            return {"result": param}

        return tool_func

    def test_register_tool(self, registry, sample_tool_func):
        """Test registering a tool."""
        registry.register("test_tool", "Test tool", sample_tool_func)

        tools = registry.get_tools()
        assert len(tools) == 1
        assert tools[0].name == "test_tool"
        assert tools[0].description == "Test tool"

    def test_get_tool(self, registry, sample_tool_func):
        """Test getting a tool by name."""
        registry.register("test_tool", "Test", sample_tool_func)

        tool = registry.get_tool("test_tool")
        assert tool is not None
        assert tool.name == "test_tool"

    def test_get_nonexistent_tool(self, registry):
        """Test getting a nonexistent tool."""
        tool = registry.get_tool("nonexistent")
        assert tool is None

    def test_unregister_tool(self, registry, sample_tool_func):
        """Test unregistering a tool."""
        registry.register("test_tool", "Test", sample_tool_func)

        assert len(registry.get_tools()) == 1

        # Unregister
        assert registry.unregister("test_tool") is True
        assert len(registry.get_tools()) == 0

        # Unregister again (should fail)
        assert registry.unregister("test_tool") is False

    def test_unregister_user_tool(self, registry, user_ctx, sample_tool_func):
        """Test unregistering a user-scoped tool."""
        registry.register("user_tool", "User", sample_tool_func, user_ctx)

        # Unregister user tool
        assert registry.unregister("user_tool", user_ctx) is True
        assert len(registry.get_tools(user_ctx)) == 0

        # Unregister non-existent
        assert registry.unregister("nonexistent", user_ctx) is False

    def test_get_tool_with_none_user_ctx(self, registry, sample_tool_func):
        """Test get_tool with None user_ctx for global tools."""
        registry.register("global_tool", "Global", sample_tool_func)

        tool = registry.get_tool("global_tool", None)
        assert tool is not None
        assert tool.name == "global_tool"

    def test_tool_override(self, registry, sample_tool_func):
        """Test that registering same tool twice overrides."""
        registry.register("tool", "First", sample_tool_func)
        registry.register("tool", "Second", sample_tool_func)

        tools = registry.get_tools()
        assert len(tools) == 1
        assert tools[0].description == "Second"

    def test_user_scoped_tools(self, registry, user_ctx, sample_tool_func):
        """Test user-scoped tools."""
        registry.register("user_tool", "User", sample_tool_func, user_ctx)

        # User should see their tool
        user_tools = registry.get_tools(user_ctx)
        assert len(user_tools) == 1
        assert user_tools[0].name == "user_tool"

        # Global tools should not see user tool
        global_tools = registry.get_tools()
        assert len(global_tools) == 0

    def test_get_tool_with_user_ctx(self, registry, user_ctx, sample_tool_func):
        """Test get_tool with user context."""
        registry.register("user_tool", "User", sample_tool_func, user_ctx)

        tool = registry.get_tool("user_tool", user_ctx)
        assert tool is not None
        assert tool.name == "user_tool"

    def test_get_tool_global_fallback(self, registry, sample_tool_func):
        """Test that global tools are accessible without user context."""
        registry.register("global_tool", "Global", sample_tool_func)

        # Should work with None user_ctx
        tool = registry.get_tool("global_tool", None)
        assert tool is not None

        # Should also work with a user_ctx (global tools visible to all)
        user_ctx = UserContext(user_id="other-user")
        tool = registry.get_tool("global_tool", user_ctx)
        assert tool is not None
