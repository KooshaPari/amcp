"""Consolidated test fixtures.

This module provides centralized, reusable fixtures for the test suite.
Fixtures are organized by concern:

- clients: Mock MCP/API clients
- database: Database adapters and configurations
- models: Sample data models for testing
- config: Configuration objects
"""

# Import all fixtures to make them available to pytest
from .clients import (
    mock_mcp_server,
    mock_bifrost_client,
    gateway_client,
    mock_router_service,
)
from .database import (
    adapter,
)
from .models import (
    sample_messages,
    sample_messages_simple,
    sample_messages_complex,
    sample_tools,
    sample_graphql_query,
    sample_graphql_mutation,
    sample_tool_definition,
)
from .config import (
    auth_config,
    sandbox_config,
    subscription_config,
    performance_config,
    error_scenarios,
    routing_strategies,
)

__all__ = [
    # clients
    "mock_mcp_server",
    "mock_bifrost_client",
    "gateway_client",
    "mock_router_service",
    # database
    "adapter",
    # models
    "sample_messages",
    "sample_messages_simple",
    "sample_messages_complex",
    "sample_tools",
    "sample_graphql_query",
    "sample_graphql_mutation",
    "sample_tool_definition",
    # config
    "auth_config",
    "sandbox_config",
    "subscription_config",
    "performance_config",
    "error_scenarios",
    "routing_strategies",
]
