"""
ACON Context Compression - Backward Compatibility Wrapper

This module maintains backward compatibility by re-exporting all symbols
from the refactored compression submodule.

For new code, prefer direct imports:
    from smartcp.optimization.compression import ACONCompressor, CompressionConfig

Reference: 2025 Context Management Research
"""

# Re-export all public symbols from submodule
from .compression import (
    # Types
    ContentType,
    ContentChunk,
    CompressionConfig,
    CompressionResult,
    # Compressors
    ContextCompressor,
    ACONCompressor,
    ImportanceScorer,
    ChunkCompressor,
    # Factory
    get_acon_compressor,
)

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
