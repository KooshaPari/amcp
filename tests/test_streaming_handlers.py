"""Tests for Streaming Handlers

Comprehensive tests for optimization pipeline streaming handlers including:
- OptimizationStreamHandler base functionality
- Prompt cache streaming
- Model routing streaming
- ReAcTree planning streaming
- Context compression streaming
- Parallel execution streaming
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from optimization import (
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
from optimization.streaming import StreamingPipeline, SSEStreamHandler, StreamEvent, StreamEventType


@pytest.fixture
def streaming_pipeline():
    """Create a test streaming pipeline."""
    return StreamingPipeline(max_concurrent_streams=10)


@pytest.fixture
async def streaming_pipeline_with_stream():
    """Create a test streaming pipeline with an active stream."""
    pipeline = StreamingPipeline(max_concurrent_streams=10)
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)

    yield pipeline, stream_id

    await pipeline.close_stream(stream_id)


# ============================================================================
# Metric Tests
# ============================================================================

def test_metric_creation():
    """Test creating an optimization metric."""
    metric = OptimizationMetric(
        type=OptimizationMetricType.COST_REDUCTION,
        value=42.5,
        unit="percent"
    )

    assert metric.type == OptimizationMetricType.COST_REDUCTION
    assert metric.value == 42.5
    assert metric.unit == "percent"
    assert metric.timestamp is not None


def test_metric_to_dict():
    """Test converting metric to dictionary."""
    metric = OptimizationMetric(
        type=OptimizationMetricType.TOKEN_REDUCTION,
        value=1024,
        unit="tokens"
    )

    result = metric.to_dict()
    assert result["type"] == "token_reduction"
    assert result["value"] == 1024
    assert result["unit"] == "tokens"
    assert "timestamp" in result


# ============================================================================
# OptimizationStreamHandler Tests
# ============================================================================

@pytest.mark.asyncio
async def test_handler_initialization(streaming_pipeline_with_stream):
    """Test handler initialization."""
    pipeline, stream_id = await streaming_pipeline_with_stream.__anext__() if hasattr(streaming_pipeline_with_stream, '__anext__') else (
        await (lambda: streaming_pipeline_with_stream)()
    )
    # Manual async fixture handling for class method compatibility
    pipeline = StreamingPipeline(max_concurrent_streams=10)
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)

    handler = OptimizationStreamHandler(stream_id, pipeline)

    assert handler.stream_id is not None
    assert handler.current_phase == OptimizationPhase.INITIALIZATION
    assert handler.start_time is not None
    assert handler.metrics == []

    await pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_emit_phase_start(streaming_pipeline):
    """Test emitting phase start event."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    handler = OptimizationStreamHandler(stream_id, pipeline)

    await handler.emit_phase_start(OptimizationPhase.ANALYSIS)
    assert handler.current_phase == OptimizationPhase.ANALYSIS

    await pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_emit_phase_complete(streaming_pipeline):
    """Test emitting phase complete event."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    handler = OptimizationStreamHandler(stream_id, pipeline)

    await handler.emit_phase_start(OptimizationPhase.ANALYSIS)
    await handler.emit_phase_complete(
        OptimizationPhase.ANALYSIS,
        result={"items_analyzed": 100}
    )
    assert handler.current_phase == OptimizationPhase.ANALYSIS

    await pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_emit_metric(streaming_pipeline):
    """Test emitting optimization metric."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    handler = OptimizationStreamHandler(stream_id, pipeline)

    metric = OptimizationMetric(
        type=OptimizationMetricType.COST_REDUCTION,
        value=50.0,
        unit="percent"
    )

    await handler.emit_metric(metric)
    assert len(handler.metrics) == 1
    assert handler.metrics[0] == metric

    await pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_emit_progress(streaming_pipeline):
    """Test emitting progress update."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    handler = OptimizationStreamHandler(stream_id, pipeline)

    await handler.emit_progress(
        current=50,
        total=100,
        details={"stage": "initialization"}
    )
    # Progress should be emitted without raising exception

    await pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_emit_error(streaming_pipeline):
    """Test emitting error event."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    handler = OptimizationStreamHandler(stream_id, pipeline)

    await handler.emit_error(
        "Test error occurred",
        error_type="TestError"
    )
    # Error should be emitted without raising exception

    await pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_emit_completion(streaming_pipeline):
    """Test emitting completion event."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    handler = OptimizationStreamHandler(stream_id, pipeline)

    result = {
        "total_cost_saved": 150.0,
        "total_tokens_saved": 5000,
        "optimization_success": True
    }

    await handler.emit_completion(True, result)
    # Completion should be emitted without raising exception

    await pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_get_summary(streaming_pipeline):
    """Test getting handler summary."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    handler = OptimizationStreamHandler(stream_id, pipeline)

    metric = OptimizationMetric(
        type=OptimizationMetricType.COST_REDUCTION,
        value=25.0,
        unit="percent"
    )
    await handler.emit_metric(metric)

    summary = handler.get_summary()
    assert summary["stream_id"] == handler.stream_id
    assert "duration" in summary
    assert summary["current_phase"] == "initialization"
    assert summary["metrics_collected"] == 1
    assert len(summary["metrics"]) == 1

    await pipeline.close_stream(stream_id)


# ============================================================================
# PromptCacheStreamHandler Tests
# ============================================================================

@pytest.mark.asyncio
async def test_emit_cache_analysis(streaming_pipeline):
    """Test emitting cache analysis results."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    opt_handler = OptimizationStreamHandler(stream_id, pipeline)
    cache_handler = PromptCacheStreamHandler(opt_handler)

    await cache_handler.emit_cache_analysis(
        total_prompts=100,
        cacheable_prompts=75
    )
    # Should emit progress without raising exception

    await pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_emit_cache_hit(streaming_pipeline):
    """Test emitting cache hit event."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    opt_handler = OptimizationStreamHandler(stream_id, pipeline)
    cache_handler = PromptCacheStreamHandler(opt_handler)

    await cache_handler.emit_cache_hit(
        prompt_hash="abc123",
        cost_saved=0.50,
        tokens_saved=512
    )

    assert len(opt_handler.metrics) >= 1

    await pipeline.close_stream(stream_id)


# ============================================================================
# ModelRoutingStreamHandler Tests
# ============================================================================

@pytest.mark.asyncio
async def test_emit_complexity_analysis(streaming_pipeline):
    """Test emitting complexity analysis result."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    opt_handler = OptimizationStreamHandler(stream_id, pipeline)
    routing_handler = ModelRoutingStreamHandler(opt_handler)

    await routing_handler.emit_complexity_analysis(
        input_text="Test input text",
        complexity_score=7.5,
        selected_model="claude-sonnet-4"
    )

    assert len(opt_handler.metrics) == 1
    assert opt_handler.metrics[0].type == OptimizationMetricType.COMPLEXITY_LEVEL

    await pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_emit_routing_decision(streaming_pipeline):
    """Test emitting routing decision."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    opt_handler = OptimizationStreamHandler(stream_id, pipeline)
    routing_handler = ModelRoutingStreamHandler(opt_handler)

    await routing_handler.emit_routing_decision(
        model="gemini-flash",
        cost_estimate=0.001,
        latency_estimate=0.5
    )
    # Should emit without raising exception

    await pipeline.close_stream(stream_id)


# ============================================================================
# ReAcTreeStreamHandler Tests
# ============================================================================

@pytest.mark.asyncio
async def test_emit_tree_exploration(streaming_pipeline):
    """Test emitting tree exploration event."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    opt_handler = OptimizationStreamHandler(stream_id, pipeline)
    tree_handler = ReAcTreeStreamHandler(opt_handler)

    await tree_handler.emit_tree_exploration(
        node_id="node_123",
        depth=3,
        reasoning="Exploring this branch for optimization"
    )

    assert len(opt_handler.metrics) == 1
    assert opt_handler.metrics[0].type == OptimizationMetricType.TREE_DEPTH

    await pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_emit_action_execution(streaming_pipeline):
    """Test emitting action execution event."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    opt_handler = OptimizationStreamHandler(stream_id, pipeline)
    tree_handler = ReAcTreeStreamHandler(opt_handler)

    await tree_handler.emit_action_execution(
        node_id="node_123",
        action="apply_optimization",
        success=True,
        result="Optimization applied successfully"
    )
    # Should emit without raising exception

    await pipeline.close_stream(stream_id)


# ============================================================================
# ContextCompressionStreamHandler Tests
# ============================================================================

@pytest.mark.asyncio
async def test_emit_compression_analysis(streaming_pipeline):
    """Test emitting compression analysis result."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    opt_handler = OptimizationStreamHandler(stream_id, pipeline)
    compression_handler = ContextCompressionStreamHandler(opt_handler)

    await compression_handler.emit_compression_analysis(
        original_tokens=10000,
        compressed_tokens=5000
    )

    assert len(opt_handler.metrics) == 1
    assert opt_handler.metrics[0].type == OptimizationMetricType.TOKEN_REDUCTION
    assert opt_handler.metrics[0].value == 50.0

    await pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_emit_chunk_compression(streaming_pipeline):
    """Test emitting chunk compression event."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    opt_handler = OptimizationStreamHandler(stream_id, pipeline)
    compression_handler = ContextCompressionStreamHandler(opt_handler)

    await compression_handler.emit_chunk_compression(
        chunk_id="chunk_001",
        original_size=1024,
        compressed_size=512
    )
    # Should emit without raising exception

    await pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_token_reduction_percentage_calculation(streaming_pipeline):
    """Test token reduction percentage calculation."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    opt_handler = OptimizationStreamHandler(stream_id, pipeline)
    compression_handler = ContextCompressionStreamHandler(opt_handler)

    await compression_handler.emit_compression_analysis(
        original_tokens=1000,
        compressed_tokens=300
    )

    metric = opt_handler.metrics[0]
    assert metric.value == 70.0  # 70% reduction

    await pipeline.close_stream(stream_id)


# ============================================================================
# ParallelExecutionStreamHandler Tests
# ============================================================================

@pytest.mark.asyncio
async def test_emit_parallelization(streaming_pipeline):
    """Test emitting parallelization metric."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    opt_handler = OptimizationStreamHandler(stream_id, pipeline)
    parallel_handler = ParallelExecutionStreamHandler(opt_handler)

    await parallel_handler.emit_parallelization(
        total_tasks=100,
        parallel_tasks=50
    )

    assert len(opt_handler.metrics) == 1
    assert opt_handler.metrics[0].type == OptimizationMetricType.PARALLELIZATION_FACTOR
    assert opt_handler.metrics[0].value == 0.5

    await pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_emit_task_execution(streaming_pipeline):
    """Test emitting task execution event."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    opt_handler = OptimizationStreamHandler(stream_id, pipeline)
    parallel_handler = ParallelExecutionStreamHandler(opt_handler)

    await parallel_handler.emit_task_execution(
        task_id="task_001",
        task_name="process_batch",
        duration=1.5,
        success=True
    )
    # Should emit without raising exception

    await pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_emit_concurrency_status(streaming_pipeline):
    """Test emitting concurrency status."""
    pipeline = streaming_pipeline
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(sse_handler)
    opt_handler = OptimizationStreamHandler(stream_id, pipeline)
    parallel_handler = ParallelExecutionStreamHandler(opt_handler)

    await parallel_handler.emit_concurrency_status(
        active_tasks=8,
        max_concurrency=10
    )
    # Should emit without raising exception

    await pipeline.close_stream(stream_id)


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_full_optimization_pipeline(streaming_pipeline):
    """Test a full optimization pipeline with multiple handlers."""
    # Create optimization stream
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await streaming_pipeline.create_stream(sse_handler)

    # Create main handler
    opt_handler = OptimizationStreamHandler(stream_id, streaming_pipeline)

    # Create specialized handlers
    cache_handler = PromptCacheStreamHandler(opt_handler)
    routing_handler = ModelRoutingStreamHandler(opt_handler)
    parallel_handler = ParallelExecutionStreamHandler(opt_handler)

    # Simulate optimization pipeline
    await opt_handler.emit_phase_start(OptimizationPhase.ANALYSIS)
    await cache_handler.emit_cache_analysis(total_prompts=100, cacheable_prompts=80)
    await routing_handler.emit_complexity_analysis(
        input_text="test input",
        complexity_score=6.5,
        selected_model="claude-sonnet-4"
    )

    await opt_handler.emit_phase_complete(OptimizationPhase.ANALYSIS)

    await opt_handler.emit_phase_start(OptimizationPhase.OPTIMIZATION)
    await parallel_handler.emit_parallelization(total_tasks=50, parallel_tasks=40)
    await opt_handler.emit_phase_complete(OptimizationPhase.OPTIMIZATION)

    # Verify metrics collected
    summary = opt_handler.get_summary()
    assert summary["metrics_collected"] >= 2

    await streaming_pipeline.close_stream(stream_id)


@pytest.mark.asyncio
async def test_handler_phases_sequence(streaming_pipeline):
    """Test expected sequence of optimization phases."""
    sse_handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await streaming_pipeline.create_stream(sse_handler)
    handler = OptimizationStreamHandler(stream_id, streaming_pipeline)

    phases_to_test = [
        OptimizationPhase.INITIALIZATION,
        OptimizationPhase.ANALYSIS,
        OptimizationPhase.OPTIMIZATION,
        OptimizationPhase.EXECUTION,
        OptimizationPhase.VALIDATION,
        OptimizationPhase.COMPLETION,
    ]

    for phase in phases_to_test:
        await handler.emit_phase_start(phase)
        assert handler.current_phase == phase
        await handler.emit_phase_complete(phase)

    await streaming_pipeline.close_stream(stream_id)


# ============================================================================
# Factory Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_optimization_stream():
    """Test creating optimization stream."""
    stream_id = await create_optimization_stream()
    assert stream_id is not None
    assert isinstance(stream_id, str)
    assert len(stream_id) > 0


@pytest.mark.asyncio
async def test_get_optimization_handler():
    """Test getting optimization handler."""
    stream_id = await create_optimization_stream()
    handler = await get_optimization_handler(stream_id)

    assert handler is not None
    assert isinstance(handler, OptimizationStreamHandler)
    assert handler.stream_id == stream_id


# ============================================================================
# Coverage Tests
# ============================================================================

@pytest.mark.asyncio
async def test_metric_types_coverage():
    """Test coverage of all metric types."""
    metric_types = [
        OptimizationMetricType.COST_REDUCTION,
        OptimizationMetricType.TOKEN_REDUCTION,
        OptimizationMetricType.TIME_IMPROVEMENT,
        OptimizationMetricType.QUALITY_SCORE,
        OptimizationMetricType.CACHE_HIT,
        OptimizationMetricType.COMPLEXITY_LEVEL,
        OptimizationMetricType.TREE_DEPTH,
        OptimizationMetricType.PARALLELIZATION_FACTOR,
    ]

    for metric_type in metric_types:
        metric = OptimizationMetric(
            type=metric_type,
            value=42.0,
            unit="test"
        )
        assert metric.type == metric_type


@pytest.mark.asyncio
async def test_optimization_phase_coverage():
    """Test coverage of all optimization phases."""
    phases = [
        OptimizationPhase.INITIALIZATION,
        OptimizationPhase.ANALYSIS,
        OptimizationPhase.OPTIMIZATION,
        OptimizationPhase.EXECUTION,
        OptimizationPhase.VALIDATION,
        OptimizationPhase.COMPLETION,
    ]

    for phase in phases:
        assert phase.value is not None
        assert isinstance(phase.value, str)
