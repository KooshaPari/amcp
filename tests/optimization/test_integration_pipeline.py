"""
Tests for Optimization Integration Pipeline.

Tests the OptimizationPipeline that coordinates all optimization components.
Covers: request optimization, tool execution, cache warming.
"""

import pytest
import sys
import os
import time
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from optimization.integration import OptimizationPipeline
from optimization.config import OptimizationConfig
from optimization.integration import (
    OptimizedRequest,
    ExecutionBatch,
    RoutingDecision,
)
from optimization.model_router.models import ComplexityLevel


class TestOptimizationPipeline:
    """Tests for OptimizationPipeline."""

    @pytest.fixture
    def pipeline(self):
        """Create pipeline."""
        config = OptimizationConfig(
            enable_prompt_caching=True,
            enable_context_compression=True,
            enable_model_routing=True,
            enable_parallel_execution=True,
        )
        return OptimizationPipeline(config)

    @pytest.fixture
    def pipeline_with_compression(self):
        """Create pipeline with compression enabled and low threshold."""
        config = OptimizationConfig(
            enable_prompt_caching=True,
            enable_context_compression=True,
            enable_model_routing=True,
            enable_parallel_execution=True,
            use_compression_above_tokens=100,  # Low threshold for testing
        )
        return OptimizationPipeline(config)

    @pytest.fixture
    def pipeline_with_planning(self):
        """Create pipeline with planning enabled."""
        config = OptimizationConfig(
            enable_prompt_caching=True,
            enable_context_compression=True,
            enable_model_routing=True,
            enable_parallel_execution=True,
            enable_planning=True,
            use_planning_above_complexity=ComplexityLevel.SIMPLE,
        )
        return OptimizationPipeline(config)

    @pytest.mark.asyncio
    async def test_optimize_request(self, pipeline):
        """Test full request optimization."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is Python?"},
        ]

        result = await pipeline.optimize_request(messages)

        assert result.model is not None
        assert result.routing_decision is not None
        assert result.metrics.total_latency_ms >= 0

    @pytest.mark.asyncio
    async def test_optimize_request_with_force_model(self, pipeline):
        """Test optimization with forced model (lines 110-112, 121)."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is Python?"},
        ]

        result = await pipeline.optimize_request(messages, force_model="gpt-4")

        assert result.model == "gpt-4"
        assert result.routing_decision.rationale == "User override"

    @pytest.mark.asyncio
    async def test_optimize_request_with_compression(self, pipeline_with_compression):
        """Test optimization with context compression (lines 145-158)."""
        # Create a long message that exceeds the compression threshold
        long_content = "This is a test. " * 100  # Creates a long message
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": long_content},
        ]

        result = await pipeline_with_compression.optimize_request(messages)

        assert result.compression_result is not None
        assert result.metrics.compression_applied is True
        assert result.metrics.original_tokens > result.metrics.compressed_tokens

    @pytest.mark.asyncio
    async def test_optimize_request_with_planning(self, pipeline_with_planning):
        """Test optimization with planning enabled (lines 185, 187-188)."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Complex multi-step task requiring planning"},
        ]

        result = await pipeline_with_planning.optimize_request(messages)

        # Planning should be marked as applied when complexity is high
        assert hasattr(result.metrics, 'planning_applied')

    @pytest.mark.asyncio
    async def test_optimize_request_cache_hit(self, pipeline):
        """Test optimization with cache hit to test savings calculation (line 258)."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is Python?"},
        ]

        # First call to populate cache
        await pipeline.optimize_request(messages)
        
        # Second call should hit cache
        result = await pipeline.optimize_request(messages)

        assert result.metrics.cache_hit is True
        assert result.metrics.cache_tokens_saved > 0

    @pytest.mark.asyncio
    async def test_execute_tools_with_planning(self, pipeline_with_planning):
        """Test tool execution with planning enabled (lines 270-272, 281-282)."""
        async def mock_tool(name: str, input: dict) -> str:
            return f"Result: {name}"

        tools = [
            ("search", {"query": "test"}),
            ("list", {"path": "/"}),
        ]

        batch = await pipeline_with_planning.execute_tools(
            tools, 
            mock_tool, 
            goal="Find files and search content"
        )

        assert batch is not None
        assert len(batch.results) == 2

    @pytest.mark.asyncio
    async def test_execute_tools_without_planning(self, pipeline):
        """Test tool execution without planning (lines 290-291)."""
        async def mock_tool(name: str, input: dict) -> str:
            return f"Result: {name}"

        tools = [
            ("search", {"query": "test"}),
        ]

        batch = await pipeline.execute_tools(tools, mock_tool)

        assert batch is not None
        assert len(batch.results) == 1

    @pytest.mark.asyncio
    async def test_cache_warming_empty_list(self, pipeline):
        """Test cache warming with empty list (lines 220-226)."""
        warmed = await pipeline.warm_cache([])
        assert warmed == 0

    @pytest.mark.asyncio
    async def test_cache_warming_with_prompts(self, pipeline):
        """Test cache warming with common system prompts (lines 230-235)."""
        prompts = [
            "You are a helpful assistant.",
            "You are a code reviewer.",
            "You are a data analyst.",
        ]

        warmed = await pipeline.warm_cache(prompts)
        assert warmed == 3

        # Stats should show cached entries
        stats = await pipeline.get_cache_stats()
        assert stats["total_entries"] >= 3

    @pytest.mark.asyncio
    async def test_cache_warming_duplicate_prompts(self, pipeline):
        """Test cache warming with duplicate prompts."""
        prompts = [
            "You are a helpful assistant.",
            "You are a helpful assistant.",  # Duplicate
            "You are a code reviewer.",
        ]

        warmed = await pipeline.warm_cache(prompts)
        assert warmed == 3  # All should be warmed (including duplicates)

    @pytest.mark.asyncio
    async def test_get_cache_stats(self, pipeline):
        """Test getting cache statistics."""
        stats = await pipeline.get_cache_stats()
        
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert "total_entries" in stats
        assert "tokens_cached" in stats
        assert "estimated_savings_usd" in stats

    def test_get_available_models(self, pipeline):
        """Test getting list of available models."""
        models = pipeline.get_available_models()
        assert isinstance(models, list)

    @pytest.mark.asyncio
    async def test_optimize_request_error_handling(self, pipeline):
        """Test error handling in optimization pipeline."""
        # Create a message that might cause routing issues
        messages = [
            {"role": "system", "content": ""},  # Empty system message
            {"role": "user", "content": ""},   # Empty user message
        ]

        # Should not raise an exception
        result = await pipeline.optimize_request(messages)
        assert result is not None

    @pytest.mark.asyncio
    async def test_execute_tools_with_errors(self, pipeline):
        """Test tool execution with errors."""
        async def failing_tool(name: str, input: dict) -> str:
            if name == "failing_tool":
                raise ValueError("Tool failed")
            return f"Result: {name}"

        tools = [
            ("failing_tool", {"param": "test"}),
            ("working_tool", {"param": "test"}),
        ]

        batch = await pipeline.execute_tools(tools, failing_tool)
        
        # Should have both results, one with error
        assert len(batch.results) == 2

    @pytest.mark.asyncio
    async def test_optimize_request_with_context(self, pipeline):
        """Test optimization with additional context."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is Python?"},
        ]
        context = {
            "user_preferences": {"language": "python"},
            "session_id": "test-session"
        }

        result = await pipeline.optimize_request(messages, context=context)
        assert result.model is not None
        assert result.routing_decision is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
