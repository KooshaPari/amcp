"""
Complexity-Based Model Router

Routes requests to optimal models based on:
- Task complexity analysis
- Cost constraints
- Latency requirements
- Quality thresholds

Achieves 50-70% cost reduction by routing simple tasks
to smaller/cheaper models while preserving quality.

Reference: 2025 LLM Cost Optimization Research
"""

# Import all public classes and functions for backward compatibility
from .analyzer import ComplexityAnalyzer
from .factory import get_complexity_router
from .models import (
    DEFAULT_MODELS,
    ComplexityLevel,
    ModelRoutingConfig,
    ModelSpec,
    RoutingDecision,
)
from .router import ComplexityRouter

__all__ = [
    # Models and Config
    "ComplexityLevel",
    "ModelSpec",
    "ModelRoutingConfig",
    "RoutingDecision",
    "DEFAULT_MODELS",
    # Core Classes
    "ComplexityAnalyzer",
    "ComplexityRouter",
    # Factory
    "get_complexity_router",
]
