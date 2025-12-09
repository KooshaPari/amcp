"""Integration tests for Bifrost SDK tool routing functionality."""

import pytest
import asyncio
import time
from typing import List

from bifrost_extensions import GatewayClient
from bifrost_extensions.models import ToolRoutingRequest, ToolRoutingDecision
from bifrost_extensions.exceptions import ValidationError, TimeoutError as BifrostTimeoutError


class TestToolRoutingIntegration:
    """Test tool routing with semantic router integration."""

    @pytest.mark.asyncio
    async def test_basic_tool_routing(self, gateway_client, sample_tools):
        """Test basic tool routing."""
        decision = await gateway_client.route_tool(
            action="search for Python documentation",
            available_tools=sample_tools,
        )

        assert decision is not None
        assert decision.recommended_tool in sample_tools
        assert 0.0 <= decision.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_tool_routing_web_search(self, gateway_client):
        """Test tool routing for web search action."""
        tools = ["web_search", "doc_search", "code_search"]

        decision = await gateway_client.route_tool(
            action="find latest news about AI",
            available_tools=tools,
        )

        assert decision is not None
        assert decision.recommended_tool is not None
        assert decision.reasoning is not None

    @pytest.mark.asyncio
    async def test_tool_routing_code_search(self, gateway_client):
        """Test tool routing for code search action."""
        tools = ["web_search", "doc_search", "code_search", "file_search"]

        decision = await gateway_client.route_tool(
            action="find implementation of binary search",
            available_tools=tools,
        )

        assert decision is not None
        assert decision.recommended_tool in tools

    @pytest.mark.asyncio
    async def test_tool_routing_with_context(self, gateway_client, sample_tools):
        """Test tool routing with additional context."""
        decision = await gateway_client.route_tool(
            action="search database schema",
            available_tools=sample_tools,
            context={"domain": "backend", "language": "python"},
        )

        assert decision is not None
        assert decision.recommended_tool in sample_tools

    @pytest.mark.asyncio
    async def test_tool_routing_alternatives(self, gateway_client, sample_tools):
        """Test that tool routing provides alternatives."""
        decision = await gateway_client.route_tool(
            action="search for information",
            available_tools=sample_tools,
        )

        assert decision is not None
        if decision.alternatives:
            assert len(decision.alternatives) > 0
            for alt in decision.alternatives:
                assert alt in sample_tools

    @pytest.mark.asyncio
    async def test_tool_routing_validation_empty_action(self, gateway_client, sample_tools):
        """Test validation error with empty action."""
        with pytest.raises(ValidationError, match="Action cannot be empty"):
            await gateway_client.route_tool(
                action="",
                available_tools=sample_tools,
            )

    @pytest.mark.asyncio
    async def test_tool_routing_validation_empty_tools(self, gateway_client):
        """Test validation error with empty tools list."""
        with pytest.raises(ValidationError, match="Must provide at least one available tool"):
            await gateway_client.route_tool(
                action="search something",
                available_tools=[],
            )

    @pytest.mark.asyncio
    async def test_tool_routing_timeout(self, gateway_client, sample_tools):
        """Test tool routing timeout handling."""
        with pytest.raises(BifrostTimeoutError):
            await gateway_client.route_tool(
                action="search for something",
                available_tools=sample_tools,
                timeout=0.001,  # 1ms - should timeout
            )

    @pytest.mark.asyncio
    async def test_tool_routing_custom_timeout(self, gateway_client, sample_tools):
        """Test tool routing with custom timeout."""
        start = time.perf_counter()

        decision = await gateway_client.route_tool(
            action="search for information",
            available_tools=sample_tools,
            timeout=5.0,
        )

        duration = time.perf_counter() - start

        assert decision is not None
        assert duration < 5.0


class TestToolRoutingPerformance:
    """Performance tests for tool routing."""

    @pytest.mark.asyncio
    async def test_tool_routing_latency(self, gateway_client, sample_tools):
        """Test tool routing latency is reasonable."""
        latencies = []

        for _ in range(50):
            start = time.perf_counter()
            await gateway_client.route_tool(
                action="search for something",
                available_tools=sample_tools,
            )
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)

        latencies.sort()
        p50 = latencies[24]  # 50th percentile
        p95 = latencies[47]  # 95th percentile

        # Tool routing should be fast (<100ms P95)
        assert p50 < 50, f"P50 latency {p50:.2f}ms too high"
        assert p95 < 100, f"P95 latency {p95:.2f}ms too high"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_tool_routing(self, gateway_client, sample_tools):
        """Test concurrent tool routing requests."""
        actions = [
            "search web",
            "search code",
            "search docs",
            "search files",
        ] * 25  # 100 total requests

        tasks = []
        for action in actions:
            task = gateway_client.route_tool(
                action=action,
                available_tools=sample_tools,
            )
            tasks.append(task)

        start = time.perf_counter()
        results = await asyncio.gather(*tasks)
        duration = time.perf_counter() - start

        # All should succeed
        assert len(results) == 100
        for result in results:
            assert result is not None
            assert result.recommended_tool in sample_tools

        # Should handle concurrency efficiently
        assert duration < 10.0, f"Concurrent tool routing took {duration:.2f}s"


class TestToolRoutingSemantics:
    """Test semantic understanding in tool routing."""

    @pytest.mark.asyncio
    async def test_tool_routing_semantic_similarity(self, gateway_client):
        """Test that semantically similar actions route to same tool."""
        tools = ["web_search", "database_query", "api_call"]

        # Semantically similar actions
        actions = [
            "search the internet for information",
            "look up data on the web",
            "find info online",
        ]

        decisions = []
        for action in actions:
            decision = await gateway_client.route_tool(
                action=action,
                available_tools=tools,
            )
            decisions.append(decision)

        # All should route to similar tool (likely web_search)
        recommended_tools = [d.recommended_tool for d in decisions]

        # At least some consistency expected
        assert len(set(recommended_tools)) <= 2, \
            f"Too much variance in routing: {recommended_tools}"

    @pytest.mark.asyncio
    async def test_tool_routing_domain_specific(self, gateway_client):
        """Test domain-specific tool routing."""
        tools = ["sql_query", "web_search", "code_execution"]

        # Database-related action
        decision_db = await gateway_client.route_tool(
            action="query user records from database",
            available_tools=tools,
        )

        # Code-related action
        decision_code = await gateway_client.route_tool(
            action="run Python script to process data",
            available_tools=tools,
        )

        # Web-related action
        decision_web = await gateway_client.route_tool(
            action="search online for API documentation",
            available_tools=tools,
        )

        # All should have reasonable confidence
        assert decision_db.confidence > 0.5
        assert decision_code.confidence > 0.5
        assert decision_web.confidence > 0.5


class TestToolRoutingEdgeCases:
    """Test edge cases in tool routing."""

    @pytest.mark.asyncio
    async def test_tool_routing_single_tool(self, gateway_client):
        """Test routing with only one available tool."""
        decision = await gateway_client.route_tool(
            action="do something",
            available_tools=["only_tool"],
        )

        assert decision is not None
        assert decision.recommended_tool == "only_tool"
        # Should still have reasonable confidence
        assert decision.confidence > 0.5

    @pytest.mark.asyncio
    async def test_tool_routing_many_tools(self, gateway_client):
        """Test routing with many available tools."""
        tools = [f"tool_{i}" for i in range(50)]

        decision = await gateway_client.route_tool(
            action="search for something",
            available_tools=tools,
        )

        assert decision is not None
        assert decision.recommended_tool in tools

    @pytest.mark.asyncio
    async def test_tool_routing_ambiguous_action(self, gateway_client, sample_tools):
        """Test routing with ambiguous action description."""
        decision = await gateway_client.route_tool(
            action="do it",
            available_tools=sample_tools,
        )

        assert decision is not None
        # Confidence might be lower for ambiguous actions
        assert 0.0 <= decision.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_tool_routing_long_action(self, gateway_client, sample_tools):
        """Test routing with very long action description."""
        long_action = " ".join(["search for information"] * 50)

        decision = await gateway_client.route_tool(
            action=long_action,
            available_tools=sample_tools,
        )

        assert decision is not None
        assert decision.recommended_tool in sample_tools
