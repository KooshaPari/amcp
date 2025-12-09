"""Performance test fixtures and configuration."""

import asyncio
import os
import time
from typing import Any, AsyncGenerator, Dict, List

import pytest
import psutil
from bifrost_extensions.client.gateway import GatewayClient
from bifrost_extensions.models import Message, RoutingStrategy


@pytest.fixture(scope="session")
def performance_metrics_dir():
    """Directory for storing performance metrics."""
    metrics_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(metrics_dir, exist_ok=True)
    return metrics_dir


@pytest.fixture
async def gateway_client() -> AsyncGenerator[GatewayClient, None]:
    """Provide Gateway client for performance testing."""
    client = GatewayClient(
        base_url=os.getenv("BIFROST_URL", "http://localhost:8000"),
        timeout=60.0,  # Longer timeout for load tests
    )
    yield client


@pytest.fixture
def sample_messages() -> List[Dict[str, str]]:
    """Sample messages for routing tests."""
    return [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
        {"role": "user", "content": "Can you help me write a Python function?"},
    ]


@pytest.fixture
def complex_messages() -> List[Dict[str, str]]:
    """Complex messages for stress testing."""
    return [
        {
            "role": "user",
            "content": """
            Write a comprehensive Python function that:
            1. Reads a large CSV file (100MB+)
            2. Performs data cleaning and validation
            3. Applies statistical transformations
            4. Generates visualizations
            5. Exports results to multiple formats

            Include proper error handling, logging, and documentation.
            """,
        }
    ]


@pytest.fixture
def tool_actions() -> List[str]:
    """Sample tool actions for routing tests."""
    return [
        "search for Python documentation",
        "analyze code for bugs",
        "generate unit tests",
        "optimize SQL query",
        "review security vulnerabilities",
    ]


@pytest.fixture
def available_tools() -> List[str]:
    """Available tools for routing."""
    return [
        "web_search",
        "doc_search",
        "code_analyzer",
        "test_generator",
        "sql_optimizer",
        "security_scanner",
    ]


@pytest.fixture
def classification_prompts() -> List[str]:
    """Sample prompts for classification."""
    return [
        "Fix the bug in this Python code",  # Simple
        "Write a REST API with authentication",  # Moderate
        "Build a distributed microservices architecture",  # Complex
        "What is 2 + 2?",  # Simple
        "Explain quantum computing concepts",  # Moderate
    ]


class PerformanceTracker:
    """Track performance metrics during tests."""

    def __init__(self):
        self.metrics: List[Dict[str, Any]] = []
        self.start_time = 0
        self.process = psutil.Process()

    def start(self):
        """Start tracking."""
        self.start_time = time.perf_counter()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.start_cpu = self.process.cpu_percent()

    def stop(self, operation: str, count: int = 1) -> Dict[str, Any]:
        """Stop tracking and record metrics."""
        duration = time.perf_counter() - self.start_time
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        cpu_percent = self.process.cpu_percent()

        metric = {
            "operation": operation,
            "duration_s": duration,
            "count": count,
            "throughput": count / duration if duration > 0 else 0,
            "avg_latency_ms": (duration * 1000) / count if count > 0 else 0,
            "memory_mb": end_memory,
            "memory_delta_mb": end_memory - self.start_memory,
            "cpu_percent": cpu_percent,
            "timestamp": time.time(),
        }

        self.metrics.append(metric)
        return metric

    def get_metrics(self) -> List[Dict[str, Any]]:
        """Get all recorded metrics."""
        return self.metrics

    def clear(self):
        """Clear all metrics."""
        self.metrics.clear()


@pytest.fixture
def perf_tracker():
    """Provide performance tracker."""
    return PerformanceTracker()


class LatencyPercentiles:
    """Calculate latency percentiles."""

    def __init__(self):
        self.latencies: List[float] = []

    def record(self, latency_ms: float):
        """Record a latency measurement."""
        self.latencies.append(latency_ms)

    def calculate(self) -> Dict[str, float]:
        """Calculate percentiles."""
        if not self.latencies:
            return {}

        sorted_latencies = sorted(self.latencies)
        n = len(sorted_latencies)

        return {
            "p50": sorted_latencies[int(n * 0.50)],
            "p90": sorted_latencies[int(n * 0.90)],
            "p95": sorted_latencies[int(n * 0.95)],
            "p99": sorted_latencies[int(n * 0.99)],
            "min": sorted_latencies[0],
            "max": sorted_latencies[-1],
            "mean": sum(sorted_latencies) / n,
            "count": n,
        }

    def clear(self):
        """Clear latencies."""
        self.latencies.clear()


@pytest.fixture
def latency_tracker():
    """Provide latency percentiles tracker."""
    return LatencyPercentiles()


@pytest.fixture
def performance_targets():
    """Target performance metrics."""
    return {
        "routing_latency_p95_ms": 50,
        "tool_routing_latency_p95_ms": 10,
        "classification_latency_p95_ms": 5,
        "throughput_rps": 1000,
        "memory_per_request_mb": 10,
        "concurrent_100_success_rate": 0.99,
        "concurrent_1000_success_rate": 0.95,
    }


async def run_concurrent_requests(
    coro_func, count: int, concurrency: int = 100
) -> List[Any]:
    """Run concurrent requests with controlled concurrency."""
    semaphore = asyncio.Semaphore(concurrency)

    async def limited_request():
        async with semaphore:
            return await coro_func()

    tasks = [limited_request() for _ in range(count)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results


@pytest.fixture
def concurrent_executor():
    """Provide concurrent request executor."""
    return run_concurrent_requests


def calculate_success_rate(results: List[Any]) -> float:
    """Calculate success rate from results."""
    successful = sum(1 for r in results if not isinstance(r, Exception))
    return successful / len(results) if results else 0.0


@pytest.fixture
def success_rate_calculator():
    """Provide success rate calculator."""
    return calculate_success_rate
