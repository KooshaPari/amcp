"""
Tests for search operations.

Tests semantic search functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch

from infrastructure.bifrost.queries import SearchResult


class TestSearch:
    """Test search operations."""

    @pytest.mark.asyncio
    async def test_semantic_search(self, bifrost_client_instance):
        """Test semantic search."""
        client = bifrost_client_instance
        mock_data = {
            "semanticSearch": [
                {
                    "id": "1",
                    "content": "Project documentation",
                    "metadata": {"type": "document"},
                    "score": 0.95
                },
                {
                    "id": "2",
                    "content": "Related project",
                    "metadata": {"type": "entity"},
                    "score": 0.82
                }
            ]
        }

        with patch.object(client, "query", AsyncMock(return_value=mock_data)):
            results = await client.semantic_search(
                query="project information",
                limit=10,
                filters={"workspace_id": "123"}
            )

            assert len(results) == 2
            assert isinstance(results[0], SearchResult)
            assert results[0].id == "1"
            assert results[0].score == 0.95
            assert results[0].metadata["type"] == "document"
