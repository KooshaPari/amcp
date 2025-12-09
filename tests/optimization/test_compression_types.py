"""
Tests for compression types and properties.

Tests edge cases for ContentChunk and CompressionResult properties.
"""

import pytest
from optimization.compression.types import (
    ContentChunk,
    ContentType,
    CompressionResult,
)


class TestContentChunkProperties:
    """Tests for ContentChunk properties."""

    def test_content_chunk_compression_ratio_edge_cases(self):
        """Test ContentChunk.compression_ratio property edge cases (lines 79-83)."""
        # Test 1: original_content is None → should return 1.0
        chunk1 = ContentChunk(
            id="test1",
            content="compressed content",
            content_type=ContentType.USER_MESSAGE,
            token_count=10,
            position=0,
        )
        chunk1.original_content = None
        assert chunk1.compression_ratio == 1.0

        # Test 2: original_content is empty string → should return 1.0
        chunk2 = ContentChunk(
            id="test2",
            content="compressed",
            content_type=ContentType.USER_MESSAGE,
            token_count=5,
            position=0,
        )
        chunk2.original_content = ""
        assert chunk2.compression_ratio == 1.0

        # Test 3: original_len == 0 → should return 1.0
        chunk3 = ContentChunk(
            id="test3",
            content="compressed",
            content_type=ContentType.USER_MESSAGE,
            token_count=5,
            position=0,
        )
        chunk3.original_content = ""  # len = 0
        assert chunk3.compression_ratio == 1.0

        # Test 4: Normal compression case
        chunk4 = ContentChunk(
            id="test4",
            content="compressed",  # 10 chars
            content_type=ContentType.USER_MESSAGE,
            token_count=5,
            position=0,
        )
        chunk4.original_content = "original longer content"  # 24 chars
        ratio = chunk4.compression_ratio
        expected_ratio = len("compressed") / len("original longer content")
        assert ratio == expected_ratio
        assert 0 < ratio < 1

        # Test 5: No compression (same content)
        chunk5 = ContentChunk(
            id="test5",
            content="same content",
            content_type=ContentType.USER_MESSAGE,
            token_count=5,
            position=0,
        )
        chunk5.original_content = "same content"
        assert chunk5.compression_ratio == 1.0

        # Test 6: Expansion (larger content than original)
        chunk6 = ContentChunk(
            id="test6",
            content="expanded content longer than original",
            content_type=ContentType.USER_MESSAGE,
            token_count=8,
            position=0,
        )
        chunk6.original_content = "short"
        ratio = chunk6.compression_ratio
        assert ratio > 1.0


class TestCompressionResultProperties:
    """Tests for CompressionResult properties."""

    def test_compression_result_tokens_saved(self):
        """Test CompressionResult.tokens_saved property (line 100)."""
        chunks = [
            ContentChunk(
                id="chunk1",
                content="test",
                content_type=ContentType.USER_MESSAGE,
                token_count=5,
                position=0,
            )
        ]

        result = CompressionResult(
            original_tokens=100,
            compressed_tokens=70,
            chunks=chunks,
            compression_ratio=0.7,
            preserved_importance=0.9,
        )

        assert result.tokens_saved == 30  # 100 - 70

        # Edge case: no savings
        result2 = CompressionResult(
            original_tokens=50,
            compressed_tokens=50,
            chunks=chunks,
            compression_ratio=1.0,
            preserved_importance=1.0,
        )
        assert result2.tokens_saved == 0

        # Edge case: maximum savings
        result3 = CompressionResult(
            original_tokens=200,
            compressed_tokens=0,
            chunks=chunks,
            compression_ratio=0.0,
            preserved_importance=0.5,
        )
        assert result3.tokens_saved == 200

    def test_compression_result_cost_savings_estimate(self):
        """Test CompressionResult.cost_savings_estimate property (line 105)."""
        chunks = [
            ContentChunk(
                id="chunk1",
                content="test",
                content_type=ContentType.USER_MESSAGE,
                token_count=5,
                position=0,
            )
        ]

        # Test normal case: 1000 tokens saved
        result = CompressionResult(
            original_tokens=2000,
            compressed_tokens=1000,
            chunks=chunks,
            compression_ratio=0.5,
            preserved_importance=0.9,
        )

        expected_cost = (1000 / 1000) * 0.003  # (tokens_saved / 1000) * 0.003
        assert result.cost_savings_estimate == pytest.approx(expected_cost, rel=0.001)

        # Edge case: no savings
        result2 = CompressionResult(
            original_tokens=100,
            compressed_tokens=100,
            chunks=chunks,
            compression_ratio=1.0,
            preserved_importance=1.0,
        )
        assert result2.cost_savings_estimate == 0.0

        # Edge case: fractional tokens
        result3 = CompressionResult(
            original_tokens=1550,
            compressed_tokens=750,
            chunks=chunks,
            compression_ratio=750/1550,
            preserved_importance=0.85,
        )
        expected_cost3 = (800 / 1000) * 0.003  # 800 tokens saved
        assert result3.cost_savings_estimate == pytest.approx(expected_cost3, rel=0.001)

        # Edge case: large savings
        result4 = CompressionResult(
            original_tokens=10000,
            compressed_tokens=1000,
            chunks=chunks,
            compression_ratio=0.1,
            preserved_importance=0.8,
        )
        expected_cost4 = (9000 / 1000) * 0.003  # 9000 tokens saved
        assert result4.cost_savings_estimate == pytest.approx(expected_cost4, rel=0.001)
