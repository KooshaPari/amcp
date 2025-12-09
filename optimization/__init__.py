"""
SmartCP Optimization Module

2025-grade optimizations for agentic AI systems:
- Prompt caching (90% cost reduction on cache hits)
- Complexity-based model routing (50-70% cost reduction)
- ReAcTree planning (61% success vs 31% ReAct)
- ACON context compression (26-54% token reduction)
- Parallel tool execution (3-5x throughput)
- Multi-agent orchestration (hierarchical delegation)
"""

from .core_integration import *
from .core_caching import *
from .core_routing import *
from .core_planning import *
from .core_compression import *
from .core_parallel import *
from .core_streaming import *
from .core_http2 import *
from .core_fastapi import *
from .core_handlers import *

__all__ = [
    # Core integration
    "OptimizationConfig",
    "OptimizationMetrics",
    "OptimizedRequest",
    "OptimizationPipeline",
    "get_optimization_pipeline",
    # Caching
    "PromptCache",
    "PromptCacheConfig",
    # Routing
    "ComplexityRouter",
    "ModelRoutingConfig",
    "ComplexityLevel",
    # Planning
    "PlanningStrategy",
    "ReAcTreePlanner",
    "PlanNode",
    "PlanningConfig",
    # Compression
    "ContextCompressor",
    "ACONCompressor",
    "CompressionConfig",
    # Parallel
    "ParallelToolExecutor",
    "ExecutionConfig",
    "ToolResult",
    # Streaming
    "StreamEvent",
    "StreamEventType",
    "StreamMetrics",
    "SSEStreamHandler",
    "StreamingPipeline",
    "StreamingOptimizer",
    "get_streaming_pipeline",
    # FastAPI
    "create_streaming_router",
    # HTTP/2
    "HTTP2Config",
    "HTTP2ServerFactory",
    "HTTP2Middleware",
    "create_http2_middleware",
    "get_server_startup_command",
    "HTTP2App",
    "setup_http2_app",
    # Handlers
    "OptimizationStreamHandler",
    "OptimizationPhase",
    "OptimizationMetric",
    "OptimizationMetricType",
    "PromptCacheStreamHandler",
    "ModelRoutingStreamHandler",
    "ReAcTreeStreamHandler",
    "ContextCompressionStreamHandler",
    "ParallelExecutionStreamHandler",
    "create_optimization_stream",
    "get_optimization_handler",
]
