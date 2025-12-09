# Coverage Improvement Work Packages

Work packages for agents to improve test coverage in the `optimization` module.

**Current Status**: 66% overall coverage (1029 missing lines)
**Target**: 80%+ overall, 90%+ for core modules

---

## Package 1: Quick Win - Parallel Executor Edge Cases (HIGH PRIORITY)

**Objective**: Achieve 100% coverage for `optimization/parallel_executor/executor.py`

**Current Coverage**: 97% (2 missing lines)

**Missing Lines**:
- Line 101: Return statement after retry exhaustion path
- Line 152: Exception handling in batch execution when `isinstance(result, Exception)` is True

**Files to Modify**:
- `tests/optimization/test_parallel_executor_detailed.py`

**Tasks**:
1. Add test for retry exhaustion path (line 101):
   - Create a tool that fails consistently
   - Set `max_retries` to a low number (e.g., 2)
   - Verify that after all retries are exhausted, the function returns the failed result
   - Ensure the return statement at line 101 is executed

2. Add test for exception handling in batch (line 152):
   - Create a batch execution where `asyncio.gather(..., return_exceptions=True)` returns an Exception object
   - Verify that the exception is caught and converted to a `ToolResult` with `FAILED` status
   - Ensure line 152 (`if isinstance(result, Exception):`) is executed

**Acceptance Criteria**:
- Both missing lines are covered
- Coverage reaches 100% for `executor.py`
- All existing tests still pass
- New tests follow existing test patterns in the file

**Reference Code**:
```python
# See optimization/parallel_executor/executor.py lines 85-101 and 145-155
# See existing tests in tests/optimization/test_parallel_executor_detailed.py
```

---

## Package 2: Quick Win - Compression Types Properties (HIGH PRIORITY)

**Objective**: Achieve 95%+ coverage for `optimization/compression/types.py`

**Current Coverage**: 88% (7 missing lines)

**Missing Lines**:
- Lines 79-83: `compression_ratio` property edge case (when `original_content` is empty/None)
- Line 100: `tokens_saved` property
- Line 105: `cost_savings_estimate` property

**Files to Modify**:
- `tests/optimization/test_compression_compressor.py` (or create `test_compression_types.py`)

**Tasks**:
1. Test `ContentChunk.compression_ratio` property edge cases:
   - Test when `original_content` is `None` → should return 1.0
   - Test when `original_content` is empty string → should return 1.0
   - Test when `original_len == 0` → should return 1.0
   - Test normal case with actual compression

2. Test `CompressionResult.tokens_saved` property:
   - Create a `CompressionResult` with `original_tokens=100` and `compressed_tokens=70`
   - Verify `tokens_saved` returns 30

3. Test `CompressionResult.cost_savings_estimate` property:
   - Create a `CompressionResult` with `tokens_saved=1000`
   - Verify `cost_savings_estimate` returns `(1000 / 1000) * 0.003 = 0.003`
   - Test edge case with `tokens_saved=0` → should return 0.0

**Acceptance Criteria**:
- All 7 missing lines are covered
- Coverage reaches 95%+ for `types.py`
- Edge cases properly tested
- All existing tests still pass

**Reference Code**:
```python
# See optimization/compression/types.py lines 76-105
# Property definitions:
# - ContentChunk.compression_ratio (lines 76-83)
# - CompressionResult.tokens_saved (lines 97-100)
# - CompressionResult.cost_savings_estimate (lines 102-105)
```

---

## Package 3: Quick Win - PreAct Planning Memory Integration (HIGH PRIORITY)

**Objective**: Achieve 90%+ coverage for `optimization/planning/preact.py`

**Current Coverage**: 78% (18 missing lines)

**Missing Lines**:
- Lines 107-155: Memory integration paths (reflection, episodic memory recording, semantic fact assertion)
- Lines 236-242: Global planner instance creation (`get_preact_planner`)

**Files to Modify**:
- `tests/optimization/test_preact_memory_integration.py` (already exists, needs enhancement)

**Tasks**:
1. Enhance memory integration tests (lines 107-155):
   - Test the full path where `tree.best_path` exists AND `prediction` exists
   - Verify `actual_outcome` extraction (line 107)
   - Verify reflection is called with correct parameters (lines 113-116)
   - Verify reflection is stored in metadata (lines 123-126)
   - Verify episodic memory recording (lines 132-141)
   - Test semantic fact assertion when `discovered_facts` exists in metadata (lines 145-155)
   - Test edge case where `discovered_facts` is empty list
   - Test edge case where fact dict is missing required keys

2. Test global planner instance creation (lines 236-242):
   - Test `get_preact_planner()` creates new instance when `_preact_planner` is None
   - Test `get_preact_planner()` returns existing instance when already created
   - Test with custom config, preact_config, and memory_system parameters
   - Test that subsequent calls return the same instance

**Acceptance Criteria**:
- All 18 missing lines are covered
- Coverage reaches 90%+ for `preact.py`
- Memory integration paths fully tested
- Global instance management tested
- All existing tests still pass

**Reference Code**:
```python
# See optimization/planning/preact.py lines 105-155 and 229-242
# See existing tests in tests/optimization/test_preact_memory_integration.py
# Memory system interface: optimization/memory/episodic.py
```

---

## Package 4: Medium Priority - Model Router Edge Cases

**Objective**: Improve coverage for `optimization/model_router/router.py` from 70% to 85%+

**Current Coverage**: 70% (25 missing lines)

**Missing Lines**: 69-72, 77-78, 80-81, 89-102, 113, 155-167, 213, 217-218, 222

**Files to Modify**:
- `tests/optimization/test_model_router.py` (enhance existing)

**Tasks**:
1. Review missing lines in `router.py` to understand what paths are not covered
2. Add tests for:
   - Router fallback paths (lines 69-72, 77-78, 80-81)
   - Error handling paths (lines 89-102, 113)
   - Complex routing scenarios (lines 155-167)
   - Edge cases (lines 213, 217-218, 222)

**Acceptance Criteria**:
- Coverage improves to 85%+
- Critical routing paths tested
- Error handling paths tested
- All existing tests still pass

**Reference Code**:
```python
# See optimization/model_router/router.py
# See existing tests in tests/optimization/test_model_router.py
```

---

## Package 5: Medium Priority - Integration Pipeline Edge Cases

**Objective**: Improve coverage for `optimization/integration.py` from 69% to 80%+

**Current Coverage**: 69% (30 missing lines)

**Missing Lines**: 110-112, 121, 145-158, 185, 187-188, 220-226, 230-235, 258, 270-272, 281-282, 290-291

**Files to Modify**:
- `tests/optimization/test_integration_pipeline.py` (enhance existing)

**Tasks**:
1. Review missing lines to identify untested paths
2. Add tests for:
   - Error handling in pipeline stages
   - Edge cases in optimization flow
   - Cache warming scenarios
   - Tool execution edge cases

**Acceptance Criteria**:
- Coverage improves to 80%+
- Pipeline error paths tested
- Edge cases covered
- All existing tests still pass

**Reference Code**:
```python
# See optimization/integration.py
# See existing tests in tests/optimization/test_integration_pipeline.py
```

---

## Package 6: Medium Priority - PreAct Predictor Edge Cases

**Objective**: Improve coverage for `optimization/preact_predictor.py` from 86% to 92%+

**Current Coverage**: 86% (32 missing lines)

**Missing Lines**: 191-192, 203-206, 246, 248, 250, 264-270, 296, 299, 303, 306, 322, 341-345, 348, 386, 411, 448, 450, 476, 481, 502, 532-533, 537-538

**Files to Modify**:
- `tests/optimization/test_preact_predictor.py` (enhance existing)

**Tasks**:
1. Review missing lines to identify untested prediction/reflection paths
2. Add tests for:
   - Edge cases in prediction generation
   - Reflection accuracy calculations
   - Confidence level mappings
   - Cache eviction scenarios
   - Episodic example retrieval edge cases

**Acceptance Criteria**:
- Coverage improves to 92%+
- Prediction edge cases tested
- Reflection paths tested
- All existing tests still pass

**Reference Code**:
```python
# See optimization/preact_predictor.py
# See existing tests in tests/optimization/test_preact_predictor.py
```

---

## Package 7: Medium Priority - Prompt Cache Edge Cases

**Objective**: Improve coverage for `optimization/prompt_cache.py` from 93% to 97%+

**Current Coverage**: 93% (12 missing lines)

**Missing Lines**: 177, 310-311, 315-318, 336-339, 352

**Files to Modify**:
- `tests/optimization/test_prompt_cache.py` (enhance existing)

**Tasks**:
1. Review missing lines to identify untested cache paths
2. Add tests for:
   - Cache expiration edge cases
   - Cache size limit eviction
   - Prefix matching edge cases
   - Cache statistics edge cases

**Acceptance Criteria**:
- Coverage improves to 97%+
- Cache edge cases tested
- All existing tests still pass

**Reference Code**:
```python
# See optimization/prompt_cache.py
# See existing tests in tests/optimization/test_prompt_cache.py
```

---

## Package 8: Low Priority - Memory Subsystems (Optional)

**Objective**: Improve coverage for memory modules from 30-43% to 60%+

**Modules**:
- `optimization/memory/episodic.py`: 43% (88 missing lines)
- `optimization/memory/forgetting.py`: 32% (102 missing lines)
- `optimization/memory/semantic.py`: 41% (93 missing lines)
- `optimization/memory/working.py`: 33% (126 missing lines)
- `optimization/memory/integration/system.py`: 41% (75 missing lines)

**Files to Create/Modify**:
- `tests/optimization/test_memory_episodic.py` (create if doesn't exist)
- `tests/optimization/test_memory_forgetting.py` (create if doesn't exist)
- `tests/optimization/test_memory_semantic.py` (create if doesn't exist)
- `tests/optimization/test_memory_working.py` (create if doesn't exist)
- `tests/optimization/test_memory_integration.py` (create if doesn't exist)

**Tasks**:
1. Create comprehensive test suites for each memory subsystem
2. Test core functionality:
   - Episodic memory: task recording, recall, similarity search
   - Forgetting: decay mechanisms, cleanup
   - Semantic memory: fact storage, retrieval, querying
   - Working memory: temporary storage, context management
   - Integration: system-level coordination

**Acceptance Criteria**:
- Each module reaches 60%+ coverage
- Core functionality tested
- Integration paths tested
- All tests pass

**Note**: This is low priority as memory subsystems may be less critical for core optimization functionality.

---

## Package 9: Low Priority - Streaming Module (Optional)

**Objective**: Improve coverage for `optimization/streaming.py` from 36% to 60%+

**Current Coverage**: 36% (127 missing lines)

**Files to Create/Modify**:
- `tests/optimization/test_streaming.py` (create if doesn't exist)

**Tasks**:
1. Create comprehensive test suite for streaming functionality
2. Test:
   - Stream creation and management
   - Event emission and subscription
   - Error handling in streaming
   - Stream lifecycle management

**Acceptance Criteria**:
- Coverage improves to 60%+
- Core streaming paths tested
- Error handling tested
- All tests pass

**Note**: Low priority unless streaming is actively used.

---

## Package 10: Low Priority - HTTP2 Modules (Optional)

**Objective**: Improve coverage for HTTP2 modules from 33-37% to 60%+

**Modules**:
- `optimization/http2_app.py`: 33% (34 missing lines)
- `optimization/http2_config.py`: 37% (77 missing lines)

**Files to Create/Modify**:
- `tests/optimization/test_http2_app.py` (create if doesn't exist)
- `tests/optimization/test_http2_config.py` (create if doesn't exist)

**Tasks**:
1. Create test suites for HTTP2 functionality
2. Test:
   - HTTP2 app initialization and configuration
   - HTTP2-specific features
   - Configuration edge cases

**Acceptance Criteria**:
- Each module reaches 60%+ coverage
- Core HTTP2 paths tested
- All tests pass

**Note**: Low priority unless HTTP2 is actively used.

---

## Agent Instructions

### For Each Package:

1. **Read the Context**:
   - Review the target file(s) to understand what needs testing
   - Review existing tests to understand patterns
   - Check `tests/optimization/conftest.py` for shared fixtures

2. **Follow Test Patterns**:
   - Use `@pytest.mark.asyncio` for async tests
   - Use fixtures from `conftest.py` when available
   - Follow naming: `test_<functionality>_<scenario>`
   - Keep tests focused and isolated

3. **Memory Considerations**:
   - Keep test data sizes reasonable (avoid large multipliers)
   - Use `max_nodes`, `max_iterations`, `timeout_seconds` in planning tests
   - Clean up resources (close TestClient, await async generators)

4. **Verification**:
   - Run: `uv run pytest tests/optimization/ --cov=optimization --cov-report=term-missing`
   - Verify target coverage is achieved
   - Ensure all existing tests still pass
   - Check for any new memory issues

5. **Documentation**:
   - Add docstrings to new test methods
   - Update this file with completion status

### Priority Order:

1. **Start with Packages 1-3** (Quick Wins) - Highest ROI
2. **Then Packages 4-7** (Medium Priority) - Good coverage gains
3. **Finally Packages 8-10** (Low Priority) - Only if time permits

---

## Completion Tracking

- [ ] Package 1: Parallel Executor Edge Cases
- [ ] Package 2: Compression Types Properties
- [ ] Package 3: PreAct Planning Memory Integration
- [ ] Package 4: Model Router Edge Cases
- [ ] Package 5: Integration Pipeline Edge Cases
- [ ] Package 6: PreAct Predictor Edge Cases
- [ ] Package 7: Prompt Cache Edge Cases
- [ ] Package 8: Memory Subsystems (Optional)
- [ ] Package 9: Streaming Module (Optional)
- [ ] Package 10: HTTP2 Modules (Optional)

---

**Last Updated**: After adding memory integration tests
**Current Overall Coverage**: 66%
**Target Overall Coverage**: 80%+
