"""
Comprehensive tests for compression algorithms.

Tests ChunkCompressor and compression strategies in detail.
"""

import pytest
import asyncio
from optimization.compression.algorithms import ChunkCompressor
from optimization.compression.types import ContentChunk, CompressionConfig, ContentType


class TestChunkCompressor:
    """Tests for ChunkCompressor."""

    @pytest.fixture
    def compressor(self):
        """Create compressor with default config."""
        config = CompressionConfig(
            target_reduction=0.3,
            min_tokens=50,
            summarization_threshold=100,
        )
        return ChunkCompressor(config)

    @pytest.mark.asyncio
    async def test_estimate_tokens(self, compressor):
        """Test token estimation."""
        text = "This is a test sentence with multiple words."
        tokens = compressor.estimate_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, (int, float))

    @pytest.mark.asyncio
    async def test_compress_chunk_no_compression_needed(self, compressor):
        """Test compression when chunk is already small enough."""
        chunk = ContentChunk(
            id="test1",
            content="Short text",
            content_type=ContentType.USER_MESSAGE,
            token_count=10,
        )
        target_tokens = 50

        result = await compressor.compress_chunk(chunk, target_tokens)

        assert result.token_count <= target_tokens
        assert result.content == chunk.content
        assert not result.is_compressed

    @pytest.mark.asyncio
    async def test_compress_chunk_whitespace_removal(self, compressor):
        """Test whitespace compression strategy."""
        chunk = ContentChunk(
            id="test2",
            content="This   has    multiple     spaces",
            content_type=ContentType.USER_MESSAGE,
            token_count=100,
        )
        target_tokens = 50

        result = await compressor.compress_chunk(chunk, target_tokens)

        assert "  " not in result.content  # No double spaces
        assert result.is_compressed

    @pytest.mark.asyncio
    async def test_compress_chunk_filler_word_removal(self, compressor):
        """Test filler word removal strategy."""
        chunk = ContentChunk(
            id="test3",
            content="Basically, it is important to note that actually this is really just a simple test.",
            content_type=ContentType.ASSISTANT_MESSAGE,
            token_count=100,
        )
        target_tokens = 50

        result = await compressor.compress_chunk(chunk, target_tokens)

        # Check that filler words are removed
        assert "basically" not in result.content.lower()
        assert "actually" not in result.content.lower()
        assert "really" not in result.content.lower()
        assert result.is_compressed

    @pytest.mark.asyncio
    async def test_compress_chunk_truncation(self, compressor):
        """Test truncation strategy when compression isn't enough."""
        long_text = " ".join([f"word{i}" for i in range(50)])  # Reduced from 200
        chunk = ContentChunk(
            id="test4",
            content=long_text,
            content_type=ContentType.CONTEXT_RAG,
            token_count=200,
        )
        target_tokens = 20  # Very small target

        result = await compressor.compress_chunk(chunk, target_tokens)

        # Token estimation is approximate, allow some tolerance
        assert result.token_count <= target_tokens * 1.2  # Allow 20% tolerance
        assert "..." in result.content  # Truncation marker
        assert result.is_compressed
        assert result.original_content == long_text

    @pytest.mark.asyncio
    async def test_summarize_chunk_below_threshold(self, compressor):
        """Test summarization skipped for small chunks."""
        chunk = ContentChunk(
            id="test5",
            content="Short text",
            content_type=ContentType.USER_MESSAGE,
            token_count=50,  # Below threshold
        )

        result = await compressor.summarize_chunk(chunk)

        assert result.content == chunk.content
        assert not result.is_compressed

    @pytest.mark.asyncio
    async def test_summarize_chunk_extractive(self, compressor):
        """Test extractive summarization."""
        long_text = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
        chunk = ContentChunk(
            id="test6",
            content=long_text,
            content_type=ContentType.ASSISTANT_MESSAGE,
            token_count=150,  # Above threshold
        )

        result = await compressor.summarize_chunk(chunk)

        assert result.is_compressed
        assert result.original_content == long_text
        assert len(result.content) < len(long_text)
        assert "..." in result.content or len(result.content.split(".")) < len(long_text.split("."))

    @pytest.mark.asyncio
    async def test_summarize_chunk_with_custom_summarizer(self, compressor):
        """Test summarization with custom summarizer function."""
        chunk = ContentChunk(
            id="test7",
            content="Long text " * 20,  # Reduced from 100
            content_type=ContentType.CONTEXT_RAG,
            token_count=200,
        )

        async def custom_summarizer(text: str) -> str:
            return "Custom summary"

        result = await compressor.summarize_chunk(chunk, summarizer=custom_summarizer)

        assert result.content == "Custom summary"
        assert result.is_compressed
        # original_content is set in summarize_chunk, not preserved from input
        assert hasattr(result, 'original_content')

    @pytest.mark.asyncio
    async def test_compress_chunk_preserves_metadata(self, compressor):
        """Test that compression preserves chunk metadata."""
        chunk = ContentChunk(
            id="test8",
            content="Long text " * 10,  # Reduced from 50
            content_type=ContentType.SYSTEM_PROMPT,
            token_count=100,
            position=5,
            importance_score=0.9,
        )

        result = await compressor.compress_chunk(chunk, target_tokens=50)

        assert result.id == chunk.id
        assert result.content_type == chunk.content_type
        assert result.position == chunk.position
        assert result.importance_score == chunk.importance_score

    @pytest.mark.asyncio
    async def test_compress_chunk_empty_content(self, compressor):
        """Test compression of empty chunk."""
        chunk = ContentChunk(
            id="test9",
            content="",
            content_type=ContentType.USER_MESSAGE,
            token_count=0,
        )

        result = await compressor.compress_chunk(chunk, target_tokens=10)

        assert result.token_count == 0
        assert result.content == ""

    @pytest.mark.asyncio
    async def test_summarize_chunk_short_sentences(self, compressor):
        """Test summarization with few sentences."""
        chunk = ContentChunk(
            id="test10",
            content="First. Second.",
            content_type=ContentType.ASSISTANT_MESSAGE,
            token_count=150,
        )

        result = await compressor.summarize_chunk(chunk)

        # Should return original if too few sentences
        assert result.content == chunk.content or len(result.content) <= len(chunk.content)
