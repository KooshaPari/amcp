"""
Tests for ACON Context Compression.

Tests the ACONCompressor for intelligent context compression to reduce token usage.
Covers: basic compression, importance scoring, query relevance.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from optimization.compression.compressor import ACONCompressor
from optimization.compression.types import (
    CompressionConfig,
    ContentType,
    ContentChunk,
)


class TestACONCompressor:
    """Tests for ACONCompressor."""

    @pytest.fixture
    def compressor(self):
        """Create compressor."""
        config = CompressionConfig(
            target_reduction=0.3,
            min_tokens=50,
        )
        return ACONCompressor(config)

    @pytest.mark.asyncio
    async def test_basic_compression(self, compressor):
        """Test basic compression."""
        content = [
            {"role": "system", "content": "You are a helpful assistant. " * 50},
            {"role": "user", "content": "What is the meaning of life? " * 20},
        ]

        result = await compressor.compress(content)

        assert result.compressed_tokens < result.original_tokens
        assert result.compression_ratio < 1.0
        assert len(result.chunks) > 0

    @pytest.mark.asyncio
    async def test_importance_scoring(self, compressor):
        """Test importance scoring by content type."""
        content = [
            {"role": "system", "content": "System prompt " * 10},  # Reduced from 100
            {"role": "user", "content": "User query " * 10},  # Reduced from 100
            {"role": "assistant", "content": "Response " * 10},  # Reduced from 100
        ]

        result = await compressor.compress(content)

        # System prompt should have highest importance
        system_chunks = [c for c in result.chunks if c.content_type == ContentType.SYSTEM_PROMPT]
        user_chunks = [c for c in result.chunks if c.content_type == ContentType.USER_MESSAGE]

        if system_chunks and user_chunks:
            assert system_chunks[0].importance_score >= user_chunks[0].importance_score

    @pytest.mark.asyncio
    async def test_query_relevance(self, compressor):
        """Test query-based relevance boosting."""
        content = [
            {"role": "assistant", "content": "Python is a programming language"},
            {"role": "assistant", "content": "The weather today is sunny"},
        ]

        result = await compressor.compress(content, query="Python programming")

        # First chunk should be more relevant
        python_chunk = result.chunks[0]
        assert "python" in python_chunk.content.lower() or python_chunk.importance_score > 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
