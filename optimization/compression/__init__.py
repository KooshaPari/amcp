"""
ACON Context Compression Implementation

Implements ACON (Agentive CONtext compression) from 2025 research
achieving 26-54% token reduction while preserving task performance.

Key features:
- Hierarchical importance scoring
- Dynamic chunk selection
- Semantic similarity preservation
- Conversation history summarization
- Tool output compression

Reference: 2025 Context Management Research

Usage:
    from smartcp.optimization.compression import (
        ACONCompressor,
        CompressionConfig,
        get_acon_compressor,
    )

    # Use factory function
    compressor = get_acon_compressor()
    result = await compressor.compress(messages)

    # Or create custom instance
    config = CompressionConfig(target_reduction=0.5)
    compressor = ACONCompressor(config)
    result = await compressor.compress(messages, query="relevant query")
"""

from typing import Optional

from .types import (
    ContentType,
    ContentChunk,
    CompressionConfig,
    CompressionResult,
)
from .compressor import (
    ContextCompressor,
    ACONCompressor,
)
from .scoring import ImportanceScorer
from .algorithms import ChunkCompressor

__all__ = [
    # Types
    "ContentType",
    "ContentChunk",
    "CompressionConfig",
    "CompressionResult",
    # Compressors
    "ContextCompressor",
    "ACONCompressor",
    "ImportanceScorer",
    "ChunkCompressor",
    # Factory
    "get_acon_compressor",
]

# Global compressor instance
_acon_compressor: Optional[ACONCompressor] = None


def get_acon_compressor(config: CompressionConfig = None) -> ACONCompressor:
    """Get or create global ACON compressor instance."""
    global _acon_compressor
    if _acon_compressor is None:
        _acon_compressor = ACONCompressor(config or CompressionConfig())
    return _acon_compressor
