"""
Optimization Configuration

Configuration classes for the optimization system.
Centralizes all feature flags and component configs.

Reference: MASTER_SPECIFICATION_2025.md Phase 1-2 Implementation
"""

from dataclasses import dataclass, field

from .prompt_cache import PromptCacheConfig
from .model_router import ModelRoutingConfig, ComplexityLevel
from .planning_strategy import PlanningConfig
from .context_compression import CompressionConfig
from .parallel_executor import ExecutionConfig


@dataclass
class OptimizationConfig:
    """Master configuration for all optimizations."""

    # Feature flags
    enable_prompt_caching: bool = True
    enable_context_compression: bool = True
    enable_model_routing: bool = True
    enable_planning: bool = True
    enable_parallel_execution: bool = True

    # Component configs
    prompt_cache_config: PromptCacheConfig = field(default_factory=PromptCacheConfig)
    model_routing_config: ModelRoutingConfig = field(default_factory=ModelRoutingConfig)
    planning_config: PlanningConfig = field(default_factory=PlanningConfig)
    compression_config: CompressionConfig = field(default_factory=CompressionConfig)
    execution_config: ExecutionConfig = field(default_factory=ExecutionConfig)

    # Thresholds
    use_planning_above_complexity: ComplexityLevel = ComplexityLevel.COMPLEX
    use_compression_above_tokens: int = 5000

    # Metrics
    enable_metrics: bool = True
