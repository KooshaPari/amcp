# Work Package 03: PreAct Planning Memory Integration

**Priority**: HIGH  
**Estimated Time**: 1-2 hours  
**Current Coverage**: 78% → Target: 90%+

## Objective

Achieve 90%+ coverage for `optimization/planning/preact.py` by testing memory integration paths and global instance creation.

## Missing Lines

- **Lines 107-155**: Memory integration paths (reflection, episodic memory, semantic facts)
- **Lines 236-242**: Global planner instance creation (`get_preact_planner`)

## Tasks

### Task 1: Enhance Memory Integration Tests (Lines 107-155)

Enhance `tests/optimization/test_preact_memory_integration.py`:

```python
@pytest.mark.asyncio
async def test_full_memory_integration_with_discovered_facts(
    self, planner, mock_memory_system, mock_tool_executor
):
    """Test complete memory integration path including discovered facts (lines 107-155)."""
    goal = "Test goal with facts discovery"
    context = {"tools": ["discover_tool"]}
    
    # Create a tree that will have best_path and prediction
    tree = await planner.plan(goal, context, mock_tool_executor)
    
    # Manually add discovered_facts to metadata to test assertion path
    if tree.best_path:
        tree.metadata = tree.metadata or {}
        tree.metadata["discovered_facts"] = [
            {
                "entity": "test_entity",
                "property": "test_property",
                "value": "test_value",
                "confidence": 0.9,
            },
            {
                "entity": "another_entity",
                "property": "another_property",
                "value": "another_value",
                "confidence": 0.8,
            },
        ]
        
        # Re-trigger memory integration by calling plan again with facts
        # OR manually call the memory integration code path
        # For now, verify the structure allows facts to be asserted
        
        # Verify memory.record_task was called
        assert mock_memory_system.record_task.called
        
        # If we can trigger the fact assertion path, verify assert_fact calls
        # This may require patching or restructuring the test
```

**Note**: The discovered_facts path (lines 145-155) may require restructuring the test to inject facts into tree.metadata before the memory integration code runs. Consider:
- Patching `planner.plan` to inject facts
- Creating a tree manually and calling memory integration code directly
- Using a mock that allows setting metadata before reflection

### Task 2: Test Global Planner Instance Creation (Lines 236-242)

Add to `tests/optimization/test_preact_planner.py` or create new test file:

```python
from optimization.planning_strategy import get_preact_planner, PlanningConfig
from optimization.preact_predictor import PreActConfig
from unittest.mock import MagicMock

def test_get_preact_planner_creates_new_instance():
    """Test get_preact_planner creates new instance when None (lines 236-242)."""
    # Reset global state
    import optimization.planning_strategy as planning_module
    planning_module._preact_planner = None
    
    # First call should create new instance
    planner1 = get_preact_planner()
    assert planner1 is not None
    assert isinstance(planner1, PreActPlanner)
    
    # Second call should return same instance
    planner2 = get_preact_planner()
    assert planner2 is planner1  # Same instance
    
    # Cleanup
    planning_module._preact_planner = None

def test_get_preact_planner_with_custom_config():
    """Test get_preact_planner with custom parameters."""
    import optimization.planning_strategy as planning_module
    planning_module._preact_planner = None
    
    config = PlanningConfig(max_depth=3)
    preact_config = PreActConfig(enable_prediction=True)
    memory_system = MagicMock()
    
    planner = get_preact_planner(config, preact_config, memory_system)
    
    assert planner.config.max_depth == 3
    assert planner.preact.config.enable_prediction is True
    assert planner.memory is memory_system
    
    # Cleanup
    planning_module._preact_planner = None
```

## Verification

Run coverage check:
```bash
uv run pytest tests/optimization/test_preact_memory_integration.py \
  tests/optimization/test_preact_planner.py \
  --cov=optimization.planning.preact \
  --cov-report=term-missing -v
```

**Success Criteria**:
- ✅ Coverage shows 90%+ for `preact.py`
- ✅ Lines 107-155 are covered (memory integration)
- ✅ Lines 236-242 are covered (global instance)
- ✅ All existing tests still pass
- ✅ Memory integration paths fully tested

## Reference

- File: `optimization/planning/preact.py`
- Existing tests: `tests/optimization/test_preact_memory_integration.py`
- Memory interface: `optimization/memory/episodic.py`
- See lines 105-155 (memory integration) and 229-242 (global instance)

## Notes

- The discovered_facts path may require creative testing approaches
- Consider using mocks to inject facts into tree.metadata
- Global instance tests need to reset `_preact_planner` between tests
