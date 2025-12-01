"""
Test Metrics & Reporting - 95% Coverage, 100% Pass, 0% Error

Provides:
- Test metrics collection
- Coverage reporting
- Pass rate tracking
- Error rate monitoring
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class TestMetrics:
    """Test metrics."""
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    errors: int = 0
    warnings: int = 0
    total_time: float = 0.0
    coverage: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    test_results: List[Dict] = field(default_factory=list)
    
    @property
    def pass_rate(self) -> float:
        """Calculate pass rate."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        if self.total_tests == 0:
            return 0.0
        return (self.errors / self.total_tests) * 100
    
    @property
    def fail_rate(self) -> float:
        """Calculate fail rate."""
        if self.total_tests == 0:
            return 0.0
        return (self.failed_tests / self.total_tests) * 100
    
    def add_test_result(self, name: str, status: str, duration: float, error: Optional[str] = None):
        """Add test result."""
        self.test_results.append({
            "name": name,
            "status": status,
            "duration": duration,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        
        if status == "passed":
            self.passed_tests += 1
        elif status == "failed":
            self.failed_tests += 1
            self.errors += 1
        elif status == "skipped":
            self.skipped_tests += 1
        
        self.total_tests += 1
    
    def get_summary(self) -> Dict:
        """Get summary."""
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "skipped_tests": self.skipped_tests,
            "errors": self.errors,
            "warnings": self.warnings,
            "pass_rate": f"{self.pass_rate:.2f}%",
            "error_rate": f"{self.error_rate:.2f}%",
            "fail_rate": f"{self.fail_rate:.2f}%",
            "coverage": f"{self.coverage:.2f}%",
            "total_time": f"{self.total_time:.2f}s"
        }


class TestReporter:
    """Test reporter."""
    
    def __init__(self):
        self.metrics = TestMetrics()
        self.start_time = None
    
    def start(self):
        """Start reporting."""
        self.start_time = time.time()
        self.metrics.start_time = datetime.now()
    
    def end(self):
        """End reporting."""
        if self.start_time:
            self.metrics.total_time = time.time() - self.start_time
        self.metrics.end_time = datetime.now()
    
    def report_test(self, name: str, status: str, duration: float, error: Optional[str] = None):
        """Report test."""
        self.metrics.add_test_result(name, status, duration, error)
    
    def set_coverage(self, coverage: float):
        """Set coverage."""
        self.metrics.coverage = coverage
    
    def get_report(self) -> str:
        """Get report."""
        summary = self.metrics.get_summary()
        report = "TEST REPORT\n"
        report += "=" * 50 + "\n"
        for key, value in summary.items():
            report += f"{key}: {value}\n"
        report += "=" * 50 + "\n"
        return report
    
    def get_json_report(self) -> Dict:
        """Get JSON report."""
        return {
            "metrics": self.metrics.get_summary(),
            "results": self.metrics.test_results,
            "start_time": self.metrics.start_time.isoformat() if self.metrics.start_time else None,
            "end_time": self.metrics.end_time.isoformat() if self.metrics.end_time else None
        }


class CoverageAnalyzer:
    """Coverage analyzer."""
    
    def __init__(self):
        self.covered_lines = 0
        self.total_lines = 0
        self.covered_branches = 0
        self.total_branches = 0
        self.covered_functions = 0
        self.total_functions = 0
    
    def add_line_coverage(self, covered: int, total: int):
        """Add line coverage."""
        self.covered_lines = covered
        self.total_lines = total
    
    def add_branch_coverage(self, covered: int, total: int):
        """Add branch coverage."""
        self.covered_branches = covered
        self.total_branches = total
    
    def add_function_coverage(self, covered: int, total: int):
        """Add function coverage."""
        self.covered_functions = covered
        self.total_functions = total
    
    @property
    def line_coverage(self) -> float:
        """Get line coverage."""
        if self.total_lines == 0:
            return 0.0
        return (self.covered_lines / self.total_lines) * 100
    
    @property
    def branch_coverage(self) -> float:
        """Get branch coverage."""
        if self.total_branches == 0:
            return 0.0
        return (self.covered_branches / self.total_branches) * 100
    
    @property
    def function_coverage(self) -> float:
        """Get function coverage."""
        if self.total_functions == 0:
            return 0.0
        return (self.covered_functions / self.total_functions) * 100
    
    @property
    def overall_coverage(self) -> float:
        """Get overall coverage."""
        coverages = [self.line_coverage, self.branch_coverage, self.function_coverage]
        return sum(coverages) / len(coverages) if coverages else 0.0
    
    def get_coverage_report(self) -> Dict:
        """Get coverage report."""
        return {
            "line_coverage": f"{self.line_coverage:.2f}%",
            "branch_coverage": f"{self.branch_coverage:.2f}%",
            "function_coverage": f"{self.function_coverage:.2f}%",
            "overall_coverage": f"{self.overall_coverage:.2f}%"
        }


class QualityGateChecker:
    """Quality gate checker."""
    
    def __init__(self, coverage_threshold: float = 95.0, pass_rate_threshold: float = 100.0, error_threshold: float = 0.0):
        self.coverage_threshold = coverage_threshold
        self.pass_rate_threshold = pass_rate_threshold
        self.error_threshold = error_threshold
    
    def check_coverage(self, coverage: float) -> bool:
        """Check coverage."""
        return coverage >= self.coverage_threshold
    
    def check_pass_rate(self, pass_rate: float) -> bool:
        """Check pass rate."""
        return pass_rate >= self.pass_rate_threshold
    
    def check_error_rate(self, error_rate: float) -> bool:
        """Check error rate."""
        return error_rate <= self.error_threshold
    
    def check_all(self, metrics: TestMetrics, coverage: float) -> bool:
        """Check all gates."""
        coverage_ok = self.check_coverage(coverage)
        pass_rate_ok = self.check_pass_rate(metrics.pass_rate)
        error_rate_ok = self.check_error_rate(metrics.error_rate)
        
        return coverage_ok and pass_rate_ok and error_rate_ok
    
    def get_gate_status(self, metrics: TestMetrics, coverage: float) -> Dict:
        """Get gate status."""
        return {
            "coverage": {
                "threshold": f"{self.coverage_threshold:.2f}%",
                "actual": f"{coverage:.2f}%",
                "passed": self.check_coverage(coverage)
            },
            "pass_rate": {
                "threshold": f"{self.pass_rate_threshold:.2f}%",
                "actual": f"{metrics.pass_rate:.2f}%",
                "passed": self.check_pass_rate(metrics.pass_rate)
            },
            "error_rate": {
                "threshold": f"{self.error_threshold:.2f}%",
                "actual": f"{metrics.error_rate:.2f}%",
                "passed": self.check_error_rate(metrics.error_rate)
            },
            "overall": self.check_all(metrics, coverage)
        }

