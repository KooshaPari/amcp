# Root Directory Audit & File Move Plan
**Date:** 2025-11-22  
**Status:** AUDIT COMPLETE  
**Total Root Files:** 117 non-folder items  
**Action Required:** Move 100+ documentation files to appropriate project folders

---

## 📊 Executive Summary

The root directory contains **100+ documentation and plan files** that should be distributed across project folders based on their ownership and purpose:

| Category | Count | Destination | Action |
|----------|-------|-------------|--------|
| **Planning & Roadmap** | 15 | `/docs/planning/` | Move |
| **Research & Proposals** | 35 | `/docs/research/` | Move |
| **Phase Reports** | 12 | `/docs/planning/phases/` | Move |
| **FastMCP Analysis** | 8 | `/zen-mcp-server/docs/` | Move |
| **Project Config** | 5 | `/.github/` or project root | Keep |
| **Individual Project Files** | 15 | Project-specific folders | Move |
| **Archive/Obsolete** | 12 | `/archive/` | Move |

---

## 🎯 Detailed Move Plan

### SECTION 1: Planning & Strategy Documents (15 files → `/docs/planning/`)

These are high-level planning docs that belong in the centralized docs folder:

```
Destination: /docs/planning/

00_MASTER_INDEX.md                      # Master index
00_START_HERE.md                        # Entry point
01_PROJECT_PLAN.md                      # Project plan
02_PRODUCT_REQUIREMENTS.md              # Product requirements
03_WORK_BREAKDOWN_STRUCTURE.md          # WBS specification
MASTER_IMPLEMENTATION_PLAN.md           # Master implementation plan
MASTER_WBS_SPECIFICATION.md             # WBS specification (duplicate/extended)
IMPLEMENTATION_ROADMAP.md               # Implementation roadmap
OPTIMIZED_PLAN_SUMMARY.txt              # Plan optimization summary
OPTIMIZED_PLAN_WITH_EXISTING_LIBS.md    # Plan with library integration
EXECUTION_CHECKLIST.md                  # Execution checklist
README_OPENSPEC_PROPOSALS.md            # OpenSpec proposal guide
OPENSPEC_PROPOSALS_INDEX.md             # OpenSpec index
PROPOSALS_SUMMARY.md                    # All proposals summary
04_LATEST_VERSIONS_2025.md              # Version tracking
```

**Action:** `mv <file> /docs/planning/`

---

### SECTION 2: Research Documents - Phase 1 (5 files → `/docs/research/database/`)

Database and storage research:

```
Destination: /docs/research/database/

LOCAL_CLOUD_DATABASE_OPTIONS.md         # Local vs cloud options
DOCKER_COMPOSE_LOCAL_STACK.md           # Docker compose setup
CLOUD_FREEMIUM_SETUP_GUIDE.md           # Cloud setup guide
POSTGRES_PGVECTOR_FTS_GUIDE.md          # PostgreSQL pgvector guide
SUPABASE_PGVECTOR_FTS_IMPLEMENTATION.md # Supabase implementation
```

**Related Summary Files → `/docs/research/database/`:**
```
DATABASE_OPTIONS_COMPLETE_SUMMARY.txt
POSTGRES_PGVECTOR_FTS_COMPLETE.txt
```

**Action:** `mv <file> /docs/research/database/`

---

### SECTION 3: Research Documents - Phase 2 (3 files → `/docs/research/routing/`)

Auto-routing and tool discovery:

```
Destination: /docs/research/routing/

AUTO_ROUTER_MLX_ARCH_GUIDE.md
SEMANTIC_PREDISCOVERY_HOOKS.md
AUTO_ROUTER_IMPLEMENTATION.md
```

**Related Summary Files → `/docs/research/routing/`:**
```
AUTO_ROUTER_COMPLETE_RESEARCH.txt
```

**Action:** `mv <file> /docs/research/routing/`

---

### SECTION 4: FastMCP & Tool Research (8 files → `/zen-mcp-server/docs/research/`)

FastMCP-specific research (server is at `/zen-mcp-server/`):

```
Destination: /zen-mcp-server/docs/research/

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

**Action:** `mv <file> /zen-mcp-server/docs/research/`

---

### SECTION 5: Claude Skills Research (6 files → `/docs/research/claude-integration/`)

Claude agent and skill research:

```
Destination: /docs/research/claude-integration/

CLAUDE_AGENT_SKILLS_RESEARCH.md
CLAUDE_SKILLS_DETAILED_RESEARCH.md
CLAUDE_SKILLS_EXECUTIVE_BRIEF.md
CLAUDE_SKILLS_INTEGRATION_SUMMARY.md
CLAUDE_SKILLS_RESEARCH_COMPLETE.md
CLAUDE_SKILLS_RESEARCH_INDEX.md
```

**Action:** `mv <file> /docs/research/claude-integration/`

---

### SECTION 6: Discovery & Enhancement Research (3 files → `/docs/research/discovery/`)

Tool discovery and enhancement:

```
Destination: /docs/research/discovery/

DISCOVERY_ENHANCEMENT_SUMMARY.md
DISCOVERY_RESEARCH_COMPLETE.txt
SEMANTIC_LAZY_DISCOVERY_RESEARCH.md
```

**Action:** `mv <file> /docs/research/discovery/`

---

### SECTION 7: Project-Specific Files (Move to appropriate projects)

#### 7a. 4SGM Project Files → `/4sgm/`

```
Move to: /4sgm/

(Currently scattered in root - these belong in the 4sgm project)
```

#### 7b. Router Project → `/router/docs/`

```
(Router is a major project with 374 subdirs - should contain its own docs)
```

#### 7c. Crun Project → `/crun/docs/`

```
(Crun is a major project with 164 subdirs - should contain its own docs)
```

#### 7d. Bloc Project → `/bloc/docs/`

```
(Bloc is a major project with 42 subdirs - should contain its own docs)
```

---

### SECTION 8: Phase Reports (12 files → `/docs/planning/phases/`)

Phase completion and progress reports:

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

**Action:** `mv <file> /docs/planning/phases/`

---

### SECTION 9: Summary & Index Documents (5 files → `/docs/`)

High-level summaries:

```
Destination: /docs/

COMPREHENSIVE_RESEARCH_CATALOG_COMPLETE.md
MASTER_DOCUMENTS_SUMMARY.txt
RESEARCH_COMPLETE_FINAL_SUMMARY.md
RESEARCH_DELIVERABLES_MANIFEST.txt
RESEARCH_FINDINGS.md
ULTIMATE_MASTER_INDEX_COMPLETE.md
FILE_MANIFEST.txt
```

**Action:** `mv <file> /docs/`

---

### SECTION 10: Setup & Deployment Guides (4 files → `/docs/guides/setup/`)

Setup and deployment documentation:

```
Destination: /docs/guides/setup/

SETUP_GUIDE_LATEST.md
DEPLOYMENT_GUIDE.md
DEV_STATUS.md
README_DEV.md
```

**Action:** `mv <file> /docs/guides/setup/`

---

### SECTION 11: Library & Usage Guides (3 files → `/docs/guides/`)

Reference documentation:

```
Destination: /docs/guides/

LIBRARY_USAGE_GUIDE.md
DELIVERY_SUMMARY.md
EXECUTIVE_SUMMARY.md
```

**Action:** `mv <file> /docs/guides/`

---

### SECTION 12: Architecture & Overview (1 file → `/docs/`)

```
Destination: /docs/

ARCHITECTURE_OVERVIEW_DIAGRAM.md
```

**Action:** `mv <file> /docs/`

---

### SECTION 13: Proposals (12 files → `/docs/research/proposals/`)

OpenSpec proposals:

```
Destination: /docs/research/proposals/

PROPOSAL_01_FASTMCP_2_13_UPGRADE.md
PROPOSAL_02_MULTI_TRANSPORT_AUTH.md
PROPOSAL_03_BASH_ENVIRONMENT.md
PROPOSAL_04_MULTI_LANGUAGE_EXECUTORS.md
PROPOSAL_05_ENHANCED_DISCOVERY.md
PROPOSAL_05_TOOL_DISCOVERY_SEARCH.md
PROPOSAL_06_TOOL_MANAGEMENT_LIFECYCLE.md
PROPOSAL_07_CLAUDE_AGENT_SKILLS.md
PROPOSAL_08_TYPED_TOOL_COMPOSITION.md
PROPOSAL_09_POLYGLOT_STORAGE.md
PROPOSAL_10_ADVANCED_SERVER_FEATURES.md
PROPOSAL_11_CLIENT_PROXY_MIDDLEWARE.md
PROPOSAL_12_MCP_REGISTRY_AUTOMATION.md
```

**Also move:** `openspec_proposals_master.md`

**Action:** `mv <file> /docs/research/proposals/`

---

### SECTION 14: MCP Registry Research (2 files → `/docs/research/mcp-registry/`)

```
Destination: /docs/research/mcp-registry/

MCP_REGISTRY_AUTOMATED_INSTALL_RESEARCH.md
MCP_REGISTRY_RESEARCH_COMPLETE.txt
```

**Action:** `mv <file> /docs/research/mcp-registry/`

---

### SECTION 15: Compilation & Documentation (2 files → `/docs/`)

```
Destination: /docs/

COMPILATION_SUMMARY.txt
DOCUMENTATION_INFRASTRUCTURE_AUDIT_PLAN.md
DOCUMENTATION_INFRASTRUCTURE_MASTER_SUMMARY.md
```

**Action:** `mv <file> /docs/`

---

### SECTION 16: Files to KEEP in Root

These files should remain in root (configuration, entry points, etc.):

```
✅ KEEP IN ROOT:

.github/           # GitHub workflows
Dockerfile         # Container definition
pyproject.toml     # Project metadata
requirements.txt   # Python dependencies
main.py            # Entry point
mkdocs.yml         # Documentation config
.env               # Environment
.gitignore         # Git config
.pre-commit-config.yaml
apply_p0_fixes.sh  # Utility script
tunnel_config.json # Configuration
infra_common.py    # Common infrastructure
migrate_cache_metrics.py
```

---

### SECTION 17: Files to ARCHIVE (12 files → `/archive/`)

Obsolete or completed session files:

```
Destination: /archive/

(Files that are marked as "COMPLETE" or session-specific)

Look for:
- Files with "COMPLETE" or "FINAL" that are outdated
- Session-specific analysis files
- Duplicate documentation

Examples:
- Various "*_COMPLETE.md" files that predate newer versions
- Migration reports from completed work
```

---

## 📋 Execution Steps

### Step 1: Create Target Directories
```bash
mkdir -p /docs/planning/phases
mkdir -p /docs/research/database
mkdir -p /docs/research/routing
mkdir -p /docs/research/claude-integration
mkdir -p /docs/research/discovery
mkdir -p /docs/research/proposals
mkdir -p /docs/research/mcp-registry
mkdir -p /docs/guides/setup
mkdir -p /zen-mcp-server/docs/research
```

### Step 2: Execute Moves by Section

For each section above, run:
```bash
# Example for planning files:
mv /docs/planning/* /docs/planning/  # Already there
mv 00_MASTER_INDEX.md /docs/planning/
mv 00_START_HERE.md /docs/planning/
# ... etc

# Example for research:
mv LOCAL_CLOUD_DATABASE_OPTIONS.md /docs/research/database/
mv DOCKER_COMPOSE_LOCAL_STACK.md /docs/research/database/
# ... etc
```

### Step 3: Verify and Update References

After moving files:
1. Update any relative import paths in code
2. Update `mkdocs.yml` with new file locations
3. Test documentation links: `mkdocs serve`
4. Verify git status: `git status`

### Step 4: Commit Changes

```bash
git add -A
git commit -m "refactor: reorganize root documentation into logical structure

- Move planning documents to /docs/planning/
- Move research documents to /docs/research/<domain>/
- Move phase reports to /docs/planning/phases/
- Move proposals to /docs/research/proposals/
- Move FastMCP-specific docs to zen-mcp-server/docs/research/
- Keep only essential root files (config, entry points, utilities)

This improves discoverability and maintainability of documentation."
```

---

## 🗂️ Target Folder Structure (After Moves)

```
root/
├── CLAUDE.md                          # Keep - Project guidelines
├── AGENTS.md                          # Keep - Agent guidelines
├── Dockerfile                         # Keep - Container def
├── main.py                            # Keep - Entry point
├── pyproject.toml                     # Keep - Project config
├── requirements.txt                   # Keep - Dependencies
├── apply_p0_fixes.sh                  # Keep - Utility
├── mkdocs.yml                         # Keep - Docs config
│
├── .github/                           # Keep - Workflows
├── .venv/                             # Keep - Virtual env
├── docs/                              # All documentation
│   ├── planning/
│   │   ├── 00_MASTER_INDEX.md
│   │   ├── 01_PROJECT_PLAN.md
│   │   ├── 02_PRODUCT_REQUIREMENTS.md
│   │   ├── 03_WORK_BREAKDOWN_STRUCTURE.md
│   │   ├── MASTER_IMPLEMENTATION_PLAN.md
│   │   ├── EXECUTION_CHECKLIST.md
│   │   ├── phases/
│   │   │   ├── PHASE_1_FINAL_SUMMARY.txt
│   │   │   ├── PHASE_2_IMPLEMENTATION_COMPLETE.md
│   │   │   └── ... (all phase reports)
│   │   └── ... (all planning docs)
│   ├── research/
│   │   ├── database/
│   │   │   ├── LOCAL_CLOUD_DATABASE_OPTIONS.md
│   │   │   ├── POSTGRES_PGVECTOR_FTS_GUIDE.md
│   │   │   └── ... (database research)
│   │   ├── routing/
│   │   │   ├── AUTO_ROUTER_MLX_ARCH_GUIDE.md
│   │   │   └── ... (routing research)
│   │   ├── claude-integration/
│   │   │   ├── CLAUDE_AGENT_SKILLS_RESEARCH.md
│   │   │   └── ... (Claude research)
│   │   ├── discovery/
│   │   ├── proposals/
│   │   │   ├── PROPOSAL_01_*.md
│   │   │   └── ... (all proposals)
│   │   ├── mcp-registry/
│   │   └── ... (research summaries)
│   ├── guides/
│   │   ├── setup/
│   │   │   ├── SETUP_GUIDE_LATEST.md
│   │   │   └── DEPLOYMENT_GUIDE.md
│   │   └── ... (other guides)
│   └── README.md
│
├── zen-mcp-server/                    # FastMCP server
│   ├── docs/
│   │   ├── research/
│   │   │   ├── FASTMCP_COMPLETE_ANALYSIS_SUMMARY.md
│   │   │   └── ... (FastMCP research)
│   │   └── ... (existing docs)
│   └── ... (existing structure)
│
├── 4sgm/                              # E-commerce project
├── crun/                              # Planning/CLI tool
├── bloc/                              # Code analysis tool
├── router/                            # Routing engine
└── ... (other project folders)
```

---

## ✅ Verification Checklist

After completing moves:

- [ ] All destination directories created
- [ ] All files moved to appropriate folders
- [ ] No duplicate files in root or destination folders
- [ ] `mkdocs.yml` updated with new paths
- [ ] Relative imports still work
- [ ] Git tracks all moves (not deletes + adds)
- [ ] Documentation links are valid: `mkdocs serve`
- [ ] All tests pass: `uv run pytest`
- [ ] Commit created with clear message

---

## 📊 Summary Statistics

| Metric | Count |
|--------|-------|
| **Total files to move** | 100+ |
| **Planning files** | 15 |
| **Research files** | 35 |
| **Phase reports** | 12 |
| **Proposal files** | 13 |
| **Guide files** | 10 |
| **Archive candidates** | 12 |
| **Files to keep in root** | ~20 |

---

## 🎯 Impact

**Benefits:**
- ✅ Cleaner root directory (easier to navigate)
- ✅ Better documentation organization
- ✅ Easier to find relevant research/plans
- ✅ Clear separation by domain (database, routing, Claude, etc.)
- ✅ Project-specific docs stay with their projects
- ✅ Improved discoverability for new contributors

**No Breaking Changes:**
- All functionality remains the same
- Only file organization changes
- All imports and configs update accordingly
