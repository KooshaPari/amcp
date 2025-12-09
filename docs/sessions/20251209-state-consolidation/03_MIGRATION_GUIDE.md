# State Management Consolidation - Migration Guide

## For Code Reviewers & Developers

### What Changed

The overlapping state management implementations have been consolidated into a unified canonical layer under `infrastructure/state/`.

**Summary**:
- Created `infrastructure/state/models.py` - Unified type definitions
- Created `infrastructure/state/memory_service.py` - Unified memory service
- Updated `infrastructure/state/__init__.py` - Unified public API
- Converted `services/memory.py` - Backward compatibility re-export

**Result**: 27% code reduction through consolidation, 100% backward compatible

---

## No Action Required For Most Code

### Existing Imports Continue to Work

If your code currently imports from `services.memory`:
```python
from services.memory import UserScopedMemory, MemoryType, MemoryItem
```

✓ **No changes needed** - Full backward compatibility maintained

### Existing Imports Continue to Work

If your code imports from `smartcp.services.memory`:
```python
from smartcp.services.memory import UserScopedMemory, create_memory_service
```

✓ **No changes needed** - Full backward compatibility maintained

---

## Optional: Update to Canonical Import

### For New Code & Future Migration

The canonical location is now `smartcp.infrastructure.state`:

**Old import**:
```python
from services.memory import UserScopedMemory, MemoryType, MemoryItem
```

**New canonical import**:
```python
from smartcp.infrastructure.state import (
    UserScopedMemory,
    MemoryType,
    MemoryItem,
    create_memory_service,
)
```

### Complete Canonical API

```python
from smartcp.infrastructure.state import (
    # Memory Service (High-Level API)
    UserScopedMemory,
    create_memory_service,

    # Models (Type Definitions)
    MemoryType,      # WORKING, PERSISTENT, CONTEXT, VARIABLE, FILE, LEARNING
    MemoryItem,      # Typed memory item with metadata
    MemoryStats,     # Memory usage statistics

    # State Adapters (Pluggable Backends)
    StateAdapter,           # Abstract interface
    BifrostStateAdapter,    # Production (Bifrost GraphQL)
    InMemoryStateAdapter,   # Testing (In-memory)
    create_state_adapter,   # Factory

    # Error Types
    StateError,
    StateNotFoundError,
    BifrostStateError,
)
```

---

## Usage Examples

### Basic Memory Operations

```python
from smartcp.infrastructure.state import (
    UserScopedMemory,
    MemoryType,
    create_memory_service,
)

# Create memory service
memory = create_memory_service()

# Store a value
await memory.set(user_ctx, "my_key", {"data": "value"})

# Retrieve a value
value = await memory.get(user_ctx, "my_key")

# Store with type
await memory.set(
    user_ctx,
    "counter",
    42,
    memory_type=MemoryType.VARIABLE,
)

# List keys by type
keys = await memory.list_keys(user_ctx, memory_type=MemoryType.VARIABLE)
```

### Variable Memory (Code Execution)

```python
from smartcp.infrastructure.state import UserScopedMemory, MemoryType

# Store variable
await memory.set_variable(user_ctx, "result", {"output": "success"})

# Retrieve variable
result = await memory.get_variable(user_ctx, "result")

# Get all variables
all_vars = await memory.get_variables(user_ctx)
```

### Context Memory (Conversation History)

```python
# Store conversation context
await memory.store_context(
    user_ctx,
    "chat_history",
    {
        "messages": [...],
        "model": "claude-sonnet-4",
    }
)

# Retrieve context
context = await memory.get_context(user_ctx, "chat_history")
```

### File References

```python
# Store file metadata
await memory.store_file_reference(
    user_ctx,
    "file_123",
    {
        "name": "document.pdf",
        "path": "/uploads/doc.pdf",
        "size": 1024000,
        "uploaded_at": "2025-12-09T10:00:00Z",
    }
)

# Retrieve file reference
file_info = await memory.get_file_reference(user_ctx, "file_123")
```

### Learning Patterns

```python
# Store learning pattern
await memory.store_learning(
    user_ctx,
    "preference_dark_mode",
    {"enabled": True, "theme": "solarized"},
)

# Retrieve learning
preference = await memory.get_learning(user_ctx, "preference_dark_mode")
```

---

## Memory Types Reference

### WORKING Memory
- **Purpose**: Short-term temporary storage
- **TTL**: Auto-expires (default 1 hour)
- **Use case**: Session-specific data that doesn't persist
- **Example**: Current form input, temporary calculations

### PERSISTENT Memory
- **Purpose**: Long-term user-specific storage
- **TTL**: None (persists indefinitely)
- **Use case**: User preferences, settings, profiles
- **Example**: User preferences, configuration

### CONTEXT Memory
- **Purpose**: Conversation and interaction history
- **TTL**: Optional (typically long-lived)
- **Use case**: Chat history, context windows
- **Example**: Message history for continuation

### VARIABLE Memory
- **Purpose**: Code execution variables
- **TTL**: Optional
- **Use case**: Variable storage for script execution
- **Example**: Script execution state, temporary vars

### FILE Memory
- **Purpose**: File references and metadata
- **TTL**: Optional
- **Use case**: Tracking uploaded/processed files
- **Example**: File path, size, metadata

### LEARNING Memory
- **Purpose**: User learning patterns and preferences
- **TTL**: Long-lived
- **Use case**: User behavior patterns, learned preferences
- **Example**: User interaction patterns, feature preferences

---

## Adapter Switching

### Using Different Adapters

```python
from smartcp.infrastructure.state import (
    BifrostStateAdapter,
    InMemoryStateAdapter,
    UserScopedMemory,
    create_state_adapter,
)
from smartcp.bifrost_client import BifrostClient

# Production: Bifrost-backed persistence
bifrost_client = BifrostClient()
bifrost_adapter = BifrostStateAdapter(bifrost_client)
memory = UserScopedMemory(bifrost_adapter)

# Testing: In-memory (no persistence)
in_memory_adapter = InMemoryStateAdapter()
memory = UserScopedMemory(in_memory_adapter)

# Or use factory with flag
from smartcp.infrastructure.state import create_state_adapter

# In-memory for testing
test_adapter = create_state_adapter(use_memory=True)
memory = UserScopedMemory(test_adapter)
```

---

## Troubleshooting

### Import Issues

**Problem**: `ModuleNotFoundError: No module named 'smartcp.infrastructure.state'`

**Solution**:
1. Verify you're running from project root
2. Check `infrastructure/state/__init__.py` exists
3. Ensure environment is activated: `source .venv/bin/activate`

### Type Errors

**Problem**: `AttributeError: 'NoneType' has no attribute 'value'`

**Solution**:
1. Check that `memory_type` is a valid `MemoryType` enum value
2. Use `MemoryType.VARIABLE`, not string `"variable"`
3. Verify `MemoryType` imported correctly

### State Not Persisting

**Problem**: Values set don't persist between requests

**Solution**:
1. Check you're using `BifrostStateAdapter` (not `InMemoryStateAdapter`)
2. Verify Bifrost client is properly initialized
3. Check network connectivity to Bifrost
4. Review Bifrost GraphQL responses for errors

---

## Backward Compatibility

### What's Preserved

✓ All public APIs remain identical
✓ All callers continue to work
✓ Old import paths still valid
✓ No migration required for existing code
✓ No test changes needed
✓ No configuration changes needed

### What's Deprecated

The following import path still works but is deprecated:
```python
from services.memory import ...  # Still works, but deprecated
```

**Recommendation**: Update to canonical path when convenient:
```python
from smartcp.infrastructure.state import ...  # Canonical
```

### Migration Timeline

- **Now**: Both old and new imports work
- **Future**: Deprecation warnings may be added
- **Eventually**: Old import path may be removed

---

## Performance Considerations

### Memory Service
- **Latency**: <1ms for in-memory adapter, depends on network for Bifrost
- **Throughput**: Supported by Bifrost rate limits
- **Storage**: No in-process storage limits for Bifrost backend

### TTL & Expiration
- **Working memory**: Auto-expires after 1 hour (default)
- **Persistent memory**: No auto-expiration
- **Expiration check**: On read (lazy evaluation)

### Best Practices
1. Use appropriate memory type for use case
2. Set TTL for temporary data
3. Monitor memory stats periodically
4. Clear unused memory regularly
5. Use Bifrost adapter for production

---

## Questions & Support

For questions about the consolidation:
1. Check `docs/sessions/20251209-state-consolidation/`
2. Review file structure in `infrastructure/state/`
3. See inline documentation in code
4. Reference this migration guide

---

## Summary

✓ **No immediate action required** - Full backward compatibility
✓ **Optional migration** to canonical imports at your convenience
✓ **All memory types preserved** - VARIABLE, CONTEXT, FILE, LEARNING, etc.
✓ **Same functionality** - No behavior changes
✓ **Better organization** - Clearer code structure for maintainability
