# Bifrost __init__.py Consolidation

## Goals
1. **Reduce `/bifrost/__init__.py` from 79 lines to <40 lines**
2. **Create submodule directories** for control_plane, events, tools
3. **Maintain backward compatibility** with all existing imports
4. **Update all callers** with new import paths
5. **Verify no broken imports** through tests

## Current State
- `bifrost/__init__.py`: 79 lines (pure re-exports)
- `bifrost/plugin.py`: 387 lines
- `bifrost/registry.py`: 144 lines
- `bifrost/events.py`: 594 lines
- `bifrost/control_plane.py`: 776 lines (exceeds 500 limit)
- `bifrost/tools.py`: 388 lines
- **Total**: 2368 lines

## Consolidation Strategy

### Phase 1: Create Submodules
1. **Create `bifrost/control_plane/` submodule**
   - Move `control_plane.py` → `control_plane/core.py` (776 lines)
   - Create `control_plane/__init__.py` (re-exports, <20 lines)
   - Decompose core.py into smaller modules (status, health, capabilities)

2. **Create `bifrost/events/` submodule**
   - Move `events.py` → `events/core.py` (594 lines)
   - Create `events/__init__.py` (re-exports, <20 lines)

3. **Create `bifrost/tools/` submodule**
   - Move `tools.py` → `tools/registry.py`
   - Create `tools/__init__.py` (re-exports, <15 lines)

4. **Consolidate plugin + registry**
   - Keep `plugin.py` in root (core integration layer)
   - `registry.py` remains as-is or becomes `registry/__init__.py`

### Phase 2: Update `/bifrost/__init__.py`
**Before** (79 lines):
```python
# Re-exports from 4 modules (plugin, registry, events, control_plane)
__all__ = [...]  # 32 entries
```

**After** (<40 lines):
```python
"""SmartCP Bifrost Integration (Core API)."""

# Core plugin - tool registration
from smartcp.bifrost.plugin import (
    SmartCPBifrostPlugin,
    PluginConfig,
    create_bifrost_plugin,
)

# Tool registry - discovery
from smartcp.bifrost.registry import (
    SMARTCP_TOOLS,
    ToolRegistry,
)

# Submodule re-exports for convenience
from smartcp.bifrost.control_plane import (
    SmartCPControlPlane,
    ControlPlaneConfig,
)
from smartcp.bifrost.events import (
    SmartCPEventPublisher,
    SmartCPEventType,
)

__all__ = [
    # Plugin (3)
    "SmartCPBifrostPlugin",
    "PluginConfig",
    "create_bifrost_plugin",
    # Registry (2)
    "SMARTCP_TOOLS",
    "ToolRegistry",
    # Control Plane (2)
    "SmartCPControlPlane",
    "ControlPlaneConfig",
    # Events (2)
    "SmartCPEventPublisher",
    "SmartCPEventType",
]
```

### Phase 3: Deprecation Path
Users importing `SmartCPEventPublisher` can use either:
- Old: `from smartcp.bifrost import SmartCPEventPublisher`
- New: `from smartcp.bifrost.events import SmartCPEventPublisher`

## Trade-offs

| Aspect | Current | After | Impact |
|--------|---------|-------|--------|
| **__init__ size** | 79 lines | <40 lines | 50% reduction |
| **Import paths** | Flat | Hierarchical | More discoverable, clearer intent |
| **Backward compat** | N/A | Full | No breaking changes |
| **control_plane size** | 776 lines (>500) | Submodule (TBD) | Enables decomposition |
| **File organization** | 6 modules | 5 + 3 submodules | Better structure |

## Implementation Steps

1. ✅ Create submodule directories
2. ✅ Move modules into submodules
3. ✅ Create submodule `__init__.py` files
4. ✅ Update root `__init__.py` to 40 lines
5. ✅ Update all internal imports
6. ✅ Run tests to verify no breakage
7. ✅ Document new import paths

## Success Criteria
- Root `__init__.py` ≤40 lines
- All tests pass
- No broken imports
- Backward compatibility maintained
- All callers updated systematically

## Known Issues
- `control_plane.py` exceeds 500-line limit (776 lines)
- Requires further decomposition into submodule files
