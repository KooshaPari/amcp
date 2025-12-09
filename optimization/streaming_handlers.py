"""Stream Response Handlers for Optimization Pipeline

Provides handlers for streaming optimization pipeline progress, metrics, and results
over HTTP/2 and SSE connections.

Handlers for:
- Prompt caching optimization (cache hits, cost reduction)
- Model routing and complexity analysis
- ReAcTree planning execution and tree traversal
- Context compression and token reduction
- Parallel tool execution with progress tracking
- Streaming optimization and batching

Integration Points:
- FastAPI StreamingResponse for efficient protocol handling
- HTTP/2 multiplexing for concurrent stream optimization
- SSE for real-time progress updates
- Metrics collection for performance monitoring
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, Optional

from .streaming import StreamEvent, StreamEventType, StreamingPipeline, get_streaming_pipeline

logger = logging.getLogger(__name__)


class OptimizationPhase(str, Enum):
    """Phases of optimization pipeline execution."""
    INITIALIZATION = "initialization"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    EXECUTION = "execution"
    VALIDATION = "validation"
    COMPLETION = "completion"


class OptimizationMetricType(str, Enum):
    """Types of optimization metrics."""
    COST_REDUCTION = "cost_reduction"
    TOKEN_REDUCTION = "token_reduction"
    TIME_IMPROVEMENT = "time_improvement"
    QUALITY_SCORE = "quality_score"
    CACHE_HIT = "cache_hit"
    COMPLEXITY_LEVEL = "complexity_level"
    TREE_DEPTH = "tree_depth"
    PARALLELIZATION_FACTOR = "parallelization_factor"


@dataclass
class OptimizationMetric:
    """Single optimization metric."""
    type: OptimizationMetricType
    value: float
    unit: str
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
        }


class OptimizationStreamHandler:
    """Handler for streaming optimization pipeline progress."""

    def __init__(self, stream_id: str, pipeline: StreamingPipeline):
        """Initialize optimization stream handler.

        Args:
            stream_id: Unique stream identifier
            pipeline: StreamingPipeline for emitting events
        """
        self.stream_id = stream_id
        self.pipeline = pipeline
        self.start_time = time.time()
        self.current_phase = OptimizationPhase.INITIALIZATION
        self.metrics: list[OptimizationMetric] = []
        self.phase_start_time = self.start_time

    async def emit_phase_start(self, phase: OptimizationPhase) -> None:
        """Emit phase start event.

        Args:
            phase: Optimization phase starting
        """
        self.current_phase = phase
        self.phase_start_time = time.time()

        event = StreamEvent(
            type=StreamEventType.PROGRESS,
            data={
                "phase": phase.value,
                "action": "phase_started",
                "timestamp": self.phase_start_time,
            }
        )
        await self.pipeline.emit_event(self.stream_id, event)
        logger.debug(f"Stream {self.stream_id}: phase {phase.value} started")

    async def emit_phase_complete(
        self,
        phase: OptimizationPhase,
        result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit phase complete event.

        Args:
            phase: Optimization phase completed
            result: Optional result data from phase
        """
        duration = time.time() - self.phase_start_time

        event = StreamEvent(
            type=StreamEventType.PROGRESS,
            data={
                "phase": phase.value,
                "action": "phase_completed",
                "duration": duration,
                "result": result,
            }
        )
        await self.pipeline.emit_event(self.stream_id, event)
        logger.debug(f"Stream {self.stream_id}: phase {phase.value} completed in {duration:.2f}s")

    async def emit_metric(self, metric: OptimizationMetric) -> None:
        """Emit optimization metric.

        Args:
            metric: Optimization metric to emit
        """
        self.metrics.append(metric)

        event = StreamEvent(
            type=StreamEventType.DATA,
            data={
                "metric": metric.to_dict(),
                "total_metrics": len(self.metrics),
            }
        )
        await self.pipeline.emit_event(self.stream_id, event)
        logger.debug(
            f"Stream {self.stream_id}: metric {metric.type.value} = {metric.value} {metric.unit}"
        )

    async def emit_progress(
        self,
        current: int,
        total: int,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit progress update.

        Args:
            current: Current progress count
            total: Total items to process
            details: Optional detailed information
        """
        percentage = (current / total * 100) if total > 0 else 0

        event = StreamEvent(
            type=StreamEventType.PROGRESS,
            data={
                "current": current,
                "total": total,
                "percentage": percentage,
                "phase": self.current_phase.value,
                "details": details,
            }
        )
        await self.pipeline.emit_event(self.stream_id, event)

    async def emit_data(self, data: Dict[str, Any]) -> None:
        """Emit data update.

        Args:
            data: Data to emit
        """
        event = StreamEvent(
            type=StreamEventType.DATA,
            data=data
        )
        await self.pipeline.emit_event(self.stream_id, event)

    async def emit_error(self, error: str, error_type: Optional[str] = None) -> None:
        """Emit error event.

        Args:
            error: Error message
            error_type: Optional error type
        """
        event = StreamEvent(
            type=StreamEventType.ERROR,
            data={
                "error": error,
                "error_type": error_type,
                "timestamp": time.time(),
            }
        )
        await self.pipeline.emit_event(self.stream_id, event)
        logger.error(f"Stream {self.stream_id}: {error}")

    async def emit_completion(
        self,
        success: bool,
        result: Dict[str, Any],
    ) -> None:
        """Emit completion event with final result.

        Args:
            success: Whether optimization succeeded
            result: Final result dictionary
        """
        total_duration = time.time() - self.start_time

        event = StreamEvent(
            type=StreamEventType.COMPLETE,
            data={
                "success": success,
                "duration": total_duration,
                "phases_completed": self.current_phase.value,
                "metric_count": len(self.metrics),
                "result": result,
            }
        )
        await self.pipeline.emit_event(self.stream_id, event)
        logger.info(f"Stream {self.stream_id}: optimization completed in {total_duration:.2f}s")

    def get_summary(self) -> Dict[str, Any]:
        """Get stream summary.

        Returns:
            Summary dictionary with metrics and timing
        """
        duration = time.time() - self.start_time
        return {
            "stream_id": self.stream_id,
            "duration": duration,
            "current_phase": self.current_phase.value,
            "metrics_collected": len(self.metrics),
            "metrics": [m.to_dict() for m in self.metrics],
        }


class PromptCacheStreamHandler:
    """Handler for prompt caching optimization streaming."""

    def __init__(self, handler: OptimizationStreamHandler):
        """Initialize cache stream handler.

        Args:
            handler: Base optimization stream handler
        """
        self.handler = handler

    async def emit_cache_analysis(
        self,
        total_prompts: int,
        cacheable_prompts: int,
    ) -> None:
        """Emit cache analysis results.

        Args:
            total_prompts: Total number of prompts
            cacheable_prompts: Number of cacheable prompts
        """
        cacheable_percentage = (
            (cacheable_prompts / total_prompts * 100)
            if total_prompts > 0 else 0
        )

        await self.handler.emit_progress(
            cacheable_prompts,
            total_prompts,
            details={
                "operation": "cache_analysis",
                "cacheable_percentage": cacheable_percentage,
            }
        )

    async def emit_cache_hit(
        self,
        prompt_hash: str,
        cost_saved: float,
        tokens_saved: int,
    ) -> None:
        """Emit cache hit event.

        Args:
            prompt_hash: Hash of cached prompt
            cost_saved: Cost saved (USD)
            tokens_saved: Tokens saved
        """
        metrics = [
            OptimizationMetric(
                type=OptimizationMetricType.COST_REDUCTION,
                value=cost_saved,
                unit="USD"
            ),
            OptimizationMetric(
                type=OptimizationMetricType.CACHE_HIT,
                value=1.0,
                unit="hit"
            ),
        ]

        for metric in metrics:
            await self.handler.emit_metric(metric)

        await self.handler.emit_data({
            "operation": "cache_hit",
            "prompt_hash": prompt_hash,
            "cost_saved": cost_saved,
            "tokens_saved": tokens_saved,
        })


class ModelRoutingStreamHandler:
    """Handler for model routing and complexity analysis streaming."""

    def __init__(self, handler: OptimizationStreamHandler):
        """Initialize model routing stream handler.

        Args:
            handler: Base optimization stream handler
        """
        self.handler = handler

    async def emit_complexity_analysis(
        self,
        input_text: str,
        complexity_score: float,
        selected_model: str,
    ) -> None:
        """Emit complexity analysis result.

        Args:
            input_text: Input text analyzed
            complexity_score: Computed complexity score (0-10)
            selected_model: Model selected based on complexity
        """
        await self.handler.emit_metric(
            OptimizationMetric(
                type=OptimizationMetricType.COMPLEXITY_LEVEL,
                value=complexity_score,
                unit="score"
            )
        )

        await self.handler.emit_data({
            "operation": "complexity_analysis",
            "input_length": len(input_text),
            "complexity_score": complexity_score,
            "selected_model": selected_model,
        })

    async def emit_routing_decision(
        self,
        model: str,
        cost_estimate: float,
        latency_estimate: float,
    ) -> None:
        """Emit routing decision.

        Args:
            model: Selected model
            cost_estimate: Estimated cost (USD)
            latency_estimate: Estimated latency (seconds)
        """
        await self.handler.emit_data({
            "operation": "routing_decision",
            "model": model,
            "cost_estimate": cost_estimate,
            "latency_estimate": latency_estimate,
        })


class ReAcTreeStreamHandler:
    """Handler for ReAcTree planning streaming."""

    def __init__(self, handler: OptimizationStreamHandler):
        """Initialize ReAcTree stream handler.

        Args:
            handler: Base optimization stream handler
        """
        self.handler = handler

    async def emit_tree_exploration(
        self,
        node_id: str,
        depth: int,
        reasoning: str,
    ) -> None:
        """Emit tree exploration event.

        Args:
            node_id: Node identifier in tree
            depth: Depth in tree
            reasoning: Reasoning text
        """
        await self.handler.emit_metric(
            OptimizationMetric(
                type=OptimizationMetricType.TREE_DEPTH,
                value=float(depth),
                unit="levels"
            )
        )

        await self.handler.emit_data({
            "operation": "tree_exploration",
            "node_id": node_id,
            "depth": depth,
            "reasoning_length": len(reasoning),
        })

    async def emit_action_execution(
        self,
        node_id: str,
        action: str,
        success: bool,
        result: Optional[str] = None,
    ) -> None:
        """Emit action execution event.

        Args:
            node_id: Node executing action
            action: Action description
            success: Whether action succeeded
            result: Optional result of action
        """
        await self.handler.emit_data({
            "operation": "action_execution",
            "node_id": node_id,
            "action": action,
            "success": success,
            "result_length": len(result) if result else 0,
        })


class ContextCompressionStreamHandler:
    """Handler for context compression streaming."""

    def __init__(self, handler: OptimizationStreamHandler):
        """Initialize context compression stream handler.

        Args:
            handler: Base optimization stream handler
        """
        self.handler = handler

    async def emit_compression_analysis(
        self,
        original_tokens: int,
        compressed_tokens: int,
    ) -> None:
        """Emit compression analysis result.

        Args:
            original_tokens: Original token count
            compressed_tokens: Compressed token count
        """
        reduction_percentage = (
            ((original_tokens - compressed_tokens) / original_tokens * 100)
            if original_tokens > 0 else 0
        )

        await self.handler.emit_metric(
            OptimizationMetric(
                type=OptimizationMetricType.TOKEN_REDUCTION,
                value=reduction_percentage,
                unit="percent"
            )
        )

        await self.handler.emit_data({
            "operation": "compression_analysis",
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "reduction_percentage": reduction_percentage,
        })

    async def emit_chunk_compression(
        self,
        chunk_id: str,
        original_size: int,
        compressed_size: int,
    ) -> None:
        """Emit chunk compression event.

        Args:
            chunk_id: Chunk identifier
            original_size: Original size in bytes
            compressed_size: Compressed size in bytes
        """
        compression_ratio = (
            (compressed_size / original_size)
            if original_size > 0 else 1.0
        )

        await self.handler.emit_data({
            "operation": "chunk_compression",
            "chunk_id": chunk_id,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": compression_ratio,
        })


class ParallelExecutionStreamHandler:
    """Handler for parallel tool execution streaming."""

    def __init__(self, handler: OptimizationStreamHandler):
        """Initialize parallel execution stream handler.

        Args:
            handler: Base optimization stream handler
        """
        self.handler = handler

    async def emit_parallelization(
        self,
        total_tasks: int,
        parallel_tasks: int,
    ) -> None:
        """Emit parallelization metric.

        Args:
            total_tasks: Total number of tasks
            parallel_tasks: Number of parallel tasks
        """
        parallelization_factor = (
            (parallel_tasks / total_tasks)
            if total_tasks > 0 else 0.0
        )

        await self.handler.emit_metric(
            OptimizationMetric(
                type=OptimizationMetricType.PARALLELIZATION_FACTOR,
                value=parallelization_factor,
                unit="factor"
            )
        )

    async def emit_task_execution(
        self,
        task_id: str,
        task_name: str,
        duration: float,
        success: bool,
    ) -> None:
        """Emit task execution event.

        Args:
            task_id: Task identifier
            task_name: Task name
            duration: Execution duration (seconds)
            success: Whether task succeeded
        """
        await self.handler.emit_data({
            "operation": "task_execution",
            "task_id": task_id,
            "task_name": task_name,
            "duration": duration,
            "success": success,
        })

    async def emit_concurrency_status(
        self,
        active_tasks: int,
        max_concurrency: int,
    ) -> None:
        """Emit concurrency status.

        Args:
            active_tasks: Currently active tasks
            max_concurrency: Maximum concurrent tasks
        """
        utilization = (
            (active_tasks / max_concurrency * 100)
            if max_concurrency > 0 else 0.0
        )

        await self.handler.emit_data({
            "operation": "concurrency_status",
            "active_tasks": active_tasks,
            "max_concurrency": max_concurrency,
            "utilization_percentage": utilization,
        })


async def create_optimization_stream(
    pipeline: Optional[StreamingPipeline] = None,
) -> str:
    """Create new optimization stream.

    Args:
        pipeline: StreamingPipeline instance (uses global if not provided)

    Returns:
        Stream ID for the created stream
    """
    if pipeline is None:
        pipeline = get_streaming_pipeline()

    # Create and initialize stream
    from .streaming import SSEStreamHandler
    handler = SSEStreamHandler(queue_size=100, heartbeat_interval=30.0)
    stream_id = await pipeline.create_stream(handler)
    return stream_id


async def get_optimization_handler(
    stream_id: str,
    pipeline: Optional[StreamingPipeline] = None,
) -> OptimizationStreamHandler:
    """Get optimization handler for stream.

    Args:
        stream_id: Stream identifier
        pipeline: StreamingPipeline instance (uses global if not provided)

    Returns:
        OptimizationStreamHandler for the stream
    """
    if pipeline is None:
        pipeline = get_streaming_pipeline()

    return OptimizationStreamHandler(stream_id, pipeline)
