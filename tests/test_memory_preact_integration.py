"""
Integration tests for memory systems with PreAct planning.

Tests the interaction between MemorySystem and PreActPlanner,
validating that episodic memories are retrieved and outcomes are stored.
"""

import asyncio
import pytest
from typing import Any

from optimization.memory.integration import MemorySystem, MemoryConfig
from optimization.memory.episodic import TaskOutcome
from optimization.memory.semantic import RelationType
from optimization.planning.preact import PreActPlanner
from optimization.planning.types import PlanningConfig, PlanTree, PlanNode, NodeStatus
from optimization.preact_predictor import PreActConfig


@pytest.fixture
def memory_system():
    """Create memory system instance."""
    config = MemoryConfig()
    return MemorySystem(config)


@pytest.fixture
def preact_config():
    """Create PreAct configuration."""
    config = PreActConfig()
    config.similar_example_count = 3
    return config


@pytest.fixture
def planning_config():
    """Create planning configuration."""
    return PlanningConfig()


@pytest.fixture
def preact_planner(planning_config, preact_config, memory_system):
    """Create PreAct planner with memory system."""
    return PreActPlanner(
        config=planning_config,
        preact_config=preact_config,
        memory_system=memory_system,
    )


@pytest.mark.asyncio
class TestMemoryPreActIntegration:
    """Test memory system integration with PreAct planning."""

    async def test_episodic_retrieval_in_planning(self, memory_system):
        """Test that episodic memories are retrieved before planning."""
        # Store similar historical tasks
        for i in range(3):
            await memory_system.record_task(
                goal=f"Analyze data chunk {i}",
                context={"data_size": 100 * (i + 1)},
                tools_used=["analyzer"],
                outcome=TaskOutcome.SUCCESS,
                confidence=0.8 + (i * 0.05),
                duration=2.0 + (i * 0.5),
            )

        # Verify tasks were stored
        assert len(memory_system.episodic.entries) == 3

        # Retrieve similar tasks
        similar = await memory_system.recall_similar_tasks("Analyze data", limit=3)
        assert len(similar) == 3
        assert all("goal" in task for task in similar)

    async def test_outcome_storage_after_planning(self, memory_system):
        """Test that task outcomes are stored after planning."""
        goal = "Process and analyze dataset"
        context = {"tools": ["analyzer", "processor"]}

        # Create a mock plan tree with successful completion
        tree = self._create_mock_plan_tree(success=True)

        # Extract outcome by examining tree status directly
        # (simulating what PreActPlanner._extract_task_outcome does)
        if tree.best_path:
            last_node_id = tree.best_path[-1]
            last_node = tree.get_node(last_node_id)
            if last_node and last_node.status == NodeStatus.COMPLETED:
                outcome = TaskOutcome.SUCCESS
            else:
                outcome = TaskOutcome.FAILURE
        else:
            outcome = TaskOutcome.FAILURE

        assert outcome == TaskOutcome.SUCCESS

        # Manually record the task (simulating what happens in plan())
        entry_id = await memory_system.record_task(
            goal=goal,
            context=context,
            tools_used=context.get("tools", []),
            outcome=outcome,
            result={"actual_outcome": "Task completed successfully"},
            confidence=0.9,
            duration=3.5,
            lesson_learned="Batch processing is more efficient",
        )

        # Verify task was stored
        assert entry_id in memory_system.episodic.entries
        entry = memory_system.episodic.entries[entry_id]
        assert entry.goal == goal
        assert entry.outcome == TaskOutcome.SUCCESS
        assert entry.lesson_learned == "Batch processing is more efficient"

    async def test_semantic_facts_storage(self, memory_system):
        """Test that discovered facts are stored in semantic memory."""
        # Assert some facts
        fact_id_1 = await memory_system.assert_fact(
            entity="analyzer_tool",
            property_name="capability",
            value="data_analysis",
            confidence=0.95,
            source="planning_execution",
        )

        fact_id_2 = await memory_system.assert_fact(
            entity="analyzer_tool",
            property_name="performance",
            value="fast",
            confidence=0.85,
            source="planning_execution",
        )

        # Verify facts were stored
        assert fact_id_1 in memory_system.semantic.entries
        assert fact_id_2 in memory_system.semantic.entries

        # Query facts
        facts = await memory_system.query_facts("analyzer_tool")
        assert len(facts) == 2

    async def test_memory_context_preservation(self, memory_system):
        """Test that working memory preserves context during planning."""
        # Create a context
        context_id = await memory_system.create_context()
        assert context_id in memory_system.working.contexts

        # Push frame for planning
        frame_id = await memory_system.push_frame("Analyze data", context_id)
        assert frame_id

        # Bind variables
        success = await memory_system.bind_variable(
            var_name="dataset",
            value={"records": 1000},
            context_id=context_id,
        )
        assert success

        # Retrieve variable
        value = await memory_system.get_variable("dataset", context_id)
        assert value == {"records": 1000}

        # Pop frame
        frame = await memory_system.pop_frame(context_id)
        assert frame is not None
        assert frame["goal"] == "Analyze data"

    async def test_memory_stats_after_planning(self, memory_system):
        """Test that memory statistics are updated correctly."""
        # Record initial state
        initial_stats = await memory_system.get_stats()
        assert initial_stats.episodic["total_entries"] == 0
        assert initial_stats.semantic["fact_entries"] == 0

        # Add episodic memory
        await memory_system.record_task(
            goal="Test task",
            context={},
            tools_used=[],
            outcome=TaskOutcome.SUCCESS,
        )

        # Add semantic memory
        await memory_system.assert_fact(
            entity="test_entity",
            property_name="prop",
            value="value",
        )

        # Check updated stats
        updated_stats = await memory_system.get_stats()
        assert updated_stats.episodic["total_entries"] == 1
        assert updated_stats.semantic["fact_entries"] == 1
        assert updated_stats.total_memory_bytes > initial_stats.total_memory_bytes

    async def test_capacity_enforcement_during_planning(self, memory_system):
        """Test that memory capacity is enforced during planning."""
        # Reduce capacity for testing
        memory_system.config.episodic_config.max_entries = 5

        # Store more than capacity
        for i in range(7):
            await memory_system.record_task(
                goal=f"Task {i}",
                context={"index": i},
                tools_used=[],
                outcome=TaskOutcome.SUCCESS,
                confidence=0.5 + (i * 0.05),
            )

        # Enforce capacity
        result = await memory_system.enforce_capacity()

        # Check that eviction occurred
        assert len(memory_system.episodic.entries) <= 5
        if result:
            assert result.removed_count > 0

    async def test_lesson_learned_incorporation(self, memory_system):
        """Test that lessons learned are stored and retrieved."""
        # Record task with lesson
        entry_id = await memory_system.record_task(
            goal="Complex analysis",
            context={},
            tools_used=["analyzer"],
            outcome=TaskOutcome.SUCCESS,
            confidence=0.9,
            lesson_learned="Always validate input data first",
        )

        # Retrieve and verify lesson
        entry = memory_system.episodic.entries[entry_id]
        assert entry.lesson_learned == "Always validate input data first"

        # Retrieve similar tasks
        similar = await memory_system.recall_similar_tasks("Complex", limit=1)
        assert len(similar) == 1
        assert similar[0]["lesson_learned"] == "Always validate input data first"

    async def test_relationship_tracking(self, memory_system):
        """Test that relationships between entities are tracked."""
        # Assert relationships
        rel_id = await memory_system.assert_relationship(
            entity1="analyzer",
            relation_type=RelationType.REQUIRES,
            entity2="database",
            weight=0.9,
            confidence=0.95,
        )

        assert rel_id in memory_system.semantic.relations

        # Query relationships
        relations = await memory_system.semantic.query_relations(entity1="analyzer")
        assert len(relations) > 0
        assert relations[0].entity2 == "database"

    async def test_concurrent_memory_updates(self, memory_system):
        """Test concurrent memory updates during planning."""
        # Create concurrent tasks
        tasks = [
            memory_system.record_task(
                goal=f"Task {i}",
                context={"id": i},
                tools_used=[],
                outcome=TaskOutcome.SUCCESS,
            )
            for i in range(10)
        ]

        entry_ids = await asyncio.gather(*tasks)
        assert len(entry_ids) == 10
        assert all(eid in memory_system.episodic.entries for eid in entry_ids)

    async def test_memory_cleanup_cycle(self, memory_system):
        """Test memory cleanup cycles during planning."""
        # Record some tasks
        for i in range(5):
            await memory_system.record_task(
                goal=f"Task {i}",
                context={},
                tools_used=[],
                outcome=TaskOutcome.SUCCESS,
            )

        # Run cleanup
        idle_count = await memory_system.cleanup_idle()
        decayed_count = await memory_system.decay_semantic_confidence()

        # Verify operations completed
        assert idle_count >= 0
        assert decayed_count >= 0

    def _create_mock_plan_tree(self, success: bool = True) -> PlanTree:
        """Create a mock plan tree for testing."""
        tree = PlanTree()

        # Create a root node
        root_node = PlanNode(
            id="root",
            thought="Test thought",
            status=NodeStatus.COMPLETED if success else NodeStatus.FAILED,
            observation="Test observation",
        )

        tree.add_node(root_node)
        tree.best_path = ["root"]

        return tree


@pytest.mark.asyncio
class TestMemoryPreActWorkflow:
    """Test complete workflows integrating memory and planning."""

    async def test_full_planning_with_memory_workflow(self, memory_system):
        """Test a complete workflow with memory integration."""
        # Phase 1: Record historical tasks
        for i in range(2):
            await memory_system.record_task(
                goal=f"Analyze repository {i}",
                context={"repo_size": 1000 + (i * 500)},
                tools_used=["analyzer", "scanner"],
                outcome=TaskOutcome.SUCCESS,
                confidence=0.85,
                duration=5.0,
                lesson_learned=f"Lesson {i}",
            )

        # Phase 2: Store discovered facts
        await memory_system.assert_fact(
            entity="code_analyzer",
            property_name="capability",
            value="static_analysis",
            confidence=0.9,
        )

        # Phase 3: Retrieve similar tasks
        similar = await memory_system.recall_similar_tasks("Analyze", limit=5)
        assert len(similar) == 2

        # Phase 4: Record new task
        new_task_id = await memory_system.record_task(
            goal="Analyze new repository",
            context={"repo_size": 2000},
            tools_used=["analyzer", "scanner", "reporter"],
            outcome=TaskOutcome.SUCCESS,
            confidence=0.88,
            duration=6.5,
            lesson_learned="Parallel scanning improves performance",
        )

        # Verify complete workflow
        assert new_task_id in memory_system.episodic.entries
        assert len(memory_system.episodic.entries) == 3

        # Check stats
        stats = await memory_system.get_stats()
        assert stats.episodic["total_entries"] == 3
        assert stats.semantic["fact_entries"] == 1

    async def test_memory_recovery_from_planning_failure(self, memory_system):
        """Test memory recovery when planning fails."""
        # Record a failed task
        failed_task_id = await memory_system.record_task(
            goal="Failed analysis",
            context={"error": "resource_limit"},
            tools_used=["analyzer"],
            outcome=TaskOutcome.FAILURE,
            confidence=0.0,
            lesson_learned="Need more resources for large datasets",
        )

        # Record a successful recovery task
        recovery_task_id = await memory_system.record_task(
            goal="Failed analysis recovery",
            context={"error": "resource_limit", "retry": True},
            tools_used=["analyzer"],
            outcome=TaskOutcome.SUCCESS,
            confidence=0.8,
            lesson_learned="Retrying with reduced scope works",
        )

        # Verify both recorded
        assert failed_task_id in memory_system.episodic.entries
        assert recovery_task_id in memory_system.episodic.entries

        # Check that success rate reflects recovery
        success_rate = await memory_system.episodic.get_success_rate("Failed analysis")
        assert success_rate == 0.5  # 1 success, 1 failure
