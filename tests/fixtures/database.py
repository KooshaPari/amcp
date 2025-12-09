"""Database adapter fixtures for testing.

Provides fixtures for database adapters and related utilities:
- Neo4j adapter with mock driver
- Utility helpers (UTC timestamps, result summaries)
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock


def utcnow() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class _MockCounters:
    """Simple counters mock that provides empty __dict__."""

    pass


def create_result_summary(query_type: str = "r") -> MagicMock:
    """Create a mock result summary with properly configured counters.

    Uses a simple object for counters since MagicMock has issues with
    __dict__ manipulation in Python 3.13.
    """
    mock_counters = _MockCounters()
    return MagicMock(counters=mock_counters, query_type=query_type)


@pytest.fixture
def adapter():
    """Create adapter with mocked driver for testing."""
    try:
        from neo4j_adapter import Neo4jStorageAdapter, Neo4jConfig

        config = Neo4jConfig(uri="bolt://localhost:7687", username="neo4j", password="test")
        adapter = Neo4jStorageAdapter(config)
        return adapter
    except ImportError:
        # If neo4j_adapter not available, return None
        return None
