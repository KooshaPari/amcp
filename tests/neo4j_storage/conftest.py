"""Shared fixtures for Neo4j storage adapter tests.

Imports common database fixtures from tests.fixtures module.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock


def _utcnow() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class _MockCounters:
    """Simple counters mock that provides empty __dict__."""
    pass


def _create_result_summary(query_type: str = "r") -> MagicMock:
    """Create a mock result summary with properly configured counters."""
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
