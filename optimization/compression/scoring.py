"""
Importance scoring algorithms for context compression.

Implements hierarchical importance scoring based on content type,
position, query relevance, and length.
"""

from typing import Optional

from .types import ContentChunk, CompressionConfig


class ImportanceScorer:
    """Score chunk importance for compression decisions."""

    def __init__(self, config: CompressionConfig):
        self.config = config

    async def score_chunks(
        self,
        chunks: list[ContentChunk],
        query: Optional[str] = None,
    ) -> list[ContentChunk]:
        """Score importance of each chunk."""
        for chunk in chunks:
            # Base importance from content type
            base_weight = self.config.importance_weights.get(
                chunk.content_type.value, 0.5
            )

            # Position boost (earlier/structural content more important)
            position_boost = 1.0 + ((len(chunks) - chunk.position) / len(chunks)) * 0.2

            # Query relevance boost
            query_boost = 1.0
            if query and self.config.enable_semantic_filtering:
                query_boost = self._compute_relevance(chunk.content, query)

            # Length penalty (very long chunks might be less important per token)
            length_penalty = 1.0
            if chunk.token_count > self.config.chunk_size * 2:
                length_penalty = 0.9

            # Compute final importance
            chunk.importance_score = (
                base_weight * position_boost * query_boost * length_penalty
            )

        return chunks

    def _compute_relevance(self, content: str, query: str) -> float:
        """Compute relevance between content and query."""
        # Simple keyword overlap (in production, use embeddings)
        content_words = set(content.lower().split())
        query_words = set(query.lower().split())

        if not query_words:
            return 1.0

        overlap = len(content_words & query_words)
        relevance = overlap / len(query_words)

        # Boost if query words appear in content
        return 1.0 + relevance * 0.5
