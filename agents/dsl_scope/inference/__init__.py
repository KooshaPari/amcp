"""Inference submodule for DSL scope system.

Provides scope inference capabilities for automatic scope detection.
"""

from .types import (
    InferenceSignal,
    ToolCallAnalysis,
    ChatAnalysis,
)
from .detector import ScopeInferenceEngine
from .orchestrator import ComprehensiveScopeInferenceEngine
from .factory import get_comprehensive_inference_engine

__all__ = [
    "InferenceSignal",
    "ToolCallAnalysis",
    "ChatAnalysis",
    "ScopeInferenceEngine",
    "ComprehensiveScopeInferenceEngine",
    "get_comprehensive_inference_engine",
]
