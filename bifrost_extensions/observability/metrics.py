"""Metrics collection using prometheus-client."""

from prometheus_client import Counter, Histogram, Gauge, REGISTRY, CollectorRegistry

__all__ = [
    "Counter",
    "Histogram",
    "Gauge",
    "get_metrics_collector",
]


def get_metrics_collector():
    """Get global metrics collector (registry).

    Returns prometheus-client's default registry for backward compatibility.
    """
    return REGISTRY
