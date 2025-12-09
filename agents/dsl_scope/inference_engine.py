"""
Comprehensive scope inference engine.

DEPRECATED: This module has been decomposed into dsl_scope/inference/ submodule.
Imports are preserved for backward compatibility.

New code should import from dsl_scope.inference directly:
    from dsl_scope.inference import (
        InferenceSignal,
        ScopeInferenceEngine,
        ComprehensiveScopeInferenceEngine,
        get_comprehensive_inference_engine,
    )
"""

# Re-export all public APIs for backward compatibility
from .inference import (
    InferenceSignal,
    ToolCallAnalysis,
    ChatAnalysis,
    ScopeInferenceEngine,
    ComprehensiveScopeInferenceEngine,
    get_comprehensive_inference_engine,
)

__all__ = [
    "InferenceSignal",
    "ToolCallAnalysis",
    "ChatAnalysis",
    "ScopeInferenceEngine",
    "ComprehensiveScopeInferenceEngine",
    "get_comprehensive_inference_engine",
]
