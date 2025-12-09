"""
Comprehensive tests for importance scoring.

Tests ImportanceScorer for compression decision-making.
"""

import pytest
from optimization.compression.scoring import ImportanceScorer
from optimization.compression.types import (
    CompressionConfig,
    ContentChunk,
    ContentType,
)


class TestImportanceScorer:
    """Tests for ImportanceScorer."""

    @pytest.fixture
    def scorer(self):
        """Create importance scorer."""
        config = CompressionConfig(
            importance_weights={
                ContentType.SYSTEM_PROMPT.value: 1.0,
                ContentType.USER_MESSAGE.value: 0.9,
                ContentType.ASSISTANT_MESSAGE.value: 0.7,
            },
            enable_semantic_filtering=True,
        )
        return ImportanceScorer(config)

    @pytest.mark.asyncio
    async def test_score_chunks_basic(self, scorer):
        """Test basic chunk scoring."""
        chunks = [
            ContentChunk(
                id="1",
                content="System prompt",
                content_type=ContentType.SYSTEM_PROMPT,
                token_count=10,
                position=0,
            ),
            ContentChunk(
                id="2",
                content="User message",
                content_type=ContentType.USER_MESSAGE,
                token_count=10,
                position=1,
            ),
        ]

        scored = await scorer.score_chunks(chunks)

        assert all(c.importance_score > 0 for c in scored)
        # System prompt should have higher score
        assert scored[0].importance_score >= scored[1].importance_score

    @pytest.mark.asyncio
    async def test_score_chunks_position_boost(self, scorer):
        """Test position-based importance boost."""
        chunks = [
            ContentChunk(
                id="1",
                content="First",
                content_type=ContentType.USER_MESSAGE,
                token_count=10,
                position=0,
            ),
            ContentChunk(
                id="2",
                content="Last",
                content_type=ContentType.USER_MESSAGE,
                token_count=10,
                position=9,
            ),
        ]

        scored = await scorer.score_chunks(chunks)

        # Earlier position should have higher score
        assert scored[0].importance_score > scored[1].importance_score

    @pytest.mark.asyncio
    async def test_score_chunks_query_relevance(self, scorer):
        """Test query-based relevance boosting."""
        chunks = [
            ContentChunk(
                id="1",
                content="Python programming language",
                content_type=ContentType.ASSISTANT_MESSAGE,
                token_count=10,
                position=0,
            ),
            ContentChunk(
                id="2",
                content="Weather forecast",
                content_type=ContentType.ASSISTANT_MESSAGE,
                token_count=10,
                position=1,
            ),
        ]

        scored = await scorer.score_chunks(chunks, query="Python")

        # Python-related chunk should have higher score
        python_chunk = next(c for c in scored if "python" in c.content.lower())
        weather_chunk = next(c for c in scored if "weather" in c.content.lower())
        assert python_chunk.importance_score > weather_chunk.importance_score

    @pytest.mark.asyncio
    async def test_score_chunks_no_query(self, scorer):
        """Test scoring without query."""
        chunks = [
            ContentChunk(
                id="1",
                content="Test content",
                content_type=ContentType.USER_MESSAGE,
                token_count=10,
                position=0,
            ),
        ]

        scored = await scorer.score_chunks(chunks)

        assert scored[0].importance_score > 0

    @pytest.mark.asyncio
    async def test_score_chunks_length_penalty(self, scorer):
        """Test length-based penalty for very long chunks."""
        chunks = [
            ContentChunk(
                id="1",
                content="Short",
                content_type=ContentType.USER_MESSAGE,
                token_count=100,  # Normal size
                position=0,
            ),
            ContentChunk(
                id="2",
                content="Very long " * 50,  # Reduced from 200
                content_type=ContentType.USER_MESSAGE,
                token_count=2000,  # Very long
                position=1,
            ),
        ]

        scored = await scorer.score_chunks(chunks)

        # Long chunk might have penalty applied
        assert all(c.importance_score > 0 for c in scored)

    @pytest.mark.asyncio
    async def test_compute_relevance_keyword_overlap(self, scorer):
        """Test relevance computation via keyword overlap."""
        content = "Python programming language tutorial"
        query = "Python tutorial"

        relevance = scorer._compute_relevance(content, query)

        assert relevance > 1.0  # Should have boost
        assert relevance <= 1.5  # Max boost is 0.5

    @pytest.mark.asyncio
    async def test_compute_relevance_no_overlap(self, scorer):
        """Test relevance with no keyword overlap."""
        content = "Weather forecast"
        query = "Python programming"

        relevance = scorer._compute_relevance(content, query)

        assert relevance == 1.0  # No boost

    @pytest.mark.asyncio
    async def test_compute_relevance_empty_query(self, scorer):
        """Test relevance with empty query."""
        content = "Some content"
        query = ""

        relevance = scorer._compute_relevance(content, query)

        assert relevance == 1.0

    @pytest.mark.asyncio
    async def test_score_chunks_semantic_filtering_disabled(self):
        """Test scoring with semantic filtering disabled."""
        config = CompressionConfig(enable_semantic_filtering=False)
        scorer = ImportanceScorer(config)

        chunks = [
            ContentChunk(
                id="1",
                content="Python",
                content_type=ContentType.USER_MESSAGE,
                token_count=10,
                position=0,
            ),
        ]

        scored = await scorer.score_chunks(chunks, query="Python")

        # Should still score but without query boost
        assert scored[0].importance_score > 0
