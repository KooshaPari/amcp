"""Sample data model fixtures for testing.

Provides common sample data used across tests:
- Chat messages (simple, complex, multi-turn)
- Tool definitions
- GraphQL queries and mutations
- Message lists for conversation testing
"""

import pytest
from typing import List, Dict, Any


@pytest.fixture
def sample_messages() -> List[Dict[str, str]]:
    """Sample chat messages for testing."""
    try:
        from bifrost_extensions.models import Message

        return [
            Message(role="user", content="Write a Python function to parse JSON"),
            Message(role="assistant", content="Here's a function to parse JSON..."),
            Message(role="user", content="Add error handling"),
        ]
    except ImportError:
        # Fallback to dict format
        return [
            {"role": "user", "content": "Write a Python function to parse JSON"},
            {"role": "assistant", "content": "Here's a function to parse JSON..."},
            {"role": "user", "content": "Add error handling"},
        ]


@pytest.fixture
def sample_messages_simple() -> List[Dict[str, str]]:
    """Simple single message for testing."""
    try:
        from bifrost_extensions.models import Message

        return [Message(role="user", content="Hello")]
    except ImportError:
        return [{"role": "user", "content": "Hello"}]


@pytest.fixture
def sample_messages_complex() -> List[Dict[str, str]]:
    """Complex multi-turn conversation for testing."""
    try:
        from bifrost_extensions.models import Message

        return [
            Message(role="system", content="You are a helpful coding assistant"),
            Message(role="user", content="Implement a binary search tree in Python"),
            Message(role="assistant", content="Here's a basic BST implementation..."),
            Message(role="user", content="Add deletion with rebalancing"),
            Message(role="assistant", content="For deletion with rebalancing..."),
            Message(role="user", content="Optimize for cache locality"),
        ]
    except ImportError:
        return [
            {"role": "system", "content": "You are a helpful coding assistant"},
            {"role": "user", "content": "Implement a binary search tree in Python"},
            {"role": "assistant", "content": "Here's a basic BST implementation..."},
            {"role": "user", "content": "Add deletion with rebalancing"},
            {"role": "assistant", "content": "For deletion with rebalancing..."},
            {"role": "user", "content": "Optimize for cache locality"},
        ]


@pytest.fixture
def sample_tools() -> List[str]:
    """Sample tool names for testing."""
    return ["web_search", "doc_search", "code_search", "file_search"]


@pytest.fixture
def sample_graphql_query() -> str:
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
def sample_graphql_mutation() -> str:
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
def sample_tool_definition() -> Dict[str, Any]:
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
