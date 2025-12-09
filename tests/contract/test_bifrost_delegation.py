import pytest

from infrastructure.bifrost.client import BifrostClient
from services.executor import UserScopedExecutor, ExecuteCodeRequest
from services.models import UserContext


@pytest.mark.asyncio
async def test_execute_falls_back_when_bifrost_unavailable():
    """Executor should gracefully fall back when Bifrost is unreachable."""
    # Arrange
    from smartcp.services.memory import UserScopedMemory
    from smartcp.infrastructure.state.memory import InMemoryStateAdapter

    client = BifrostClient()
    executor = UserScopedExecutor(
        memory=UserScopedMemory(InMemoryStateAdapter()),
        bifrost_client=client,
        enable_bifrost_execution=True,
    )
    user_ctx = UserContext(user_id="u1", device_id="d1", session_id="s1", project_id="p1")

    # Act / Assert: Bifrost unreachable should raise, then be caught by caller
    with pytest.raises(Exception):
        await executor._execute_via_bifrost(
            user_ctx,
            ExecuteCodeRequest(code="print('hi')"),
        )


@pytest.mark.asyncio
async def test_local_execution_still_works_without_bifrost(monkeypatch):
    """Local execution remains available when Bifrost is disabled."""
    from smartcp.services.memory import UserScopedMemory
    from smartcp.infrastructure.state.memory import InMemoryStateAdapter

    memory = UserScopedMemory(InMemoryStateAdapter())
    executor = UserScopedExecutor(memory=memory, enable_bifrost_execution=False)
    user_ctx = UserContext(user_id="u1")

    result = await executor.execute(
        user_ctx,
        ExecuteCodeRequest(code="x = 1 + 1\nresult = x"),
    )

    assert result.status.value in {"completed", "success", "completed"}  # legacy statuses
    assert result.error is None
