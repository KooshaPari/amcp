# Bifrost SDK Performance Testing Suite

Comprehensive performance benchmarking and load testing for the Bifrost Smart LLM Gateway SDK.

## Overview

This test suite measures and validates performance across multiple dimensions:

- **Latency**: Routing, tool routing, and classification latency (P50, P95, P99)
- **Throughput**: Requests per second under various conditions
- **Concurrency**: System behavior under 100-1000+ concurrent requests
- **Memory**: Memory usage per request and leak detection
- **Load Testing**: Sustained load, spike tests, and soak tests
- **Resource Monitoring**: CPU, memory, threads, file descriptors

## Performance Targets

Based on industry best practices and benchmarked against similar systems:

| Metric | Target | Notes |
|--------|--------|-------|
| Routing Latency (P95) | < 50ms | Model selection decision time |
| Tool Routing Latency (P95) | < 10ms | Simpler logic, keyword-based |
| Classification Latency (P95) | < 5ms | Pattern matching only |
| Throughput | 1000 req/sec | Sustained throughput |
| Memory per Request | < 10MB | Average memory footprint |
| Concurrent 100 Success | 99% | High concurrency success rate |
| Concurrent 1000 Success | 95% | Very high concurrency |

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or use uv (recommended)
uv pip install -r requirements.txt
```

### Running Benchmarks

```bash
# Quick benchmark suite (recommended for development)
python run_benchmarks.py --quick

# Run all benchmarks
python run_benchmarks.py --all

# Run specific benchmark categories
python run_benchmarks.py --latency
python run_benchmarks.py --throughput
python run_benchmarks.py --load
python run_benchmarks.py --memory

# Full suite (includes long-running tests)
python run_benchmarks.py --full
```

### Using pytest Directly

```bash
# Run all performance tests
pytest -v -m benchmark

# Run specific test file
pytest -v test_routing_latency.py

# Run with coverage
pytest -v -m benchmark --cov=bifrost_extensions

# Run only fast tests (skip slow soak tests)
pytest -v -m "benchmark and not slow"

# Run specific test
pytest -v test_routing_latency.py::TestRoutingLatency::test_simple_routing_latency
```

## Test Categories

### Latency Benchmarks (`test_routing_latency.py`)

Tests latency for routing decisions:

- Simple routing latency (P50, P95, P99)
- Complex prompt routing latency
- Strategy comparison (cost vs performance vs balanced)
- Constrained routing latency
- Tool routing latency (with 1-100 tools)
- Classification latency

**Markers**: `@pytest.mark.benchmark`

**Duration**: ~2-5 minutes

### Throughput Benchmarks (`test_throughput.py`)

Tests maximum sustainable throughput:

- Routing throughput (req/sec)
- Sustained throughput (60s)
- Burst throughput (5s max)
- Mixed operation throughput
- Throughput vs message complexity
- Throughput vs strategy
- Degradation detection

**Markers**: `@pytest.mark.benchmark`

**Duration**: ~5-10 minutes

### Concurrent Load Tests (`test_concurrent_load.py`)

Tests behavior under concurrent load:

- 100 concurrent requests
- 1000 concurrent requests
- Varying concurrency levels (10-500)
- Sustained load (1000 req/sec for 5 minutes)
- Soak test (500 req/sec for 1 hour) - **SLOW**
- Traffic spike (2x instant)
- Gradual ramp-up

**Markers**: `@pytest.mark.load`, `@pytest.mark.slow` (soak test)

**Duration**: ~10-15 minutes (excluding soak test)

### Memory Tests (`test_memory_usage.py`)

Tests memory consumption and leak detection:

- Memory per request
- Memory leak detection (10 batches)
- Memory cleanup after errors
- Concurrent memory usage
- CPU usage monitoring
- Thread count stability
- File descriptor usage
- Network connection pooling
- Garbage collection behavior

**Markers**: `@pytest.mark.benchmark`

**Duration**: ~5-10 minutes

## Reports

### Automatic Report Generation

The `run_benchmarks.py` script automatically generates:

1. **JSON Report**: Machine-readable results (`performance_report_YYYYMMDD_HHMMSS.json`)
2. **Markdown Report**: Human-readable summary (`performance_report_YYYYMMDD_HHMMSS.md`)
3. **HTML Report**: Interactive HTML dashboard (`performance_report_YYYYMMDD_HHMMSS.html`)

Reports are saved to `tests/performance/reports/YYYYMMDD_HHMMSS/`

### Manual Report Generation

```python
from report_generator import PerformanceReportGenerator

reporter = PerformanceReportGenerator("output_dir")

# Add benchmark results
reporter.add_benchmark(
    name="Routing Latency",
    metrics={"p95": 42.5, "p99": 68.3},
    target={"p95": 50.0, "p99": 100.0}
)

# Generate reports
reporter.save_json_report()
reporter.generate_markdown_report()
reporter.generate_html_report()

# Generate charts
reporter.generate_latency_chart("Routing", latencies=[...])
reporter.generate_throughput_chart("Load Test", data=[...])
```

## Grafana Dashboard

### Setup

1. Import the dashboard:
```bash
# Import dashboard JSON
curl -X POST \
  -H "Content-Type: application/json" \
  -d @grafana_dashboard.json \
  http://admin:admin@localhost:3000/api/dashboards/db
```

2. Configure Prometheus data source in Grafana

3. Ensure your application exports metrics:
```python
from prometheus_client import Histogram, Counter

# Routing latency
routing_latency = Histogram(
    "bifrost_routing_latency",
    "Routing decision latency",
    buckets=[10, 25, 50, 75, 100, 250, 500, 1000]
)

# Request counter
routing_requests = Counter(
    "bifrost_routing_requests_total",
    "Total routing requests",
    ["status"]
)
```

### Dashboard Features

The Grafana dashboard includes:

- **Latency Percentiles**: P50, P95, P99 for routing, tool routing, classification
- **Throughput**: Total, success, and error RPS
- **Memory Usage**: Process memory over time
- **CPU Usage**: Process CPU percentage
- **Success Rate**: Overall success rate percentage
- **Concurrent Requests**: Active concurrent requests
- **Error Rate**: Errors by type
- **Request Duration Distribution**: Heatmap of request durations

### Alerts

Pre-configured alerts:

- High routing latency (P95 > 50ms)
- Low throughput (< 800 RPS)
- High tool routing latency (P95 > 10ms)
- High classification latency (P95 > 5ms)
- Low success rate (< 95%)

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Performance Benchmarks

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * *'  # Daily

jobs:
  performance:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r tests/performance/requirements.txt

      - name: Run quick benchmarks
        run: |
          cd tests/performance
          python run_benchmarks.py --quick

      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: performance-reports
          path: tests/performance/reports/

      - name: Comment PR with results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('tests/performance/reports/latest/performance_report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });
```

### Jenkins Example

```groovy
pipeline {
    agent any

    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r tests/performance/requirements.txt'
            }
        }

        stage('Quick Benchmarks') {
            steps {
                sh 'cd tests/performance && python run_benchmarks.py --quick'
            }
        }

        stage('Full Benchmarks') {
            when {
                branch 'main'
            }
            steps {
                sh 'cd tests/performance && python run_benchmarks.py --all'
            }
        }

        stage('Publish Reports') {
            steps {
                publishHTML([
                    reportDir: 'tests/performance/reports/latest',
                    reportFiles: 'performance_report.html',
                    reportName: 'Performance Report'
                ])
            }
        }
    }
}
```

## Advanced Usage

### Custom Fixtures

Create custom fixtures in `conftest.py`:

```python
@pytest.fixture
def custom_client():
    """Custom client with specific configuration."""
    return GatewayClient(
        base_url="http://custom-host:8000",
        timeout=120.0
    )

@pytest.fixture
def large_messages():
    """Large messages for stress testing."""
    return [
        {"role": "user", "content": "..." * 10000}
    ]
```

### Custom Benchmarks

Add new benchmarks following the pattern:

```python
@pytest.mark.asyncio
@pytest.mark.benchmark
class TestCustomBenchmark:
    """Custom benchmark tests."""

    async def test_custom_operation(
        self,
        gateway_client,
        latency_tracker,
        performance_targets
    ):
        """Test custom operation performance."""
        for _ in range(100):
            start = time.perf_counter()

            # Your operation here
            await gateway_client.custom_operation()

            latency_ms = (time.perf_counter() - start) * 1000
            latency_tracker.record(latency_ms)

        percentiles = latency_tracker.calculate()

        assert percentiles["p95"] < 100, "P95 too high"
```

### Performance Regression Testing

Compare against baseline:

```python
# Save baseline
python run_benchmarks.py --quick -o baseline_results

# Run new benchmarks
python run_benchmarks.py --quick -o current_results

# Compare (implement comparison logic)
python compare_results.py baseline_results current_results
```

## Troubleshooting

### Common Issues

**Tests timing out:**
```bash
# Increase timeout
pytest -v --timeout=300
```

**Memory errors:**
```bash
# Run tests serially
pytest -v -n 0
```

**Connection errors:**
```bash
# Check service is running
curl http://localhost:8000/health

# Start service
python server.py
```

**Import errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Performance Issues

If benchmarks show degraded performance:

1. **Check system load**: `top`, `htop`
2. **Check disk I/O**: `iostat`
3. **Check network**: `netstat -an | grep 8000`
4. **Review logs**: Check application logs for errors
5. **Profile code**: Use `py-spy` or `cProfile`
6. **Check database**: Review query performance

## Best Practices

1. **Run on dedicated hardware**: For consistent results
2. **Disable background processes**: Minimize interference
3. **Use production-like data**: Realistic message sizes and complexity
4. **Run multiple times**: Average results for stability
5. **Monitor trends**: Track performance over time
6. **Set alerts**: Be notified of regressions
7. **Document changes**: Note performance impacts in PRs

## Contributing

When adding new performance tests:

1. Follow existing patterns in test files
2. Use appropriate markers (`@pytest.mark.benchmark`, `@pytest.mark.load`)
3. Mark slow tests with `@pytest.mark.slow`
4. Set clear performance targets
5. Add test to appropriate category
6. Update this README

## References

- [pytest documentation](https://docs.pytest.org/)
- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/)
- [Locust documentation](https://docs.locust.io/)
- [Grafana documentation](https://grafana.com/docs/)
- [Prometheus documentation](https://prometheus.io/docs/)

## License

Same as main project license.
