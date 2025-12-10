"""Tests for namespace builder."""

import pytest

from smartcp.runtime.namespace import NamespaceBuilder
from smartcp.runtime.types import NamespaceConfig, UserContext


@pytest.fixture
def user_ctx():
    """Create test user context."""
    return UserContext(user_id="test-user")


@pytest.mark.asyncio
async def test_build_namespace_basic(user_ctx):
    """Test building basic namespace."""
    config = NamespaceConfig(
        include_tools=True,
        include_scope=True,
        include_mcp=False,
        include_skills=False,
        include_background=False,
    )

    builder = NamespaceBuilder(config, user_ctx)
    namespace = await builder.build()

    assert "scope" in namespace
    assert "tool" in namespace


@pytest.mark.asyncio
async def test_build_namespace_with_scope(user_ctx):
    """Test namespace includes scope API."""
    config = NamespaceConfig(include_scope=True)
    builder = NamespaceBuilder(config, user_ctx)
    namespace = await builder.build()

    assert "scope" in namespace
    scope = namespace["scope"]
    assert hasattr(scope, "session")
    assert hasattr(scope, "permanent")


@pytest.mark.asyncio
async def test_build_namespace_with_mcp(user_ctx):
    """Test namespace includes MCP API."""
    config = NamespaceConfig(include_mcp=True)
    builder = NamespaceBuilder(config, user_ctx)
    namespace = await builder.build()

    assert "mcp" in namespace
    mcp = namespace["mcp"]
    assert hasattr(mcp, "search")
    assert hasattr(mcp, "install")
    assert hasattr(mcp, "servers")


@pytest.mark.asyncio
async def test_build_namespace_with_skills(user_ctx):
    """Test namespace includes skills API."""
    config = NamespaceConfig(include_skills=True)
    builder = NamespaceBuilder(config, user_ctx)
    namespace = await builder.build()

    assert "skills" in namespace
    skills = namespace["skills"]
    assert hasattr(skills, "load")
    assert hasattr(skills, "save")
    assert hasattr(skills, "list")


@pytest.mark.asyncio
async def test_build_namespace_with_background(user_ctx):
    """Test namespace includes background task API."""
    config = NamespaceConfig(include_background=True)
    builder = NamespaceBuilder(config, user_ctx)
    namespace = await builder.build()

    assert "bg" in namespace
    assert "events" in namespace
    assert "agents" in namespace

    bg = namespace["bg"]
    assert callable(bg)


@pytest.mark.asyncio
async def test_build_namespace_with_tool_decorator(user_ctx):
    """Test namespace includes tool decorator."""
    config = NamespaceConfig(include_tools=True)
    builder = NamespaceBuilder(config, user_ctx)
    namespace = await builder.build()

    assert "tool" in namespace
    tool_decorator = namespace["tool"]
    assert callable(tool_decorator)
