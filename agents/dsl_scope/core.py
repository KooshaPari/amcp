"""
Core re-exports for dsl_scope module.

This module consolidates all public APIs from submodules for cleaner imports.
Internal clients should import directly from the appropriate submodule.
"""

# Scope levels
from .scope_levels import ScopeLevel, ScopeHierarchy, ScopeEntry

# Storage
from .storage import ScopeStorage

# Context tracking
from .context_tracking import (
    ContextManager,
    ScopeContext,
    _current_session_id,
    _current_prompt_chain_id,
    _current_tool_call_id,
    _current_iteration_id,
    _current_phase_id,
    _current_project_id,
    _current_workspace_id,
    _current_organization_id,
)

# Background tasks
from .background_tasks import (
    BackgroundTaskManager,
    BackgroundTask,
    TaskStatus,
)

# Main system
from .dsl_system import DSLScopeSystem, get_dsl_scope_system

# Project inference
from .project_inference import (
    ProjectInferenceEngine,
    InferredContext,
    get_inference_engine,
)

# Comprehensive scope inference
from .inference import ComprehensiveScopeInferenceEngine

# Inference types
from .inference.types import InferenceSignal

__all__ = [
    # Scope levels
    "ScopeLevel",
    "ScopeHierarchy",
    "ScopeEntry",
    # Storage
    "ScopeStorage",
    # Context tracking
    "ContextManager",
    "ScopeContext",
    "_current_session_id",
    "_current_prompt_chain_id",
    "_current_tool_call_id",
    "_current_iteration_id",
    "_current_phase_id",
    "_current_project_id",
    "_current_workspace_id",
    "_current_organization_id",
    # Background tasks
    "BackgroundTaskManager",
    "BackgroundTask",
    "TaskStatus",
    # Main system
    "DSLScopeSystem",
    "get_dsl_scope_system",
    # Project inference
    "ProjectInferenceEngine",
    "InferredContext",
    "get_inference_engine",
    # Comprehensive scope inference
    "ComprehensiveScopeInferenceEngine",
    # Inference types
    "InferenceSignal",
]
