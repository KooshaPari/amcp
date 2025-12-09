"""
Tests for Model Router optimization.

Tests the ComplexityRouter and ComplexityAnalyzer for intelligent model selection
based on task complexity. Covers: routing decisions, complexity detection, cost estimation.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from optimization.model_router import (
    ComplexityRouter,
    ModelRoutingConfig,
    ComplexityLevel,
    ComplexityAnalyzer,
)


class TestComplexityRouter:
    """Tests for ComplexityRouter."""

    @pytest.fixture
    def router(self):
        """Create a fresh router for each test."""
        return ComplexityRouter(ModelRoutingConfig())

    @pytest.mark.asyncio
    async def test_simple_task_routing(self, router):
        """Test routing for simple tasks."""
        decision = await router.route("What is 2+2?")

        assert decision.complexity == ComplexityLevel.SIMPLE
        # Should route to cheaper model
        assert decision.model in ["gemini-2.0-flash", "gpt-4o-mini", "claude-haiku-3.5"]

    @pytest.mark.asyncio
    async def test_complex_task_routing(self, router):
        """Test routing for complex tasks."""
        prompt = """
        Please analyze the architectural trade-offs between microservices
        and monolithic approaches. Compare and contrast their performance,
        scalability, and maintenance characteristics step by step.
        """
        decision = await router.route(prompt)

        assert decision.complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.MODERATE]
        # Should use higher quality model
        assert "sonnet" in decision.model.lower() or decision.model == router.config.default_model

    @pytest.mark.asyncio
    async def test_cost_estimation(self, router):
        """Test cost estimation."""
        decision = await router.route(
            "Explain quantum computing",
            output_tokens_estimate=2000
        )

        assert decision.estimated_cost_usd > 0
        assert decision.estimated_latency_ms > 0

    @pytest.mark.asyncio
    async def test_override(self, router):
        """Test model override."""
        decision = await router.route_with_override(
            "Simple question",
            override_model="claude-sonnet-4"
        )

        assert decision.model == "claude-sonnet-4"
        assert "override" in decision.rationale.lower()

    def test_get_available_models(self, router):
        """Test getting available models list (covers lines 217-218, 222)."""
        models = router.get_available_models()
        
        # Should return list of model names
        assert isinstance(models, list)
        assert len(models) > 0
        
        # All models should be in config
        for model in models:
            assert model in router.config.models

    def test_add_model(self, router):
        """Test adding a model specification (covers line 222)."""
        from optimization.model_router.models import ModelSpec
        new_spec = ModelSpec(
            name="test-model",
            provider="test-provider",
            cost_per_1k_input=0.001,
            cost_per_1k_output=0.002,
            max_context=128000,
            quality_score=0.9,
            latency_p50_ms=200
        )
        
        initial_count = len(router.get_available_models())
        router.add_model(new_spec)
        updated_count = len(router.get_available_models())
        
        # Should add new model
        assert updated_count == initial_count + 1
        assert "test-model" in router.get_available_models()

    @pytest.mark.asyncio
    async def test_simple_task_fallback(self, router):
        """Test simple task routing fallback paths (covers lines 69-72)."""
        # Configure for cost optimization
        router.config.optimize_for = "cost"
        decision = await router.route("What is 2+2?")
        
        # Should find appropriate simple task model
        assert decision.complexity == ComplexityLevel.SIMPLE
        assert decision.model in ["gemini-2.0-flash", "gpt-4o-mini", "claude-haiku-3.5"]

    @pytest.mark.asyncio
    async def test_cost_estimation_invalid_model(self, router):
        """Test cost estimation for invalid model (covers line 113)."""
        # Test with invalid model
        cost = router._estimate_cost("invalid-model-name", 100, 100)
        assert cost == 0.0

    @pytest.mark.asyncio
    async def test_route_with_override_invalid_model(self, router):
        """Test routing with invalid override model (covers line 213)."""
        decision = await router.route_with_override(
            "Test prompt",
            override_model="non-existent-model"
        )
        
        # Should fall back to normal routing (not use invalid model)
        assert decision.model != "non-existent-model"
        assert decision.complexity != ComplexityLevel.EXPERT  # Should re-analyze


class TestComplexityAnalyzer:
    """Tests for ComplexityAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer."""
        return ComplexityAnalyzer(ModelRoutingConfig())

    def test_simple_detection(self, analyzer):
        """Test simple task detection."""
        assert analyzer.analyze("What is Python?") == ComplexityLevel.SIMPLE
        assert analyzer.analyze("Hello") == ComplexityLevel.SIMPLE
        assert analyzer.analyze("Define OOP") == ComplexityLevel.SIMPLE

    def test_complex_detection(self, analyzer):
        """Test complex task detection."""
        prompt = "Analyze and compare the trade-offs between approaches"
        assert analyzer.analyze(prompt) == ComplexityLevel.COMPLEX

        prompt = "Explain step by step how to evaluate this in detail"
        assert analyzer.analyze(prompt) == ComplexityLevel.COMPLEX

    def test_context_override(self, analyzer):
        """Test context-based override."""
        assert analyzer.analyze(
            "Simple question",
            context={"require_expert": True}
        ) == ComplexityLevel.EXPERT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
