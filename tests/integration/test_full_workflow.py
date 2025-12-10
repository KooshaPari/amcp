"""Integration tests for full workflow."""

import pytest

from smartcp.runtime import AgentRuntime, UserContext
from smartcp.runtime.types import ExecutionStatus


class TestFullWorkflow:
    """Integration tests for complete workflows."""

    @pytest.fixture
    def runtime(self):
        """Create an agent runtime."""
        return AgentRuntime()

    @pytest.fixture
    def user_ctx(self):
        """Create a user context."""
        return UserContext(user_id="workflow-user", workspace_id="ws-123")

    @pytest.mark.asyncio
    async def test_data_processing_workflow(self, runtime, user_ctx):
        """Test a complete data processing workflow."""
        code = """
# 1. Initialize data in session scope
await scope.session.set("data", [1, 2, 3, 4, 5])

# 2. Define a processing tool
@tool
async def process_data() -> dict:
    data = await scope.session.get("data")
    processed = [x * 2 for x in data]
    await scope.session.set("processed", processed)
    return {"count": len(processed)}

# 3. Process data
result = await process_data()
print(f"Processed {result['count']} items")

# 4. Verify processed data
processed = await scope.session.get("processed")
print(f"First item: {processed[0]}")

# 5. Promote to permanent storage
await scope.promote("processed", "session", "permanent")
"""
        result = await runtime.execute(code, user_ctx)

        assert result.status == ExecutionStatus.COMPLETED
        assert "Processed 5 items" in result.output
        assert "First item: 2" in result.output

    @pytest.mark.asyncio
    async def test_multi_step_workflow(self, runtime, user_ctx):
        """Test a multi-step workflow with background tasks."""
        code = """
# Step 1: Setup
await scope.session.set("step", 1)
await scope.session.set("results", [])

# Step 2: Define async processing function
async def process_step(step_num):
    import asyncio
    await asyncio.sleep(0.05)  # Simulate work
    return f"Step {step_num} completed"

# Step 3: Process steps in background
tasks = []
for i in range(3):
    task = bg(process_step(i + 1))
    tasks.append(task)

# Step 4: Wait for all tasks
results = []
for task in tasks:
    result = await task
    results.append(result)
    await scope.session.set("results", results)

# Step 5: Finalize
final_results = await scope.session.get("results")
print(f"Completed {len(final_results)} steps")
"""
        result = await runtime.execute(code, user_ctx)

        assert result.status == ExecutionStatus.COMPLETED
        assert "Completed 3 steps" in result.output

    @pytest.mark.asyncio
    async def test_skill_workflow(self, runtime, user_ctx):
        """Test workflow using skills."""
        code = """
# Save a skill
skill_content = '''
# Data Processing Skill

Processes data and stores results.
'''
await skills.save("data_processor", skill_content)

# Load the skill
skill = await skills.load("data_processor")
print(f"Skill loaded: {skill['status']}")

# List skills
all_skills = await skills.list()
print(f"Total skills: {len(all_skills)}")
"""
        result = await runtime.execute(code, user_ctx)

        assert result.status == ExecutionStatus.COMPLETED
        assert "Skill loaded: loaded" in result.output
        assert "Total skills: 1" in result.output
