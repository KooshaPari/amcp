"""
Scope inference engine - decomposed for modularity.

Re-exports all public APIs to maintain backward compatibility.
"""

# Data structures
from .types import (
    InferenceSignal,
    ToolCallAnalysis,
    ChatAnalysis,
)

# Core detection engine
from .detector import ScopeInferenceEngine

# Orchestration layer
from .orchestrator import ComprehensiveScopeInferenceEngine

# Factory
from .factory import get_comprehensive_inference_engine


__all__ = [
    # Types
    "InferenceSignal",
    "ToolCallAnalysis",
    "ChatAnalysis",
    # Engines
    "ScopeInferenceEngine",
    "ComprehensiveScopeInferenceEngine",
    # Factory
    "get_comprehensive_inference_engine",
]
