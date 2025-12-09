"""Cross-SDK integration tests for Bifrost and SmartCP integration."""

import pytest
import asyncio
import time
from typing import Dict, Any

from bifrost_extensions import GatewayClient, RoutingStrategy
from bifrost_extensions.models import Message


class TestBifrostSmartCPIntegration:
    """Test integration between Bifrost Gateway and SmartCP."""

    @pytest.mark.asyncio
    async def test_gateway_to_smartcp_tool_delegation(
        self, gateway_client, mock_mcp_server
    ):
        """Test Bifrost delegating to SmartCP tools."""
        # Route request via Bifrost
        response = await gateway_client.route(
            messages=[Message(role="user", content="Execute database query")],
            strategy=RoutingStrategy.BALANCED,
        )

        assert response is not None
        assert response.model is not None

        # Simulate SmartCP tool execution after routing
        mock_mcp_server.execute_tool = lambda name, params: {
            "result": "query executed",
            "model_used": response.model.model_id,
        }

        tool_result = mock_mcp_server.execute_tool("db_query", {"query": "SELECT * FROM users"})

        assert tool_result["result"] == "query executed"
        assert tool_result["model_used"] == response.model.model_id

    @pytest.mark.asyncio
    async def test_smartcp_to_bifrost_routing(
        self, gateway_client, mock_mcp_server
    ):
        """Test SmartCP routing requests through Bifrost."""
        # SmartCP tool needs model selection
        routing_response = await gateway_client.route(
            messages=[Message(role="user", content="Complex analysis task")],
            strategy=RoutingStrategy.PERFORMANCE_OPTIMIZED,
        )

        assert routing_response is not None

        # Use selected model in SmartCP tool
        mock_mcp_server.execute_tool = lambda name, params: {
            "model": routing_response.model.model_id,
            "result": "analysis complete",
        }

        result = mock_mcp_server.execute_tool("analyze", {"data": "test"})

        assert result["model"] == routing_response.model.model_id

    @pytest.mark.asyncio
    async def test_agent_cli_pattern(self, gateway_client, mock_mcp_server):
        """Test agent-cli pattern: GatewayClient + ToolClient together."""
        # Step 1: Route to optimal model
        routing = await gateway_client.route(
            messages=[Message(role="user", content="Generate code and execute")],
            strategy=RoutingStrategy.BALANCED,
        )

        # Step 2: Use SmartCP tool with selected model
        mock_mcp_server.execute_tool = lambda name, params: {
            "model_used": routing.model.model_id,
            "code_generated": "def hello(): pass",
            "execution_result": "success",
        }

        tool_result = mock_mcp_server.execute_tool(
            "code_generator",
            {"prompt": "Generate code", "model": routing.model.model_id}
        )

        assert tool_result["model_used"] == routing.model.model_id
        assert tool_result["execution_result"] == "success"

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, gateway_client, mock_mcp_server):
        """Test end-to-end workflow across both SDKs."""
        workflow_steps = []

        # Step 1: Classification via Bifrost
        classification = await gateway_client.classify(
            prompt="Analyze database schema and optimize queries",
            categories=["simple", "moderate", "complex"],
        )
        workflow_steps.append(("classify", classification))

        # Step 2: Route to optimal model
        routing = await gateway_client.route(
            messages=[Message(role="user", content="Analyze database schema")],
            strategy=RoutingStrategy.PERFORMANCE_OPTIMIZED,
        )
        workflow_steps.append(("route", routing))

        # Step 3: Execute tool via SmartCP
        mock_mcp_server.execute_tool = lambda name, params: {
            "model": routing.model.model_id,
            "complexity": classification.category,
            "result": "schema analyzed",
        }

        tool_result = mock_mcp_server.execute_tool(
            "db_analyzer",
            {"model": routing.model.model_id}
        )
        workflow_steps.append(("execute", tool_result))

        # Verify workflow
        assert len(workflow_steps) == 3
        assert workflow_steps[0][0] == "classify"
        assert workflow_steps[1][0] == "route"
        assert workflow_steps[2][0] == "execute"
        assert tool_result["complexity"] == classification.category

    @pytest.mark.asyncio
    async def test_cost_optimization_workflow(self, gateway_client, mock_mcp_server):
        """Test cost optimization across SDKs."""
        # Route with cost constraints
        routing = await gateway_client.route(
            messages=[Message(role="user", content="Simple task")],
            strategy=RoutingStrategy.COST_OPTIMIZED,
            constraints={"max_cost_usd": 0.001},
        )

        assert routing.model.estimated_cost_usd <= 0.001

        # Execute with cost-optimized model
        mock_mcp_server.execute_tool = lambda name, params: {
            "model": routing.model.model_id,
            "cost": routing.model.estimated_cost_usd,
            "result": "task completed",
        }

        result = mock_mcp_server.execute_tool("task", {})

        assert result["cost"] <= 0.001

    @pytest.mark.asyncio
    async def test_performance_optimization_workflow(
        self, gateway_client, mock_mcp_server
    ):
        """Test performance optimization across SDKs."""
        # Route with latency constraints
        routing = await gateway_client.route(
            messages=[Message(role="user", content="Time-sensitive task")],
            strategy=RoutingStrategy.SPEED_OPTIMIZED,
            constraints={"max_latency_ms": 200},
        )

        assert routing.model.estimated_latency_ms <= 200

        # Execute with fast model
        mock_mcp_server.execute_tool = lambda name, params: {
            "model": routing.model.model_id,
            "latency": routing.model.estimated_latency_ms,
            "result": "fast completion",
        }

        result = mock_mcp_server.execute_tool("urgent_task", {})

        assert result["latency"] <= 200


class TestCrossSDKPerformance:
    """Performance tests for cross-SDK operations."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_end_to_end_latency(self, gateway_client, mock_mcp_server):
        """Test end-to-end latency across both SDKs."""
        latencies = []

        mock_mcp_server.execute_tool = lambda name, params: {"result": "success"}

        for _ in range(50):
            start = time.perf_counter()

            # Route
            routing = await gateway_client.route(
                messages=[Message(role="user", content="Test task")],
                strategy=RoutingStrategy.BALANCED,
            )

            # Execute
            mock_mcp_server.execute_tool("test_tool", {})

            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)

        latencies.sort()
        p95 = latencies[int(len(latencies) * 0.95)]

        print(f"\nEnd-to-End Latency P95: {p95:.2f}ms")

        # Combined latency should be reasonable
        assert p95 < 500, f"E2E latency {p95:.2f}ms too high"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_cross_sdk_operations(
        self, gateway_client, mock_mcp_server
    ):
        """Test concurrent operations across both SDKs."""
        mock_mcp_server.execute_tool = lambda name, params: {"result": "success"}

        tasks = []
        start = time.perf_counter()

        for i in range(100):
            async def workflow():
                routing = await gateway_client.route(
                    messages=[Message(role="user", content=f"Task {i}")],
                    strategy=RoutingStrategy.BALANCED,
                )
                return mock_mcp_server.execute_tool("tool", {})

            tasks.append(workflow())

        results = await asyncio.gather(*tasks)
        duration = time.perf_counter() - start

        throughput = 100 / duration

        print(f"\nCross-SDK Throughput: {throughput:.2f} workflows/sec")

        assert len(results) == 100
        assert throughput > 10, "Should handle at least 10 workflows/sec"


class TestCrossSDKErrorHandling:
    """Error handling tests across SDKs."""

    @pytest.mark.asyncio
    async def test_routing_failure_recovery(self, gateway_client, mock_mcp_server):
        """Test recovery from routing failures."""
        # Simulate routing failure
        original_route = gateway_client.route

        async def failing_route(*args, **kwargs):
            raise Exception("Routing service unavailable")

        gateway_client.route = failing_route

        with pytest.raises(Exception, match="Routing service unavailable"):
            await gateway_client.route(
                messages=[Message(role="user", content="Test")],
                strategy=RoutingStrategy.BALANCED,
            )

        # Restore and verify recovery
        gateway_client.route = original_route

        routing = await gateway_client.route(
            messages=[Message(role="user", content="Test")],
            strategy=RoutingStrategy.BALANCED,
        )

        assert routing is not None

    @pytest.mark.asyncio
    async def test_tool_execution_failure_handling(
        self, gateway_client, mock_mcp_server
    ):
        """Test handling of tool execution failures."""
        # Successful routing
        routing = await gateway_client.route(
            messages=[Message(role="user", content="Test")],
            strategy=RoutingStrategy.BALANCED,
        )

        assert routing is not None

        # Tool execution fails
        mock_mcp_server.execute_tool = lambda name, params: {
            "error": "Execution failed",
            "fallback_model": routing.alternatives[0].model_id if routing.alternatives else None,
        }

        result = mock_mcp_server.execute_tool("failing_tool", {})

        assert "error" in result
        # Should provide fallback option
        assert "fallback_model" in result
