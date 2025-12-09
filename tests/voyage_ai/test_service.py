"""Tests for Voyage AI embedding service."""

import pytest
from unittest.mock import AsyncMock, patch
from services.embeddings import (
    EmbeddingResult,
    BatchEmbeddingResult,
    RerankResult,
    InputType,
)


class TestVoyageEmbeddingService:
    """Test Voyage embedding service."""

    @pytest.mark.asyncio
    async def test_embed_entity(self, embedding_service):
        """Test embedding an entity."""
        mock_result = EmbeddingResult(
            embedding=[0.1, 0.2, 0.3],
            text="Entity Name | Description",
            model="voyage-3",
            input_type="document",
            usage={"total_tokens": 10}
        )

        with patch.object(
            embedding_service.client, 'embed', new_callable=AsyncMock
        ) as mock_embed:
            mock_embed.return_value = mock_result

            result = await embedding_service.embed_entity(
                entity_id="entity-1",
                name="Entity Name",
                description="Description",
                metadata={"key": "value"}
            )

            assert len(result) == 3
            mock_embed.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_query(self, embedding_service):
        """Test embedding a query."""
        mock_result = EmbeddingResult(
            embedding=[0.4, 0.5, 0.6],
            text="search query",
            model="voyage-3",
            input_type="query",
            usage={"total_tokens": 5}
        )

        with patch.object(
            embedding_service.client, 'embed', new_callable=AsyncMock
        ) as mock_embed:
            mock_embed.return_value = mock_result

            result = await embedding_service.embed_query("search query")

            assert len(result) == 3
            mock_embed.assert_called_once()
            # Verify input_type is QUERY
            call_args = mock_embed.call_args
            assert call_args[1]["input_type"] == InputType.QUERY

    @pytest.mark.asyncio
    async def test_semantic_search(self, embedding_service):
        """Test semantic search over candidates."""
        candidates = [
            ("id1", "First document text"),
            ("id2", "Second document text"),
        ]

        # Using normalized vectors for clear cosine similarity comparison
        # Query: [1, 0, 0] - unit vector in x direction
        # Doc1: [0.9, 0.1, 0] - high similarity to query
        # Doc2: [0.1, 0.9, 0] - low similarity to query
        query_embedding = [1.0, 0.0, 0.0]
        mock_batch_result = BatchEmbeddingResult(
            embeddings=[
                EmbeddingResult(
                    embedding=[0.9, 0.1, 0.0],
                    text="First document text",
                    model="voyage-3",
                    input_type="document",
                    usage={"total_tokens": 10}
                ),
                EmbeddingResult(
                    embedding=[0.1, 0.9, 0.0],
                    text="Second document text",
                    model="voyage-3",
                    input_type="document",
                    usage={"total_tokens": 10}
                ),
            ],
            model="voyage-3",
            total_tokens=20,
            processing_time_ms=50.0
        )

        with patch.object(
            embedding_service, 'embed_query', new_callable=AsyncMock
        ) as mock_query:
            mock_query.return_value = query_embedding

            with patch.object(
                embedding_service.client, 'embed_batch', new_callable=AsyncMock
            ) as mock_batch:
                mock_batch.return_value = mock_batch_result

                results = await embedding_service.semantic_search(
                    "test query", candidates, top_k=2
                )

                assert len(results) == 2
                # First doc should be more similar (higher cosine similarity with query)
                assert results[0][0] == "id1"

    @pytest.mark.asyncio
    async def test_rerank_search_results(self, embedding_service):
        """Test reranking search results."""
        initial_results = [
            ("id1", "Document one", 0.5),
            ("id2", "Document two", 0.4),
            ("id3", "Document three", 0.3),
        ]

        mock_rerank_results = [
            RerankResult(index=1, document="Document two", relevance_score=0.95),
            RerankResult(index=0, document="Document one", relevance_score=0.8),
            RerankResult(index=2, document="Document three", relevance_score=0.3),
        ]

        with patch.object(
            embedding_service.client, 'rerank', new_callable=AsyncMock
        ) as mock_rerank:
            mock_rerank.return_value = mock_rerank_results

            results = await embedding_service.rerank_search_results(
                "query", initial_results
            )

            assert len(results) == 3
            # Document two should be first after reranking
            assert results[0][0] == "id2"
            assert results[0][2] == 0.95
