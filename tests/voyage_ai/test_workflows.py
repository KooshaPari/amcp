"""Tests for integration workflow scenarios."""

import pytest
from unittest.mock import AsyncMock, patch
from services.embeddings import (
    VoyageConfig,
    VoyageAIClient,
    VoyageEmbeddingService,
    EmbeddingResult,
    InputType,
)


class TestIntegrationWorkflow:
    """Test full integration workflow."""

    @pytest.mark.asyncio
    async def test_embed_cache_hit(self):
        """Test that cached embeddings are returned without API call."""
        config = VoyageConfig(api_key="test-key")
        client = VoyageAIClient(config)

        # Pre-populate cache
        await client.cache.set(
            "cached text", "voyage-3", [0.1, 0.2, 0.3], input_type=None
        )

        # Embed should return cached value without making API call
        result = await client.embed("cached text", use_cache=True)

        assert result.cached is True
        assert result.embedding == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_service_uses_correct_input_types(self):
        """Test that embedding service uses correct input types."""
        config = VoyageConfig(api_key="test-key")
        client = VoyageAIClient(config)
        service = VoyageEmbeddingService(client)

        with patch.object(client, 'embed', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = EmbeddingResult(
                embedding=[0.1],
                text="test",
                model="voyage-3",
                input_type="query",
                usage={"total_tokens": 5}
            )

            # embed_query should use InputType.QUERY
            await service.embed_query("test query")

            mock_embed.assert_called_with("test query", input_type=InputType.QUERY)

        with patch.object(client, 'embed', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = EmbeddingResult(
                embedding=[0.1],
                text="test",
                model="voyage-3",
                input_type="document",
                usage={"total_tokens": 5}
            )

            # embed_entity should use InputType.DOCUMENT
            await service.embed_entity("id", "name", "desc")

            mock_embed.assert_called_once()
            call_args = mock_embed.call_args
            assert call_args[1]["input_type"] == InputType.DOCUMENT
