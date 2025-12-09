"""
ACON context compression implementation.

Main compressor class implementing the ACON algorithm from 2025 research.
"""

import asyncio
import hashlib
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Optional, Callable, Awaitable

from .types import (
    ContentChunk,
    ContentType,
    CompressionConfig,
    CompressionResult,
)
from .scoring import ImportanceScorer
from .algorithms import ChunkCompressor

logger = logging.getLogger(__name__)


class ContextCompressor(ABC):
    """Abstract base class for context compression."""

    def __init__(self, config: CompressionConfig):
        self.config = config

    @abstractmethod
    async def compress(
        self,
        content: list[dict[str, Any]],
        query: Optional[str] = None,
    ) -> CompressionResult:
        """Compress content while preserving important information."""


class ACONCompressor(ContextCompressor):
    """
    ACON (Agentive CONtext compression) implementation.

    Algorithm:
    1. Segment content into typed chunks
    2. Score importance of each chunk
    3. Filter/compress based on scores
    4. Optionally summarize long sections
    5. Reconstruct compressed context

    Usage:
        compressor = ACONCompressor(CompressionConfig())

        result = await compressor.compress(
            content=[
                {"role": "system", "content": "..."},
                {"role": "user", "content": "..."},
            ],
            query="What files need to be updated?"
        )

        # result.chunks contains compressed content
        # result.compression_ratio shows reduction achieved
    """

    def __init__(self, config: CompressionConfig = None):
        super().__init__(config or CompressionConfig())
        self._cache: dict[str, CompressionResult] = {}
        self._lock = asyncio.Lock()
        self._scorer = ImportanceScorer(self.config)
        self._compressor = ChunkCompressor(self.config)

    def _get_content_type(self, message: dict[str, Any]) -> ContentType:
        """Determine content type from message."""
        role = message.get("role", "")

        if role == "system":
            return ContentType.SYSTEM_PROMPT
        elif role == "user":
            return ContentType.USER_MESSAGE
        elif role == "assistant":
            return ContentType.ASSISTANT_MESSAGE
        elif role == "tool":
            return ContentType.TOOL_OUTPUT
        else:
            return ContentType.CONTEXT_RAG

    def _generate_chunk_id(self, content: str, position: int) -> str:
        """Generate unique chunk ID."""
        hash_input = f"{position}:{content[:100]}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]

    async def _segment_content(
        self,
        content: list[dict[str, Any]],
    ) -> list[ContentChunk]:
        """Segment content into typed chunks."""
        chunks = []

        for i, message in enumerate(content):
            text = message.get("content", "")
            content_type = self._get_content_type(message)

            # For long content, split into smaller chunks
            if len(text) > self.config.chunk_size * 4:
                # Split by paragraphs or sentences
                paragraphs = re.split(r'\n\n+', text)
                for j, para in enumerate(paragraphs):
                    chunk = ContentChunk(
                        id=self._generate_chunk_id(para, i * 1000 + j),
                        content=para,
                        content_type=content_type,
                        token_count=int(self._compressor.estimate_tokens(para)),
                        position=i * 1000 + j,
                    )
                    chunks.append(chunk)
            else:
                chunk = ContentChunk(
                    id=self._generate_chunk_id(text, i),
                    content=text,
                    content_type=content_type,
                    token_count=int(self._compressor.estimate_tokens(text)),
                    position=i,
                )
                chunks.append(chunk)

        return chunks

    async def compress(
        self,
        content: list[dict[str, Any]],
        query: Optional[str] = None,
        summarizer: Optional[Callable[[str], Awaitable[str]]] = None,
    ) -> CompressionResult:
        """
        Compress content using ACON algorithm.

        Args:
            content: List of message dicts
            query: Optional query for relevance scoring
            summarizer: Optional async function for summarization

        Returns:
            CompressionResult with compressed chunks
        """
        async with self._lock:
            # Check cache
            cache_key = hashlib.md5(
                str(content).encode() + (query or "").encode()
            ).hexdigest()

            if self.config.enable_cache and cache_key in self._cache:
                logger.debug(f"Cache hit for compression: {cache_key[:8]}")
                return self._cache[cache_key]

            # Segment content into chunks
            chunks = await self._segment_content(content)
            original_tokens = sum(c.token_count for c in chunks)

            # Score importance
            chunks = await self._scorer.score_chunks(chunks, query)

            # Sort by importance (preserve order for same importance)
            chunks.sort(key=lambda c: (-c.importance_score, c.position))

            # Calculate target tokens
            target_tokens = int(
                original_tokens * (1 - self.config.target_reduction)
            )
            target_tokens = max(target_tokens, self.config.min_tokens)
            target_tokens = min(target_tokens, self.config.max_output_tokens)

            # Compress chunks to meet target
            compressed_chunks = []
            current_tokens = 0

            for chunk in chunks:
                if current_tokens >= target_tokens:
                    # Skip remaining low-importance chunks
                    continue

                remaining = target_tokens - current_tokens
                if chunk.token_count > remaining:
                    # Compress this chunk
                    chunk = await self._compressor.compress_chunk(chunk, remaining)

                # Summarize if needed
                if (
                    self.config.enable_summarization
                    and chunk.token_count > self.config.summarization_threshold
                ):
                    chunk = await self._compressor.summarize_chunk(chunk, summarizer)

                compressed_chunks.append(chunk)
                current_tokens += chunk.token_count

            # Sort back by original position
            compressed_chunks.sort(key=lambda c: c.position)

            # Calculate metrics
            compressed_tokens = sum(c.token_count for c in compressed_chunks)
            compression_ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0

            # Calculate preserved importance
            total_importance = sum(c.importance_score for c in chunks)
            preserved_importance = (
                sum(c.importance_score for c in compressed_chunks) / total_importance
                if total_importance > 0 else 1.0
            )

            result = CompressionResult(
                original_tokens=original_tokens,
                compressed_tokens=compressed_tokens,
                chunks=compressed_chunks,
                compression_ratio=compression_ratio,
                preserved_importance=preserved_importance,
            )

            # Cache result with size limit
            if self.config.enable_cache:
                # Enforce cache size limit
                if len(self._cache) >= self.config.max_cache_size:
                    # Remove oldest entry (simple FIFO)
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    logger.debug(f"Cache evicted entry: {oldest_key[:8]}... (size limit reached)")
                self._cache[cache_key] = result

            logger.info(
                f"Compression complete: {original_tokens} -> {compressed_tokens} tokens "
                f"({compression_ratio:.1%}), preserved importance: {preserved_importance:.1%}"
            )

            return result

    async def decompress_for_display(
        self,
        result: CompressionResult,
    ) -> list[dict[str, Any]]:
        """Reconstruct messages from compressed chunks."""
        messages = []
        current_role = None
        current_content = []

        for chunk in result.chunks:
            role = "user"  # Default
            if chunk.content_type == ContentType.SYSTEM_PROMPT:
                role = "system"
            elif chunk.content_type == ContentType.ASSISTANT_MESSAGE:
                role = "assistant"
            elif chunk.content_type == ContentType.TOOL_OUTPUT:
                role = "tool"

            if role != current_role:
                if current_content:
                    messages.append({
                        "role": current_role,
                        "content": "\n".join(current_content),
                    })
                current_role = role
                current_content = [chunk.content]
            else:
                current_content.append(chunk.content)

        if current_content:
            messages.append({
                "role": current_role,
                "content": "\n".join(current_content),
            })

        return messages
