"""Fixtures for SmartCP SDK integration tests."""

import pytest
import asyncio
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_mcp_server():
    """Mock MCP server for testing."""
    server = MagicMock()
    server.name = "test-mcp-server"
    server.version = "1.0.0"
    return server


@pytest.fixture
def mock_bifrost_client():
    """Mock BifrostClient for SmartCP tests."""
    client = AsyncMock()

    async def mock_route(*args, **kwargs):
        return {
            "model": {
                "model_id": "claude-sonnet-4",
                "provider": "anthropic",
                "estimated_cost_usd": 0.005,
                "estimated_latency_ms": 200,
            },
            "confidence": 0.9,
        }

    client.route = mock_route
    return client


@pytest.fixture
def sample_graphql_query():
    """Sample GraphQL query for testing."""
    return """
    query GetUser($id: ID!) {
        user(id: $id) {
            id
            name
            email
        }
    }
    """


@pytest.fixture
def sample_graphql_mutation():
    """Sample GraphQL mutation for testing."""
    return """
    mutation CreateEntity($input: EntityInput!) {
        createEntity(input: $input) {
            id
            name
            created_at
        }
    }
    """


@pytest.fixture
def sample_tool_definition():
    """Sample MCP tool definition."""
    return {
        "name": "test_tool",
        "description": "A test tool for integration testing",
        "input_schema": {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "integer"},
            },
            "required": ["param1"],
        },
    }


@pytest.fixture
def auth_config():
    """Authentication configuration for testing."""
    return {
        "oauth": {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "auth_url": "https://auth.example.com/oauth/authorize",
            "token_url": "https://auth.example.com/oauth/token",
        },
        "api_key": {
            "header_name": "X-API-Key",
            "key_value": "test-api-key",
        },
    }


@pytest.fixture
def sandbox_config():
    """Sandbox configuration for testing."""
    return {
        "enabled": True,
        "timeout_seconds": 30,
        "max_memory_mb": 512,
        "allowed_imports": ["os", "json", "datetime"],
        "blocked_imports": ["subprocess", "socket"],
    }


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


@pytest.fixture
def subscription_config():
    """Subscription configuration for testing."""
    return {
        "enabled": True,
        "transports": ["websocket", "sse"],
        "max_connections": 100,
        "keepalive_interval": 30,
    }


@pytest.fixture(scope="function")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()
