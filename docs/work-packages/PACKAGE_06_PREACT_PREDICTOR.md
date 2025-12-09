# Work Package 06: PreAct Predictor Edge Cases

**Priority**: MEDIUM  
**Estimated Time**: 1-2 hours  
**Current Coverage**: 86% → Target: 92%+

## Objective

Improve coverage for `optimization/preact_predictor.py` by testing edge cases in prediction and reflection.

## Missing Lines

191-192, 203-206, 246, 248, 250, 264-270, 296, 299, 303, 306, 322, 341-345, 348, 386, 411, 448, 450, 476, 481, 502, 532-533, 537-538

## Tasks

1. **Review Missing Lines**: Read `optimization/preact_predictor.py` to understand what paths are not covered
2. **Add Tests**: Enhance `tests/optimization/test_preact_predictor.py` with tests for:
   - Edge cases in prediction generation (lines 191-192, 203-206)
   - Reflection accuracy calculations (lines 246, 248, 250, 264-270)
   - Confidence level mappings (lines 296, 299, 303, 306, 322)
   - Cache eviction scenarios (lines 341-345, 348)
   - Episodic example retrieval edge cases (lines 386, 411, 448, 450, 476, 481, 502, 532-533, 537-538)

## Approach

1. Read the predictor code to understand each missing line
2. Identify what conditions trigger those paths
3. Write tests that exercise those conditions
4. Verify coverage improves

## Verification

```bash
uv run pytest tests/optimization/test_preact_predictor.py \
  --cov=optimization.preact_predictor \
  --cov-report=term-missing -v
```

**Success Criteria**:
- ✅ Coverage improves to 92%+
- ✅ Prediction edge cases tested
- ✅ Reflection paths tested
- ✅ All existing tests still pass

## Reference

- File: `optimization/preact_predictor.py`
- Existing tests: `tests/optimization/test_preact_predictor.py`
