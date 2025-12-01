"""
Context tracking using contextvars for async-safe scope management.

Uses Python's contextvars module to track scope context across async
operations without thread-local state issues.
"""

from contextvars import ContextVar, copy_context
from typing import Optional
from dataclasses import dataclass, field


# Context variables for tracking active scopes (async-safe)
_current_session_id: ContextVar[Optional[str]] = ContextVar(
    'current_session_id', default=None
)
_current_phase_id: ContextVar[Optional[str]] = ContextVar(
    'current_phase_id', default=None
)
_current_project_id: ContextVar[Optional[str]] = ContextVar(
    'current_project_id', default=None
)
_current_workspace_id: ContextVar[Optional[str]] = ContextVar(
    'current_workspace_id', default=None
)
_current_organization_id: ContextVar[Optional[str]] = ContextVar(
    'current_organization_id', default=None
)
_current_prompt_chain_id: ContextVar[Optional[str]] = ContextVar(
    'current_prompt_chain_id', default=None
)
_current_tool_call_id: ContextVar[Optional[str]] = ContextVar(
    'current_tool_call_id', default=None
)
_current_iteration_id: ContextVar[Optional[str]] = ContextVar(
    'current_iteration_id', default=None
)
_scope_stack: ContextVar[list[str]] = ContextVar(
    'scope_stack', default=[]
)
_local_namespace: ContextVar[dict[str, any]] = ContextVar(
    'local_namespace', default={}
)


@dataclass
class ScopeContext:
    """Immutable snapshot of current scope context."""
    session_id: Optional[str] = None
    phase_id: Optional[str] = None
    project_id: Optional[str] = None
    workspace_id: Optional[str] = None
    organization_id: Optional[str] = None
    prompt_chain_id: Optional[str] = None
    tool_call_id: Optional[str] = None
    iteration_id: Optional[str] = None
    scope_stack: list[str] = field(default_factory=list)
    local_ns: dict[str, any] = field(default_factory=dict)

    def get_effective_scope_id(self) -> Optional[str]:
        """Get most specific active scope ID."""
        if self.iteration_id:
            return self.iteration_id
        if self.tool_call_id:
            return self.tool_call_id
        if self.prompt_chain_id:
            return self.prompt_chain_id
        if self.session_id:
            return self.session_id
        if self.phase_id:
            return self.phase_id
        if self.project_id:
            return self.project_id
        if self.workspace_id:
            return self.workspace_id
        if self.organization_id:
            return self.organization_id
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "phase_id": self.phase_id,
            "project_id": self.project_id,
            "workspace_id": self.workspace_id,
            "organization_id": self.organization_id,
            "prompt_chain_id": self.prompt_chain_id,
            "tool_call_id": self.tool_call_id,
            "iteration_id": self.iteration_id,
            "scope_stack": self.scope_stack.copy(),
            "effective_scope": self.get_effective_scope_id(),
        }


class ContextManager:
    """Manage context variables with snapshot/restore capabilities."""

    @staticmethod
    def get_current_context() -> ScopeContext:
        """Get immutable snapshot of current scope context."""
        return ScopeContext(
            session_id=_current_session_id.get(),
            phase_id=_current_phase_id.get(),
            project_id=_current_project_id.get(),
            workspace_id=_current_workspace_id.get(),
            organization_id=_current_organization_id.get(),
            prompt_chain_id=_current_prompt_chain_id.get(),
            tool_call_id=_current_tool_call_id.get(),
            iteration_id=_current_iteration_id.get(),
            scope_stack=_scope_stack.get().copy() if _scope_stack.get() else [],
            local_ns=_local_namespace.get().copy() if _local_namespace.get() else {},
        )

    @staticmethod
    async def set_session_context(session_id: str) -> None:
        """Set session context."""
        _current_session_id.set(session_id)
        stack = _scope_stack.get().copy() if _scope_stack.get() else []
        stack.append(f"session:{session_id}")
        _scope_stack.set(stack)

    @staticmethod
    async def set_tool_call_context(tool_call_id: str, tool_name: str) -> None:
        """Set tool call context."""
        _current_tool_call_id.set(tool_call_id)
        stack = _scope_stack.get().copy() if _scope_stack.get() else []
        stack.append(f"tool_call:{tool_call_id}:{tool_name}")
        _scope_stack.set(stack)

    @staticmethod
    async def set_prompt_chain_context(chain_id: str, turn: int) -> None:
        """Set prompt chain context."""
        _current_prompt_chain_id.set(chain_id)
        stack = _scope_stack.get().copy() if _scope_stack.get() else []
        stack.append(f"prompt_chain:{chain_id}:turn{turn}")
        _scope_stack.set(stack)

    @staticmethod
    async def set_iteration_context(iteration_id: str) -> None:
        """Set iteration context."""
        _current_iteration_id.set(iteration_id)
        stack = _scope_stack.get().copy() if _scope_stack.get() else []
        stack.append(f"iteration:{iteration_id}")
        _scope_stack.set(stack)

    @staticmethod
    async def set_phase_context(phase_id: str, phase_type: str) -> None:
        """Set phase context (plan/docwrite/impl)."""
        _current_phase_id.set(phase_id)
        stack = _scope_stack.get().copy() if _scope_stack.get() else []
        stack.append(f"phase:{phase_id}:{phase_type}")
        _scope_stack.set(stack)

    @staticmethod
    async def set_project_context(project_id: str, project_name: Optional[str] = None) -> None:
        """Set project context (can be inferred)."""
        _current_project_id.set(project_id)
        stack = _scope_stack.get().copy() if _scope_stack.get() else []
        name_part = f":{project_name}" if project_name else ""
        stack.append(f"project:{project_id}{name_part}")
        _scope_stack.set(stack)

    @staticmethod
    async def set_workspace_context(workspace_id: str, workspace_name: Optional[str] = None) -> None:
        """Set workspace context."""
        _current_workspace_id.set(workspace_id)
        stack = _scope_stack.get().copy() if _scope_stack.get() else []
        name_part = f":{workspace_name}" if workspace_name else ""
        stack.append(f"workspace:{workspace_id}{name_part}")
        _scope_stack.set(stack)

    @staticmethod
    async def set_organization_context(org_id: str, org_name: Optional[str] = None) -> None:
        """Set organization context."""
        _current_organization_id.set(org_id)
        stack = _scope_stack.get().copy() if _scope_stack.get() else []
        name_part = f":{org_name}" if org_name else ""
        stack.append(f"organization:{org_id}{name_part}")
        _scope_stack.set(stack)

    @staticmethod
    def get_local_namespace() -> dict[str, any]:
        """Get current local namespace."""
        return _local_namespace.get().copy() if _local_namespace.get() else {}

    @staticmethod
    def update_local_namespace(updates: dict[str, any]) -> None:
        """Update local namespace."""
        ns = _local_namespace.get().copy() if _local_namespace.get() else {}
        ns.update(updates)
        _local_namespace.set(ns)

    @staticmethod
    def create_scope_context(ctx: ScopeContext) -> None:
        """Restore context from snapshot."""
        if ctx.session_id:
            _current_session_id.set(ctx.session_id)
        if ctx.phase_id:
            _current_phase_id.set(ctx.phase_id)
        if ctx.project_id:
            _current_project_id.set(ctx.project_id)
        if ctx.workspace_id:
            _current_workspace_id.set(ctx.workspace_id)
        if ctx.organization_id:
            _current_organization_id.set(ctx.organization_id)
        if ctx.prompt_chain_id:
            _current_prompt_chain_id.set(ctx.prompt_chain_id)
        if ctx.tool_call_id:
            _current_tool_call_id.set(ctx.tool_call_id)
        if ctx.iteration_id:
            _current_iteration_id.set(ctx.iteration_id)
        _scope_stack.set(ctx.scope_stack.copy() if ctx.scope_stack else [])
        _local_namespace.set(ctx.local_ns.copy() if ctx.local_ns else {})

    @staticmethod
    def clear_context() -> None:
        """Clear all context variables."""
        _current_session_id.set(None)
        _current_phase_id.set(None)
        _current_project_id.set(None)
        _current_workspace_id.set(None)
        _current_organization_id.set(None)
        _current_prompt_chain_id.set(None)
        _current_tool_call_id.set(None)
        _current_iteration_id.set(None)
        _scope_stack.set([])
        _local_namespace.set({})
