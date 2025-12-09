"""Shared fixtures for streaming performance tests.

Domain-specific fixtures for streaming performance testing.
"""

import pytest
from optimization import (
    OptimizationStreamHandler,
    OptimizationPhase,
    OptimizationMetric,
    OptimizationMetricType,
)
from optimization.streaming import StreamingPipeline, SSEStreamHandler


@pytest.fixture
def streaming_pipeline():
    """Create a test streaming pipeline."""
    return StreamingPipeline(max_concurrent_streams=100)
