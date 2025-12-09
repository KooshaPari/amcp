"""
DSL Scope System for SmartCP

11-level scope hierarchy for Python DSL with scoped variable persistence,
background task management, and project/workspace/org inference.
"""

from .core import (
    # Main exports
    get_dsl_scope_system,
    DSLScopeSystem,
    ScopeLevel,
    ScopeContext,
    ContextManager,
    BackgroundTaskManager,
    BackgroundTask,
    TaskStatus,
    ScopeStorage,
    ProjectInferenceEngine,
    InferredContext,
    get_inference_engine,
    ComprehensiveScopeInferenceEngine,
    InferenceSignal,
)

__all__ = [
    "get_dsl_scope_system",
    "DSLScopeSystem",
    "ScopeLevel",
    "ScopeContext",
    "ContextManager",
    "BackgroundTaskManager",
    "BackgroundTask",
    "TaskStatus",
    "ScopeStorage",
    "ProjectInferenceEngine",
    "InferredContext",
    "get_inference_engine",
    "ComprehensiveScopeInferenceEngine",
    "InferenceSignal",
]

__version__ = "2.0.0"
