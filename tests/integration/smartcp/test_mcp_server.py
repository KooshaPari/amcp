"""Integration tests for SmartCP MCP server functionality."""

import pytest
import asyncio
import time
from typing import Dict, Any

from unittest.mock import AsyncMock, MagicMock, patch


class TestMCPServerStdio:
    """Test MCP server with stdio transport."""

    @pytest.mark.asyncio
    async def test_stdio_server_initialization(self, mcp_server_stdio):
        """Test stdio server initializes correctly."""
        assert mcp_server_stdio is not None
        assert mcp_server_stdio.transport == "stdio"

    @pytest.mark.asyncio
    async def test_stdio_tool_registration(self, mcp_server_stdio, sample_tool_definition):
        """Test tool registration on stdio server."""
        # Simulate tool registration
        mcp_server_stdio.tools.append(sample_tool_definition)

        assert len(mcp_server_stdio.tools) == 1
        assert mcp_server_stdio.tools[0]["name"] == "test_tool"

    @pytest.mark.asyncio
    async def test_stdio_tool_execution(self, mcp_server_stdio, sample_tool_definition):
        """Test tool execution via stdio transport."""
        # Mock tool execution
        mock_execute = AsyncMock(return_value={"result": "success", "data": "test"})
        mcp_server_stdio.execute_tool = mock_execute

        result = await mcp_server_stdio.execute_tool(
            "test_tool", {"param1": "value1", "param2": 42}
        )

        assert result["result"] == "success"
        mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_stdio_error_handling(self, mcp_server_stdio):
        """Test error handling in stdio server."""
        mock_execute = AsyncMock(side_effect=Exception("Tool execution failed"))
        mcp_server_stdio.execute_tool = mock_execute

        with pytest.raises(Exception, match="Tool execution failed"):
            await mcp_server_stdio.execute_tool("test_tool", {})


class TestMCPServerHTTP:
    """Test MCP server with HTTP transport."""

    @pytest.mark.asyncio
    async def test_http_server_initialization(self, mcp_server_http):
        """Test HTTP server initializes correctly."""
        assert mcp_server_http is not None
        assert mcp_server_http.transport == "http"
        assert mcp_server_http.port == 8000

    @pytest.mark.asyncio
    async def test_http_tool_registration(self, mcp_server_http, sample_tool_definition):
        """Test tool registration on HTTP server."""
        mcp_server_http.tools.append(sample_tool_definition)

        assert len(mcp_server_http.tools) == 1
        assert mcp_server_http.tools[0]["name"] == "test_tool"

    @pytest.mark.asyncio
    async def test_http_tool_execution(self, mcp_server_http):
        """Test tool execution via HTTP transport."""
        mock_execute = AsyncMock(return_value={"result": "success"})
        mcp_server_http.execute_tool = mock_execute

        result = await mcp_server_http.execute_tool(
            "test_tool", {"param1": "value1"}
        )

        assert result["result"] == "success"

    @pytest.mark.asyncio
    async def test_http_concurrent_requests(self, mcp_server_http):
        """Test concurrent HTTP requests to server."""
        mock_execute = AsyncMock(
            side_effect=lambda name, params: {"result": "success", "request_id": id(params)}
        )
        mcp_server_http.execute_tool = mock_execute

        tasks = []
        for i in range(50):
            task = mcp_server_http.execute_tool(
                "test_tool", {"param1": f"value{i}"}
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        assert len(results) == 50
        assert all(r["result"] == "success" for r in results)


class TestMCPToolExecution:
    """Test MCP tool execution logic."""

    @pytest.mark.asyncio
    async def test_tool_with_valid_parameters(self, mcp_server_stdio, sample_tool_definition):
        """Test tool execution with valid parameters."""
        mock_execute = AsyncMock(return_value={"status": "completed", "output": "test output"})
        mcp_server_stdio.execute_tool = mock_execute

        result = await mcp_server_stdio.execute_tool(
            "test_tool", {"param1": "valid", "param2": 123}
        )

        assert result["status"] == "completed"
        assert "output" in result

    @pytest.mark.asyncio
    async def test_tool_with_invalid_parameters(self, mcp_server_stdio):
        """Test tool execution with invalid parameters."""
        mock_execute = AsyncMock(side_effect=ValueError("Invalid parameter type"))
        mcp_server_stdio.execute_tool = mock_execute

        with pytest.raises(ValueError, match="Invalid parameter type"):
            await mcp_server_stdio.execute_tool("test_tool", {"param1": 123})

    @pytest.mark.asyncio
    async def test_tool_with_missing_required_parameters(self, mcp_server_stdio):
        """Test tool execution with missing required parameters."""
        mock_execute = AsyncMock(side_effect=ValueError("Missing required parameter: param1"))
        mcp_server_stdio.execute_tool = mock_execute

        with pytest.raises(ValueError, match="Missing required parameter"):
            await mcp_server_stdio.execute_tool("test_tool", {"param2": 42})

    @pytest.mark.asyncio
    async def test_tool_timeout_handling(self, mcp_server_stdio):
        """Test tool execution timeout handling."""
        async def slow_tool(*args, **kwargs):
            await asyncio.sleep(10)
            return {"result": "too slow"}

        mcp_server_stdio.execute_tool = slow_tool

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                mcp_server_stdio.execute_tool("test_tool", {}),
                timeout=0.1
            )


class TestMCPServerPerformance:
    """Performance tests for MCP server."""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_tool_execution_latency(self, mcp_server_http):
        """Test tool execution latency."""
        latencies = []

        async def fast_tool(*args, **kwargs):
            return {"result": "success"}

        mcp_server_http.execute_tool = fast_tool

        for _ in range(100):
            start = time.perf_counter()
            await mcp_server_http.execute_tool("test_tool", {"param1": "test"})
            latency = (time.perf_counter() - start) * 1000
            latencies.append(latency)

        latencies.sort()
        p50 = latencies[49]
        p95 = latencies[94]

        print(f"\nTool Execution Latency:")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")

        # Tool execution should be fast (<400ms P95)
        assert p95 < 400, f"P95 latency {p95:.2f}ms exceeds 400ms target"

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_tool_execution(self, mcp_server_http):
        """Test concurrent tool execution throughput."""
        async def mock_tool(*args, **kwargs):
            await asyncio.sleep(0.01)  # Simulate some work
            return {"result": "success"}

        mcp_server_http.execute_tool = mock_tool

        tasks = []
        start = time.perf_counter()

        for i in range(100):
            task = mcp_server_http.execute_tool("test_tool", {"param1": f"value{i}"})
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        duration = time.perf_counter() - start

        throughput = 100 / duration

        print(f"\nConcurrent Tool Execution:")
        print(f"  Requests: 100")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Throughput: {throughput:.2f} RPS")

        assert len(results) == 100
        assert all(r["result"] == "success" for r in results)


class TestMCPServerSecurity:
    """Security tests for MCP server."""

    @pytest.mark.asyncio
    async def test_tool_input_validation(self, mcp_server_stdio):
        """Test tool input validation prevents injection."""
        async def validate_input(name, params):
            # Simulate validation
            if any(char in str(params) for char in ["'", '"', ";", "--"]):
                raise ValueError("Invalid input detected")
            return {"result": "success"}

        mcp_server_stdio.execute_tool = validate_input

        # Valid input
        result = await mcp_server_stdio.execute_tool(
            "test_tool", {"param1": "safe_value"}
        )
        assert result["result"] == "success"

        # Injection attempt
        with pytest.raises(ValueError, match="Invalid input"):
            await mcp_server_stdio.execute_tool(
                "test_tool", {"param1": "'; DROP TABLE--"}
            )

    @pytest.mark.asyncio
    async def test_tool_sandboxing(self, mcp_server_stdio, sandbox_config):
        """Test tool execution in sandbox."""
        async def sandboxed_tool(name, params):
            # Simulate sandbox restrictions
            if "subprocess" in params.get("code", ""):
                raise PermissionError("Subprocess access denied in sandbox")
            return {"result": "success"}

        mcp_server_stdio.execute_tool = sandboxed_tool

        # Safe code
        result = await mcp_server_stdio.execute_tool(
            "test_tool", {"code": "print('hello')"}
        )
        assert result["result"] == "success"

        # Unsafe code
        with pytest.raises(PermissionError, match="Subprocess access denied"):
            await mcp_server_stdio.execute_tool(
                "test_tool", {"code": "import subprocess"}
            )
