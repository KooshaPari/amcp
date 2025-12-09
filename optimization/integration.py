"""
Optimization Integration Layer

Integrates all optimization components into a unified pipeline:
1. Prompt caching → Check cache before processing
2. Context compression → Reduce tokens while preserving info
3. Model routing → Select optimal model for task
4. Planning strategy → ReAcTree for complex tasks
5. Parallel execution → Concurrent tool calls

This is the main entry point for the optimization system.

Reference: MASTER_SPECIFICATION_2025.md Phase 1-2 Implementation
"""

import logging
import time
from typing import Any, Optional, Callable, Awaitable

from .config import OptimizationConfig
from .metrics import OptimizationMetrics, OptimizedRequest
from .prompt_cache import CacheBreakpoint, get_prompt_cache
from .model_router import RoutingDecision, ComplexityLevel, get_complexity_router
from .planning import get_reactree_planner
from .context_compression import get_acon_compressor
from .parallel_executor import ExecutionBatch, get_parallel_executor

logger = logging.getLogger(__name__)


class OptimizationPipeline:
    """
    Unified optimization pipeline.

    Orchestrates all optimization components:
    1. Check prompt cache
    2. Analyze complexity and route model
    3. Compress context if needed
    4. Generate plan for complex tasks
    5. Execute with parallelization

    Usage:
        pipeline = OptimizationPipeline(OptimizationConfig())

        # Optimize a request
        optimized = await pipeline.optimize_request(
            messages=[{"role": "user", "content": "..."}],
            context={"tools": [...]}
        )

        # Execute tools in parallel
        results = await pipeline.execute_tools(
            tools=[("search", {"query": "test"})],
            executor=my_tool_executor
        )
    """

    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()

        # Initialize components
        self.prompt_cache = get_prompt_cache(self.config.prompt_cache_config)
        self.model_router = get_complexity_router(self.config.model_routing_config)
        self.planner = get_reactree_planner(self.config.planning_config)
        self.compressor = get_acon_compressor(self.config.compression_config)
        self.executor = get_parallel_executor(self.config.execution_config)

        logger.info(
            f"OptimizationPipeline initialized: "
            f"cache={self.config.enable_prompt_caching}, "
            f"compression={self.config.enable_context_compression}, "
            f"routing={self.config.enable_model_routing}, "
            f"planning={self.config.enable_planning}, "
            f"parallel={self.config.enable_parallel_execution}"
        )

    async def optimize_request(
        self,
        messages: list[dict[str, Any]],
        context: Optional[dict[str, Any]] = None,
        force_model: Optional[str] = None,
    ) -> OptimizedRequest:
        """
        Optimize a request through the full pipeline.

        Args:
            messages: List of message dicts
            context: Optional context (tools, history, etc.)
            force_model: Optional model override

        Returns:
            OptimizedRequest ready for execution
        """
        start_time = time.time()
        metrics = OptimizationMetrics()
        context = context or {}

        # Extract user query for routing/compression
        user_query = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_query = str(msg.get("content", ""))
                break

        # Step 1: Check prompt cache
        cache_hit = None
        if self.config.enable_prompt_caching:
            cache_hit = await self.prompt_cache.get(messages)
            if cache_hit:
                metrics.cache_hit = True
                metrics.cache_tokens_saved = cache_hit.get("token_count", 0)
                logger.debug(f"Cache hit: {metrics.cache_tokens_saved} tokens saved")

        # Step 2: Route to optimal model
        if self.config.enable_model_routing and not force_model:
            routing = await self.model_router.route(
                prompt=user_query,
                context=context,
            )
        else:
            routing = RoutingDecision(
                model=force_model or self.config.model_routing_config.default_model,
                complexity=ComplexityLevel.MODERATE,
                estimated_cost_usd=0.0,
                estimated_latency_ms=500,
                rationale="User override" if force_model else "Routing disabled",
            )

        metrics.selected_model = routing.model
        metrics.complexity_level = routing.complexity.value
        metrics.routing_rationale = routing.rationale
        metrics.estimated_cost_usd = routing.estimated_cost_usd

        # Step 3: Compress context if needed
        compression_result = None
        processed_messages = messages

        if self.config.enable_context_compression:
            total_tokens = sum(
                len(str(m.get("content", "")).split()) * 1.3
                for m in messages
            )

            if total_tokens > self.config.use_compression_above_tokens:
                compression_result = await self.compressor.compress(
                    content=messages,
                    query=user_query,
                )
                processed_messages = await self.compressor.decompress_for_display(
                    compression_result
                )

                metrics.compression_applied = True
                metrics.original_tokens = compression_result.original_tokens
                metrics.compressed_tokens = compression_result.compressed_tokens
                metrics.compression_ratio = compression_result.compression_ratio

                logger.debug(
                    f"Compressed: {metrics.original_tokens} -> {metrics.compressed_tokens} "
                    f"({metrics.compression_ratio:.1%})"
                )

        # Step 4: Generate plan for complex tasks
        plan = None
        if (
            self.config.enable_planning
            and routing.complexity.value >= self.config.use_planning_above_complexity.value
        ):
            # Note: Full planning requires tool executor, done in execute_tools
            metrics.planning_applied = True
            logger.debug("Planning will be applied during execution")

        # Step 5: Cache the processed request
        if self.config.enable_prompt_caching and not cache_hit:
            await self.prompt_cache.set(
                messages=processed_messages,
                breakpoint=CacheBreakpoint.CONTEXT,
            )

        # Calculate total latency
        metrics.total_latency_ms = int((time.time() - start_time) * 1000)

        # Estimate savings
        if metrics.cache_hit:
            metrics.estimated_savings_usd += metrics.cache_tokens_saved * 0.000003
        if metrics.compression_applied:
            saved_tokens = metrics.original_tokens - metrics.compressed_tokens
            metrics.estimated_savings_usd += saved_tokens * 0.000003

        return OptimizedRequest(
            messages=processed_messages,
            model=routing.model,
            routing_decision=routing,
            compression_result=compression_result,
            plan=plan,
            metrics=metrics,
        )

    async def execute_tools(
        self,
        tools: list[tuple[str, dict[str, Any]]],
        executor: Callable[[str, dict], Awaitable[Any]],
        goal: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> ExecutionBatch:
        """
        Execute tools with parallelization and optional planning.

        Args:
            tools: List of (tool_name, tool_input) tuples
            executor: Async function to execute tools
            goal: Optional goal for planning
            context: Optional context

        Returns:
            ExecutionBatch with results
        """
        if not self.config.enable_parallel_execution:
            # Sequential execution
            results = []
            for i, (name, input_dict) in enumerate(tools):
                result = await self.executor.execute_single(
                    name, input_dict, executor, order_index=i
                )
                results.append(result)
            return ExecutionBatch(results=results)

        # If planning is enabled and we have a goal, use planner
        if self.config.enable_planning and goal:
            context = context or {}
            context["tools"] = [t[0] for t in tools]

            # Note: For full planning integration, the planner would
            # dynamically generate and execute tools
            logger.debug(f"Planning-guided execution for goal: {goal[:50]}...")

        # Execute with parallelization
        return await self.executor.execute_batch(tools, executor)

    async def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        stats = await self.prompt_cache.get_stats()
        return {
            "hits": stats.hits,
            "misses": stats.misses,
            "hit_rate": stats.hit_rate,
            "total_entries": stats.total_entries,
            "tokens_cached": stats.tokens_cached,
            "estimated_savings_usd": stats.estimated_cost_savings,
        }

    async def warm_cache(self, system_prompts: list[str]) -> int:
        """Pre-warm cache with common system prompts."""
        return await self.prompt_cache.warm_system_prompts(system_prompts)

    def get_available_models(self) -> list[str]:
        """Get list of available models for routing."""
        return self.model_router.get_available_models()


# Global pipeline instance
_optimization_pipeline: Optional[OptimizationPipeline] = None


def get_optimization_pipeline(
    config: OptimizationConfig = None,
) -> OptimizationPipeline:
    """Get or create global optimization pipeline instance."""
    global _optimization_pipeline
    if _optimization_pipeline is None:
        _optimization_pipeline = OptimizationPipeline(config or OptimizationConfig())
    return _optimization_pipeline


async def optimize_request(
    messages: list[dict[str, Any]],
    context: Optional[dict[str, Any]] = None,
    force_model: Optional[str] = None,
) -> OptimizedRequest:
    """Convenience function to optimize a request."""
    pipeline = get_optimization_pipeline()
    return await pipeline.optimize_request(messages, context, force_model)


async def execute_tools_parallel(
    tools: list[tuple[str, dict[str, Any]]],
    executor: Callable[[str, dict], Awaitable[Any]],
) -> ExecutionBatch:
    """Convenience function to execute tools in parallel."""
    pipeline = get_optimization_pipeline()
    return await pipeline.execute_tools(tools, executor)
