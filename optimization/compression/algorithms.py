"""
Compression algorithms for reducing chunk sizes.

Implements text compression and summarization strategies.
"""

import re
from typing import Optional, Callable, Awaitable

from .types import ContentChunk, CompressionConfig


class ChunkCompressor:
    """Compress individual chunks using various strategies."""

    def __init__(self, config: CompressionConfig):
        self.config = config

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text."""
        return len(text.split()) * 1.3  # Rough estimate

    async def compress_chunk(
        self,
        chunk: ContentChunk,
        target_tokens: int,
    ) -> ContentChunk:
        """Compress a single chunk to target token count."""
        if chunk.token_count <= target_tokens:
            return chunk

        original = chunk.content
        compressed = original

        # Strategy 1: Remove redundant whitespace
        compressed = re.sub(r'\s+', ' ', compressed)

        # Strategy 2: Remove common filler words/phrases
        filler_patterns = [
            r'\b(basically|essentially|actually|really|just|simply)\b',
            r'\b(in order to)\b',
            r'\b(it is important to note that)\b',
            r'\b(as mentioned (earlier|before|above))\b',
        ]
        for pattern in filler_patterns:
            compressed = re.sub(pattern, '', compressed, flags=re.IGNORECASE)

        # Strategy 3: Truncate if still too long
        if self.estimate_tokens(compressed) > target_tokens:
            # Keep first and last portions
            words = compressed.split()
            keep_words = int(target_tokens * 0.8)
            half = keep_words // 2
            compressed = ' '.join(words[:half] + ['...'] + words[-half:])

        # Update chunk
        chunk.content = compressed.strip()
        chunk.token_count = int(self.estimate_tokens(chunk.content))
        chunk.is_compressed = True
        chunk.original_content = original

        return chunk

    async def summarize_chunk(
        self,
        chunk: ContentChunk,
        summarizer: Optional[Callable[[str], Awaitable[str]]] = None,
    ) -> ContentChunk:
        """Summarize a long chunk."""
        if chunk.token_count < self.config.summarization_threshold:
            return chunk

        if summarizer:
            # Use provided summarizer (typically LLM call)
            summary = await summarizer(chunk.content)
        else:
            # Simple extractive summary
            sentences = re.split(r'[.!?]+', chunk.content)
            # Keep first and last sentences
            if len(sentences) > 4:
                summary = '. '.join(
                    sentences[:2] + ['...'] + sentences[-2:]
                )
            else:
                summary = chunk.content

        chunk.original_content = chunk.content
        chunk.content = summary
        chunk.token_count = int(self.estimate_tokens(summary))
        chunk.is_compressed = True

        return chunk
