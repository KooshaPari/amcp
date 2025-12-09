"""Tests for batch operations."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from neo4j_storage_adapter import Neo4jConnectionState


class TestBatchOperations:
    """Test batch operations."""

    @pytest.mark.asyncio
    async def test_batch_create_entities(self, adapter):
        """Test batch entity creation."""
        entities_data = [
            (["Person"], {"name": "Alice"}),
            (["Person"], {"name": "Bob"}),
            (["Person"], {"name": "Charlie"}),
        ]

        mock_session = AsyncMock()
        mock_tx = AsyncMock()
        mock_tx.run = AsyncMock()
        mock_tx.commit = AsyncMock()
        mock_tx.__aenter__ = AsyncMock(return_value=mock_tx)
        mock_tx.__aexit__ = AsyncMock(return_value=None)

        mock_session.begin_transaction = MagicMock(return_value=mock_tx)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        adapter._driver = MagicMock()
        adapter._driver.session = MagicMock(return_value=mock_session)
        adapter._state = Neo4jConnectionState.CONNECTED

        entities = await adapter.batch_create_entities(entities_data)

        assert len(entities) == 3

    @pytest.mark.asyncio
    async def test_batch_create_relationships(self, adapter):
        """Test batch relationship creation."""
        relationships_data = [
            ("a", "b", "KNOWS", None),
            ("b", "c", "KNOWS", None),
        ]

        mock_session = AsyncMock()
        mock_tx = AsyncMock()
        mock_tx.run = AsyncMock()
        mock_tx.commit = AsyncMock()
        mock_tx.__aenter__ = AsyncMock(return_value=mock_tx)
        mock_tx.__aexit__ = AsyncMock(return_value=None)

        mock_session.begin_transaction = MagicMock(return_value=mock_tx)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        adapter._driver = MagicMock()
        adapter._driver.session = MagicMock(return_value=mock_session)
        adapter._state = Neo4jConnectionState.CONNECTED

        relationships = await adapter.batch_create_relationships(relationships_data)

        assert len(relationships) == 2
