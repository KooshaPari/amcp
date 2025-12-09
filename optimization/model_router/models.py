"""
Data Models and Configuration for Model Routing

Defines model specifications, routing config, and complexity levels
for intelligent model selection based on task requirements.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ComplexityLevel(str, Enum):
    """Task complexity levels."""
    SIMPLE = "simple"  # Basic queries, lookups
    MODERATE = "moderate"  # Standard reasoning
    COMPLEX = "complex"  # Multi-step, nuanced
    EXPERT = "expert"  # Specialized knowledge required


@dataclass
class ModelSpec:
    """Model specification."""
    name: str
    provider: str
    cost_per_1k_input: float
    cost_per_1k_output: float
    max_context: int
    latency_p50_ms: int
    quality_score: float  # 0-1 scale
    capabilities: list[str] = field(default_factory=list)


@dataclass
class ModelRoutingConfig:
    """Configuration for model routing."""

    # Model definitions
    models: dict[str, ModelSpec] = field(default_factory=dict)

    # Routing preferences
    default_model: str = "claude-sonnet-4"
    optimize_for: str = "balanced"  # cost, speed, quality, balanced

    # Thresholds
    simple_task_max_tokens: int = 500
    simple_task_keywords: list[str] = field(
        default_factory=lambda: [
            "what is", "define", "list", "show", "get",
            "hello", "hi", "thanks", "bye"
        ]
    )
    complex_task_indicators: list[str] = field(
        default_factory=lambda: [
            "analyze", "compare", "evaluate", "synthesize",
            "explain why", "step by step", "in detail",
            "pros and cons", "trade-offs"
        ]
    )

    # Cost constraints
    max_cost_per_request_usd: float = 0.10
    daily_budget_usd: Optional[float] = None

    # Quality constraints
    min_quality_score: float = 0.7

    # Caching integration
    use_prompt_cache: bool = True


# Default model specifications (2025 pricing)
DEFAULT_MODELS = {
    "claude-sonnet-4": ModelSpec(
        name="claude-sonnet-4",
        provider="anthropic",
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        max_context=200000,
        latency_p50_ms=800,
        quality_score=0.95,
        capabilities=["code", "reasoning", "analysis", "creative"],
    ),
    "claude-haiku-3.5": ModelSpec(
        name="claude-haiku-3.5",
        provider="anthropic",
        cost_per_1k_input=0.0008,
        cost_per_1k_output=0.004,
        max_context=200000,
        latency_p50_ms=400,
        quality_score=0.85,
        capabilities=["code", "reasoning", "quick_tasks"],
    ),
    "gemini-2.0-flash": ModelSpec(
        name="gemini-2.0-flash",
        provider="google",
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0004,
        max_context=1000000,
        latency_p50_ms=300,
        quality_score=0.82,
        capabilities=["quick_tasks", "summarization", "extraction"],
    ),
    "gpt-4o-mini": ModelSpec(
        name="gpt-4o-mini",
        provider="openai",
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        max_context=128000,
        latency_p50_ms=350,
        quality_score=0.80,
        capabilities=["quick_tasks", "code", "reasoning"],
    ),
}


@dataclass
class RoutingDecision:
    """Model routing decision with rationale."""
    model: str
    complexity: ComplexityLevel
    estimated_cost_usd: float
    estimated_latency_ms: int
    rationale: str
    fallback_model: Optional[str] = None
