#!/usr/bin/env python3
"""Validate performance testing setup.

Checks that all dependencies are installed and tests can be discovered.
"""

import sys
from pathlib import Path


def check_dependencies():
    """Check if all required dependencies are installed."""
    print("Checking dependencies...")

    required = [
        "pytest",
        "pytest_asyncio",
        "pytest_benchmark",
        "psutil",
        "matplotlib",
    ]

    missing = []

    for module in required:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError:
            print(f"  ✗ {module} - MISSING")
            missing.append(module)

    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False

    print("✅ All dependencies installed")
    return True


def check_test_files():
    """Check if all test files exist."""
    print("\nChecking test files...")

    test_dir = Path(__file__).parent

    required_files = [
        "conftest.py",
        "test_routing_latency.py",
        "test_throughput.py",
        "test_concurrent_load.py",
        "test_memory_usage.py",
        "report_generator.py",
        "run_benchmarks.py",
        "grafana_dashboard.json",
        "requirements.txt",
        "README.md",
    ]

    missing = []

    for filename in required_files:
        filepath = test_dir / filename
        if filepath.exists():
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename} - MISSING")
            missing.append(filename)

    if missing:
        print(f"\n❌ Missing files: {', '.join(missing)}")
        return False

    print("✅ All test files present")
    return True


def check_pytest_collection():
    """Check if pytest can collect tests."""
    print("\nChecking pytest test collection...")

    import subprocess

    test_dir = Path(__file__).parent

    try:
        result = subprocess.run(
            ["pytest", "--collect-only", "-q", str(test_dir)],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            # Count tests
            lines = result.stdout.strip().split("\n")
            test_count = len([l for l in lines if "test_" in l])

            print(f"  ✓ {test_count} tests discovered")
            print("✅ Pytest can collect tests")
            return True
        else:
            print(f"  ✗ Collection failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ✗ Error running pytest: {e}")
        return False


def check_grafana_dashboard():
    """Check if Grafana dashboard JSON is valid."""
    print("\nChecking Grafana dashboard...")

    import json

    dashboard_file = Path(__file__).parent / "grafana_dashboard.json"

    try:
        with open(dashboard_file) as f:
            data = json.load(f)

        if "dashboard" in data:
            panels = len(data["dashboard"].get("panels", []))
            print(f"  ✓ Valid JSON with {panels} panels")
            print("✅ Grafana dashboard valid")
            return True
        else:
            print("  ✗ Invalid dashboard structure")
            return False

    except json.JSONDecodeError as e:
        print(f"  ✗ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Run all validation checks."""
    print("="*80)
    print("Performance Testing Setup Validation")
    print("="*80)

    checks = [
        check_dependencies,
        check_test_files,
        check_pytest_collection,
        check_grafana_dashboard,
    ]

    results = []

    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Check failed with exception: {e}")
            results.append(False)

    print("\n" + "="*80)

    if all(results):
        print("✅ ALL CHECKS PASSED")
        print("\nSetup is complete! You can now run:")
        print("  python run_benchmarks.py --quick")
        print("="*80)
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nPlease fix the issues above before running benchmarks.")
        print("="*80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
