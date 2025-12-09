"""
SmartCP Optimization Module

2025-grade optimizations for agentic AI systems:
- Prompt caching (90% cost reduction on cache hits)
- Complexity-based model routing (50-70% cost reduction)
- ReAcTree planning (61% success vs 31% ReAct)
- ACON context compression (26-54% token reduction)
- Parallel tool execution (3-5x throughput)
- Multi-agent orchestration (hierarchical delegation)

Based on comprehensive 2025 research in:
- LLM inference optimization (KV cache, quantization, batching)
- Agent orchestration patterns (ReAcTree, ToT, MCTS)
- Context management (ACON, LLMLingua-2, Zep)
- Streaming optimizations (SSE, HTTP/2)
- Cost optimization (prompt caching, model routing)
"""

from .config import OptimizationConfig
from .metrics import OptimizationMetrics, OptimizedRequest
from .integration import OptimizationPipeline, get_optimization_pipeline
from .prompt_cache import PromptCache, PromptCacheConfig
from .model_router import (
    ComplexityRouter,
    ModelRoutingConfig,
    ComplexityLevel,
)
from .planning_strategy import (
    PlanningStrategy,
    ReAcTreePlanner,
    PlanNode,
    PlanningConfig,
)
from .context_compression import (
    ContextCompressor,
    ACONCompressor,
    CompressionConfig,
)
from .parallel_executor import (
    ParallelToolExecutor,
    ExecutionConfig,
    ToolResult,
)
from .streaming import (
    StreamEvent,
    StreamEventType,
    StreamMetrics,
    SSEStreamHandler,
    StreamingPipeline,
    StreamingOptimizer,
    get_streaming_pipeline,
)
from .fastapi_integration import create_streaming_router
from .http2_config import (
    HTTP2Config,
    HTTP2ServerFactory,
    HTTP2Middleware,
    create_http2_middleware,
    get_server_startup_command,
)
from .http2_app import (
    HTTP2App,
    setup_http2_app,
)
from .streaming_handlers import (
    OptimizationStreamHandler,
    OptimizationPhase,
    OptimizationMetric,
    OptimizationMetricType,
    PromptCacheStreamHandler,
    ModelRoutingStreamHandler,
    ReAcTreeStreamHandler,
    ContextCompressionStreamHandler,
    ParallelExecutionStreamHandler,
    create_optimization_stream,
    get_optimization_handler,
)

__all__ = [
    # Integration
    "OptimizationConfig",
    "OptimizationMetrics",
    "OptimizedRequest",
    "OptimizationPipeline",
    "get_optimization_pipeline",
    # Prompt caching
    "PromptCache",
    "PromptCacheConfig",
    # Model routing
    "ComplexityRouter",
    "ModelRoutingConfig",
    "ComplexityLevel",
    # Planning
    "PlanningStrategy",
    "ReAcTreePlanner",
    "PlanNode",
    "PlanningConfig",
    # Context compression
    "ContextCompressor",
    "ACONCompressor",
    "CompressionConfig",
    # Parallel execution
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
    # FastAPI integration
    "create_streaming_router",
    # HTTP/2
    "HTTP2Config",
    "HTTP2ServerFactory",
    "HTTP2Middleware",
    "create_http2_middleware",
    "get_server_startup_command",
    "HTTP2App",
    "setup_http2_app",
    # Streaming handlers
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
