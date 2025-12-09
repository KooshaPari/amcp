# Deprecated Code Import Mapping Reference

**Purpose**: Quick reference for updating all deprecated imports to new locations
**Date**: 2025-12-09
**Total Mappings**: 6 shim modules → 6 submodules

---

## Import Mapping Tables

### 1. Capability Detector Migration

| Deprecated Import | New Import |
|-------------------|-----------|
| `from router_core.domain.services.capability_detector import CapabilityDetector` | `from router_core.domain.services.capability_detection import CapabilityDetector` |
| `from router_core.domain.services.capability_detector import capability_detector` | `from router_core.domain.services.capability_detection import capability_detector` |

**Affected Files**:
- `router_core/domain/services/model_discovery_service.py`
- `router/tests/test_model_discovery.py`
- `router/tests/validation/test_performance_requirements.py`
- `router/examples/model_discovery_example.py`

---

### 2. Quantization Optimizer Migration

| Deprecated Import | New Import |
|-------------------|-----------|
| `from router_core.domain.services.quantization_optimizer import QuantizationOptimizer` | `from router_core.domain.services.quantization import QuantizationOptimizer` |
| `from router_core.domain.services.quantization_optimizer import OptimizationContext` | `from router_core.domain.services.quantization import OptimizationContext` |
| `from router_core.domain.services.quantization_optimizer import QuantizationProfile` | `from router_core.domain.services.quantization import QuantizationProfile` |
| `from router_core.domain.services.quantization_optimizer import QuantizationType` | `from router_core.domain.services.quantization import QuantizationType` |
| `from router_core.domain.services.quantization_optimizer import ResourceConstraint` | `from router_core.domain.services.quantization import ResourceConstraint` |
| `from router_core.domain.services.quantization_optimizer import TaskComplexity` | `from router_core.domain.services.quantization import TaskComplexity` |

**Affected Files**:
- `router_core/routing/adaptive/selector.py`
- `router_core/routing/adaptive/router.py`
- `router_core/domain/services/optimization_service.py`
- `router_core/domain/services/selection/simple_strategy.py`
- `router/tests/integration/test_phase2_simple.py`

---

### 3. NATS Integration Migration

| Deprecated Import | New Import |
|-------------------|-----------|
| `from router_core.infrastructure.nats_integration import NATSIntegration` | `from router_core.infrastructure.nats import NATSIntegration` |
| `from router_core.infrastructure.nats_integration import NATSConfig` | `from router_core.infrastructure.nats import NATSConfig` |
| `from router_core.infrastructure.nats_integration import EventType` | `from router_core.infrastructure.nats import EventType` |
| `from router_core.infrastructure.nats_integration import QueueType` | `from router_core.infrastructure.nats import QueueType` |
| `from router_core.infrastructure.nats_integration import RoutingDecisionEvent` | `from router_core.infrastructure.nats import RoutingDecisionEvent` |
| `from router_core.infrastructure.nats_integration import ProviderHealthEvent` | `from router_core.infrastructure.nats import ProviderHealthEvent` |
| `from router_core.infrastructure.nats_integration import NATSEventPublisher` | `from router_core.infrastructure.nats import NATSEventPublisher` |
| `from router_core.infrastructure.nats_integration import NATSHealthMonitor` | `from router_core.infrastructure.nats import NATSHealthMonitor` |
| `from router_core.infrastructure.nats_integration import NATSQueueManager` | `from router_core.infrastructure.nats import NATSQueueManager` |
| `from router_core.infrastructure.nats_integration import NATSKVStore` | `from router_core.infrastructure.nats import NATSKVStore` |

**Affected Files**:
- `router_core/monitoring/sentinel.py`

---

### 4. Provider Recommender Migration

| Deprecated Import | New Import |
|-------------------|-----------|
| `from router_core.domain.services.provider_recommender import ProviderSortStrategy` | `from router_core.domain.services.provider_recommendations import ProviderSortStrategy` |
| `from router_core.domain.services.provider_recommender import DataCollectionPolicy` | `from router_core.domain.services.provider_recommendations import DataCollectionPolicy` |
| `from router_core.domain.services.provider_recommender import ProviderPreferences` | `from router_core.domain.services.provider_recommendations import ProviderPreferences` |
| `from router_core.domain.services.provider_recommender import ProviderRecommender` | `from router_core.domain.services.provider_recommendations import ProviderRecommender` |
| `from router_core.domain.services.provider_recommender import OpenRouterRecommender` | `from router_core.domain.services.provider_recommendations import OpenRouterRecommender` |
| `from router_core.domain.services.provider_recommender import VLLMRecommender` | `from router_core.domain.services.provider_recommendations import VLLMRecommender` |
| `from router_core.domain.services.provider_recommender import OllamaRecommender` | `from router_core.domain.services.provider_recommendations import OllamaRecommender` |
| `from router_core.domain.services.provider_recommender import ProviderRecommendationService` | `from router_core.domain.services.provider_recommendations import ProviderRecommendationService` |
| `from router_core.domain.services.provider_recommender import UnifiedRecommender` | `from router_core.domain.services.provider_recommendations import UnifiedRecommender` |
| `from router_core.domain.services.provider_recommender import ModelRecommender` | `from router_core.domain.services.provider_recommendations import ModelRecommender` |
| `from router_core.domain.services.provider_recommender import NotDiamondRecommender` | `from router_core.domain.services.provider_recommendations import NotDiamondRecommender` |
| `from router_core.domain.services.provider_recommender import get_unified_recommender` | `from router_core.domain.services.provider_recommendations import get_unified_recommender` |
| `from router_core.domain.services.provider_recommender import unified_recommender` | `from router_core.domain.services.provider_recommendations import unified_recommender` |
| `from router_core.domain.services.provider_recommender import model_recommender` | `from router_core.domain.services.provider_recommendations import model_recommender` |
| `from router_core.domain.services.provider_recommender import recommender` | `from router_core.domain.services.provider_recommendations import recommender` |

**Affected Files**:
- `router_core/catalog/__init__.py`
- `router_core/catalog/byzantine_selector.py`
- `router_core/adapters/http/admin/catalog_routes.py`
- `router_core/application/di_container.py`
- `router_core/domain/services/selection/simple_strategy.py`
- `router/tests/unit/test_recommender.py`

---

### 5. Selection Service Migration

| Deprecated Import | New Import |
|-------------------|-----------|
| `from router_core.domain.services.selection_service import ByzantineStrategy` | `from router_core.domain.services.selection import ByzantineStrategy` |
| `from router_core.domain.services.selection_service import CandidateSelector` | `from router_core.domain.services.selection import CandidateSelector` |
| `from router_core.domain.services.selection_service import ProviderAwareStrategy` | `from router_core.domain.services.selection import ProviderAwareStrategy` |
| `from router_core.domain.services.selection_service import SelectionService` | `from router_core.domain.services.selection import SelectionService` |
| `from router_core.domain.services.selection_service import SimpleStrategy` | `from router_core.domain.services.selection import SimpleStrategy` |
| `from router_core.domain.services.selection_service import create_selection_service` | `from router_core.domain.services.selection import create_selection_service` |
| `from router_core.domain.services.selection_service import filter_by_budget` | `from router_core.domain.services.selection import filter_by_budget` |
| `from router_core.domain.services.selection_service import filter_by_context` | `from router_core.domain.services.selection import filter_by_context` |
| `from router_core.domain.services.selection_service import filter_by_modality` | `from router_core.domain.services.selection import filter_by_modality` |
| `from router_core.domain.services.selection_service import filter_by_quantization` | `from router_core.domain.services.selection import filter_by_quantization` |
| `from router_core.domain.services.selection_service import filter_by_rate_limits` | `from router_core.domain.services.selection import filter_by_rate_limits` |
| `from router_core.domain.services.selection_service import filter_by_tools` | `from router_core.domain.services.selection import filter_by_tools` |

**Affected Files**:
- `router_core/routing/selector_factory.py`
- `router_core/startup/health_checks.py`
- `router/tests/scripts/final_pipeline_demo.py`
- `router/benchmarks/benchmark_suite.py`

---

### 6. Streaming API Routes Migration

| Deprecated Import | New Import |
|-------------------|-----------|
| `from router_core.adapters.http.api_routes.streaming import stream_completion` | `from router_core.adapters.http.api_routes.streaming import stream_completion` |
| `from router_core.adapters.http.api_routes.streaming import initialize_streaming_state` | `from router_core.adapters.http.api_routes.streaming import initialize_streaming_state` |
| `from router_core.adapters.http.api_routes.streaming import process_streaming_chunks` | `from router_core.adapters.http.api_routes.streaming import process_streaming_chunks` |
| `from router_core.adapters.http.api_routes.streaming import process_streaming_metrics` | `from router_core.adapters.http.api_routes.streaming import process_streaming_metrics` |
| `from router_core.adapters.http.api_routes.streaming import process_streaming_chunk` | `from router_core.adapters.http.api_routes.streaming import process_streaming_chunk` |
| `from router_core.adapters.http.api_routes.streaming import build_streaming_chunk_data` | `from router_core.adapters.http.api_routes.streaming import build_streaming_chunk_data` |

**Affected Files**:
- None found in audit (this shim has no production imports - safe for immediate removal)

---

## Batch Update Commands

### Update All Capability Detector Imports
```bash
find router -name "*.py" -type f ! -path "*/__pycache__/*" -exec sed -i '' \
  's|from router_core\.domain\.services\.capability_detector import|from router_core.domain.services.capability_detection import|g' {} \;
```

### Update All Quantization Optimizer Imports
```bash
find router -name "*.py" -type f ! -path "*/__pycache__/*" -exec sed -i '' \
  's|from router_core\.domain\.services\.quantization_optimizer import|from router_core.domain.services.quantization import|g' {} \;
```

### Update All NATS Integration Imports
```bash
find router -name "*.py" -type f ! -path "*/__pycache__/*" -exec sed -i '' \
  's|from router_core\.infrastructure\.nats_integration import|from router_core.infrastructure.nats import|g' {} \;
```

### Update All Provider Recommender Imports
```bash
find router -name "*.py" -type f ! -path "*/__pycache__/*" -exec sed -i '' \
  's|from router_core\.domain\.services\.provider_recommender import|from router_core.domain.services.provider_recommendations import|g' {} \;
```

### Update All Selection Service Imports
```bash
find router -name "*.py" -type f ! -path "*/__pycache__/*" -exec sed -i '' \
  's|from router_core\.domain\.services\.selection_service import|from router_core.domain.services.selection import|g' {} \;
```

---

## Verification Commands

### Verify All Deprecated Imports Removed
```bash
grep -r "capability_detector\|quantization_optimizer\|nats_integration\|provider_recommender\|selection_service" \
  router --include="*.py" | grep -E "^[^:]*\.py:" | grep "import" | grep -v "__pycache__"
```
**Expected Result**: Empty (zero matches)

### Verify New Imports Work
```bash
python -c "
from router_core.domain.services.capability_detection import CapabilityDetector
from router_core.domain.services.quantization import QuantizationOptimizer
from router_core.domain.services.selection import SelectionService
from router_core.domain.services.provider_recommendations import ModelRecommender
from router_core.infrastructure.nats import NATSIntegration
print('All imports successful!')
"
```
**Expected Result**: "All imports successful!"

### Verify No Deprecation Warnings
```bash
pytest router/tests -v -W default::DeprecationWarning 2>&1 | grep -i "deprecated"
```
**Expected Result**: Empty (no deprecation warnings)

---

## Files to Delete (in order)

1. `router/router_core/domain/services/capability_detector.py` (23 lines)
2. `router/router_core/domain/services/quantization_optimizer.py` (29 lines)
3. `router/router_core/domain/services/selection_service.py` (63 lines)
4. `router/router_core/domain/services/provider_recommender.py` (64 lines)
5. `router/router_core/infrastructure/nats_integration.py` (45 lines)
6. `router/router_core/adapters/http/api_routes/streaming.py` (59 lines)

**Total Deleted**: 283 lines of shim code

---

## Module __init__.py Changes

### `router/router_core/domain/services/__init__.py`

**Remove These Lines**:
```python
from .capability_detector import (
    CapabilityDetector,
    capability_detector,
)
from .quantization_optimizer import (
    OptimizationContext,
    QuantizationOptimizer,
    QuantizationProfile,
    QuantizationType,
    ResourceConstraint,
    TaskComplexity,
)
from .provider_recommender import (
    DataCollectionPolicy,
    ModelRecommender,
    NotDiamondRecommender,
    OllamaRecommender,
    OpenRouterRecommender,
    ProviderPreferences,
    ProviderRecommendationService,
    ProviderRecommender,
    ProviderSortStrategy,
    UnifiedRecommender,
    VLLMRecommender,
    get_unified_recommender,
    model_recommender,
    recommender,
    unified_recommender,
)
from .selection_service import (
    ByzantineStrategy,
    CandidateSelector,
    ProviderAwareStrategy,
    SelectionService,
    SimpleStrategy,
    create_selection_service,
    filter_by_budget,
    filter_by_context,
    filter_by_modality,
    filter_by_quantization,
    filter_by_rate_limits,
    filter_by_tools,
)
```

**Verify**: Check if submodules' `__init__.py` files export these symbols for continued public API access

---

### `router/router_core/infrastructure/__init__.py`

**Remove These Lines**:
```python
from router_core.infrastructure.nats_integration import (
    EventType,
    NATSConfig,
    NATSEventPublisher,
    NATSHealthMonitor,
    NATSIntegration,
    NATSKVStore,
    NATSQueueManager,
    ProviderHealthEvent,
    QueueType,
    RoutingDecisionEvent,
)
```

**Verify**: Check if `nats` submodule's `__init__.py` exports these symbols for continued public API access

---

## Rollback Instructions

If anything goes wrong during removal, roll back with:

```bash
# Restore deleted files
git restore router/router_core/domain/services/capability_detector.py
git restore router/router_core/domain/services/quantization_optimizer.py
git restore router/router_core/domain/services/selection_service.py
git restore router/router_core/domain/services/provider_recommender.py
git restore router/router_core/infrastructure/nats_integration.py
git restore router/router_core/adapters/http/api_routes/streaming.py

# Restore modified files
git restore router/router_core/domain/services/__init__.py
git restore router/router_core/infrastructure/__init__.py
# ... plus all other modified files

# Run tests to verify rollback
pytest router/tests -v
```

---

## Success Criteria Checklist

After completing all changes:

- [ ] All deprecated imports updated to new locations (0 occurrences of old imports)
- [ ] All 6 shim files deleted
- [ ] Module `__init__.py` files updated
- [ ] Full test suite passes (`pytest router/tests -v`)
- [ ] No deprecation warnings appear
- [ ] All new imports work correctly
- [ ] Public API still accessible (same symbols exported)

---

**Created**: 2025-12-09
**Status**: READY FOR IMPLEMENTATION
**Complexity**: LOW (simple search-and-replace operations)
**Estimated Time**: ~30 minutes for all updates
