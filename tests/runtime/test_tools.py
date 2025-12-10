"""Tests for tool registry."""

import pytest

from smartcp.runtime.tools import ToolRegistry
from smartcp.runtime.tools.types import ToolDefinition
from smartcp.runtime.types import UserContext


@pytest.fixture
def tool_registry():
    """Create tool registry."""
    return ToolRegistry()


@pytest.fixture
def user_ctx():
    """Create test user context."""
    return UserContext(user_id="test-user")


async def dummy_tool(param: str) -> dict:
    """Dummy tool for testing."""
    return {"result": param}


@pytest.mark.asyncio
async def test_register_global_tool(tool_registry):
    """Test registering a global tool."""
    tool_registry.register(
        name="test_tool",
        description="Test tool",
        func=dummy_tool,
    )

    tool = tool_registry.get_tool("test_tool")
    assert tool is not None
    assert tool.name == "test_tool"
    assert tool.description == "Test tool"


@pytest.mark.asyncio
async def test_register_user_tool(tool_registry, user_ctx):
    """Test registering a user-scoped tool."""
    tool_registry.register(
        name="user_tool",
        description="User tool",
        func=dummy_tool,
        user_ctx=user_ctx,
    )

    tool = tool_registry.get_tool("user_tool", user_ctx)
    assert tool is not None
    assert tool.name == "user_tool"


@pytest.mark.asyncio
async def test_get_tools(tool_registry, user_ctx):
    """Test getting all tools for a user."""
    tool_registry.register("global_tool", "Global", dummy_tool)
    tool_registry.register("user_tool", "User", dummy_tool, user_ctx=user_ctx)

    tools = tool_registry.get_tools(user_ctx)
    assert len(tools) == 2
    tool_names = [t.name for t in tools]
    assert "global_tool" in tool_names
    assert "user_tool" in tool_names


@pytest.mark.asyncio
async def test_unregister_tool(tool_registry):
    """Test unregistering a tool."""
    tool_registry.register("test_tool", "Test", dummy_tool)
    assert tool_registry.get_tool("test_tool") is not None

    success = tool_registry.unregister("test_tool")
    assert success is True
    assert tool_registry.get_tool("test_tool") is None


@pytest.mark.asyncio
async def test_tool_isolation(tool_registry):
    """Test that user tools are isolated."""
    user1 = UserContext(user_id="user1")
    user2 = UserContext(user_id="user2")

    tool_registry.register("same_name", "Tool", dummy_tool, user_ctx=user1)
    tool_registry.register("same_name", "Tool", dummy_tool, user_ctx=user2)

    tool1 = tool_registry.get_tool("same_name", user1)
    tool2 = tool_registry.get_tool("same_name", user2)

    assert tool1 is not None
    assert tool2 is not None
    assert tool1 != tool2  # Different instances
