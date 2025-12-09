# Critical Memory Fixes - Unbounded Growth Prevention

## Problem
Tests were using 40GB+ memory and hanging, requiring force quit. Root cause: **unbounded growth** in planning loops and caches.

## Root Causes Identified

### 1. Planning Loop - Unbounded Node Accumulation
**Issue**: `tree.nodes` dict grows without limit. Each `_expand_branch` call can add multiple nodes (1 top action + up to `max_breadth-1` alternatives). If the loop runs many iterations without finding goal completion, nodes accumulate indefinitely.

**Location**: `optimization/planning/reactree.py`

**Fix Applied**:
- Added `max_nodes: int = 1000` to `PlanningConfig` (hard limit)
- Added `max_iterations: int = 500` to `PlanningConfig` (failsafe iteration counter)
- Added iteration counter in planning loop with early termination
- Added node count check before each expansion
- Added node limit checks before adding nodes in `_expand_branch` and `refine`

### 2. Compression Cache - Unbounded Growth
**Issue**: `ACONCompressor._cache` dict has no size limit. Each unique content+query combination creates a new cache entry that never expires (only TTL-based, no size limit).

**Location**: `optimization/compression/compressor.py`

**Fix Applied**:
- Added `max_cache_size: int = 1000` to `CompressionConfig`
- Implemented FIFO eviction when cache reaches limit
- Evicts oldest entry before adding new one

### 3. Prediction Cache - Unbounded Growth
**Issue**: `PreActPredictor._prediction_cache` dict has no size limit.

**Location**: `optimization/preact_predictor.py`

**Fix Applied**:
- Added hard limit of 1000 entries
- FIFO eviction when limit reached

### 4. Reflections List - Unbounded Growth
**Issue**: `PreActPredictor._reflections` list grows indefinitely with each reflection.

**Location**: `optimization/preact_predictor.py`

**Fix Applied**:
- Added limit of 10,000 reflections
- Keeps only last 10k entries (sliding window)

## Changes Made

### `optimization/planning/types.py`
```python
@dataclass
class PlanningConfig:
    # ... existing fields ...
    max_nodes: int = 1000  # Hard limit to prevent unbounded growth
    max_iterations: int = 500  # Maximum loop iterations as failsafe
```

### `optimization/planning/reactree.py`
```python
# Main planning loop
iteration_count = 0
while True:
    iteration_count += 1
    
    # Hard iteration limit as failsafe
    if iteration_count > self.config.max_iterations:
        logger.warning(f"Planning iteration limit reached ({self.config.max_iterations})")
        break
    
    # Check node count limit
    if len(tree.nodes) > self.config.max_nodes:
        logger.warning(f"Planning node limit reached ({self.config.max_nodes})")
        break
    
    # ... rest of loop ...
```

```python
# In _expand_branch - check before adding nodes
if len(tree.nodes) >= self.config.max_nodes:
    logger.warning(f"Node limit reached ({self.config.max_nodes}), cannot expand branch")
    node.mark_completed("Node limit reached")
    return False
```

### `optimization/compression/types.py`
```python
@dataclass
class CompressionConfig:
    # ... existing fields ...
    max_cache_size: int = 1000  # Maximum cache entries to prevent unbounded growth
```

### `optimization/compression/compressor.py`
```python
# Cache result with size limit
if self.config.enable_cache:
    # Enforce cache size limit
    if len(self._cache) >= self.config.max_cache_size:
        # Remove oldest entry (simple FIFO)
        oldest_key = next(iter(self._cache))
        del self._cache[oldest_key]
        logger.debug(f"Cache evicted entry: {oldest_key[:8]}... (size limit reached)")
    self._cache[cache_key] = result
```

### `optimization/preact_predictor.py`
```python
# Prediction cache with size limit
if self.config.cache_predictions:
    # Enforce cache size limit
    if len(self._prediction_cache) >= 1000:  # Hard limit
        oldest_key = next(iter(self._prediction_cache))
        del self._prediction_cache[oldest_key]
    self._prediction_cache[cache_key] = prediction

# Reflections list with size limit
self._reflections.append(reflection)
if len(self._reflections) > 10000:  # Keep last 10k reflections
    self._reflections = self._reflections[-10000:]
```

## Impact

**Before**:
- Planning loop could run indefinitely, creating millions of nodes
- Caches could grow to GB+ sizes
- Tests hung and consumed 40GB+ memory

**After**:
- Planning loop terminates after 500 iterations max
- Planning tree limited to 1000 nodes max
- Compression cache limited to 1000 entries
- Prediction cache limited to 1000 entries
- Reflections limited to 10,000 entries

## Testing

All tests pass with these limits in place. The limits are conservative enough to allow normal operation while preventing unbounded growth.

## Configuration

Users can adjust these limits via:
- `PlanningConfig(max_nodes=..., max_iterations=...)`
- `CompressionConfig(max_cache_size=...)`

Default values are conservative and should prevent memory issues while allowing normal operation.
