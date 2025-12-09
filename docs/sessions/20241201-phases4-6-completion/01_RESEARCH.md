# Research: Phases 4-6 Implementation & Testing

## pytest-asyncio Configuration

### Problem Identified
- Tests using `@pytest.mark.asyncio` were failing with async support not properly configured
- Original pytest.ini had `asyncio_mode = auto` but plugin wasn't loading correctly
- Error: "Unknown config option: asyncio_mode"

### Solution Applied
1. Installed `pytest-asyncio==1.3.0`
2. Removed explicit plugin loading from conftest.py (auto-discovery)
3. Configured pytest.ini with `asyncio_mode = auto`
4. Set `asyncio_default_fixture_loop_scope = function`

### Key Finding
- pytest-asyncio 1.3.0 automatically registers via entry points (`pytest11` group)
- Double registration occurs if explicitly loading via `pytest_plugins` AND the plugin is already auto-registered
- Solution: Let pytest auto-discover, configure via pytest.ini

## Vector Search Testing (Voyage AI)

### Challenge: Cosine Similarity Testing
Original test vectors were too similar - normalized vectors `[0.6, 0.6, 0.6]` vs `[0.1, 0.1, 0.1]` both have cosine similarity of 1.0 when compared to `[0.5, 0.5, 0.5]`.

### Solution: Orthogonal Vectors
```python
# Query: [1, 0, 0] - unit vector in x direction
# Doc1: [0.9, 0.1, 0.0] - high similarity to query (0.9 cosine)
# Doc2: [0.1, 0.9, 0.0] - low similarity to query (0.1 cosine)
```

This creates clear differentiation for assertion testing.

### References
- Cosine Similarity: cos(θ) = (A·B)/(|A||B|)
- For unit vectors: similarity = dot product of normalized vectors

## MagicMock `_mock_methods` Issue (Python 3.13)

### Problem
```python
# This fails in Python 3.13:
mock_result.consume = AsyncMock(return_value=MagicMock(counters=MagicMock(__dict__={}), query_type="w"))
```

Error: `AttributeError: _mock_methods`

### Root Cause
When passing `__dict__={}` to MagicMock constructor, Python 3.13's implementation tries to set `__dict__` as an attribute, which conflicts with MagicMock's internal `_mock_methods` attribute mechanism.

### Solution: Simple Object Class
```python
class _MockCounters:
    """Simple counters mock that provides empty __dict__."""
    pass

def _create_result_summary(query_type: str = "r") -> MagicMock:
    mock_counters = _MockCounters()
    return MagicMock(counters=mock_counters, query_type=query_type)
```

### Why This Works
- Regular Python objects have `__dict__` attribute by default
- No conflict with MagicMock's internal mechanisms
- Clean separation of concerns: MagicMock for summary, simple object for counters

## Test Architecture Patterns

### Canonical Test File Naming
All tests follow single-file pattern with fixtures/markers for variants:
- `test_entity.py` - contains all entity tests with variant fixtures
- NOT: `test_entity_unit.py`, `test_entity_integration.py`, `test_entity_e2e.py`

### Benefit
- One source of truth per component
- Easier to maintain - changes reflected everywhere
- No duplication of test logic

## References
- pytest-asyncio documentation: Async fixture scopes
- Python 3.13 unittest.mock changes: Special attribute handling
- Cosine Similarity: Standard ML metric for vector similarity
- Neo4j Python driver: Async session management and result consumption
- Voyage AI: REST API for embeddings and reranking
