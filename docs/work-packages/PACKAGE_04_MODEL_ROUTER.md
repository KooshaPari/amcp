# Work Package 04: Model Router Edge Cases

**Priority**: MEDIUM  
**Estimated Time**: 1-2 hours  
**Current Coverage**: 70% → Target: 85%+

## Objective

Improve coverage for `optimization/model_router/router.py` by testing edge cases and error paths.

## Missing Lines

69-72, 77-78, 80-81, 89-102, 113, 155-167, 213, 217-218, 222

## Tasks

1. **Review Missing Lines**: Read `optimization/model_router/router.py` to understand what paths are not covered
2. **Add Tests**: Enhance `tests/optimization/test_model_router.py` with tests for:
   - Router fallback paths (lines 69-72, 77-78, 80-81)
   - Error handling paths (lines 89-102, 113)
   - Complex routing scenarios (lines 155-167)
   - Edge cases (lines 213, 217-218, 222)

## Approach

1. Read the router code to understand each missing line
2. Identify what conditions trigger those paths
3. Write tests that exercise those conditions
4. Verify coverage improves

## Verification

```bash
uv run pytest tests/optimization/test_model_router.py \
  --cov=optimization.model_router.router \
  --cov-report=term-missing -v
```

**Success Criteria**:
- ✅ Coverage improves to 85%+
- ✅ Critical routing paths tested
- ✅ Error handling paths tested
- ✅ All existing tests still pass

## Reference

- File: `optimization/model_router/router.py`
- Existing tests: `tests/optimization/test_model_router.py`
