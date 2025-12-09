"""Tests for Voyage AI + Neo4j integration."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.embeddings import EmbeddingResult, BatchEmbeddingResult


class TestVoyageNeo4jIntegration:
    """Test Voyage AI + Neo4j integration."""

    @pytest.mark.asyncio
    async def test_setup_vector_index(self, neo4j_integration):
        """Test setting up vector index in Neo4j."""
        neo4j_integration.neo4j.create_vector_index = AsyncMock(return_value=True)

        result = await neo4j_integration.setup_vector_index(
            label="Entity", dimensions=1024
        )

        assert result is True
        neo4j_integration.neo4j.create_vector_index.assert_called_once_with(
            index_name="entity_embeddings",
            label="Entity",
            property_name="embedding",
            dimensions=1024
        )

    @pytest.mark.asyncio
    async def test_index_entity(self, neo4j_integration):
        """Test indexing an entity with embedding."""
        mock_embedding = [0.1, 0.2, 0.3]

        with patch.object(
            neo4j_integration.voyage, 'embed', new_callable=AsyncMock
        ) as mock_embed:
            mock_embed.return_value = EmbeddingResult(
                embedding=mock_embedding,
                text="Test content",
                model="voyage-3",
                input_type="document",
                usage={"total_tokens": 10}
            )

            neo4j_integration.neo4j.update_entity = AsyncMock(
                return_value={"id": "entity-1"}
            )

            result = await neo4j_integration.index_entity("entity-1", "Test content")

            assert result is True
            neo4j_integration.neo4j.update_entity.assert_called_once_with(
                "entity-1",
                {"embedding": mock_embedding}
            )

    @pytest.mark.asyncio
    async def test_semantic_search(self, neo4j_integration):
        """Test semantic search through integration."""
        query = "search query"
        mock_embedding = [0.5, 0.5, 0.5]

        with patch.object(
            neo4j_integration.voyage, 'embed', new_callable=AsyncMock
        ) as mock_embed:
            mock_embed.return_value = EmbeddingResult(
                embedding=mock_embedding,
                text=query,
                model="voyage-3",
                input_type="query",
                usage={"total_tokens": 5}
            )

            mock_results = [
                (MagicMock(id="1"), 0.9),
                (MagicMock(id="2"), 0.8),
            ]
            neo4j_integration.neo4j.vector_search = AsyncMock(
                return_value=mock_results
            )

            results = await neo4j_integration.semantic_search(
                query, top_k=10, min_score=0.5
            )

            assert len(results) == 2
            neo4j_integration.neo4j.vector_search.assert_called_once_with(
                index_name="entity_embeddings",
                query_vector=mock_embedding,
                top_k=10,
                min_score=0.5
            )

    @pytest.mark.asyncio
    async def test_batch_index_entities(self, neo4j_integration):
        """Test batch indexing entities."""
        entities = [
            ("entity-1", "First entity text"),
            ("entity-2", "Second entity text"),
            ("entity-3", "Third entity text"),
        ]

        mock_embeddings = [
            EmbeddingResult(
                embedding=[0.1],
                text="First entity text",
                model="voyage-3",
                input_type="document",
                usage={"total_tokens": 5}
            ),
            EmbeddingResult(
                embedding=[0.2],
                text="Second entity text",
                model="voyage-3",
                input_type="document",
                usage={"total_tokens": 5}
            ),
            EmbeddingResult(
                embedding=[0.3],
                text="Third entity text",
                model="voyage-3",
                input_type="document",
                usage={"total_tokens": 5}
            ),
        ]
        mock_batch_result = BatchEmbeddingResult(
            embeddings=mock_embeddings,
            model="voyage-3",
            total_tokens=15,
            processing_time_ms=100.0
        )

        with patch.object(
            neo4j_integration.voyage, 'embed_batch', new_callable=AsyncMock
        ) as mock_batch:
            mock_batch.return_value = mock_batch_result

            neo4j_integration.neo4j.update_entity = AsyncMock(
                return_value={"id": "updated"}
            )

            indexed_count = await neo4j_integration.batch_index_entities(entities)

            assert indexed_count == 3
            assert neo4j_integration.neo4j.update_entity.call_count == 3
