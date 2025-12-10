"""Unit tests for NamespaceBuilder."""

import pytest

from smartcp.runtime.namespace import NamespaceBuilder
from smartcp.runtime.tools.registry import ToolRegistry
from smartcp.runtime.types import NamespaceConfig, UserContext


class TestNamespaceBuilder:
    """Unit tests for NamespaceBuilder."""

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user")

    @pytest.fixture
    def tool_registry(self):
        """Create a tool registry."""
        registry = ToolRegistry()
        # Register a test tool
        async def test_tool(param: str) -> dict:
            return {"result": param}

        registry.register("test_tool", "Test tool", test_tool)
        return registry

    @pytest.mark.asyncio
    async def test_build_basic_namespace(self, user_ctx):
        """Test building basic namespace."""
        config = NamespaceConfig(include_tools=False, include_scope=False)
        builder = NamespaceBuilder(config, user_ctx)

        namespace = await builder.build()
        assert isinstance(namespace, dict)

    @pytest.mark.asyncio
    async def test_build_with_tools(self, user_ctx, tool_registry):
        """Test building namespace with tools."""
        config = NamespaceConfig(include_tools=True)
        builder = NamespaceBuilder(config, user_ctx, tool_registry)

        namespace = await builder.build()
        assert "test_tool" in namespace
        assert callable(namespace["test_tool"])

    @pytest.mark.asyncio
    async def test_build_with_scope(self, user_ctx):
        """Test building namespace with scope API."""
        config = NamespaceConfig(include_scope=True)
        builder = NamespaceBuilder(config, user_ctx)

        namespace = await builder.build()
        assert "scope" in namespace
        assert hasattr(namespace["scope"], "session")

    @pytest.mark.asyncio
    async def test_build_with_mcp(self, user_ctx):
        """Test building namespace with MCP API."""
        config = NamespaceConfig(include_mcp=True)
        builder = NamespaceBuilder(config, user_ctx)

        namespace = await builder.build()
        assert "mcp" in namespace
        assert hasattr(namespace["mcp"], "search")
        assert hasattr(namespace["mcp"], "servers")

    @pytest.mark.asyncio
    async def test_build_with_skills(self, user_ctx):
        """Test building namespace with skills API."""
        config = NamespaceConfig(include_skills=True)
        builder = NamespaceBuilder(config, user_ctx)

        namespace = await builder.build()
        assert "skills" in namespace
        assert hasattr(namespace["skills"], "load")
        assert hasattr(namespace["skills"], "save")

    @pytest.mark.asyncio
    async def test_build_with_background(self, user_ctx):
        """Test building namespace with background tasks."""
        config = NamespaceConfig(include_background=True)
        builder = NamespaceBuilder(config, user_ctx)

        namespace = await builder.build()
        assert "bg" in namespace
        assert callable(namespace["bg"])
        assert "events" in namespace
        assert "agents" in namespace

    @pytest.mark.asyncio
    async def test_build_with_tool_decorator(self, user_ctx, tool_registry):
        """Test building namespace with tool decorator."""
        config = NamespaceConfig(include_tools=True)
        builder = NamespaceBuilder(config, user_ctx, tool_registry)

        namespace = await builder.build()
        assert "tool" in namespace
        assert callable(namespace["tool"])

    @pytest.mark.asyncio
    async def test_tool_wrapping(self, user_ctx, tool_registry):
        """Test that tools are wrapped correctly."""
        config = NamespaceConfig(include_tools=True)
        builder = NamespaceBuilder(config, user_ctx, tool_registry)

        namespace = await builder.build()

        # Call the wrapped tool
        result = await namespace["test_tool"]("hello")
        assert result["result"] == "hello"
