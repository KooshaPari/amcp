"""
Shared fixtures for MCP Inference Bridge tests.

This module provides common fixtures used across all MCP inference tests.
"""

import pytest
from typing import Dict, Any, List

from mcp_inference_bridge import MCPInferenceBridge
from dsl_scope import get_dsl_scope_system


@pytest.fixture
def dsl_system():
    """Get DSL scope system instance."""
    return get_dsl_scope_system()


@pytest.fixture
def bridge(dsl_system):
    """Create MCP inference bridge."""
    return MCPInferenceBridge(dsl_system=dsl_system)


@pytest.fixture
def sample_messages() -> List[Dict[str, Any]]:
    """Sample OpenAI-format messages."""
    return [
        {
            "role": "user",
            "content": "I'm working on the MyApp project",
        },
        {
            "role": "assistant",
            "content": "Great! Let's start implementing the feature.",
        },
        {
            "role": "user",
            "content": "Let's write unit tests for the auth module",
        },
    ]


@pytest.fixture
def sample_tools() -> List[Dict[str, Any]]:
    """Sample tool definitions."""
    return [
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write content to a file",
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_tests",
                "description": "Run test suite",
            },
        },
    ]
