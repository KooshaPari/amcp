"""
Production load testing package.

This package contains comprehensive load testing for HTTP/2 + SSE streaming:
- Concurrent stream loads (100-500+ streams)
- Sustained high-throughput scenarios
- Bottleneck identification
- Capacity planning
- Performance degradation analysis

Modules:
- conftest: Shared fixtures and utilities
- test_load_scenarios: Concurrent and sustained load tests
- test_load_metrics: Metrics analysis and bottleneck identification
- test_load_capacity: Capacity planning and resource analysis
"""

from .conftest import (
    LoadTestMetrics,
    emit_metrics_for_stream,
    run_concurrent_load_test,
    run_sustained_load_test,
)

__all__ = [
    "LoadTestMetrics",
    "emit_metrics_for_stream",
    "run_concurrent_load_test",
    "run_sustained_load_test",
]
