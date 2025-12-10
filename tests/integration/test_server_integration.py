"""Integration tests for server integration."""

import pytest

from smartcp.runtime import AgentRuntime
from smartcp.server import SmartCPServer
from smartcp.tools.execute import get_runtime


class TestServerIntegration:
    """Integration tests for server and runtime."""

    @pytest.fixture
    def server(self):
        """Create a server instance."""
        return SmartCPServer.create()

    def test_server_creates_runtime(self, server):
        """Test that server creates and wires runtime."""
        assert hasattr(server, "runtime")
        assert isinstance(server.runtime, AgentRuntime)

    def test_runtime_wired_to_tools(self, server):
        """Test that runtime is wired to tools module."""
        runtime = get_runtime()
        assert runtime is server.runtime

    def test_server_has_mcp(self, server):
        """Test that server has MCP instance."""
        assert hasattr(server, "mcp")
        assert server.mcp is not None
