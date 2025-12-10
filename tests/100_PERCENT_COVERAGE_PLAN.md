# 🎯 100% Code Coverage Plan

**Current Coverage**: 17% → **Target**: 100%

## 📊 Coverage Analysis

### ✅ Already Covered (90-100%)
- `runtime/tools/registry.py` - 90% (4 lines missing)
- `runtime/types.py` - 98% (1 line missing)
- `runtime/__init__.py` - 100%
- `runtime/tools/types.py` - 100%

### ⚠️ Partially Covered (Needs Improvement)
- `runtime/core.py` - 32% (23 lines missing)
- `runtime/namespace.py` - 27% (47 lines missing)
- `runtime/sandbox.py` - 19% (82 lines missing)
- `runtime/tools/decorator.py` - 40% (9 lines missing)

### ❌ Not Covered (0% - Critical)
- `runtime/events/` - All modules (140 statements)
- `runtime/mcp/` - All modules (101 statements)
- `runtime/scope/` - All modules (322 statements)
- `runtime/skills/` - All modules (65 statements)
- `tools/execute.py` - 42 statements
- `tools/discovery.py` - 14 statements
- `bifrost_client.py` - ~105 statements (delegation layer - Phase 6)
- `main.py` - ~240 statements (legacy - Phase 7, may be deprecated)

## 🚀 Implementation Plan

### Phase 0: Code Cleanup & Organization (Priority 0) ⚪

**Goal**: Remove unrelated code and organize project structure

#### 0.1 Identify Unrelated Code
- [x] Found Go code in `smartcp/cmd/`, `smartcp/internal/` (should be in `bifrost-extensions/` or `hub/`)
- [x] Found Docker configs (`docker-compose.yml`, `docker-compose.local.example.yml`)
- [x] Found tunnel config (`tunnel_config.json`)
- [x] Found Go build files (`go.mod`, `go.sum`, `Makefile`)
- [x] Found legacy `main.py` (might be deprecated in favor of `server.py`)

#### 0.2 Review Go CLI Code (KEEP - Project CLI)
**Status**: ✅ **KEEP** - Go code is for SmartCP project CLI (legitimate)

**Files to Keep**:
- [x] `smartcp/cmd/smartcpcli/main.go` → **KEEP** (CLI entrypoint)
- [x] `smartcp/internal/cmd/*.go` → **KEEP** (CLI commands)
- [x] `smartcp/internal/config/config.go` → **KEEP** (CLI config)
- [x] `smartcp/internal/services/*.go` → **KEEP** (CLI services)
- [x] `smartcp/go.mod` → **KEEP** (Go module definition)
- [x] `smartcp/go.sum` → **KEEP** (Go dependencies)
- [x] `smartcp/Makefile` → **KEEP** (CLI build tooling)

**Action Items**:
- [ ] Document that Go code is for CLI (add to README)
- [ ] Ensure Go code is excluded from Python coverage
- [ ] Verify Go CLI builds correctly
- [ ] Add Go tests if missing (separate from Python coverage)

**Impact**: Go CLI code stays, but excluded from Python coverage metrics

#### 0.3 Review Docker Configs
**Files to Review**:
- [ ] `smartcp/docker-compose.yml` → Keep if needed for local dev, document purpose
- [ ] `smartcp/docker-compose.local.example.yml` → Keep if needed, document
- [x] `.dockerignore` → Already exists, verify it excludes Go build artifacts

**Action Items**:
- [ ] Document Docker configs purpose in README
- [ ] Ensure `.dockerignore` excludes Go binaries (`smartcpcli`, etc.)
- [ ] Verify Docker configs work for local development

**Decision**: Keep if needed for SmartCP local development

#### 0.4 Remove Tunnel Config
**Files to Remove**:
- [ ] `smartcp/tunnel_config.json` → Remove (unrelated to SmartCP runtime)

**Reason**: Tunnel configs belong in infrastructure/deployment, not in Python package

#### 0.5 Review Legacy Code
**Files to Review**:
- [ ] `smartcp/main.py` → Determine if deprecated or still needed
  - If deprecated: Remove and update imports
  - If needed: Add to coverage plan
- [ ] `smartcp/bifrost_client.py` → **KEEP** (needed for SmartCP → Bifrost delegation)
  - Add to coverage plan (currently 0% coverage)

#### 0.6 Update Package Configuration
**Files to Update**:
- [ ] `smartcp/pyproject.toml` → Ensure Go code excluded from Python package discovery
- [ ] `smartcp/pyproject.toml` → Review `packages` list, remove non-existent packages
- [ ] Verify all listed packages exist
- [ ] Add Go build artifacts to `.gitignore` if not already there (`smartcpcli`, `*.exe`, etc.)

**Coverage Exclusion**:
- [ ] Ensure coverage excludes Go files (`*.go`)
- [ ] Verify coverage only measures Python code (`*.py`)

**Estimated Time**: 30 minutes - 1 hour

---

### Phase 1: Fix Infrastructure (Priority 1) 🔴

**Goal**: Enable all tests to run

#### 1.1 Fix pytest-asyncio Configuration
- [ ] Update `tests/pytest.ini` with correct asyncio settings
- [ ] Verify pytest-asyncio plugin loads correctly
- [ ] Test async test execution
- [ ] **Expected Impact**: Unlocks 50+ async tests

#### 1.2 Fix Import Issues
- [ ] Fix `tools/execute.py` import paths
- [ ] Fix `tools/__init__.py` imports
- [ ] Verify all imports work correctly
- [ ] **Expected Impact**: Enables execute tool tests

**Files to Modify**:
- `tests/pytest.ini`
- `smartcp/tools/__init__.py`
- `smartcp/tools/execute.py`

**Estimated Time**: 30 minutes

---

### Phase 2: Complete Partial Coverage (Priority 2) 🟡

**Goal**: Bring partially covered modules to 100%

#### 2.1 `runtime/tools/registry.py` (90% → 100%)
**Missing**: 4 lines (likely error handling)

**Tests Needed**:
- [ ] Test `get_tool()` with None user_ctx edge cases
- [ ] Test `unregister()` with non-existent tool
- [ ] Test concurrent registration
- [ ] Test error handling paths

**File**: `tests/unit/runtime/test_tools_registry.py`

#### 2.2 `runtime/types.py` (98% → 100%)
**Missing**: 1 line

**Tests Needed**:
- [ ] Identify missing line (likely edge case)
- [ ] Add test for that specific case

**File**: `tests/unit/runtime/test_types.py`

#### 2.3 `runtime/core.py` (32% → 100%)
**Missing**: 23 lines (lines 38-43, 63-95, 110-112, 123)

**Tests Needed**:
- [ ] Test `execute()` with all namespace config options
- [ ] Test session persistence and retrieval
- [ ] Test `clear_session()` functionality
- [ ] Test error handling in execution
- [ ] Test timeout handling
- [ ] Test variable extraction from sandbox results
- [ ] Test `get_session()` with various states

**File**: `tests/unit/runtime/test_core.py` (expand existing)

#### 2.4 `runtime/namespace.py` (27% → 100%)
**Missing**: 47 lines (API building methods)

**Tests Needed**:
- [ ] Test `_build_tools()` with various tool registries
- [ ] Test `_build_scope_api()` 
- [ ] Test `_build_mcp_api()`
- [ ] Test `_build_skills_api()`
- [ ] Test `_build_background_api()`
- [ ] Test `_build_events_api()`
- [ ] Test `_build_agents_api()`
- [ ] Test `_build_tool_decorator()`
- [ ] Test `_wrap_tool()` with various tool types
- [ ] Test namespace building with all config combinations

**File**: `tests/unit/runtime/test_namespace.py` (expand existing)

#### 2.5 `runtime/sandbox.py` (19% → 100%)
**Missing**: 82 lines (most of the implementation)

**Tests Needed**:
- [ ] Test `initialize()` with PyodideSandbox available
- [ ] Test `initialize()` fallback mode
- [ ] Test `execute()` with valid code
- [ ] Test `execute()` with errors
- [ ] Test `execute()` with timeout
- [ ] Test `execute()` with namespace injection
- [ ] Test `execute()` with session persistence
- [ ] Test `get_session()` 
- [ ] Test `load_session()`
- [ ] Test `_capture_output()` helper
- [ ] Test error handling paths
- [ ] Test Pyodide-specific features

**File**: `tests/unit/runtime/test_sandbox.py` (expand existing)

#### 2.6 `runtime/tools/decorator.py` (40% → 100%)
**Missing**: 9 lines

**Tests Needed**:
- [ ] Test decorator with name parameter
- [ ] Test decorator with description parameter
- [ ] Test decorator with both parameters
- [ ] Test decorator error cases
- [ ] Test tool registration via decorator

**File**: `tests/unit/runtime/test_tools_decorator.py` (expand existing)

**Estimated Time**: 4-6 hours

---

### Phase 3: Zero Coverage Modules (Priority 3) 🟢

**Goal**: Add tests for all 0% coverage modules

#### 3.1 `runtime/scope/` (0% → 100%) - 322 statements

**3.1.1 `scope/manager.py` (36 statements)**
- [ ] Test all `ScopeManager` methods
- [ ] Test `get()` with all scope levels
- [ ] Test `set()` with all scope levels
- [ ] Test `delete()` with all scope levels
- [ ] Test `keys()` with all scope levels
- [ ] Test `promote()` between all level pairs
- [ ] Test `demote()` between all level pairs
- [ ] Test user isolation
- [ ] Test level isolation
- [ ] Test error handling

**File**: `tests/unit/runtime/test_scope_manager.py` (expand existing)

**3.1.2 `scope/storage.py` (188 statements)**
- [ ] Test `InMemoryStorage` all methods
- [ ] Test `RedisStorage` (if available)
- [ ] Test `SupabaseStorage` (if available)
- [ ] Test `create_storage()` factory
- [ ] Test `_make_key()` helper
- [ ] Test storage isolation
- [ ] Test error handling
- [ ] Test connection failures

**File**: `tests/unit/runtime/test_scope_storage.py` (expand existing)

**3.1.3 `scope/api.py` (42 statements)**
- [ ] Test all `ScopeLevelAccessor` methods
- [ ] Test all scope level accessors (block, iteration, etc.)
- [ ] Test `promote()` API method
- [ ] Test `demote()` API method
- [ ] Test error handling

**File**: `tests/unit/runtime/test_scope_api.py` (expand existing)

**3.1.4 `scope/types.py` (52 statements)**
- [ ] Test `ScopeLevel` enum values
- [ ] Test `ScopeKey` dataclass
- [ ] Test key generation
- [ ] Test level hierarchy

**File**: `tests/unit/runtime/test_scope_types.py` (NEW)

**3.1.5 `scope/__init__.py` (4 statements)**
- [ ] Test exports

**File**: `tests/unit/runtime/test_scope_init.py` (NEW)

#### 3.2 `runtime/mcp/` (0% → 100%) - 101 statements

**3.2.1 `mcp/manager.py` (39 statements)**
- [ ] Test `search_registry()` 
- [ ] Test `install_package()`
- [ ] Test `list_servers()` with user filtering
- [ ] Test `create_server()`
- [ ] Test `restart_server()`
- [ ] Test `stop_server()`
- [ ] Test `delete_server()`
- [ ] Test error handling
- [ ] Test user isolation

**File**: `tests/unit/runtime/test_mcp_manager.py` (expand existing)

**3.2.2 `mcp/api.py` (33 statements)**
- [ ] Test `MCPAPI.search()`
- [ ] Test `MCPAPI.install()`
- [ ] Test `MCPAPI.uninstall()`
- [ ] Test `MCPAPI.list_installed()`
- [ ] Test `MCPServersAPI.list()`
- [ ] Test `MCPServersAPI.create()`
- [ ] Test `MCPServersAPI.restart()`
- [ ] Test `MCPServersAPI.stop()`
- [ ] Test `MCPServersAPI.delete()`

**File**: `tests/unit/runtime/test_mcp_api.py` (expand existing)

**3.2.3 `mcp/types.py` (26 statements)**
- [ ] Test all MCP type definitions
- [ ] Test data classes
- [ ] Test validation

**File**: `tests/unit/runtime/test_mcp_types.py` (NEW)

**3.2.4 `mcp/__init__.py` (3 statements)**
- [ ] Test exports

**File**: `tests/unit/runtime/test_mcp_init.py` (NEW)

#### 3.3 `runtime/skills/` (0% → 100%) - 65 statements

**3.3.1 `skills/loader.py` (47 statements)**
- [ ] Test `load()` with existing skill
- [ ] Test `load()` with non-existent skill
- [ ] Test `save()` with new skill
- [ ] Test `save()` with existing skill
- [ ] Test `list()` with skills
- [ ] Test `list()` with no skills
- [ ] Test user isolation
- [ ] Test path helpers
- [ ] Test error handling (permissions, disk full, etc.)

**File**: `tests/unit/runtime/test_skills_loader.py` (expand existing)

**3.3.2 `skills/api.py` (15 statements)**
- [ ] Test `SkillsAPI.load()`
- [ ] Test `SkillsAPI.save()`
- [ ] Test `SkillsAPI.list()`
- [ ] Test error handling

**File**: `tests/unit/runtime/test_skills_api.py` (expand existing)

**3.3.3 `skills/__init__.py` (3 statements)**
- [ ] Test exports

**File**: `tests/unit/runtime/test_skills_init.py` (NEW)

#### 3.4 `runtime/events/` (0% → 100%) - 140 statements

**3.4.1 `events/bus.py` (50 statements)**
- [ ] Test `publish()` with subscribers
- [ ] Test `publish()` without subscribers
- [ ] Test `subscribe()` 
- [ ] Test `create_task()`
- [ ] Test `get_task_status()`
- [ ] Test `wait_for_task()` with completion
- [ ] Test `wait_for_task()` with timeout
- [ ] Test error handling
- [ ] Test concurrent operations

**File**: `tests/unit/runtime/test_events_bus.py` (expand existing)

**3.4.2 `events/api.py` (43 statements)**
- [ ] Test `EventsAPI.publish()`
- [ ] Test `EventsAPI.subscribe()`
- [ ] Test `AgentsAPI.spawn()`
- [ ] Test `AgentsAPI.send()`
- [ ] Test `BackgroundTask` class
- [ ] Test `create_background_task_api()`
- [ ] Test error handling

**File**: `tests/unit/runtime/test_events_api.py` (expand existing)

**3.4.3 `events/background.py` (44 statements)**
- [ ] Test background task creation
- [ ] Test task execution
- [ ] Test task status tracking
- [ ] Test task result retrieval
- [ ] Test error handling

**File**: `tests/unit/runtime/test_events_background.py` (NEW)

**3.4.4 `events/__init__.py` (3 statements)**
- [ ] Test exports

**File**: `tests/unit/runtime/test_events_init.py` (NEW)

#### 3.5 `tools/execute.py` (0% → 100%) - 42 statements

**Tests Needed**:
- [ ] Test `execute()` function with valid code
- [ ] Test `execute()` with errors
- [ ] Test `execute()` with timeout
- [ ] Test `clear_session()` function
- [ ] Test `runtime_status()` function
- [ ] Test `register_execute_tool()` function
- [ ] Test `_extract_user_context()` helper
- [ ] Test error handling
- [ ] Test with various user contexts

**File**: `tests/unit/tools/test_execute.py` (expand existing)

#### 3.6 `tools/discovery.py` (0% → 100%) - 14 statements

**Tests Needed**:
- [ ] Test tool discovery functions
- [ ] Test search functionality
- [ ] Test filtering
- [ ] Test error handling

**File**: `tests/unit/tools/test_discovery.py` (NEW)

#### 3.7 `tools/__init__.py` (0% → 100%) - 2 statements

**Tests Needed**:
- [ ] Test exports

**File**: `tests/unit/tools/test_tools_init.py` (NEW)

**Estimated Time**: 8-12 hours

---

### Phase 4: Edge Cases & Error Paths (Priority 4) 🔵

**Goal**: Cover all edge cases and error paths

#### 4.1 Error Handling Tests
- [ ] Network failures
- [ ] Timeout scenarios
- [ ] Invalid input validation
- [ ] Resource exhaustion
- [ ] Concurrent access issues
- [ ] Permission errors
- [ ] Storage failures

#### 4.2 Edge Cases
- [ ] Empty inputs
- [ ] Very large inputs
- [ ] Unicode handling
- [ ] Boundary conditions
- [ ] Race conditions
- [ ] Memory limits

**Estimated Time**: 4-6 hours

---

### Phase 5: Integration & E2E Coverage (Priority 5) 🟣

**Goal**: Ensure integration tests cover integration points

#### 5.1 Component Integration Tests
- [ ] ToolRegistry + NamespaceBuilder
- [ ] ScopeManager + ScopeAPI
- [ ] Runtime + Sandbox + Namespace
- [ ] All APIs working together

#### 5.2 E2E Tests
- [ ] Complete user workflows
- [ ] Multi-user scenarios
- [ ] Error recovery flows
- [ ] Performance scenarios

**Estimated Time**: 2-4 hours

---

### Phase 6: Bifrost Integration Coverage (Priority 6) 🟠

**Goal**: Test SmartCP → Bifrost delegation layer

#### 6.1 `bifrost_client.py` (0% → 100%) - ~105 statements
**Note**: This is part of SmartCP (delegation layer), not bifrost-extensions

**Tests Needed**:
- [ ] Test `BifrostClientConfig` initialization
- [ ] Test `BifrostClient.__init__()`
- [ ] Test `BifrostClient.connect()`
- [ ] Test `BifrostClient.disconnect()`
- [ ] Test `BifrostClient.health()`
- [ ] Test `BifrostClient.route_request()`
- [ ] Test `BifrostClient.query_tools()`
- [ ] Test `BifrostClient.query_tool()`
- [ ] Test `BifrostClient.semantic_search()`
- [ ] Test `BifrostClient.execute_tool()`
- [ ] Test error handling (connection failures, timeouts)
- [ ] Test GraphQL query construction
- [ ] Test response parsing
- [ ] Test retry logic (if any)

**File**: `tests/unit/test_bifrost_client.py` (expand existing)

**Estimated Time**: 2-3 hours

#### 6.2 Bifrost Integration Points
- [ ] Test `server.py` bifrost_client integration
- [ ] Test `main.py` bifrost_client integration (if still used)
- [ ] Test error handling when Bifrost unavailable
- [ ] Test delegation flow end-to-end

**Files**: 
- `tests/integration/test_bifrost_integration.py` (expand existing)
- `tests/integration/test_server_bifrost.py` (NEW)

**Estimated Time**: 30 minutes - 1 hour (reduced since Go code stays)

---

### Phase 7: Legacy Code Cleanup & Coverage (Priority 7) 🔵

**Goal**: Handle legacy code and ensure it's either covered or removed

#### 7.1 Review `main.py` Status
**Decision Points**:
- [ ] Determine if `main.py` is deprecated
- [ ] If deprecated: Remove and update all imports
- [ ] If active: Add to coverage plan (currently 0%)

**If Active, Tests Needed**:
- [ ] Test FastAPI app initialization
- [ ] Test lifespan events (startup/shutdown)
- [ ] Test health endpoint
- [ ] Test route endpoint
- [ ] Test list_tools endpoint
- [ ] Test get_tool endpoint
- [ ] Test semantic_search endpoint
- [ ] Test error handling

**File**: `tests/integration/test_main.py` (expand existing)

#### 7.2 Review Other Legacy Files
**Files to Review**:
- [ ] `smartcp/migrations/` → Are these used? Add tests if active
- [ ] `smartcp/schema/` → Review OpenAPI schema, add validation tests
- [ ] `smartcp/scripts/` → Review deployment scripts, add integration tests

**Estimated Time**: 2-4 hours (depending on what's active)

---

## 📋 Test File Checklist

### New Test Files Needed
- [ ] `tests/unit/runtime/test_scope_types.py`
- [ ] `tests/unit/runtime/test_scope_init.py`
- [ ] `tests/unit/runtime/test_mcp_types.py`
- [ ] `tests/unit/runtime/test_mcp_init.py`
- [ ] `tests/unit/runtime/test_skills_init.py`
- [ ] `tests/unit/runtime/test_events_background.py`
- [ ] `tests/unit/runtime/test_events_init.py`
- [ ] `tests/unit/tools/test_discovery.py`
- [ ] `tests/unit/tools/test_tools_init.py`

### Existing Test Files to Expand
- [ ] `tests/unit/runtime/test_tools_registry.py` (+4 lines)
- [ ] `tests/unit/runtime/test_types.py` (+1 line)
- [ ] `tests/unit/runtime/test_core.py` (+23 lines)
- [ ] `tests/unit/runtime/test_namespace.py` (+47 lines)
- [ ] `tests/unit/runtime/test_sandbox.py` (+82 lines)
- [ ] `tests/unit/runtime/test_tools_decorator.py` (+9 lines)
- [ ] `tests/unit/runtime/test_scope_manager.py` (full coverage)
- [ ] `tests/unit/runtime/test_scope_storage.py` (full coverage)
- [ ] `tests/unit/runtime/test_scope_api.py` (full coverage)
- [ ] `tests/unit/runtime/test_mcp_manager.py` (full coverage)
- [ ] `tests/unit/runtime/test_mcp_api.py` (full coverage)
- [ ] `tests/unit/runtime/test_skills_loader.py` (full coverage)
- [ ] `tests/unit/runtime/test_skills_api.py` (full coverage)
- [ ] `tests/unit/runtime/test_events_bus.py` (full coverage)
- [ ] `tests/unit/runtime/test_events_api.py` (full coverage)
- [ ] `tests/unit/tools/test_execute.py` (full coverage)

---

## ⏱️ Time Estimates

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 0: Code Cleanup | 6 tasks | 30 min - 1 hr |
| Phase 1: Infrastructure | 2 tasks | 30 minutes |
| Phase 2: Partial Coverage | 6 modules | 4-6 hours |
| Phase 3: Zero Coverage | 7 modules | 8-12 hours |
| Phase 4: Edge Cases | Various | 4-6 hours |
| Phase 5: Integration | Various | 2-4 hours |
| Phase 6: Bifrost Integration | 2 tasks | 3-5 hours |
| Phase 7: Legacy Code | 2 tasks | 2-4 hours |
| **TOTAL** | | **23-38 hours** |

---

## 🎯 Coverage Targets by Phase

| Phase | Target Coverage | Modules |
|-------|----------------|---------|
| **Current** | 17% | - |
| **After Phase 0** | 17% | Code cleanup (no coverage change) |
| **After Phase 1** | 17% | Infrastructure fixed |
| **After Phase 2** | 35-40% | Partial modules → 100% |
| **After Phase 3** | 85-90% | Zero modules → 100% |
| **After Phase 4** | 95-98% | Edge cases covered |
| **After Phase 5** | 98% | Integration verified |
| **After Phase 6** | 99% | Bifrost integration covered |
| **After Phase 7** | **100%** | All code covered (legacy handled) |

---

## 🚦 Execution Order

1. **Phase 0** (1-2 hrs) - **START HERE** - Clean up unrelated code first
2. **Phase 1** (30 min) - Fix infrastructure
3. **Phase 2** (4-6 hrs) - Quick wins on partial coverage
4. **Phase 3** (8-12 hrs) - Major coverage increase
5. **Phase 4** (4-6 hrs) - Polish edge cases
6. **Phase 5** (2-4 hrs) - Integration verification
7. **Phase 6** (3-5 hrs) - Bifrost integration coverage
8. **Phase 7** (2-4 hrs) - Legacy code handling

---

## 📊 Success Metrics

- ✅ All tests pass
- ✅ Coverage report shows 100%
- ✅ No missing lines in coverage report
- ✅ All edge cases tested
- ✅ Error paths covered
- ✅ Integration points verified

---

## 🔧 Tools & Commands

```bash
# Run coverage
coverage run --source=smartcp/runtime,smartcp/tools -m pytest smartcp/tests/unit/ -v

# Check coverage
coverage report --include="smartcp/runtime/**/*.py,smartcp/tools/**/*.py" --show-missing

# Find missing lines
coverage report --include="smartcp/runtime/**/*.py,smartcp/tools/**/*.py" --show-missing | grep -E "^\s+[0-9]+"

# HTML report
coverage html --include="smartcp/runtime/**/*.py,smartcp/tools/**/*.py"
open htmlcov/index.html
```

---

## 📝 Notes

- Focus on one module at a time
- Run coverage after each module completion
- Verify tests actually execute the missing lines
- Use `--show-missing` to identify exact lines
- Check HTML report for visual verification
- Fix async issues first to unlock most tests

---

**Status**: Ready to execute
**Next Step**: Start with Phase 1 (Infrastructure fixes)
