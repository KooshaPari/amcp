"""
Async context managers for scope entry/exit.

Provides Pythonic context manager syntax for scope operations:
    async with dsl.session_context("session_123"):
        # Session scope active
        pass
    # Session scope exited, cleaned up
"""

from contextlib import asynccontextmanager, contextmanager
from typing import Optional, AsyncGenerator, Generator, Any
from .context_tracking import ContextManager, ScopeContext
from .scope_levels import ScopeLevel
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def session_scope(session_id: str) -> AsyncGenerator[ScopeContext, None]:
    """Context manager for session scope.

    Usage:
        async with session_scope("session_123") as ctx:
            # Session scope active
            pass
        # Session scope exited
    """
    original_context = ContextManager.get_current_context()

    try:
        await ContextManager.set_session_context(session_id)
        yield ContextManager.get_current_context()
    finally:
        # Restore original context
        ContextManager.create_scope_context(original_context)
        logger.debug(f"Session scope exited: {session_id}")


@asynccontextmanager
async def tool_call_scope(
    tool_call_id: str, tool_name: str
) -> AsyncGenerator[ScopeContext, None]:
    """Context manager for tool call scope.

    Usage:
        async with tool_call_scope("call_456", "my_tool") as ctx:
            # Tool call scope active
            pass
        # Tool call scope exited
    """
    original_context = ContextManager.get_current_context()

    try:
        await ContextManager.set_tool_call_context(tool_call_id, tool_name)
        yield ContextManager.get_current_context()
    finally:
        ContextManager.create_scope_context(original_context)
        logger.debug(f"Tool call scope exited: {tool_call_id}")


@asynccontextmanager
async def prompt_chain_scope(
    chain_id: str, turn: int
) -> AsyncGenerator[ScopeContext, None]:
    """Context manager for prompt chain scope.

    Usage:
        async with prompt_chain_scope("chain_789", 1) as ctx:
            # Prompt chain scope active
            pass
        # Prompt chain scope exited
    """
    original_context = ContextManager.get_current_context()

    try:
        await ContextManager.set_prompt_chain_context(chain_id, turn)
        yield ContextManager.get_current_context()
    finally:
        ContextManager.create_scope_context(original_context)
        logger.debug(f"Prompt chain scope exited: {chain_id}")


@asynccontextmanager
async def iteration_scope(iteration_id: str) -> AsyncGenerator[ScopeContext, None]:
    """Context manager for iteration scope.

    Usage:
        async with iteration_scope("iter_123") as ctx:
            # Iteration scope active
            pass
        # Iteration scope exited
    """
    original_context = ContextManager.get_current_context()

    try:
        await ContextManager.set_iteration_context(iteration_id)
        yield ContextManager.get_current_context()
    finally:
        ContextManager.create_scope_context(original_context)
        logger.debug(f"Iteration scope exited: {iteration_id}")


@asynccontextmanager
async def phase_scope(
    phase_id: str, phase_type: str
) -> AsyncGenerator[ScopeContext, None]:
    """Context manager for phase scope (plan/docwrite/impl).

    Usage:
        async with phase_scope("phase_456", "impl") as ctx:
            # Phase scope active
            pass
        # Phase scope exited
    """
    original_context = ContextManager.get_current_context()

    try:
        await ContextManager.set_phase_context(phase_id, phase_type)
        yield ContextManager.get_current_context()
    finally:
        ContextManager.create_scope_context(original_context)
        logger.debug(f"Phase scope exited: {phase_id} ({phase_type})")


@asynccontextmanager
async def project_scope(
    project_id: str, project_name: Optional[str] = None
) -> AsyncGenerator[ScopeContext, None]:
    """Context manager for project scope.

    Usage:
        async with project_scope("proj_789", "MyApp") as ctx:
            # Project scope active
            pass
        # Project scope exited
    """
    original_context = ContextManager.get_current_context()

    try:
        await ContextManager.set_project_context(project_id, project_name)
        yield ContextManager.get_current_context()
    finally:
        ContextManager.create_scope_context(original_context)
        logger.debug(f"Project scope exited: {project_id}")


@asynccontextmanager
async def workspace_scope(
    workspace_id: str, workspace_name: Optional[str] = None
) -> AsyncGenerator[ScopeContext, None]:
    """Context manager for workspace scope.

    Usage:
        async with workspace_scope("ws_123", "Engineering") as ctx:
            # Workspace scope active
            pass
        # Workspace scope exited
    """
    original_context = ContextManager.get_current_context()

    try:
        await ContextManager.set_workspace_context(workspace_id, workspace_name)
        yield ContextManager.get_current_context()
    finally:
        ContextManager.create_scope_context(original_context)
        logger.debug(f"Workspace scope exited: {workspace_id}")


@asynccontextmanager
async def organization_scope(
    org_id: str, org_name: Optional[str] = None
) -> AsyncGenerator[ScopeContext, None]:
    """Context manager for organization scope.

    Usage:
        async with organization_scope("org_456", "Acme Corp") as ctx:
            # Organization scope active
            pass
        # Organization scope exited
    """
    original_context = ContextManager.get_current_context()

    try:
        await ContextManager.set_organization_context(org_id, org_name)
        yield ContextManager.get_current_context()
    finally:
        ContextManager.create_scope_context(original_context)
        logger.debug(f"Organization scope exited: {org_id}")


@contextmanager
def local_scope(
    namespace: Optional[dict[str, Any]] = None
) -> Generator[dict[str, Any], None, None]:
    """Context manager for local (block) scope.

    Usage:
        with local_scope({"temp": 123}) as ns:
            # Local scope active with temp variable
            pass
        # Local scope exited
    """
    original_ns = ContextManager.get_local_namespace()

    try:
        if namespace:
            ContextManager.update_local_namespace(namespace)

        yield ContextManager.get_local_namespace()
    finally:
        # Restore local namespace
        ContextManager.update_local_namespace(original_ns)
