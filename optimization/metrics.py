"""
Optimization Metrics

Metrics and result models for optimization pipeline.
Tracks performance, cost savings, and execution statistics.

Reference: MASTER_SPECIFICATION_2025.md Phase 1-2 Implementation
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from .model_router import RoutingDecision
from .context_compression import CompressionResult
from .planning import PlanTree


@dataclass
class OptimizationMetrics:
    """Metrics from optimization pipeline."""

    # Cache metrics
    cache_hit: bool = False
    cache_tokens_saved: int = 0

    # Compression metrics
    compression_applied: bool = False
    original_tokens: int = 0
    compressed_tokens: int = 0
    compression_ratio: float = 1.0

    # Routing metrics
    selected_model: str = ""
    complexity_level: str = ""
    routing_rationale: str = ""
    estimated_cost_usd: float = 0.0

    # Planning metrics
    planning_applied: bool = False
    plan_nodes: int = 0
    plan_depth: int = 0

    # Execution metrics
    tools_executed: int = 0
    parallel_speedup: float = 1.0
    execution_time_ms: int = 0

    # Totals
    total_latency_ms: int = 0
    estimated_savings_usd: float = 0.0


@dataclass
class OptimizedRequest:
    """An optimized request ready for execution."""

    messages: list[dict[str, Any]]
    model: str
    routing_decision: RoutingDecision
    compression_result: Optional[CompressionResult] = None
    plan: Optional[PlanTree] = None
    metrics: OptimizationMetrics = field(default_factory=OptimizationMetrics)

    @property
    def token_count(self) -> int:
        """Estimated token count."""
        if self.compression_result:
            return self.compression_result.compressed_tokens
        return sum(
            len(str(m.get("content", "")).split()) * 1.3
            for m in self.messages
        )
