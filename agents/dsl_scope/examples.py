"""
Example usage of the DSL scope system.

Demonstrates:
- Scoped variable persistence
- Background task management (bg/await)
- Context managers
- Scope hierarchy navigation
"""

import asyncio
from . import get_dsl_scope_system, ScopeLevel


async def example_scoped_variables():
    """Example: Variable persistence across scope hierarchy."""
    print("\n=== Example 1: Scoped Variables ===\n")

    dsl = get_dsl_scope_system()

    # Global scope - shared across all sessions
    await dsl.set("api_key", "sk_global_123", ScopeLevel.GLOBAL, persist=True)
    print("✓ Set global API key")

    # Session scope - per CLI session
    async with dsl.session_context("user_session_001"):
        await dsl.set("user_id", "user_42", ScopeLevel.SESSION)
        await dsl.set("workspace_id", "workspace_789", ScopeLevel.SESSION)
        print("✓ Set session variables")

        # Lookup: finds in session scope
        user = await dsl.get("user_id")
        print(f"  user_id from session: {user}")

        # Lookup: finds in global scope (hierarchy)
        api_key = await dsl.get("api_key")
        print(f"  api_key from global: {api_key}")

        # Tool call scope - single invocation
        async with dsl.tool_call_context("tool_call_001", "data_processor"):
            await dsl.set("temp_cache", {"key": "value"}, ScopeLevel.TOOL_CALL)
            print("✓ Set tool_call variable")

            # Lookup across hierarchy: block → tool_call → session → global
            cache = await dsl.get("temp_cache")
            print(f"  temp_cache from tool_call: {cache}")

            # Tool-specific context is isolated
            temp = await dsl.get("temp_cache", ScopeLevel.TOOL_CALL)
            print(f"  temp_cache (explicit): {temp}")

        # After tool call scope exits, temp_cache is gone
        temp_after = await dsl.get("temp_cache")
        print(f"  temp_cache after exit: {temp_after}")  # None

    print()


async def example_background_tasks():
    """Example: Background task with suspension/resumption."""
    print("\n=== Example 2: Background Tasks ===\n")

    dsl = get_dsl_scope_system()

    async def long_running_process():
        """Simulated long-running task."""
        for i in range(5):
            await asyncio.sleep(1)
            print(f"  Progress: {i+1}/5")
        return {"status": "completed", "items_processed": 100}

    # Create background task
    task_id = await dsl.create_background_task(long_running_process)
    print(f"✓ Created task: {task_id}")

    # Start execution (non-blocking)
    await dsl.run_background_task(task_id)
    print(f"✓ Task running in background...")

    # Do other work while task runs
    await asyncio.sleep(2)
    print(f"  Main thread doing other work...")

    # Suspend task (Ctrl+Z equivalent)
    await dsl.suspend_task(task_id)
    print(f"✓ Task suspended")

    # Check status
    status = await dsl.get_task_status(task_id)
    print(f"  Task status: {status.value}")

    # Resume task
    await asyncio.sleep(1)
    await dsl.resume_task(task_id)
    print(f"✓ Task resumed")

    # Get result when done (await equivalent)
    result = await dsl.get_task_result(task_id)
    print(f"✓ Task result: {result}")
    print()


async def example_prompt_chain():
    """Example: Multi-turn conversation with scope hierarchy."""
    print("\n=== Example 3: Prompt Chain Scope ===\n")

    dsl = get_dsl_scope_system()

    async with dsl.session_context("conversation_session_001"):
        # Initialize conversation state
        await dsl.set("messages", [], ScopeLevel.PROMPT_CHAIN)
        await dsl.set("model", "claude-3-sonnet", ScopeLevel.SESSION)
        print("✓ Session started with empty message list")

        # Turn 1
        async with dsl.prompt_chain_context("chat_001", turn=1):
            user_msg = "What is the capital of France?"
            messages = await dsl.get("messages") or []
            messages.append({"role": "user", "content": user_msg})
            await dsl.set("messages", messages, ScopeLevel.PROMPT_CHAIN)

            print(f"  Turn 1: {user_msg}")

        # Turn 2
        async with dsl.prompt_chain_context("chat_001", turn=2):
            # Messages from turn 1 are accessible
            messages = await dsl.get("messages")
            print(f"  Context: {len(messages)} messages from previous turn")

            assistant_msg = "The capital of France is Paris."
            messages.append({"role": "assistant", "content": assistant_msg})
            await dsl.set("messages", messages, ScopeLevel.PROMPT_CHAIN)

            print(f"  Turn 2: {assistant_msg}")

        # Turn 3
        async with dsl.prompt_chain_context("chat_001", turn=3):
            messages = await dsl.get("messages")
            print(f"  Turn 3: Have {len(messages)} messages in context")

    print()


async def example_scope_isolation():
    """Example: Demonstrate scope isolation and cleanup."""
    print("\n=== Example 4: Scope Isolation ===\n")

    dsl = get_dsl_scope_system()

    async with dsl.session_context("test_session"):
        # Set in different scopes
        await dsl.set("block_var", "I am block-scoped", ScopeLevel.BLOCK)
        await dsl.set("session_var", "I am session-scoped", ScopeLevel.SESSION)
        await dsl.set("permanent_var", "I am permanent", ScopeLevel.PERMANENT)

        print("✓ Variables set in different scopes")

        # All accessible from within session
        block = await dsl.get("block_var")
        session = await dsl.get("session_var")
        permanent = await dsl.get("permanent_var")

        print(f"  block_var: {block}")
        print(f"  session_var: {session}")
        print(f"  permanent_var: {permanent}")

        # Clear block scope
        await dsl.clear_scope(ScopeLevel.BLOCK)
        print("✓ Cleared BLOCK scope")

        # Block var is gone
        block_after = await dsl.get("block_var")
        session_after = await dsl.get("session_var")

        print(f"  block_var after clear: {block_after}")  # None
        print(f"  session_var still exists: {session_after}")  # Still there

    # After session exits, session_var is gone
    permanent_outside = await dsl.get("permanent_var")
    session_outside = await dsl.get("session_var")

    print(f"  permanent_var after session: {permanent_outside}")  # Still exists
    print(f"  session_var after session: {session_outside}")  # None

    print()


async def main():
    """Run all examples."""
    print("=" * 60)
    print("DSL Scope System Examples")
    print("=" * 60)

    await example_scoped_variables()
    await example_background_tasks()
    await example_prompt_chain()
    await example_scope_isolation()

    print("=" * 60)
    print("All examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
