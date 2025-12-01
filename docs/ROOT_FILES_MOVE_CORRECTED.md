# Root Files Audit: Move to Project Homes (CORRECTED)
**Date:** 2025-11-22  
**Status:** AUDIT COMPLETE (REVISED)  
**Correction:** FASTMCP_* and TOOL_TYPING_* files belong to **smartcp**, not zen-mcp-server

---

## 📊 Summary

Files in root directory that belong to **specific projects**:

| Project | Current Location | Target | Files Count | Status |
|---------|------------------|--------|-------------|--------|
| **smartcp** | root | `/smartcp/docs/` | 20 | **CORRECTED** |
| **pheno-sdk** | root | `/pheno-sdk/docs/` | 70+ | As before |
| **zen-mcp-server** | root | `/zen-mcp-server/docs/` | 5-8 | Reduced |
| **router** | root | `/router/docs/` | 20-25 | As before |
| **bloc** | root | `/bloc/docs/` | 8-10 | As before |
| **crun** | root | `/crun/docs/` | 5-8 | As before |
| **4sgm** | root | `/4sgm/docs/` | 3-5 | As before |
| **Cross-project** | root | `/docs/research/` | 35+ | As before |
| **Archive** | root | `/archive/` | 10-15 | As before |

---

## 🎯 SMARTCP Files (Move to `/smartcp/docs/`) ✨ **CORRECTED**

**SmartCP** is the new MCP-related intelligent tool composition project. It owns the FastMCP research and tool typing work:

```
→ /smartcp/docs/research/

FASTMCP_COMPLETE_ANALYSIS_SUMMARY.md
FASTMCP_COMPLETE_RESEARCH_INDEX.md
FASTMCP_FEATURE_COVERAGE_MATRIX.md
FASTMCP_FEATURES_CHECKLIST.md
FASTMCP_SERVER_FEATURES_ANALYSIS.md
TOOL_STORAGE_ARCHITECTURE_RESEARCH.md
TOOL_TYPING_COMPOSITION_RESEARCH.md
TOOL_TYPING_STORAGE_RESEARCH_COMPLETE.md
TOOL_TYPING_STORAGE_INDEX.md
TOOL_TYPING_STORAGE_SUMMARY.md
```

**These are smartcp's core research documents** that inform the project proposals:
- PROPOSAL_01_FASTMCP_2_13_UPGRADE.md
- PROPOSAL_02_MULTI_TRANSPORT_AUTH.md
- PROPOSAL_03_BASH_ENVIRONMENT.md
- PROPOSAL_04_MULTI_LANGUAGE_EXECUTORS.md
- PROPOSAL_05_HIERARCHICAL_MEMORY.md
- PROPOSAL_06_ASYNC_SYNC_PARALLEL.md
- PROPOSAL_07_ADVANCED_DISCOVERY.md
- PROPOSAL_08_MCP_REGISTRY.md
- PROPOSAL_09_TOOL_LIFECYCLE.md

*(Proposals already in `/smartcp/` - keep them there)*

**Total: ~10 research files** → `/smartcp/docs/research/`

**Related Summary Files → `/smartcp/docs/`:**
```
SMARTCP_OPENSPEC_PROPOSALS_INDEX.md (already in smartcp)
```

---

## 🎯 PHENO-SDK Files (Move to `/pheno-sdk/`)

**Pheno-SDK** is the foundational library. These files are pheno-sdk research/docs:

```
→ /pheno-sdk/docs/

ARCHITECTURE_TOOLS_PLAN.md
ARCHITECTURE_TOOLS_RESEARCH_COMPLETE.md
ARCHITECTURE_VISION_VISUAL.md
AUDIT_COMPLETION_INDEX.md
BUILD_STATUS_FINAL.md
BUILD_SUCCESS_FINAL.md
CODE_PATTERNS_AND_ANTIPATTERNS_AUDIT.md
CODEBASE_RE-AUDIT_REPORT.md
COMMUNITY_CONTRIBUTION_GUIDE.md
COMPLETE_IMPLEMENTATION_MASTER_INDEX.md
COMPLETE_IMPLEMENTATION_READY.md
COMPREHENSIVE_DOCUMENTATION_ASSETS.md
COMPREHENSIVE_ENHANCEMENT_SPECS.md
CONTINUED_RESEARCH_AUDIT.md
DEEP_CODE_INSPECTION_REPORT.md
DEEP_DIVE_AUDIT_2025.md
DEEPER_AUDIT_REPORT.md
DEPENDENCY_CHANGELOG_NOV_2025.json
DEPLOYMENT_READY.md
DOCSTRING_ADDITIONS_SUMMARY.md
DOCSTRING_BEFORE_AFTER.md
DOCSTRING_ENHANCEMENT_INDEX.md
DOCSTRING_IMPROVEMENT_FINAL_STATUS.md
DOCSTRING_IMPROVEMENT_PLAN.md
DOCSTRING_QUALITY_ROADMAP.md
DOCSTRING_STRATEGY.md
DOCUMENTATION_AUDIT_COMPLETE.md
DOCUMENTATION_BUILD_STATUS.md
DOCUMENTATION_CLEANUP_REPORT.md
DOCUMENTATION_COMPLETENESS_AUDIT.md
DOCUMENTATION_QUALITY_SUMMARY.md
FINAL_100_100_MASTER_SUMMARY.md
FINAL_COMPREHENSIVE_AUDIT_INDEX.md
FINAL_DOCUMENTATION_SUMMARY.md
FINAL_PROJECT_SUMMARY.md
FULL_IMPLEMENTATION_COMPLETE.md
IMPLEMENTATION_COMPLETE_MASTER_SUMMARY.md
IMPLEMENTATION_PROGRESS_PHASE1.md
IMPLEMENTATION_START_SUMMARY.md
IMPLEMENTATION_STARTED_SUMMARY.md
LIBRARY_REPLACEMENTS_2025.md
LINT_COMPLIANCE_100_PERCENT.md
MIGRATION_COMPLETE.md
MODULES_README_GUIDE.md
OPTIMIZATION_SCRIPT.py
PARAMETER_REFACTORING_GUIDE.md
QUALITY_100_100_COMPLETE.md
QUALITY_IMPROVEMENT_ACTION_PLAN.md
README_COMPLETION_REPORT.md
REMEDIATION_PLAN.md
RESEARCH_SUMMARY.md
RETURN_SIMPLIFICATION_GUIDE.md
SECRETS_MIGRATION_GUIDE.md
SESSION_COMPLETION_REPORT.md
SESSION_COMPLETION_SUMMARY.txt
SESSION_FINAL_SUMMARY.md
SESSION_SUMMARY_AND_ROADMAP.md
TASK_COMPLETION_REPORT.md
TUTORIALS_AND_EXAMPLES_AUDIT.md
ULTIMATE_EXTENDED_AUDIT_SUMMARY.md
ULTRA_DEEP_GRANULAR_AUDIT.md
VERIFICATION_CHECKLIST.md
VERIFICATION_SUMMARY.md
VERTICAL_INTEGRATION_STRATEGY.md
WEB_RESEARCH_AUDIT_REPORT.md
PHENO_SDK_COMPLETE_DELIVERY.md
PHENOSDK_COMPONENT_REGISTRY_PROPOSAL.md

→ /pheno-sdk/docs/phases/

ALL_PHASES_COMPLETE_FINAL_SUMMARY.md
PHASE_1_1_COMPLETION_SUMMARY.md
PHASE_1_COMPLETION_STATUS.md
PHASE_1_COMPLETION_SUMMARY.md
PHASE_1_EXECUTIVE_SUMMARY.md
PHASE_1_FINAL_COMPLETION.md
PHASE_1_INDEX.md
PHASE_1_QUICK_START.md
PHASE_1_README.md
PHASE_1_RESOURCES.md
PHASE_2_ARCHITECTURE_PLAN.md
PHASE_2_COMPLETION_SUMMARY.md
PHASE_2_INDEX.md
PHASE_2_INTEGRATION_GUIDE.md
PHASE_3_ARCHITECTURE_PLAN.md
PHASE_3_COMPLETE_FINAL.md
PHASE_3_COMPLETION_SUMMARY.md
PHASE_3_EXECUTIVE_SUMMARY.md
PHASE_3_INDEX.md
PHASE_4_ARCHITECTURE_PLAN.md
PHASE_4_COMPLETE_ECOSYSTEM.md
PHASE_4_COMPLETION_SUMMARY.md
PHASE_4_INDEX.md
PHASE_5_ARCHITECTURE_PLAN.md
PHASE_5_COMPLETION_SUMMARY.md
PHASE_5_INDEX.md
PHASE_6_ARCHITECTURE_PLAN.md
PHASE_6_COMPLETION_SUMMARY.md
PHASE_6_FINAL_REPORT.md
PHASE_6_INDEX.md
PHASE_6_RESEARCH_FINDINGS.md
PHASE_6_ROADMAP.md
PHASE_6_STATUS.md
PHASE_6_VISION.md
PHASE_7_ARCHITECTURE_PLAN.md
PHASE_7_COMPLETION_SUMMARY.md
PHASE_7_VISION.md
PHASE1_COMPLETE_FINAL_SUMMARY.md
PHASE1_COMPLETION_SUMMARY.md
PHASE1_IMPLEMENTATION_GUIDE.md
PHASE1_IMPLEMENTATION_PLAN.md
PHASE2_COMPLETION_SUMMARY.md
PHASE2_DOCSTRING_EXPANSION_PLAN.md
PHASE2_IMPLEMENTATION_GUIDE.md
PHASE3_ADVANCED_QUALITY.md
PHASE3_EXECUTION_SUMMARY.md
PHASE3_IMPLEMENTATION_GUIDE.md
PHASE4_IMPLEMENTATION_GUIDE.md
PHASE5_IMPLEMENTATION_GUIDE.md
PHASE6_IMPLEMENTATION_GUIDE.md

→ /pheno-sdk/scripts/

automated_implementation.py
automated_refactoring.py
cleanup_and_complete.py
code_quality_improvements.py
deploy_test.py
deploy_to_aws.py
execute_complete_migration.sh
execute_registry_cleanup.sh
execute_tier1_cleanup.sh
final_100_completion.py
final_completion_script.py
fix_init_files.py
migrate_to_simplified.py
test_final_validation.py
test_phase5_6.py

→ /pheno-sdk/

API_GENERATION_COMPLETION_SUMMARY.md
API_REFERENCE_MAPPING.md
API_REFERENCE_PROGRESS.md
CURRENT_GAPS_AND_UI_ASSESSMENT.md
DECOMPOSITION_VERIFICATION_REPORT.md
DECOMPOSITION_VERIFICATION_SUMMARY.md
DEVELOPMENT.md
DOCSTRING_ADDITIONS_SUMMARY.md
FUMADOCS_ENHANCEMENT_PHASE1_COMPLETE.md
FUMADOCS_PHASE1_SESSION_SUMMARY.md
FUMADOCS_PLUGIN_OPTIMIZATION.md
GAP_ANALYSIS_REPORT.md
generate_api_pages.py
enhance_api_pages.py
enhance_phase7_data_classes.py
HOMEPAGE_REDESIGN_COMPLETE.md
HOTFIX_BUILD_ERRORS.md
INTEGRATION_STATUS_REPORT.md
MKDOCS_QUICK_REFERENCE.md
MKDOCS_VERIFICATION_REPORT.md
NAVIGATION_FIXES_COMPLETION_REPORT.md
README_DOCUMENTATION_SYSTEM.md
```

**Total: ~70+ files** → `/pheno-sdk/`

---

## 🎯 ZEN-MCP-SERVER Files (Move to `/zen-mcp-server/`)

**Zen-MCP-Server** is the enterprise MCP server. These are its specific files:

```
→ /zen-mcp-server/docs/ or /zen-mcp-server/

(Already has existing docs structure)
(Check for any zen-mcp-server specific files in root that aren't FASTMCP/TOOL_TYPING)
```

**Note:** The FASTMCP_* and TOOL_TYPING_* files moved to smartcp above.

**Total: ~0-3 files** (if any remaining) → `/zen-mcp-server/docs/`

---

## 🎯 ROUTER Files (Move to `/router/`)

Router is the routing engine:

```
→ /router/docs/

(Router already has extensive documentation)
Look for any ROUTER* or routing-specific files in root
```

**Total: Check for ROUTER* files** → `/router/docs/`

---

## 🎯 BLOC Files (Move to `/bloc/`)

Bloc is the code analysis tool:

```
→ /bloc/docs/

COCOMO_GUIDE.md
HACK_CHECKER_IMPROVEMENTS.md
```

**Total: ~2 files** → `/bloc/docs/`

---

## 🎯 CRUN Files (Move to `/crun/`)

CRUN is the multi-agent orchestration platform:

```
→ /crun/docs/

(CRUN already has extensive docs)
Check for any CRUN-specific files in root
```

**Total: Check for CRUN* files** → `/crun/docs/`

---

## 🎯 4SGM Files (Move to `/4sgm/`)

4SGM is the e-commerce project:

```
→ /4sgm/4sgm/docs/

(Check for any 4sgm-specific docs in root)
```

**Total: Check for 4SGM* files** → `/4sgm/4sgm/docs/`

---

## 🎯 General/Cross-Project Files (Root-level)

These belong in `/docs/` at root (general/cross-project):

```
Destination: /docs/planning/ or /docs/

00_MASTER_INDEX.md                      # Overview of all projects
00_START_HERE.md                        # Entry point
01_PROJECT_PLAN.md                      # Cross-project plan
02_PRODUCT_REQUIREMENTS.md              # Cross-project requirements
03_WORK_BREAKDOWN_STRUCTURE.md          # Cross-project WBS
04_LATEST_VERSIONS_2025.md              # Version tracking
MASTER_IMPLEMENTATION_PLAN.md
MASTER_WBS_SPECIFICATION.md
IMPLEMENTATION_ROADMAP.md
OPTIMIZED_PLAN_SUMMARY.txt
OPTIMIZED_PLAN_WITH_EXISTING_LIBS.md
EXECUTION_CHECKLIST.md
PROPOSALS_SUMMARY.md
OPENSPEC_PROPOSALS_INDEX.md
README_OPENSPEC_PROPOSALS.md
OPENSPEC_PROPOSALS_MASTER.md
```

**Total: ~15-16 files** → `/docs/planning/` (or keep in root if orchestration docs)

---

## 🎯 Database Research Files (Root-level)

Cross-project database research:

```
Destination: /docs/research/database/

LOCAL_CLOUD_DATABASE_OPTIONS.md
DOCKER_COMPOSE_LOCAL_STACK.md
CLOUD_FREEMIUM_SETUP_GUIDE.md
POSTGRES_PGVECTOR_FTS_GUIDE.md
SUPABASE_PGVECTOR_FTS_IMPLEMENTATION.md
DATABASE_OPTIONS_COMPLETE_SUMMARY.txt
POSTGRES_PGVECTOR_FTS_COMPLETE.txt
```

**Total: ~7 files** → `/docs/research/database/`

---

## 🎯 AutoRouter Research Files (Root-level)

Cross-project auto-routing research:

```
Destination: /docs/research/routing/

AUTO_ROUTER_MLX_ARCH_GUIDE.md
SEMANTIC_PREDISCOVERY_HOOKS.md
AUTO_ROUTER_IMPLEMENTATION.md
AUTO_ROUTER_COMPLETE_RESEARCH.txt
SEMANTIC_LAZY_DISCOVERY_RESEARCH.md
```

**Total: ~5 files** → `/docs/research/routing/`

---

## 🎯 Claude Integration Research (Root-level)

Cross-project Claude integration:

```
Destination: /docs/research/claude-integration/

CLAUDE_AGENT_SKILLS_RESEARCH.md
CLAUDE_SKILLS_DETAILED_RESEARCH.md
CLAUDE_SKILLS_EXECUTIVE_BRIEF.md
CLAUDE_SKILLS_INTEGRATION_SUMMARY.md
CLAUDE_SKILLS_RESEARCH_COMPLETE.md
CLAUDE_SKILLS_RESEARCH_INDEX.md
```

**Total: ~6 files** → `/docs/research/claude-integration/`

---

## 🎯 Proposals & Research (Root-level)

Cross-project proposals (NOT smartcp proposals - those stay in smartcp):

```
Destination: /docs/research/proposals/

PROPOSAL_01_FASTMCP_2_13_UPGRADE.md ← MOVE TO /smartcp/
PROPOSAL_02_MULTI_TRANSPORT_AUTH.md ← MOVE TO /smartcp/
PROPOSAL_03_BASH_ENVIRONMENT.md ← MOVE TO /smartcp/
PROPOSAL_04_MULTI_LANGUAGE_EXECUTORS.md ← MOVE TO /smartcp/
PROPOSAL_05_ENHANCED_DISCOVERY.md (cross-project - keep here)
PROPOSAL_05_TOOL_DISCOVERY_SEARCH.md ← MOVE TO /smartcp/
PROPOSAL_06_TOOL_MANAGEMENT_LIFECYCLE.md ← MOVE TO /smartcp/
PROPOSAL_07_CLAUDE_AGENT_SKILLS.md (cross-project - keep here)
PROPOSAL_08_TYPED_TOOL_COMPOSITION.md ← MOVE TO /smartcp/
PROPOSAL_09_POLYGLOT_STORAGE.md ← MOVE TO /smartcp/
PROPOSAL_10_ADVANCED_SERVER_FEATURES.md (zen-mcp? or smartcp? - check content)
PROPOSAL_11_CLIENT_PROXY_MIDDLEWARE.md (zen-mcp? or smartcp? - check content)
PROPOSAL_12_MCP_REGISTRY_AUTOMATION.md ← MOVE TO /smartcp/
```

**Wait: Some proposals may already be in smartcp!** Check if these are duplicates.

---

## 🎯 MCP Registry Research (Root-level)

Cross-project MCP research:

```
Destination: /docs/research/mcp-registry/ OR /smartcp/docs/research/

MCP_REGISTRY_AUTOMATED_INSTALL_RESEARCH.md ← LIKELY smartcp
MCP_REGISTRY_RESEARCH_COMPLETE.txt ← LIKELY smartcp
```

**Total: ~2 files** → Check if smartcp-specific or cross-project

---

## 🎯 Discovery Research (Root-level)

```
Destination: /docs/research/discovery/

DISCOVERY_ENHANCEMENT_SUMMARY.md
DISCOVERY_RESEARCH_COMPLETE.txt
```

**Total: ~2 files** → `/docs/research/discovery/`

---

## 🎯 Phase Reports (Root-level)

General project phases (not pheno-sdk specific):

```
Destination: /docs/planning/phases/

PHASE_1_FINAL_SUMMARY.txt
PHASE_1_IMPLEMENTATION_COMPLETE.md
PHASE_2_IMPLEMENTATION_COMPLETE.md
PHASE2_COMPLETE.md
PHASE2_SUMMARY.txt
PHASE_3_COMPLETE_SUMMARY.md
PHASE_3_CONTENT_EXPANSION_COMPLETE.md
PHASE_3_INDEX.md
PHASE_3_PROGRESS_REPORT.md
PHASE_3_SESSION_SUMMARY.md
PHASE_3_VALIDATION_CHECKLIST.md
PHASE3_COMPLETE.md
PHASE_4_IMPLEMENTATION_GUIDE.md
PHASE_4_START.md
PHASE4_COMPLETE.md
```

**Note: Most of these are pheno-sdk phases - verify before moving to root /docs/**

---

## 🎯 Guides & Setup (Root-level)

```
Destination: /docs/guides/setup/

SETUP_GUIDE_LATEST.md
DEPLOYMENT_GUIDE.md
DEV_STATUS.md
README_DEV.md
DELIVERY_SUMMARY.md
EXECUTIVE_SUMMARY.md
LIBRARY_USAGE_GUIDE.md
```

**Total: ~7 files** → `/docs/guides/setup/`

---

## 🎯 Summary & Documentation (Root-level)

```
Destination: /docs/

COMPREHENSIVE_RESEARCH_CATALOG_COMPLETE.md
MASTER_DOCUMENTS_SUMMARY.txt
RESEARCH_COMPLETE_FINAL_SUMMARY.md
RESEARCH_DELIVERABLES_MANIFEST.txt
RESEARCH_FINDINGS.md
ULTIMATE_MASTER_INDEX_COMPLETE.md
FILE_MANIFEST.txt
ARCHITECTURE_OVERVIEW_DIAGRAM.md
COMPILATION_SUMMARY.txt
DOCUMENTATION_INFRASTRUCTURE_AUDIT_PLAN.md
DOCUMENTATION_INFRASTRUCTURE_MASTER_SUMMARY.md
```

**Total: ~11 files** → `/docs/`

---

## 📋 Execution Plan

### Step 1: Create Target Directories

```bash
# SmartCP
mkdir -p /smartcp/docs/research

# Pheno-SDK
mkdir -p /pheno-sdk/docs/phases
mkdir -p /pheno-sdk/scripts

# Zen-MCP-Server
mkdir -p /zen-mcp-server/docs/research

# General docs (if not exists)
mkdir -p /docs/planning/phases
mkdir -p /docs/research/{database,routing,claude-integration,proposals,mcp-registry,discovery}
mkdir -p /docs/guides/setup
```

### Step 2: Move SmartCP Files (Priority 1)

```bash
# Move FASTMCP and TOOL_TYPING research to smartcp
mv FASTMCP_*.md /smartcp/docs/research/
mv TOOL_TYPING_*.md /smartcp/docs/research/

# Verify smartcp proposals are already there
ls /smartcp/PROPOSAL_*.md
```

### Step 3: Move Pheno-SDK Files (Priority 2)

```bash
mv PHASE_*.md /pheno-sdk/docs/phases/
mv PHASE*.md /pheno-sdk/docs/phases/
mv API_*.md /pheno-sdk/docs/
mv DOCSTRING_*.md /pheno-sdk/docs/
# ... etc (many files)
```

### Step 4: Move Cross-Project Files (Priority 3)

```bash
mv LOCAL_CLOUD_*.md /docs/research/database/
mv POSTGRES_*.md /docs/research/database/
mv AUTO_ROUTER_*.md /docs/research/routing/
# ... etc
```

### Step 5: Verify and Update References

After moves:
1. Update `mkdocs.yml` with new paths
2. Check for any hardcoded file references
3. Test documentation build: `mkdocs serve`
4. Verify git moves (not deletes): `git status`

### Step 6: Commit

```bash
git add -A
git commit -m "refactor: move project documentation to respective project folders

MAJOR CORRECTION: FASTMCP_* and TOOL_TYPING_* files belong to smartcp, not zen-mcp-server

- Move FastMCP and tool typing research to /smartcp/docs/research/
- Move pheno-sdk docs to /pheno-sdk/docs/
- Move cross-project docs to /docs/research and /docs/planning/
- Move setup/deployment guides to /docs/guides/setup/

This improves organization and makes each project self-contained."
```

---

## ✅ Verification Checklist

- [ ] All destination directories created
- [ ] **SmartCP files moved first** (FASTMCP_*, TOOL_TYPING_*)
- [ ] Pheno-SDK files moved
- [ ] Cross-project files moved
- [ ] No duplicate files created
- [ ] `mkdocs.yml` paths updated
- [ ] Documentation builds without errors: `mkdocs serve`
- [ ] Git tracks as moves (not deletes): `git status --short | grep "^R "`
- [ ] All tests pass: `uv run pytest`
- [ ] Commit created with clear message

---

## 🎯 Key Corrections

**ORIGINAL ERROR:**
- Assigned FASTMCP_* and TOOL_TYPING_* to zen-mcp-server ❌

**CORRECTED:**
- FASTMCP_* and TOOL_TYPING_* belong to **smartcp** ✅
- Zen-MCP-Server keeps its own specific documentation
- SmartCP is the project for intelligent tool composition and FastMCP enhancements

**IMPACT:**
- SmartCP gets ~10 research files
- Zen-MCP-Server gets ~0-3 remaining files (if any)
- Pheno-SDK remains with ~70+ files
- Cross-project research remains in /docs/
