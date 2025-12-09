# Deprecated Code Removal - Implementation Checklist

**Task**: Remove 6 deprecated shim modules and update all import references
**Total Work Items**: 27
**Risk Level**: LOW (pure re-export wrappers only)
**Estimated Time**: ~1 hour

---

## Phase 1: Update Production Code Imports (11 files)

### Quantization Optimizer → Quantization (4 files)

#### [ ] File 1: `router/router_core/routing/adaptive/selector.py`
- **Current Import**: `from router_core.domain.services.quantization_optimizer import QuantizationOptimizer`
- **New Import**: `from router_core.domain.services.quantization import QuantizationOptimizer`
- **Verify**: No other imports from quantization_optimizer in this file

#### [ ] File 2: `router/router_core/routing/adaptive/router.py`
- **Current Import**: `from router_core.domain.services.quantization_optimizer import QuantizationOptimizer`
- **New Import**: `from router_core.domain.services.quantization import QuantizationOptimizer`
- **Verify**: No other imports from quantization_optimizer in this file

#### [ ] File 3: `router/router_core/domain/services/optimization_service.py`
- **Current Import**: `from router_core.domain.services.quantization_optimizer import (...)`
- **New Import**: `from router_core.domain.services.quantization import (...)`
- **Verify**: Update all imports from this module

#### [ ] File 4: `router/router_core/domain/services/selection/simple_strategy.py`
- **Current Import**: `from router_core.domain.services.quantization_optimizer import (...)`
- **New Import**: `from router_core.domain.services.quantization import (...)`
- **Verify**: Check for conditional imports in docstring examples

---

### Capability Detector → Capability Detection (3 files)

#### [ ] File 5: `router/router_core/domain/services/model_discovery_service.py`
- **Current Imports**:
  - `from router_core.domain.services.capability_detector import CapabilityDetector`
  - `from router_core.domain.services.capability_detector import capability_detector` (in docstring example)
- **New Imports**:
  - `from router_core.domain.services.capability_detection import CapabilityDetector`
  - `from router_core.domain.services.capability_detection import capability_detector`
- **Verify**: Check all 3 import occurrences in this file

---

### NATS Integration → NATS (1 file)

#### [ ] File 6: `router/router_core/monitoring/sentinel.py`
- **Current Import**: `from router_core.infrastructure.nats_integration import NATSIntegration`
- **New Import**: `from router_core.infrastructure.nats import NATSIntegration`
- **Verify**: Check for any other imports from nats_integration

---

### Provider Recommender → Provider Recommendations (4 files)

#### [ ] File 7: `router/router_core/catalog/__init__.py`
- **Current Import**: `from router_core.domain.services.provider_recommender import ModelRecommender`
- **New Import**: `from router_core.domain.services.provider_recommendations import ModelRecommender`
- **Verify**: Check all imports and exports in this file

#### [ ] File 8: `router/router_core/catalog/byzantine_selector.py`
- **Current Import**: `from router_core.domain.services.provider_recommender import model_recommender`
- **New Import**: `from router_core.domain.services.provider_recommendations import model_recommender`
- **Verify**: No other imports from provider_recommender

#### [ ] File 9: `router/router_core/adapters/http/admin/catalog_routes.py`
- **Current Import**: `from router_core.domain.services.provider_recommender import model_recommender`
- **New Import**: `from router_core.domain.services.provider_recommendations import model_recommender`
- **Verify**: No other imports from provider_recommender

#### [ ] File 10: `router/router_core/application/di_container.py`
- **Current Import**: `from router_core.domain.services.provider_recommender import NotDiamondRecommender`
- **New Import**: `from router_core.domain.services.provider_recommendations import NotDiamondRecommender`
- **Verify**: No other imports from provider_recommender

---

### Selection Service → Selection (2 files)

#### [ ] File 11: `router/router_core/routing/selector_factory.py`
- **Current Import**: `from router_core.domain.services.selection_service import (...)`
- **New Import**: `from router_core.domain.services.selection import (...)`
- **Verify**: Update all imports from this module; check conditional imports

#### [ ] File 12: `router/router_core/startup/health_checks.py`
- **Current Imports**:
  - `from router_core.domain.services.selection_service import SelectionService`
  - `from router_core.domain.services.selection_service import (...)` (conditional in other location)
- **New Imports**:
  - `from router_core.domain.services.selection import SelectionService`
  - `from router_core.domain.services.selection import (...)`
- **Verify**: Check all import occurrences (noted as 2 in docstring)

---

### Provider Recommendations Cross-Reference (1 more file)

#### [ ] File 13: `router/router_core/domain/services/selection/simple_strategy.py`
- **Current Import**: `from router_core.domain.services.provider_recommender import ProviderRecommendationService`
- **New Import**: `from router_core.domain.services.provider_recommendations import ProviderRecommendationService`
- **Verify**: No other imports from provider_recommender in this file

---

## Phase 2: Update Module Public APIs (2 files)

### [ ] File 14: `router/router_core/domain/services/__init__.py`
- **Action**: Remove all re-exports from deprecated shim modules:
  - Remove: `from .quantization_optimizer import (...)`
  - Remove: `from .capability_detector import (...)`
  - Remove: `from .provider_recommender import (...)`
  - Remove: `from .selection_service import (...)`
- **Keep**: Imports from actual submodules if they exist
- **Verify**: Ensure public API is still exported from submodules

### [ ] File 15: `router/router_core/infrastructure/__init__.py`
- **Action**: Remove re-export from deprecated shim module:
  - Remove: `from router_core.infrastructure.nats_integration import (...)`
- **Keep**: Imports from actual nats submodule if they exist
- **Verify**: Ensure public API is still exported from nats submodule

---

## Phase 3: Update Test Code (8 files)

### Test Files Using Deprecated Imports

#### [ ] Test File 1: `router/tests/test_model_discovery.py`
- **Current Import**: `from router_core.domain.services.capability_detector import capability_detector`
- **New Import**: `from router_core.domain.services.capability_detection import capability_detector`
- **Verify**: Run test after update

#### [ ] Test File 2: `router/tests/unit/test_recommender.py`
- **Current Import**: `from router_core.domain.services.provider_recommender import NotDiamondRecommender`
- **New Import**: `from router_core.domain.services.provider_recommendations import NotDiamondRecommender`
- **Verify**: Run test after update

#### [ ] Test File 3: `router/tests/integration/test_phase2_simple.py`
- **Current Import**: Check for imports from `quantization_optimizer`
- **Action**: Update to import from `quantization` submodule
- **Verify**: Run test after update

#### [ ] Test File 4: `router/tests/validation/test_performance_requirements.py`
- **Current Import**: `from router_core.domain.services.capability_detector import CapabilityDetector`
- **New Import**: `from router_core.domain.services.capability_detection import CapabilityDetector`
- **Verify**: Run test after update

#### [ ] Test File 5: `router/tests/scripts/final_pipeline_demo.py`
- **Current Import**: `from router_core.domain.services.selection_service import (...)`
- **New Import**: `from router_core.domain.services.selection import (...)`
- **Verify**: Check all imports; run script after update

#### [ ] Example File 1: `router/examples/model_discovery_example.py`
- **Current Import**: `from router_core.domain.services.capability_detector import capability_detector`
- **New Import**: `from router_core.domain.services.capability_detection import capability_detector`
- **Verify**: Example runs without import errors

#### [ ] Benchmark File 1: `router/benchmarks/benchmark_suite.py`
- **Current Import**: `from router_core.domain.services.selection_service import SelectionService as CandidateSelector`
- **New Import**: `from router_core.domain.services.selection import SelectionService as CandidateSelector`
- **Verify**: Benchmark runs after update

#### [ ] SDK Tests (Reference - DO NOT MODIFY)
- `router/tests/integration/phase2_sdk/test_sdk_integration.py` - Uses `sdk_wrapper.py` (ACTIVE, NOT DEPRECATED)
- `router/tests/integration/phase2_sdk/test_sdk_wrapper.py` - Uses `sdk_wrapper.py` (ACTIVE, NOT DEPRECATED)
- `router/tests/integration/phase2_sdk/test_sdk_factory.py` - Uses `sdk_wrapper.py` (ACTIVE, NOT DEPRECATED)
- **Action**: Leave these untouched - sdk_wrapper is not deprecated

---

## Phase 4: Delete Deprecated Shim Files (6 files)

### [ ] Delete 1: `router/router_core/domain/services/capability_detector.py`
- **Size**: 23 lines
- **Action**: Delete file
- **Verify**: All imports updated before deletion

### [ ] Delete 2: `router/router_core/domain/services/quantization_optimizer.py`
- **Size**: 29 lines
- **Action**: Delete file
- **Verify**: All imports updated before deletion

### [ ] Delete 3: `router/router_core/domain/services/selection_service.py`
- **Size**: 63 lines
- **Action**: Delete file
- **Verify**: All imports updated before deletion; deprecation warning no longer triggered

### [ ] Delete 4: `router/router_core/domain/services/provider_recommender.py`
- **Size**: 64 lines
- **Action**: Delete file
- **Verify**: All imports updated before deletion

### [ ] Delete 5: `router/router_core/infrastructure/nats_integration.py`
- **Size**: 45 lines
- **Action**: Delete file
- **Verify**: All imports updated before deletion

### [ ] Delete 6: `router/router_core/adapters/http/api_routes/streaming.py`
- **Size**: 59 lines
- **Action**: Delete file
- **Verify**: No production imports (already verified in audit)

---

## Phase 5: Verification & Testing (4 items)

### [ ] Verification 1: Search for Remaining References
```bash
# Search for any remaining imports of deprecated modules
grep -r "capability_detector\|quantization_optimizer\|nats_integration\|provider_recommender\|selection_service" \
  --include="*.py" router/ | grep -v "__pycache__" | grep -v "\.pyc"
```
- **Expected Result**: Zero matches (all imports updated)
- **Action**: If any found, update those files before proceeding

### [ ] Verification 2: Run Full Test Suite
```bash
# Run all tests to verify no behavioral changes
pytest router/tests/ -v
```
- **Expected Result**: All tests pass
- **Action**: Fix any failing tests before proceeding

### [ ] Verification 3: Check for Deprecated Warnings
```bash
# Run tests with deprecation warnings visible
pytest router/tests/ -v -W default::DeprecationWarning
```
- **Expected Result**: No DeprecationWarning from selection_service (it's deleted)
- **Action**: If warnings appear, check for missed imports

### [ ] Verification 4: Import Check
```python
# In a test file, verify new imports work
from router_core.domain.services.capability_detection import CapabilityDetector
from router_core.domain.services.quantization import QuantizationOptimizer
from router_core.domain.services.selection import SelectionService
from router_core.domain.services.provider_recommendations import ModelRecommender
from router_core.infrastructure.nats import NATSIntegration
# All should import without error
```
- **Expected Result**: All imports successful
- **Action**: If any fail, verify the submodules export the correct symbols

---

## Pre-Removal Safety Checklist

- [ ] All deprecated shims explicitly marked DEPRECATED in docstrings
- [ ] All deprecated shims are pure re-export wrappers (zero business logic)
- [ ] All actual implementations exist in submodules (verified)
- [ ] All callers identified (11 production + 8 test files)
- [ ] All imports can be directly mapped to new submodules
- [ ] No circular dependencies introduced by new imports
- [ ] Deprecation warnings already in place (selection_service.py)
- [ ] Migration paths documented in each shim's docstring

---

## Do NOT Remove

- ⚠️ `router/router_core/adapters/providers/sdk_wrapper.py` - ACTIVE FEATURE (569 lines)
- ⚠️ `router/main.py` - No deprecated code (252 lines)

---

## Post-Removal Validation

### Metrics After Removal

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Deprecated Shim Files | 6 | 0 | -6 files |
| Deprecated Shim Lines | 283 | 0 | -283 lines |
| Import Complexity | Higher (goes through shims) | Lower (direct) | Simplified |
| Active Features | 1 | 1 | Unchanged |
| Test Coverage | Same | Same (+ no warnings) | Improved |

### Success Criteria

✅ All deprecated shim files deleted
✅ All 11 production files updated
✅ All 8 test/example files updated
✅ All 2 module __init__.py files updated
✅ Full test suite passes
✅ Zero DeprecationWarnings about removed modules
✅ Zero import errors in production code
✅ All submodule public APIs still accessible

---

## Rollback Plan

If issues occur:
1. Restore the 6 deleted files from git: `git restore router/router_core/domain/services/capability_detector.py` etc.
2. Revert import changes: `git checkout -- router/router_core/...`
3. Run test suite to verify rollback successful

---

## Expected Changes Summary

- **Files Modified**: 15 (11 production + 2 __init__.py + 2 test/example)
- **Files Deleted**: 6 (283 lines of shim code)
- **Code Removed**: 283 lines (100% pure re-export code)
- **Code Added**: 0 lines (only imports change, no logic changes)
- **Tests Modified**: 6 files (simple import updates)
- **Breaking Changes**: None (internal modules only, re-exported from submodules)
- **Performance Impact**: Negligible (removes one indirection layer)

---

**Created**: 2025-12-09
**Status**: READY FOR IMPLEMENTATION
**Next Step**: Follow phases 1-5 in order, checking off items as completed
