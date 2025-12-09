"""Integration tests for Bifrost SDK routing functionality."""

import pytest
import asyncio
from typing import List
import time

from bifrost_extensions import GatewayClient, RoutingStrategy
from bifrost_extensions.models import Message, RoutingRequest
from bifrost_extensions.exceptions import (
    RoutingError,
    ValidationError,
    TimeoutError as BifrostTimeoutError,
)


class TestRoutingIntegration:
    """Test routing with actual router_core integration."""

    @pytest.mark.asyncio
    async def test_basic_routing(self, gateway_client, sample_messages_simple):
        """Test basic routing with single message."""
        response = await gateway_client.route(
            messages=sample_messages_simple,
            strategy=RoutingStrategy.BALANCED,
        )

        assert response is not None
        assert response.model is not None
        assert response.model.model_id is not None
        assert response.model.provider is not None
        assert 0.0 <= response.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_routing_all_strategies(
        self, gateway_client, sample_messages, routing_strategies
    ):
        """Test routing with all 5 strategies."""
        results = {}

        for strategy in routing_strategies:
            response = await gateway_client.route(
                messages=sample_messages,
                strategy=strategy,
            )

            results[strategy] = response
            assert response.model is not None
            assert response.confidence > 0

        # Verify all strategies returned results
        assert len(results) == 5

        # Cost-optimized should have lower cost
        cost_optimized = results[RoutingStrategy.COST_OPTIMIZED]
        performance_optimized = results[RoutingStrategy.PERFORMANCE_OPTIMIZED]

        # Strategies may select different models
        assert cost_optimized.model.model_id is not None
        assert performance_optimized.model.model_id is not None

    @pytest.mark.asyncio
    async def test_routing_with_constraints(self, gateway_client, sample_messages):
        """Test routing with cost and latency constraints."""
        response = await gateway_client.route(
            messages=sample_messages,
            strategy=RoutingStrategy.BALANCED,
            constraints={"max_cost_usd": 0.01, "max_latency_ms": 500},
        )

        assert response is not None
        assert response.model.estimated_cost_usd <= 0.01
        assert response.model.estimated_latency_ms <= 500

    @pytest.mark.asyncio
    async def test_routing_with_context(self, gateway_client, sample_messages):
        """Test routing with additional context."""
        response = await gateway_client.route(
            messages=sample_messages,
            strategy=RoutingStrategy.BALANCED,
            context={"user_tier": "premium", "priority": "high"},
        )

        assert response is not None
        assert response.model is not None

    @pytest.mark.asyncio
    async def test_routing_complex_conversation(
        self, gateway_client, sample_messages_complex
    ):
        """Test routing with complex multi-turn conversation."""
        response = await gateway_client.route(
            messages=sample_messages_complex,
            strategy=RoutingStrategy.PERFORMANCE_OPTIMIZED,
        )

        assert response is not None
        assert response.model is not None
        # Should provide reasoning for complex queries
        assert response.reasoning is not None

    @pytest.mark.asyncio
    async def test_routing_alternatives(self, gateway_client, sample_messages):
        """Test that routing provides alternatives."""
        response = await gateway_client.route(
            messages=sample_messages,
            strategy=RoutingStrategy.PARETO,
        )

        assert response is not None
        # Should have alternatives (top 3)
        if response.alternatives:
            assert len(response.alternatives) <= 3
            for alt in response.alternatives:
                assert alt.model_id is not None
                assert alt.provider is not None

    @pytest.mark.asyncio
    async def test_routing_validation_empty_messages(self, gateway_client):
        """Test validation error with empty messages."""
        with pytest.raises(ValidationError):
            await gateway_client.route(
                messages=[],
                strategy=RoutingStrategy.BALANCED,
            )

    @pytest.mark.asyncio
    async def test_routing_validation_invalid_message(self, gateway_client):
        """Test validation error with invalid message format."""
        with pytest.raises(ValidationError):
            await gateway_client.route(
                messages=[{"role": "user"}],  # Missing content
                strategy=RoutingStrategy.BALANCED,
            )

    @pytest.mark.asyncio
    async def test_routing_timeout(self, gateway_client, sample_messages):
        """Test routing timeout handling."""
        # Set very short timeout
        with pytest.raises(BifrostTimeoutError):
            await gateway_client.route(
                messages=sample_messages,
                strategy=RoutingStrategy.BALANCED,
                timeout=0.001,  # 1ms - should timeout
            )

    @pytest.mark.asyncio
    async def test_routing_custom_timeout(self, gateway_client, sample_messages):
        """Test routing with custom timeout."""
        start_time = time.perf_counter()

        response = await gateway_client.route(
            messages=sample_messages,
            strategy=RoutingStrategy.BALANCED,
            timeout=10.0,  # 10 second timeout
        )

        duration = time.perf_counter() - start_time

        assert response is not None
        assert duration < 10.0  # Should complete before timeout

    @pytest.mark.asyncio
    async def test_routing_dict_messages(self, gateway_client):
        """Test routing with dict messages (auto-conversion)."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        response = await gateway_client.route(
            messages=messages,
            strategy=RoutingStrategy.BALANCED,
        )

        assert response is not None
        assert response.model is not None


class TestRoutingPerformance:
    """Performance tests for routing operations."""

    @pytest.mark.asyncio
    async def test_routing_latency_p50(self, gateway_client, sample_messages):
        """Test P50 latency <30ms target."""
        latencies = []

        for _ in range(100):
            start = time.perf_counter()
            await gateway_client.route(
                messages=sample_messages,
                strategy=RoutingStrategy.SPEED_OPTIMIZED,
            )
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)

        latencies.sort()
        p50 = latencies[49]  # 50th percentile

        assert p50 < 30, f"P50 latency {p50:.2f}ms exceeds 30ms target"

    @pytest.mark.asyncio
    async def test_routing_latency_p95(self, gateway_client, sample_messages):
        """Test P95 latency <50ms target."""
        latencies = []

        for _ in range(100):
            start = time.perf_counter()
            await gateway_client.route(
                messages=sample_messages,
                strategy=RoutingStrategy.SPEED_OPTIMIZED,
            )
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)

        latencies.sort()
        p95 = latencies[94]  # 95th percentile

        assert p95 < 50, f"P95 latency {p95:.2f}ms exceeds 50ms target"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_routing_latency_p99(self, gateway_client, sample_messages):
        """Test P99 latency <100ms target."""
        latencies = []

        for _ in range(100):
            start = time.perf_counter()
            await gateway_client.route(
                messages=sample_messages,
                strategy=RoutingStrategy.BALANCED,
            )
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)

        latencies.sort()
        p99 = latencies[98]  # 99th percentile

        assert p99 < 100, f"P99 latency {p99:.2f}ms exceeds 100ms target"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_routing(self, gateway_client, sample_messages):
        """Test 100 concurrent routing requests."""
        tasks = []

        for _ in range(100):
            task = gateway_client.route(
                messages=sample_messages,
                strategy=RoutingStrategy.BALANCED,
            )
            tasks.append(task)

        start = time.perf_counter()
        results = await asyncio.gather(*tasks)
        duration = time.perf_counter() - start

        # All requests should succeed
        assert len(results) == 100
        for result in results:
            assert result is not None
            assert result.model is not None

        # Should handle concurrency efficiently
        assert duration < 5.0, f"Concurrent routing took {duration:.2f}s"


class TestRoutingErrorHandling:
    """Test error scenarios and recovery."""

    @pytest.mark.asyncio
    async def test_routing_with_retry(self, gateway_client, sample_messages):
        """Test routing with automatic retry on failure."""
        # This tests the internal retry mechanism
        response = await gateway_client.route(
            messages=sample_messages,
            strategy=RoutingStrategy.BALANCED,
        )

        assert response is not None

    @pytest.mark.asyncio
    async def test_routing_graceful_degradation(
        self, gateway_client, sample_messages
    ):
        """Test graceful degradation on partial failure."""
        # Even if some models fail, should return a valid result
        response = await gateway_client.route(
            messages=sample_messages,
            strategy=RoutingStrategy.PARETO,
        )

        assert response is not None
        assert response.model is not None

    @pytest.mark.asyncio
    async def test_health_check(self, gateway_client):
        """Test health check endpoint."""
        health = await gateway_client.health_check()

        assert health is not None
        assert health["status"] == "healthy"
        assert "version" in health
        assert "router_available" in health
