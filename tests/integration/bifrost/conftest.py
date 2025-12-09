"""Fixtures for Bifrost SDK integration tests.

Imports common fixtures from tests.fixtures module. Any Bifrost-specific
fixtures can be added here.
"""

import pytest

# All common fixtures (mock_router_service, gateway_client, sample_messages,
# sample_tools, performance_config, routing_strategies, error_scenarios) are
# imported from tests.fixtures via conftest.py


@pytest.fixture
def mock_llm_responses():
    """Mock LLM API responses for testing."""
    return {
        "classification": {
            "category": "code_generation",
            "confidence": 0.9,
            "complexity": "moderate",
        },
        "tool_routing": {
            "tool": "code_search",
            "confidence": 0.85,
            "reasoning": "Code-related query",
        },
    }
