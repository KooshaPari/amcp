"""
Main DSL scope system - unified API for all scope operations.

Combines variable storage, background tasks, and context management
into a single coherent system.
"""

import logging
from typing import Optional, Any, Callable
from dsl_scope.scope_levels import ScopeLevel, ScopeHierarchy
from dsl_scope.context_tracking import ContextManager, ScopeContext
from dsl_scope.storage import ScopeStorage
from dsl_scope.background_tasks import BackgroundTaskManager, TaskStatus
from dsl_scope.context_managers import (
    session_scope,
    tool_call_scope,
    prompt_chain_scope,
    iteration_scope,
    phase_scope,
    project_scope,
    workspace_scope,
    organization_scope,
    local_scope,
)
from dsl_scope.project_inference import get_inference_engine, InferredContext

logger = logging.getLogger(__name__)


class DSLScopeSystem:
    """Unified DSL scope system with all features."""

    def __init__(self, db_path: str = "dsl_scope.db"):
        self.storage = ScopeStorage(db_path)
        self.background_tasks = BackgroundTaskManager()
        self.context_manager = ContextManager

    # === SCOPE VARIABLE MANAGEMENT ===

    async def set(
        self,
        key: str,
        value: Any,
        scope: ScopeLevel = ScopeLevel.SESSION,
        ttl: Optional[int] = None,
        persist: bool = True,
    ) -> None:
        """Set variable in scope."""
        await self.storage.set(key, value, scope, ttl, persist)
        logger.debug(f"Set {key} in {scope.value} scope")

    async def get(self, key: str, scope: Optional[ScopeLevel] = None) -> Optional[Any]:
        """Get variable from scope (auto-lookup hierarchy if scope not specified)."""
        if scope:
            return await self.storage.get(key, scope)

        # Auto-lookup across hierarchy
        current_ctx = self.context_manager.get_current_context()
        # Get scopes from most specific to most general
        scopes = ScopeHierarchy.get_scope_chain(ScopeLevel.PERMANENT)
        return await self.storage.lookup(key, scopes)

    async def delete(self, key: str, scope: ScopeLevel) -> bool:
        """Delete variable from scope."""
        return await self.storage.delete(key, scope)

    async def clear_scope(self, scope: ScopeLevel) -> None:
        """Clear all variables in scope."""
        await self.storage.clear_scope(scope)
        logger.info(f"Cleared {scope.value} scope")

    async def list_keys(self, scope: ScopeLevel) -> list[str]:
        """List all keys in a scope."""
        return await self.storage.list_keys(scope)

    # === SCOPE CONTEXT MANAGEMENT ===

    def get_current_context(self) -> ScopeContext:
        """Get current scope context snapshot."""
        return self.context_manager.get_current_context()

    async def enter_session(self, session_id: str) -> None:
        """Enter session scope."""
        await self.context_manager.set_session_context(session_id)

    async def enter_tool_call(self, tool_call_id: str, tool_name: str) -> None:
        """Enter tool call scope."""
        await self.context_manager.set_tool_call_context(tool_call_id, tool_name)

    async def enter_prompt_chain(self, chain_id: str, turn: int) -> None:
        """Enter prompt chain scope."""
        await self.context_manager.set_prompt_chain_context(chain_id, turn)

    # === BACKGROUND TASK MANAGEMENT ===

    async def create_background_task(
        self, coro: Callable, task_id: Optional[str] = None
    ) -> str:
        """Create background task (bg equivalent)."""
        return await self.background_tasks.create_task(coro, task_id)

    async def run_background_task(self, task_id: str) -> None:
        """Start background task execution."""
        await self.background_tasks.run_task(task_id)

    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get background task status."""
        return await self.background_tasks.get_task_status(task_id)

    async def get_task_result(self, task_id: str) -> Optional[Any]:
        """Get background task result (await equivalent)."""
        return await self.background_tasks.get_task_result(task_id)

    async def suspend_task(self, task_id: str) -> bool:
        """Suspend background task (Ctrl+Z equivalent)."""
        return await self.background_tasks.suspend_task(task_id)

    async def resume_task(self, task_id: str) -> bool:
        """Resume background task."""
        return await self.background_tasks.resume_task(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel background task."""
        return await self.background_tasks.cancel_task(task_id)

    async def list_tasks(
        self, status: Optional[TaskStatus] = None
    ) -> dict[str, dict]:
        """List background tasks."""
        return await self.background_tasks.list_tasks(status)

    # === CONTEXT MANAGERS ===

    def session_context(self, session_id: str):
        """Async context manager for session scope."""
        return session_scope(session_id)

    def tool_call_context(self, tool_call_id: str, tool_name: str):
        """Async context manager for tool call scope."""
        return tool_call_scope(tool_call_id, tool_name)

    def prompt_chain_context(self, chain_id: str, turn: int):
        """Async context manager for prompt chain scope."""
        return prompt_chain_scope(chain_id, turn)

    def iteration_context(self, iteration_id: str):
        """Async context manager for iteration scope."""
        return iteration_scope(iteration_id)

    def phase_context(self, phase_id: str, phase_type: str):
        """Async context manager for phase scope (plan/docwrite/impl)."""
        return phase_scope(phase_id, phase_type)

    def project_context(self, project_id: str, project_name: Optional[str] = None):
        """Async context manager for project scope."""
        return project_scope(project_id, project_name)

    def workspace_context(self, workspace_id: str, workspace_name: Optional[str] = None):
        """Async context manager for workspace scope."""
        return workspace_scope(workspace_id, workspace_name)

    def organization_context(self, org_id: str, org_name: Optional[str] = None):
        """Async context manager for organization scope."""
        return organization_scope(org_id, org_name)

    def local_context(self, namespace: Optional[dict[str, Any]] = None):
        """Context manager for local scope."""
        return local_scope(namespace)

    # === PROJECT INFERENCE ===

    def infer_project(self, message: str) -> InferredContext:
        """Infer project/workspace/org context from message."""
        engine = get_inference_engine()
        return engine.infer_from_message(message)

    def infer_from_history(self, window: int = 10) -> InferredContext:
        """Infer context from recent conversation history."""
        engine = get_inference_engine()
        return engine.infer_from_history(window)

    async def auto_set_inferred_context(self, inferred: InferredContext) -> None:
        """Automatically set scopes from inferred context."""
        if inferred.organization_id and inferred.confidence > 0.7:
            await self.context_manager.set_organization_context(
                inferred.organization_id, inferred.organization_name
            )

        if inferred.workspace_id and inferred.confidence > 0.7:
            await self.context_manager.set_workspace_context(
                inferred.workspace_id, inferred.workspace_name
            )

        if inferred.project_id and inferred.confidence > 0.5:
            await self.context_manager.set_project_context(
                inferred.project_id, inferred.project_name
            )

    # === CLEANUP ===

    async def cleanup(self) -> None:
        """Cleanup all resources."""
        await self.background_tasks.cleanup()
        logger.info("DSL scope system cleanup complete")


# Global singleton instance
_dsl_scope_system: Optional[DSLScopeSystem] = None


def get_dsl_scope_system(db_path: str = "dsl_scope.db") -> DSLScopeSystem:
    """Get or create global DSL scope system singleton."""
    global _dsl_scope_system
    if _dsl_scope_system is None:
        _dsl_scope_system = DSLScopeSystem(db_path)
    return _dsl_scope_system
