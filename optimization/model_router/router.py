"""
Complexity-Based Model Router

Routes requests to optimal models based on task complexity,
cost constraints, and quality requirements.
"""

import asyncio
import logging
from typing import Any, Optional

from .analyzer import ComplexityAnalyzer
from .models import (
    ComplexityLevel,
    DEFAULT_MODELS,
    ModelRoutingConfig,
    RoutingDecision,
)

logger = logging.getLogger(__name__)


class ComplexityRouter:
    """
    Routes requests to optimal models based on complexity.

    Usage:
        router = ComplexityRouter(ModelRoutingConfig())

        decision = await router.route(
            prompt="What is 2+2?",
            context={"tools": [...]}
        )

        # Use decision.model for the request
    """

    def __init__(self, config: ModelRoutingConfig = None):
        self.config = config or ModelRoutingConfig()

        # Initialize models
        if not self.config.models:
            self.config.models = DEFAULT_MODELS

        self.analyzer = ComplexityAnalyzer(self.config)
        self._daily_cost = 0.0
        self._lock = asyncio.Lock()

        logger.info(
            f"ComplexityRouter initialized: "
            f"default={self.config.default_model}, "
            f"optimize_for={self.config.optimize_for}"
        )

    def _get_model_for_complexity(
        self,
        complexity: ComplexityLevel,
        token_estimate: int,
    ) -> tuple[str, str]:
        """Get optimal model for complexity level."""
        models = self.config.models
        optimize = self.config.optimize_for

        if complexity == ComplexityLevel.SIMPLE:
            # Use cheapest/fastest model
            if optimize in ("cost", "balanced"):
                if "gemini-2.0-flash" in models:
                    return "gemini-2.0-flash", "Cheapest model for simple task"
                if "gpt-4o-mini" in models:
                    return "gpt-4o-mini", "Fast/cheap model for simple task"
            if "claude-haiku-3.5" in models:
                return "claude-haiku-3.5", "Fast Anthropic model for simple task"

        elif complexity == ComplexityLevel.MODERATE:
            # Balance cost and quality
            if optimize == "cost":
                if "claude-haiku-3.5" in models:
                    return "claude-haiku-3.5", "Cost-optimized for moderate task"
            if optimize == "speed":
                if "gemini-2.0-flash" in models:
                    return "gemini-2.0-flash", "Speed-optimized for moderate task"
            # Default to Sonnet for balanced
            return self.config.default_model, "Balanced model for moderate task"

        elif complexity == ComplexityLevel.COMPLEX:
            # Use high-quality model
            if "claude-sonnet-4" in models:
                return "claude-sonnet-4", "High-quality model for complex task"
            return self.config.default_model, "Default model for complex task"

        else:  # EXPERT
            # Use best available model
            best_model = max(
                models.items(),
                key=lambda x: x[1].quality_score
            )
            return (
                best_model[0],
                f"Best quality model ({best_model[1].quality_score}) for expert task"
            )

        return self.config.default_model, "Default model fallback"

    def _estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate request cost."""
        spec = self.config.models.get(model)
        if not spec:
            return 0.0

        input_cost = (input_tokens / 1000) * spec.cost_per_1k_input
        output_cost = (output_tokens / 1000) * spec.cost_per_1k_output

        return input_cost + output_cost

    async def route(
        self,
        prompt: str,
        context: Optional[dict[str, Any]] = None,
        output_tokens_estimate: int = 1000,
    ) -> RoutingDecision:
        """
        Route request to optimal model.

        Args:
            prompt: User prompt
            context: Optional context dict
            output_tokens_estimate: Estimated output tokens

        Returns:
            Routing decision
        """
        async with self._lock:
            # Analyze complexity
            complexity = self.analyzer.analyze(prompt, context)

            # Estimate input tokens
            input_tokens = len(prompt.split()) * 1.3  # Rough estimate

            # Get model recommendation
            model, rationale = self._get_model_for_complexity(
                complexity, int(input_tokens)
            )

            # Estimate cost
            cost = self._estimate_cost(model, int(input_tokens), output_tokens_estimate)

            # Check cost constraints
            if cost > self.config.max_cost_per_request_usd:
                # Try to find cheaper alternative
                for alt_model, spec in sorted(
                    self.config.models.items(),
                    key=lambda x: x[1].cost_per_1k_input
                ):
                    alt_cost = self._estimate_cost(
                        alt_model, int(input_tokens), output_tokens_estimate
                    )
                    if alt_cost <= self.config.max_cost_per_request_usd:
                        if spec.quality_score >= self.config.min_quality_score:
                            model = alt_model
                            cost = alt_cost
                            rationale = f"Cost-constrained: {rationale}"
                            break

            # Get fallback
            fallback = None
            if model != self.config.default_model:
                fallback = self.config.default_model

            # Get latency estimate
            spec = self.config.models.get(model)
            latency = spec.latency_p50_ms if spec else 500

            decision = RoutingDecision(
                model=model,
                complexity=complexity,
                estimated_cost_usd=cost,
                estimated_latency_ms=latency,
                rationale=rationale,
                fallback_model=fallback,
            )

            logger.debug(
                f"Routing decision: model={model}, complexity={complexity.value}, "
                f"cost=${cost:.4f}, rationale={rationale}"
            )

            return decision

    async def route_with_override(
        self,
        prompt: str,
        override_model: Optional[str] = None,
        override_complexity: Optional[ComplexityLevel] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> RoutingDecision:
        """Route with optional overrides."""
        if override_model and override_model in self.config.models:
            complexity = override_complexity or ComplexityLevel.MODERATE
            spec = self.config.models[override_model]
            return RoutingDecision(
                model=override_model,
                complexity=complexity,
                estimated_cost_usd=0.0,  # Not calculated for override
                estimated_latency_ms=spec.latency_p50_ms,
                rationale=f"User override: {override_model}",
            )

        return await self.route(prompt, context)

    def add_model(self, spec) -> None:
        """Add or update a model specification."""
        self.config.models[spec.name] = spec
        logger.info(f"Added model: {spec.name}")

    def get_available_models(self) -> list[str]:
        """Get list of available models."""
        return list(self.config.models.keys())
