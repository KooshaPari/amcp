# Phase 0.5: Reference Directory Organization - Execution Log

**Start Date:** 2025-12-09
**Phase:** 0.5 (Reference Directory Organization)
**Status:** IN PROGRESS

---

## Findings

### Embedded Git Repositories Confirmed

✓ **`./router/.git`** - 1.7GB, complete git repository (KRouter)
✓ **`./python-proto-ref/.git`** - 920KB, complete git repository (MCP Reference)

### Root-Level Python Files: 54 Total

```
./__init__.py
./advanced_discovery.py
./agent_automation.py
./analyze_coverage.py
./bash_executor.py
./bifrost_client.py
./claude_integration.py
./cli_hooks.py
./conftest.py
./fastmcp_2_13_server.py
./fastmcp_advanced.py
./fastmcp_inference_server.py
./filesystem_concurrency.py
./fix_tests.py
./go_executor.py
./hierarchical_memory.py
./infra_common_constants.py
./infra_common_manager.py
./infra_common_types.py
./infra_common_utils.py
./infra_common.py
./learning_system.py
./main.py
./mcp_agent_discovery.py
./mcp_custom_builder.py
./mcp_hot_reload.py
./mcp_inference_bridge.py
./mcp_lazy_loader.py
./mcp_lifecycle_manager.py
./mcp_real_registry.py
./mcp_registry.py
./mcp_security_sandbox.py
./mcp_server_discovery.py
./mcp_tool_aggregator.py
./mcp_tool_composer.py
./mlx_router.py
./multi_language_executor.py
./multi_transport.py
./neo4j_storage_adapter.py
./server_control.py
./semantic_discovery.py
./smartcp_integration.py
./tool_lifecycle.py
./tool_type_system.py
./typescript_executor.py
./vector_graph_db.py
(... and more)
```

### Reference Directories

✓ `./router/` - KRouter (embedded .git, 1.7GB)
✓ `./python-proto-ref/` - MCP Reference (embedded .git, 920KB)
✓ `./dsl_scope/` - DSL inference engine (16 files, 292KB)
✓ `./vibeproxy/` - Proxy/app layer (36KB)

---

## Execution Plan

### STEP 1: Investigate Ambiguous Directories
- [ ] Analyze `/dsl_scope/` - Is it active or research?
- [ ] Analyze `/vibeproxy/` - What is its purpose?
- [ ] Decision matrix for each

### STEP 2: Extract Embedded Repos (Preserve Git History)
- [ ] Prepare extraction: Ensure clean state, backup
- [ ] Extract `/router/` → independent KRouter repo
  - [ ] Create git history-only extraction
  - [ ] Prepare for GitHub publication
  - [ ] Remove from smartcp while preserving git history reference
- [ ] Extract `/python-proto-ref/` → independent reference repo
  - [ ] Create git history-only extraction
  - [ ] Prepare for GitHub publication
  - [ ] Remove from smartcp

### STEP 3: Consolidate Root-Level Files
- [ ] Audit each file (purpose, dependencies, usage)
- [ ] Create target module directories
- [ ] Move files to proper locations:
  - [ ] MCP files (11) → `mcp/` module
  - [ ] Executors (4) → `infrastructure/executors/`
  - [ ] Infra commons (5) → `infrastructure/common/`
  - [ ] Storage adapters (3) → `infrastructure/adapters/`
  - [ ] Discovery/learning (3) → `bifrost_extensions/`
  - [ ] FastMCP variants (3) → merge into `server.py`
  - [ ] Tool management (2) → `tools/`
  - [ ] Utilities (4) → various infrastructure targets
- [ ] Update all imports
- [ ] Run tests

### STEP 4: Organize Archives
- [ ] Review `docs/archive/`
- [ ] Clean temporal metadata
- [ ] Move relevant items to sessions
- [ ] Create extracted-repositories documentation

### STEP 5: Verification & Testing
- [ ] No functionality regressions
- [ ] All tests passing
- [ ] Git history clean
- [ ] Documentation updated

---

## Progress Tracking

### Started: Investigation Phase
✓ Confirmed embedded .git repos
✓ Counted root-level files (54)
✓ Located reference directories
→ Next: Investigate ambiguous dirs

---

## Notes

- Router project size (1.7GB) indicates it's substantial standalone product
- Python-proto-ref (920KB) is educational reference implementation
- Both have complete git histories that should be preserved
- Extraction will reduce smartcp from 8.7GB to ~6.1GB (30% reduction)

---

**Owner:** Development Team
**Target Completion:** 1-3 weeks
**Next Review:** After Step 1 (investigation phase)
