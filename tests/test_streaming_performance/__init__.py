"""Performance benchmarks for HTTP/2 + SSE streaming.

Measures throughput, latency, resource usage, and concurrent handling
capabilities of the streaming optimization pipeline.
"""

from .comparison import (
    test_http2_multiplexing_benefit,
    test_metric_latency_distribution,
    test_streaming_vs_polling_simulation,
)
from .concurrent_operations import (
    test_concurrent_mixed_operations,
    test_concurrent_phase_transitions,
)
from .concurrent_streams import (
    test_concurrent_streams_throughput,
    test_stream_scalability,
)
from .resource_usage import (
    test_memory_efficiency_with_streams,
    test_performance_summary,
)
from .single_stream import (
    test_full_optimization_pipeline_duration,
    test_large_metric_payload_throughput,
    test_single_stream_throughput,
)

__all__ = [
    # Single stream tests
    "test_single_stream_throughput",
    "test_large_metric_payload_throughput",
    "test_full_optimization_pipeline_duration",
    # Concurrent stream tests
    "test_concurrent_streams_throughput",
    "test_stream_scalability",
    # Concurrent operations tests
    "test_concurrent_phase_transitions",
    "test_concurrent_mixed_operations",
    # Comparison and resource tests
    "test_metric_latency_distribution",
    "test_http2_multiplexing_benefit",
    "test_streaming_vs_polling_simulation",
    "test_memory_efficiency_with_streams",
    "test_performance_summary",
]
