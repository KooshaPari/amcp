"""Performance report generator.

Generates comprehensive performance benchmark reports.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np


class PerformanceReportGenerator:
    """Generate performance benchmark reports."""

    def __init__(self, output_dir: str):
        """Initialize report generator.

        Args:
            output_dir: Directory for report output
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_data: Dict[str, Any] = {
            "timestamp": self.timestamp,
            "benchmarks": {},
            "summary": {},
        }

    def add_benchmark(
        self, name: str, metrics: Dict[str, Any], target: Dict[str, Any] = None
    ):
        """Add benchmark results.

        Args:
            name: Benchmark name
            metrics: Metric values
            target: Target values for comparison
        """
        self.report_data["benchmarks"][name] = {
            "metrics": metrics,
            "target": target or {},
            "passed": self._check_targets(metrics, target) if target else None,
        }

    def _check_targets(self, metrics: Dict[str, Any], targets: Dict[str, Any]) -> bool:
        """Check if metrics meet targets."""
        for key, target_value in targets.items():
            if key not in metrics:
                continue

            metric_value = metrics[key]

            # Handle different comparison types
            if isinstance(target_value, dict):
                # Range comparison: {min: X, max: Y}
                if "min" in target_value and metric_value < target_value["min"]:
                    return False
                if "max" in target_value and metric_value > target_value["max"]:
                    return False
            elif isinstance(target_value, (int, float)):
                # Assume "less than" for latency/error rate
                if metric_value > target_value:
                    return False

        return True

    def generate_summary(self):
        """Generate summary statistics."""
        benchmarks = self.report_data["benchmarks"]

        passed = sum(1 for b in benchmarks.values() if b.get("passed"))
        failed = sum(1 for b in benchmarks.values() if b.get("passed") is False)
        total = len([b for b in benchmarks.values() if b.get("passed") is not None])

        self.report_data["summary"] = {
            "total_benchmarks": len(benchmarks),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
        }

    def generate_latency_chart(
        self, benchmark_name: str, latencies: List[float], output_name: str = None
    ):
        """Generate latency percentile chart.

        Args:
            benchmark_name: Name for chart title
            latencies: List of latency values (ms)
            output_name: Output filename (defaults to benchmark_name)
        """
        output_name = output_name or f"{benchmark_name}_latency"

        sorted_latencies = sorted(latencies)
        percentiles = [50, 75, 90, 95, 99]
        n = len(sorted_latencies)

        values = [sorted_latencies[int(n * p / 100)] for p in percentiles]

        plt.figure(figsize=(10, 6))
        plt.bar([str(p) for p in percentiles], values, color="steelblue")
        plt.xlabel("Percentile")
        plt.ylabel("Latency (ms)")
        plt.title(f"{benchmark_name} - Latency Percentiles")
        plt.grid(axis="y", alpha=0.3)

        # Add value labels
        for i, (p, v) in enumerate(zip(percentiles, values)):
            plt.text(i, v, f"{v:.2f}ms", ha="center", va="bottom")

        output_path = self.output_dir / f"{output_name}.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        return str(output_path)

    def generate_throughput_chart(
        self,
        benchmark_name: str,
        throughput_data: List[Dict[str, Any]],
        output_name: str = None,
    ):
        """Generate throughput over time chart.

        Args:
            benchmark_name: Name for chart title
            throughput_data: List of {time: X, throughput: Y}
            output_name: Output filename
        """
        output_name = output_name or f"{benchmark_name}_throughput"

        times = [d["time"] for d in throughput_data]
        throughputs = [d["throughput"] for d in throughput_data]

        plt.figure(figsize=(12, 6))
        plt.plot(times, throughputs, marker="o", linewidth=2, markersize=6)
        plt.xlabel("Time (s)")
        plt.ylabel("Throughput (req/s)")
        plt.title(f"{benchmark_name} - Throughput Over Time")
        plt.grid(alpha=0.3)

        output_path = self.output_dir / f"{output_name}.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        return str(output_path)

    def generate_memory_chart(
        self, benchmark_name: str, memory_data: List[Dict[str, Any]], output_name: str = None
    ):
        """Generate memory usage chart.

        Args:
            benchmark_name: Name for chart title
            memory_data: List of {time: X, memory_mb: Y}
            output_name: Output filename
        """
        output_name = output_name or f"{benchmark_name}_memory"

        times = [d["time"] for d in memory_data]
        memory = [d["memory_mb"] for d in memory_data]

        plt.figure(figsize=(12, 6))
        plt.plot(times, memory, marker="s", linewidth=2, markersize=6, color="coral")
        plt.xlabel("Time (s)")
        plt.ylabel("Memory (MB)")
        plt.title(f"{benchmark_name} - Memory Usage Over Time")
        plt.grid(alpha=0.3)

        output_path = self.output_dir / f"{output_name}.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        return str(output_path)

    def generate_comparison_chart(
        self, benchmarks: Dict[str, Dict[str, float]], metric_name: str
    ):
        """Generate comparison chart across benchmarks.

        Args:
            benchmarks: {benchmark_name: {metric: value}}
            metric_name: Metric to compare
        """
        names = list(benchmarks.keys())
        values = [benchmarks[name].get(metric_name, 0) for name in names]

        plt.figure(figsize=(12, 6))
        bars = plt.bar(range(len(names)), values, color="mediumseagreen")
        plt.xticks(range(len(names)), names, rotation=45, ha="right")
        plt.ylabel(metric_name)
        plt.title(f"Comparison: {metric_name}")
        plt.grid(axis="y", alpha=0.3)

        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{value:.2f}",
                ha="center",
                va="bottom",
            )

        output_path = self.output_dir / f"comparison_{metric_name.replace(' ', '_')}.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        return str(output_path)

    def save_json_report(self):
        """Save detailed JSON report."""
        self.generate_summary()

        report_path = self.output_dir / f"performance_report_{self.timestamp}.json"

        with open(report_path, "w") as f:
            json.dump(self.report_data, f, indent=2, default=str)

        return str(report_path)

    def generate_markdown_report(self) -> str:
        """Generate markdown report.

        Returns:
            Path to generated markdown file
        """
        self.generate_summary()

        md_lines = []
        md_lines.append(f"# Performance Benchmark Report")
        md_lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Summary
        summary = self.report_data["summary"]
        md_lines.append("## Summary\n")
        md_lines.append(f"- Total Benchmarks: {summary['total_benchmarks']}")
        md_lines.append(f"- Passed: {summary['passed']}")
        md_lines.append(f"- Failed: {summary['failed']}")
        md_lines.append(f"- Pass Rate: {summary['pass_rate']:.1%}\n")

        # Benchmarks
        md_lines.append("## Benchmark Results\n")

        for name, data in self.report_data["benchmarks"].items():
            passed = data.get("passed")
            status = "✅ PASS" if passed else "❌ FAIL" if passed is False else "⏭️ N/A"

            md_lines.append(f"### {name} {status}\n")

            # Metrics table
            metrics = data["metrics"]
            targets = data.get("target", {})

            md_lines.append("| Metric | Value | Target | Status |")
            md_lines.append("|--------|-------|--------|--------|")

            for metric, value in metrics.items():
                target = targets.get(metric, "N/A")
                target_str = f"{target}" if target != "N/A" else "N/A"

                if target != "N/A":
                    met = value <= target if isinstance(target, (int, float)) else True
                    status_icon = "✓" if met else "✗"
                else:
                    status_icon = "-"

                value_str = f"{value:.2f}" if isinstance(value, float) else str(value)
                md_lines.append(f"| {metric} | {value_str} | {target_str} | {status_icon} |")

            md_lines.append("")

        # Save markdown
        report_path = self.output_dir / f"performance_report_{self.timestamp}.md"

        with open(report_path, "w") as f:
            f.write("\n".join(md_lines))

        return str(report_path)

    def generate_html_report(self) -> str:
        """Generate HTML report with charts.

        Returns:
            Path to generated HTML file
        """
        self.generate_summary()

        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("<title>Performance Benchmark Report</title>")
        html.append("<style>")
        html.append(
            """
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }
            h1, h2, h3 { color: #333; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #4CAF50; color: white; }
            .pass { color: green; font-weight: bold; }
            .fail { color: red; font-weight: bold; }
            .chart { margin: 20px 0; text-align: center; }
            .chart img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; }
            .summary { background: #e8f5e9; padding: 20px; border-radius: 4px; margin: 20px 0; }
        """
        )
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")
        html.append('<div class="container">')

        # Header
        html.append("<h1>Performance Benchmark Report</h1>")
        html.append(f"<p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")

        # Summary
        summary = self.report_data["summary"]
        html.append('<div class="summary">')
        html.append("<h2>Summary</h2>")
        html.append(f"<p>Total Benchmarks: {summary['total_benchmarks']}</p>")
        html.append(f"<p>Passed: <span class='pass'>{summary['passed']}</span></p>")
        html.append(f"<p>Failed: <span class='fail'>{summary['failed']}</span></p>")
        html.append(f"<p>Pass Rate: {summary['pass_rate']:.1%}</p>")
        html.append("</div>")

        # Benchmarks
        html.append("<h2>Benchmark Results</h2>")

        for name, data in self.report_data["benchmarks"].items():
            passed = data.get("passed")
            status_class = "pass" if passed else "fail" if passed is False else ""
            status_text = "PASS" if passed else "FAIL" if passed is False else "N/A"

            html.append(f"<h3>{name} <span class='{status_class}'>[{status_text}]</span></h3>")

            # Metrics table
            html.append("<table>")
            html.append("<tr><th>Metric</th><th>Value</th><th>Target</th><th>Status</th></tr>")

            metrics = data["metrics"]
            targets = data.get("target", {})

            for metric, value in metrics.items():
                target = targets.get(metric, "N/A")
                target_str = f"{target}" if target != "N/A" else "N/A"

                if target != "N/A":
                    met = value <= target if isinstance(target, (int, float)) else True
                    status_icon = "✓" if met else "✗"
                else:
                    status_icon = "-"

                value_str = f"{value:.2f}" if isinstance(value, float) else str(value)

                html.append(
                    f"<tr><td>{metric}</td><td>{value_str}</td><td>{target_str}</td><td>{status_icon}</td></tr>"
                )

            html.append("</table>")

        html.append("</div>")
        html.append("</body>")
        html.append("</html>")

        # Save HTML
        report_path = self.output_dir / f"performance_report_{self.timestamp}.html"

        with open(report_path, "w") as f:
            f.write("\n".join(html))

        return str(report_path)
