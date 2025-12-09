"""Fixtures for SmartCP SDK integration tests.

Imports common fixtures from tests.fixtures module. Any SmartCP-specific
fixtures can be added here.
"""

import pytest
from unittest.mock import MagicMock

# All common fixtures are imported from tests.fixtures via conftest.py


@pytest.fixture
async def mcp_server_stdio():
    """MCP server with stdio transport for testing."""
    # Mock stdio server setup
    server = MagicMock()
    server.transport = "stdio"
    server.tools = []
    return server


@pytest.fixture
async def mcp_server_http():
    """MCP server with HTTP transport for testing."""
    # Mock HTTP server setup
    server = MagicMock()
    server.transport = "http"
    server.port = 8000
    server.tools = []
    return server
