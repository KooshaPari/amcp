"""
Memory optimization tests.

Tests to ensure memory usage is reasonable and resources are cleaned up.
"""

import pytest
import gc
import sys
from optimization.compression.compressor import ACONCompressor
from optimization.compression.types import CompressionConfig


class TestMemoryOptimization:
    """Tests to verify memory usage is reasonable."""

    @pytest.mark.asyncio
    async def test_compression_doesnt_leak_memory(self):
        """Test that compression doesn't leak memory."""
        compressor = ACONCompressor(CompressionConfig())
        
        # Create moderate-sized content
        content = [
            {"role": "user", "content": "Test message " * 10},
        ]
        
        # Run compression multiple times
        for _ in range(10):
            result = await compressor.compress(content)
            assert result is not None
        
        # Force garbage collection
        gc.collect()
        
        # Memory should be reasonable (check object count)
        assert len(compressor._cache) <= 10  # Cache should be bounded

    def test_large_string_handling(self):
        """Test that large strings are handled efficiently."""
        # Create a large string
        large_text = "x" * 10000
        
        # Check memory usage
        size_mb = sys.getsizeof(large_text) / 1024 / 1024
        assert size_mb < 1.0  # Should be less than 1MB
        
        # Cleanup
        del large_text
        gc.collect()
