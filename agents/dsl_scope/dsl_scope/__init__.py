"""
DSL Scope System for SmartCP

This module implements a complete 11-level scope hierarchy for the Python DSL:
- BLOCK: Function/block-local scope
- ITERATION: Single iteration scope
- TOOL_CALL: Single tool invocation scope
- PROMPT_CHAIN: Multi-turn conversation scope
- SESSION: Entire CLI session scope
- PHASE: Session phase scope (plan/docwrite/impl)
- PROJECT: Project scope (can be inferred)
- WORKSPACE: Workspace scope
- ORGANIZATION: Organization scope
- GLOBAL: Cross-session shared scope
- PERMANENT: Forever-persisted scope

Features:
- Scoped variable persistence (in-memory → Redis → Supabase)
- Background task management (bg/await pattern)
- Project/workspace/org inference from chat
- Type system with contracts
- Extension CRUD
- Scope-aware context managers
"""

from dsl_scope.scope_levels import ScopeLevel, ScopeHierarchy, ScopeEntry
from dsl_scope.storage import ScopeStorage
from dsl_scope.context_tracking import (
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
from dsl_scope.background_tasks import (
    BackgroundTaskManager,
    BackgroundTask,
    TaskStatus,
)
from dsl_scope.dsl_system import DSLScopeSystem, get_dsl_scope_system
from dsl_scope.project_inference import (
    ProjectInferenceEngine,
    InferredContext,
    get_inference_engine,
)
from dsl_scope.inference import ComprehensiveScopeInferenceEngine

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
]

__version__ = "2.0.0"
