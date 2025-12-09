# Phase 0.5: Investigation Findings

**Date:** 2025-12-09

---

## Investigation Results

### Embedded Git Repositories (EXTRACT)

✓ **`./router/.git`**
- Status: Embedded git repository (separate .git directory)
- Size: 1.7GB
- Decision: **EXTRACT** - Move to independent KRouter repository

✓ **`./python-proto-ref/.git`**
- Status: Embedded git repository (separate .git directory)
- Size: 920KB
- Decision: **EXTRACT** - Move to independent reference repository

---

### Ambiguous Directories (REVISED DECISION)

#### `/dsl_scope/` Directory

**Investigation Results:**
- Python files: 16
- Markdown files: 1
- **References from outside: 5+ active usages**
  - `./MCP_INFERENCE_INTEGRATION.md`
  - `./tests/mcp_inference/conftest.py`
  - `./tests/mcp_inference/test_integration.py`
  - `./tests/mcp_inference/test_bridge.py`
  - `./mcp_inference_bridge.py`

**Decision: KEEP AND INTEGRATE**
- Rationale: Active component used by MCP inference system
- Action: Organize as `smartcp/agents/dsl/` module (part of main structure)
- Move to: `smartcp/agents/dsl_scope/` or consolidate into agents framework

#### `/vibeproxy/` Directory

**Investigation Results:**
- Code files: 5 Python files
  - `vibeproxy/__init__.py`
  - `vibeproxy/config.py`
  - `vibeproxy/proxy.py`
  - `vibeproxy/factory.py`
  - `vibeproxy/backends.py`
- **References from outside: 99+ active usages**

**Decision: KEEP AND INTEGRATE**
- Rationale: Heavily used proxy/routing layer in smartcp
- Action: Organize as core smartcp module
- Move to: `smartcp/services/vibeproxy/` or `smartcp/infrastructure/routing/`

---

## Revised Phase 0.5 Strategy

### EXTRACT (Remove Embedded Repos)
1. `/router/` → Independent KRouter repo
2. `/python-proto-ref/` → Independent reference repo

### CONSOLIDATE (Root-Level Files)
1. 54 Python files at root → organized into modules
   - MCP files (11) → `mcp/`
   - Executors (4) → `infrastructure/executors/`
   - Infra commons (5) → `infrastructure/common/`
   - Storage adapters (3) → `infrastructure/adapters/`
   - FastMCP variants (3) → merge into `server.py`
   - Tool management (2) → `tools/`
   - Utilities → various targets

### REORGANIZE (Existing Directories)
1. `dsl_scope/` → Move to `smartcp/agents/dsl_scope/` (keep, it's active)
2. `vibeproxy/` → Move to `smartcp/services/vibeproxy/` (keep, it's heavily used)

---

## Impact Analysis

### Size Reduction
- Before: 8.7GB total
- After extraction: ~6.1GB (remove router 1.7GB + python-proto-ref 920KB)
- Reduction: 30%

### Root-Level Python Files
- Before: 54
- After: 0

### Module Organization
- Before: Chaotic (files scattered across root + various directories)
- After: Clean hierarchy with clear responsibilities

---

## Next Steps (Implementation Order)

1. **Extract embedded repos** (2-3 days)
   - Preserve git history
   - Prepare for independent publication
   - Remove from smartcp

2. **Consolidate root files** (3-5 days)
   - Move to appropriate modules
   - Update all imports
   - Verify tests pass

3. **Reorganize dsl_scope/** (1 day)
   - Move to `agents/dsl_scope/`
   - Update imports

4. **Reorganize vibeproxy/** (1 day)
   - Move to `services/vibeproxy/`
   - Update imports

5. **Final testing & verification** (2-3 days)
   - Run full test suite
   - Verify no regressions
   - Update documentation

**Total Estimated Effort: 1-2 weeks**

---

## File Consolidation Mapping

### Root Level Files → Target Locations

**MCP Integration (11 files → `smartcp/mcp/`)**
```
mcp_registry.py              → mcp/registry.py
mcp_server_discovery.py      → mcp/discovery.py
mcp_custom_builder.py        → mcp/builder.py
mcp_lazy_loader.py           → mcp/loaders.py
mcp_lifecycle_manager.py     → mcp/lifecycle.py
mcp_hot_reload.py            → mcp/reloader.py
mcp_agent_discovery.py       → mcp/tools/discovery.py
mcp_tool_aggregator.py       → mcp/tools/aggregator.py
mcp_tool_composer.py         → mcp/tools/composer.py
mcp_security_sandbox.py      → mcp/security.py
mcp_inference_bridge.py      → mcp/inference.py
```

**Executors (4 files → `smartcp/infrastructure/executors/`)**
```
bash_executor.py             → infrastructure/executors/bash.py
typescript_executor.py       → infrastructure/executors/typescript.py
go_executor.py               → infrastructure/executors/go.py
multi_language_executor.py   → infrastructure/executors/multi_language.py
```

**Infrastructure Commons (5 files → `smartcp/infrastructure/common/`)**
```
infra_common.py              → infrastructure/common/client.py
infra_common_constants.py    → infrastructure/common/constants.py
infra_common_manager.py      → infrastructure/common/manager.py
infra_common_types.py        → infrastructure/common/types.py
infra_common_utils.py        → infrastructure/common/utils.py
```

**Storage Adapters (3 files)**
```
neo4j_storage_adapter.py     → infrastructure/adapters/neo4j/adapter.py
vector_graph_db.py           → infrastructure/adapters/vector_db.py
multi_transport.py           → infrastructure/adapters/transport.py
```

**Discovery/Learning (3 files → `smartcp/bifrost_extensions/`)**
```
advanced_discovery.py        → bifrost_extensions/discovery/advanced.py
semantic_discovery.py        → bifrost_extensions/discovery/semantic.py
learning_system.py           → bifrost_extensions/learning.py
```

**FastMCP Variants (3+ files → consolidate into `smartcp/server.py`)**
```
fastmcp_2_13_server.py       → merge into server.py
fastmcp_advanced.py          → merge into server.py
fastmcp_inference_server.py  → merge into server.py
```

**Tool Management (2 files → `smartcp/tools/`)**
```
tool_lifecycle.py            → tools/lifecycle.py
tool_type_system.py          → tools/type_system.py
```

**Utilities & Integration**
```
bifrost_client.py            → infrastructure/bifrost/client.py (dedupe)
claude_integration.py        → infrastructure/adapters/claude.py
server_control.py            → infrastructure/server_control.py
filesystem_concurrency.py    → infrastructure/common/concurrency.py
hierarchical_memory.py       → optimization/memory/hierarchical.py
smartcp_integration.py       → infrastructure/adapters/smartcp.py
```

**Deprecated/Obsolete**
```
mlx_router.py                → DELETE (replaced by router/ - now extracted)
```

**Keep at Root (Core Entry Points)**
```
__init__.py
main.py                      (ASGI entry)
server.py                    (MCP server - after consolidation)
app.py                       (Vercel ASGI)
cli.py                       (CLI interface)
conftest.py                  (pytest configuration)
```

---

**Status:** Investigation Complete, Ready for Implementation
**Recommendation:** Proceed with extraction and consolidation in order listed above
