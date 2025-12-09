"""
Data types for context compression.

Defines core types, enums, and configuration for the ACON compression algorithm.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ContentType(str, Enum):
    """Types of content for compression."""
    SYSTEM_PROMPT = "system_prompt"
    USER_MESSAGE = "user_message"
    ASSISTANT_MESSAGE = "assistant_message"
    TOOL_DEFINITION = "tool_definition"
    TOOL_OUTPUT = "tool_output"
    CONTEXT_RAG = "context_rag"
    CONVERSATION_HISTORY = "conversation_history"


@dataclass
class CompressionConfig:
    """Configuration for context compression."""

    # Target compression
    target_reduction: float = 0.4  # 40% reduction target
    min_tokens: int = 100  # Never compress below this
    max_output_tokens: int = 50000  # Maximum output size

    # Importance weights by content type
    importance_weights: dict[str, float] = field(
        default_factory=lambda: {
            ContentType.SYSTEM_PROMPT.value: 1.0,  # Never compress
            ContentType.USER_MESSAGE.value: 0.95,  # Minimal compression
            ContentType.TOOL_DEFINITION.value: 0.85,  # Light compression
            ContentType.ASSISTANT_MESSAGE.value: 0.7,  # Moderate compression
            ContentType.TOOL_OUTPUT.value: 0.5,  # Heavy compression OK
            ContentType.CONTEXT_RAG.value: 0.6,  # Moderate compression
            ContentType.CONVERSATION_HISTORY.value: 0.4,  # Heavy compression
        }
    )

    # Chunking parameters
    chunk_size: int = 512  # Tokens per chunk for analysis
    chunk_overlap: int = 64  # Overlap between chunks

    # Summarization
    enable_summarization: bool = True
    summarization_threshold: int = 2000  # Summarize chunks above this

    # Semantic filtering
    enable_semantic_filtering: bool = True
    similarity_threshold: float = 0.7

    # Caching
    enable_cache: bool = True
    cache_ttl: int = 3600
    max_cache_size: int = 1000  # Maximum cache entries to prevent unbounded growth


@dataclass
class ContentChunk:
    """A chunk of content with metadata."""

    id: str
    content: str
    content_type: ContentType
    importance_score: float = 1.0
    token_count: int = 0
    position: int = 0  # Original position
    is_compressed: bool = False
    original_content: Optional[str] = None

    @property
    def compression_ratio(self) -> float:
        """Calculate compression ratio."""
        if not self.original_content:
            return 1.0
        original_len = len(self.original_content)
        current_len = len(self.content)
        return current_len / original_len if original_len > 0 else 1.0


@dataclass
class CompressionResult:
    """Result of context compression."""

    original_tokens: int
    compressed_tokens: int
    chunks: list[ContentChunk]
    compression_ratio: float
    preserved_importance: float  # Weighted importance preserved
    summary: Optional[str] = None

    @property
    def tokens_saved(self) -> int:
        """Tokens saved by compression."""
        return self.original_tokens - self.compressed_tokens

    @property
    def cost_savings_estimate(self) -> float:
        """Estimated cost savings (assumes $0.003/1K tokens)."""
        return (self.tokens_saved / 1000) * 0.003
