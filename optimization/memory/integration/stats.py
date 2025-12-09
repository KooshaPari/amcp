"""
Memory System Statistics

Statistics collection and reporting for memory systems.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..forgetting import EvictionResult


@dataclass
class MemoryStats:
    """Statistics for all memory systems."""

    episodic: Dict[str, Any]
    semantic: Dict[str, Any]
    working: Dict[str, Any]
    total_memory_bytes: int
    capacity_utilization: float
    last_cleanup: float
    last_eviction: Optional[EvictionResult] = None
