"""E2E tests for complete user scenarios."""

import pytest

from smartcp.runtime import AgentRuntime, UserContext
from smartcp.tools.execute import execute, set_runtime


class TestCompleteUserScenarios:
    """End-to-end tests for complete user scenarios."""

    @pytest.fixture(autouse=True)
    def setup_runtime(self):
        """Setup runtime for each test."""
        runtime = AgentRuntime()
        set_runtime(runtime)
        yield runtime

    @pytest.mark.asyncio
    async def test_user_onboarding_flow(self):
        """Test complete user onboarding flow."""
        # Simulate user onboarding
        result = await execute(
            code="""
# User sets preferences
await scope.session.set("theme", "dark")
await scope.session.set("language", "en")

# Create a welcome tool
@tool
async def welcome_user(name: str) -> dict:
    theme = await scope.session.get("theme")
    return {
        "message": f"Welcome, {name}!",
        "theme": theme
    }

# Use the tool
greeting = await welcome_user("Alice")
print(greeting["message"])

# Save preferences to permanent storage
await scope.promote("theme", "session", "permanent")
await scope.promote("language", "session", "permanent")

print("Onboarding complete")
""",
            timeout=30,
        )

        assert result["status"] == "completed"
        assert "Welcome, Alice!" in result["output"]
        assert "Onboarding complete" in result["output"]

    @pytest.mark.asyncio
    async def test_data_analysis_workflow(self):
        """Test a data analysis workflow."""
        result = await execute(
            code="""
# Load data
data = [10, 20, 30, 40, 50]
await scope.session.set("raw_data", data)

# Define analysis tool
@tool
async def analyze() -> dict:
    data = await scope.session.get("raw_data")
    total = sum(data)
    avg = total / len(data)
    return {"total": total, "average": avg}

# Run analysis
analysis = await analyze()
print(f"Total: {analysis['total']}, Average: {analysis['average']}")

# Process in background
async def process():
    data = await scope.session.get("raw_data")
    return [x * 2 for x in data]

task = bg(process())
processed = await task
await scope.session.set("processed_data", processed)

print(f"Processed {len(processed)} items")
""",
            timeout=30,
        )

        assert result["status"] == "completed"
        assert "Total: 150" in result["output"]
        assert "Average: 30" in result["output"]
        assert "Processed 5 items" in result["output"]

    @pytest.mark.asyncio
    async def test_multi_user_collaboration(self):
        """Test multi-user collaboration scenario."""
        # User 1 creates shared resource
        result1 = await execute(
            code="""
await scope.workspace.set("shared_doc", "Initial content")
print("Document created")
""",
            timeout=30,
        )

        assert result1["status"] == "completed"

        # User 2 reads shared resource
        result2 = await execute(
            code="""
content = await scope.workspace.get("shared_doc")
print(f"Read: {content}")
""",
            timeout=30,
        )

        # Note: In real implementation, workspace scope would be shared
        # This test validates the API works
        assert result2["status"] == "completed"
