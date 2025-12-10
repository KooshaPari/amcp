"""Unit tests for tool decorator."""

import pytest

from smartcp.runtime.tools.decorator import create_tool_decorator
from smartcp.runtime.tools.registry import ToolRegistry
from smartcp.runtime.types import UserContext


class TestToolDecorator:
    """Unit tests for tool decorator."""

    @pytest.fixture
    def registry(self):
        """Create a tool registry."""
        return ToolRegistry()

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="test-user")

    @pytest.fixture
    def tool_decorator(self, registry, user_ctx):
        """Create a tool decorator."""
        return create_tool_decorator(registry, user_ctx)

    def test_basic_decorator(self, tool_decorator, registry, user_ctx):
        """Test basic @tool decorator usage."""
        # The decorator returns a function that takes name/description
        # So we need to call it: @tool_decorator() or @tool_decorator(name="...")
        
        @tool_decorator()
        async def my_tool(param: str) -> dict:
            """My tool description."""
            return {"result": param}

        tools = registry.get_tools(user_ctx)
        assert len(tools) == 1
        assert tools[0].name == "my_tool"
        assert tools[0].description == "My tool description."

    def test_decorator_with_name(self, tool_decorator, registry, user_ctx):
        """Test decorator with explicit name."""

        @tool_decorator(name="custom_name")
        async def my_tool() -> dict:
            return {}

        tools = registry.get_tools(user_ctx)
        assert tools[0].name == "custom_name"

    def test_decorator_with_description(self, tool_decorator, registry, user_ctx):
        """Test decorator with explicit description."""

        @tool_decorator(description="Custom description")
        async def my_tool() -> dict:
            """Docstring."""
            return {}

        tools = registry.get_tools(user_ctx)
        assert tools[0].description == "Custom description"

    def test_multiple_tools(self, tool_decorator, registry, user_ctx):
        """Test registering multiple tools with decorator."""

        @tool_decorator()
        async def tool1() -> dict:
            """Tool 1."""
            return {}

        @tool_decorator()
        async def tool2() -> dict:
            """Tool 2."""
            return {}

        tools = registry.get_tools(user_ctx)
        assert len(tools) == 2
        assert {t.name for t in tools} == {"tool1", "tool2"}
