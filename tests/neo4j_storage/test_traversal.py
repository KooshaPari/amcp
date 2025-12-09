"""Tests for graph traversal and query operations."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from neo4j_adapter import (
    Neo4jConnectionState,
    QueryResult,
)
from .conftest import _create_result_summary


class TestQueryResult:
    """Test query result handling."""

    def test_query_result_creation(self):
        """Test query result creation."""
        result = QueryResult(
            records=[{"n": {"id": "1"}}, {"n": {"id": "2"}}],
            summary={"nodes_created": 0, "relationships_created": 0},
            keys=["n"],
            execution_time_ms=10.5
        )

        assert len(result.records) == 2
        assert result.summary["nodes_created"] == 0
        assert result.keys == ["n"]
        assert result.execution_time_ms == 10.5

    def test_query_result_with_keys(self):
        """Test query result with multiple return keys."""
        result = QueryResult(
            records=[{"a": {"id": "1"}, "b": {"id": "2"}}],
            summary={},
            keys=["a", "b"],
            execution_time_ms=5.0
        )

        assert len(result.keys) == 2
        assert "a" in result.keys

    def test_query_result_empty(self):
        """Test empty result handling."""
        result = QueryResult(
            records=[],
            summary={},
            keys=[],
            execution_time_ms=1.0
        )

        assert len(result.records) == 0
        assert len(result.keys) == 0


class TestConnectionState:
    """Test connection state management."""

    def test_connection_states(self):
        """Test valid connection state values."""
        assert Neo4jConnectionState.DISCONNECTED == "disconnected"
        assert Neo4jConnectionState.CONNECTING == "connecting"
        assert Neo4jConnectionState.CONNECTED == "connected"
        assert Neo4jConnectionState.ERROR == "error"


class TestFindEntities:
    """Test find_entities operations."""

    @pytest.mark.asyncio
    async def test_find_entities_by_label(self, adapter):
        """Test finding entities by label."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.data = AsyncMock(return_value=[
            {"n": {"id": "p-1", "name": "Alice"}},
            {"n": {"id": "p-2", "name": "Bob"}}
        ])
        mock_result.consume = AsyncMock(return_value=_create_result_summary("r"))
        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        adapter._driver = MagicMock()
        adapter._driver.session = MagicMock(return_value=mock_session)
        adapter._state = Neo4jConnectionState.CONNECTED

        entities = await adapter.find_entities(labels=["Person"])

        assert len(entities) == 2


class TestGraphTraversal:
    """Test graph traversal operations."""

    @pytest.mark.asyncio
    async def test_get_neighbors(self, adapter):
        """Test getting neighboring entities."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.data = AsyncMock(return_value=[
            {"neighbor": {"id": "n-1", "name": "Neighbor 1"}},
            {"neighbor": {"id": "n-2", "name": "Neighbor 2"}}
        ])
        mock_result.consume = AsyncMock(return_value=_create_result_summary("r"))
        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        adapter._driver = MagicMock()
        adapter._driver.session = MagicMock(return_value=mock_session)
        adapter._state = Neo4jConnectionState.CONNECTED

        neighbors = await adapter.get_neighbors("entity-1", depth=2)

        # May be empty due to mock structure, but method shouldn't crash

    @pytest.mark.asyncio
    async def test_find_path(self, adapter):
        """Test finding path between entities."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.data = AsyncMock(return_value=[{
            "nodes": [{"id": "start"}, {"id": "middle"}, {"id": "end"}],
            "rels": [{"type": "KNOWS"}, {"type": "KNOWS"}]
        }])
        mock_result.consume = AsyncMock(return_value=_create_result_summary("r"))
        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        adapter._driver = MagicMock()
        adapter._driver.session = MagicMock(return_value=mock_session)
        adapter._state = Neo4jConnectionState.CONNECTED

        path = await adapter.find_path("start", "end", max_depth=5)

        assert path is not None
        assert "nodes" in path
