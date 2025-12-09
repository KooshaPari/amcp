"""Tests for Voyage AI client."""

import pytest
from unittest.mock import AsyncMock, patch
from services.embeddings import InputType


class TestVoyageAIClient:
    """Test Voyage AI client."""

    def test_client_initialization(self, voyage_client):
        """Test client initialization."""
        assert voyage_client.config.api_key == "test-api-key"
        assert voyage_client._rate_limiter is not None

    @pytest.mark.asyncio
    async def test_embed_single_text(self, voyage_client):
        """Test embedding single text."""
        mock_response = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}],
            "model": "voyage-3",
            "usage": {"total_tokens": 10}
        }

        with patch.object(
            voyage_client, '_make_request', new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await voyage_client.embed("Test text", use_cache=False)

            assert len(result.embedding) == 3
            assert result.usage["total_tokens"] == 10

    @pytest.mark.asyncio
    async def test_embed_with_input_type(self, voyage_client):
        """Test embedding with input type specified."""
        mock_response = {
            "data": [{"embedding": [0.1]}],
            "model": "voyage-3",
            "usage": {"total_tokens": 5}
        }

        with patch.object(
            voyage_client, '_make_request', new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await voyage_client.embed(
                "Test query", input_type=InputType.QUERY, use_cache=False
            )

            mock_request.assert_called_once()
            assert result.embedding == [0.1]

    @pytest.mark.asyncio
    async def test_embed_batch(self, voyage_client):
        """Test batch embedding."""
        texts = ["Text 1", "Text 2", "Text 3"]
        mock_response = {
            "data": [
                {"embedding": [0.1]},
                {"embedding": [0.2]},
                {"embedding": [0.3]}
            ],
            "model": "voyage-3",
            "usage": {"total_tokens": 15}
        }

        with patch.object(
            voyage_client, '_make_request', new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await voyage_client.embed_batch(texts, use_cache=False)

            assert len(result.embeddings) == 3
            assert result.total_tokens == 15

    @pytest.mark.asyncio
    async def test_rerank(self, voyage_client):
        """Test document reranking."""
        query = "What is machine learning?"
        documents = [
            "Machine learning is a subset of AI",
            "Cooking is an art form",
            "Deep learning uses neural networks"
        ]

        mock_response = {
            "data": [
                {"index": 0, "relevance_score": 0.95},
                {"index": 2, "relevance_score": 0.85},
                {"index": 1, "relevance_score": 0.1}
            ],
            "model": "rerank-2",
            "usage": {"total_tokens": 50}
        }

        with patch.object(
            voyage_client, '_make_request', new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            results = await voyage_client.rerank(query, documents)

            assert len(results) == 3
            assert results[0].relevance_score == 0.95

    @pytest.mark.asyncio
    async def test_rerank_with_top_k(self, voyage_client):
        """Test reranking with top_k limit."""
        mock_response = {
            "data": [
                {"index": 0, "relevance_score": 0.9},
                {"index": 1, "relevance_score": 0.8}
            ],
            "model": "rerank-2",
            "usage": {"total_tokens": 30}
        }

        with patch.object(
            voyage_client, '_make_request', new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            results = await voyage_client.rerank(
                "query", ["doc1", "doc2", "doc3"], top_k=2
            )

            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_client_close(self, voyage_client):
        """Test client cleanup."""
        # Initialize http client by calling embed
        mock_response = {
            "data": [{"embedding": [0.1]}],
            "model": "voyage-3",
            "usage": {"total_tokens": 5}
        }

        with patch.object(
            voyage_client, '_make_request', new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response
            await voyage_client.embed("test", use_cache=False)

        # Close should not raise
        await voyage_client.close()
        assert voyage_client._http_client is None
