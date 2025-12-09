#!/usr/bin/env python3
"""Performance benchmark runner.

Runs all performance benchmarks and generates comprehensive reports.

Usage:
    python run_benchmarks.py --all                  # Run all benchmarks
    python run_benchmarks.py --latency              # Run latency benchmarks only
    python run_benchmarks.py --throughput           # Run throughput benchmarks only
    python run_benchmarks.py --load                 # Run load tests only
    python run_benchmarks.py --memory               # Run memory tests only
    python run_benchmarks.py --quick                # Run quick benchmark suite
    python run_benchmarks.py --full                 # Run full benchmark suite (includes soak test)
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from report_generator import PerformanceReportGenerator


class BenchmarkRunner:
    """Run and report on performance benchmarks."""

    def __init__(self, output_dir: str = None):
        """Initialize benchmark runner."""
        self.output_dir = output_dir or str(
            Path(__file__).parent / "reports" / datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        os.makedirs(self.output_dir, exist_ok=True)

        self.report_gen = PerformanceReportGenerator(self.output_dir)
        self.test_results = []

    def run_pytest(self, markers: str = None, test_file: str = None, args: list = None) -> int:
        """Run pytest with specified markers.

        Args:
            markers: Pytest markers to run (-m flag)
            test_file: Specific test file to run
            args: Additional pytest arguments

        Returns:
            Exit code
        """
        cmd = ["pytest", "-v", "--tb=short"]

        if markers:
            cmd.extend(["-m", markers])

        if test_file:
            cmd.append(test_file)
        else:
            cmd.append(str(Path(__file__).parent))

        if args:
            cmd.extend(args)

        # Add JSON report
        json_report = os.path.join(self.output_dir, "pytest_report.json")
        cmd.extend(["--json-report", f"--json-report-file={json_report}"])

        print(f"\n{'='*80}")
        print(f"Running: {' '.join(cmd)}")
        print(f"{'='*80}\n")

        result = subprocess.run(cmd)
        return result.returncode

    def run_latency_benchmarks(self):
        """Run latency benchmarks."""
        print("\n🚀 Running Latency Benchmarks...")

        exit_code = self.run_pytest(
            test_file="test_routing_latency.py",
            markers="benchmark and not slow",
        )

        if exit_code == 0:
            print("✅ Latency benchmarks passed")
        else:
            print("❌ Latency benchmarks failed")

        return exit_code

    def run_throughput_benchmarks(self):
        """Run throughput benchmarks."""
        print("\n🚀 Running Throughput Benchmarks...")

        exit_code = self.run_pytest(
            test_file="test_throughput.py",
            markers="benchmark and not slow",
        )

        if exit_code == 0:
            print("✅ Throughput benchmarks passed")
        else:
            print("❌ Throughput benchmarks failed")

        return exit_code

    def run_load_tests(self, include_soak: bool = False):
        """Run load tests."""
        print("\n🚀 Running Load Tests...")

        markers = "load"
        if not include_soak:
            markers += " and not slow"

        exit_code = self.run_pytest(test_file="test_concurrent_load.py", markers=markers)

        if exit_code == 0:
            print("✅ Load tests passed")
        else:
            print("❌ Load tests failed")

        return exit_code

    def run_memory_tests(self):
        """Run memory tests."""
        print("\n🚀 Running Memory Tests...")

        exit_code = self.run_pytest(
            test_file="test_memory_usage.py",
            markers="benchmark",
        )

        if exit_code == 0:
            print("✅ Memory tests passed")
        else:
            print("❌ Memory tests failed")

        return exit_code

    def run_quick_suite(self):
        """Run quick benchmark suite (no slow tests)."""
        print("\n🚀 Running Quick Benchmark Suite...")

        exit_code = self.run_pytest(markers="benchmark and not slow")

        if exit_code == 0:
            print("✅ Quick suite passed")
        else:
            print("❌ Quick suite failed")

        return exit_code

    def run_full_suite(self):
        """Run full benchmark suite (includes slow tests)."""
        print("\n🚀 Running Full Benchmark Suite...")

        exit_code = self.run_pytest(markers="benchmark or load")

        if exit_code == 0:
            print("✅ Full suite passed")
        else:
            print("❌ Full suite failed")

        return exit_code

    def generate_reports(self):
        """Generate performance reports."""
        print("\n📊 Generating Reports...")

        # Check if pytest JSON report exists
        json_report_path = os.path.join(self.output_dir, "pytest_report.json")

        if os.path.exists(json_report_path):
            with open(json_report_path) as f:
                pytest_data = json.load(f)

            # Extract benchmark data
            for test in pytest_data.get("tests", []):
                if test.get("outcome") == "passed":
                    self.report_gen.add_benchmark(
                        name=test.get("nodeid", "unknown"),
                        metrics={"duration": test.get("duration", 0)},
                    )

        # Generate reports
        json_path = self.report_gen.save_json_report()
        print(f"  ✓ JSON report: {json_path}")

        md_path = self.report_gen.generate_markdown_report()
        print(f"  ✓ Markdown report: {md_path}")

        html_path = self.report_gen.generate_html_report()
        print(f"  ✓ HTML report: {html_path}")

        print(f"\n📁 All reports saved to: {self.output_dir}")

    def print_summary(self):
        """Print benchmark summary."""
        print("\n" + "=" * 80)
        print("PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 80)

        json_report_path = os.path.join(self.output_dir, "pytest_report.json")

        if os.path.exists(json_report_path):
            with open(json_report_path) as f:
                data = json.load(f)

            summary = data.get("summary", {})

            print(f"\nTotal Tests: {summary.get('total', 0)}")
            print(f"Passed: {summary.get('passed', 0)}")
            print(f"Failed: {summary.get('failed', 0)}")
            print(f"Duration: {summary.get('duration', 0):.2f}s")

        print("\n" + "=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Bifrost SDK performance benchmarks")

    parser.add_argument("--all", action="store_true", help="Run all benchmarks (quick suite)")
    parser.add_argument("--latency", action="store_true", help="Run latency benchmarks")
    parser.add_argument("--throughput", action="store_true", help="Run throughput benchmarks")
    parser.add_argument("--load", action="store_true", help="Run load tests")
    parser.add_argument("--memory", action="store_true", help="Run memory tests")
    parser.add_argument("--quick", action="store_true", help="Run quick suite (no slow tests)")
    parser.add_argument("--full", action="store_true", help="Run full suite (includes slow tests)")
    parser.add_argument("--output", "-o", help="Output directory for reports")
    parser.add_argument("--no-report", action="store_true", help="Skip report generation")

    args = parser.parse_args()

    # Default to quick suite if no options specified
    if not any(
        [
            args.all,
            args.latency,
            args.throughput,
            args.load,
            args.memory,
            args.quick,
            args.full,
        ]
    ):
        args.quick = True

    runner = BenchmarkRunner(output_dir=args.output)

    exit_codes = []

    try:
        if args.latency:
            exit_codes.append(runner.run_latency_benchmarks())

        if args.throughput:
            exit_codes.append(runner.run_throughput_benchmarks())

        if args.load:
            exit_codes.append(runner.run_load_tests(include_soak=args.full))

        if args.memory:
            exit_codes.append(runner.run_memory_tests())

        if args.quick:
            exit_codes.append(runner.run_quick_suite())

        if args.full:
            exit_codes.append(runner.run_full_suite())

        if args.all:
            # Run all benchmark types
            exit_codes.append(runner.run_latency_benchmarks())
            exit_codes.append(runner.run_throughput_benchmarks())
            exit_codes.append(runner.run_load_tests())
            exit_codes.append(runner.run_memory_tests())

    finally:
        # Always generate reports
        if not args.no_report:
            runner.generate_reports()

        runner.print_summary()

    # Return non-zero if any tests failed
    sys.exit(max(exit_codes) if exit_codes else 0)


if __name__ == "__main__":
    main()
