# Final Cleanup: Move Remaining Files to Project Homes
**Date:** 2025-11-22  
**Status:** Phase 2 Planning  
**Goal:** Root directory contains ONLY project folders (no shared /docs/ or .md files)

---

## 📊 Current Situation

Root still has:
1. **5 Audit/Move Documentation Files** in root
   - AGENTS.md
   - CLAUDE.md
   - AUDIT_DOCUMENTS.md
   - MOVE_EXECUTION_SUMMARY.md
   - ROOT_FILE_AUDIT_AND_MOVE_PLAN.md
   - ROOT_FILES_MOVE_CORRECTED.md
   - ROOT_FILES_MOVE_TO_PROJECTS.md

2. **docs/ Folder** (cross-project - should not exist!)
   - /docs/planning/
   - /docs/research/
   - /docs/guides/

3. **Many non-project folders** that appear to be utilities/shared

---

## 🎯 Where Audit Files Should Go

The 4 audit documents should move into a project that owns research/documentation:

### Option 1: **dphi**
- Has `openspec/` structure
- Has comprehensive documentation
- Recently modified (2025-11-21)
- Good fit for documentation oversight

### Option 2: **pheno-sdk**
- Foundational framework
- Has extensive docs/
- Owns infrastructure research
- Could house audit trail

### Option 3: **smartcp**
- Owns tool composition research
- Has openspec/ for proposals
- Recently active

---

## 🎯 Where /docs/ Folder Content Goes

Since `/docs/` is cross-project and should not exist, ALL content must move to appropriate projects:

### /docs/planning/ (13 files)
```
00_MASTER_INDEX.md → dphi/ or pheno-sdk/
00_START_HERE.md → root entry point (DELETE or move to main project)
01_PROJECT_PLAN.md → trace/ or dphi/
02_PRODUCT_REQUIREMENTS.md → trace/ or dphi/
03_WORK_BREAKDOWN_STRUCTURE.md → trace/ or dphi/
04_LATEST_VERSIONS_2025.md → pheno-sdk/ (version control)
MASTER_IMPLEMENTATION_PLAN.md → trace/ (project orchestration)
MASTER_WBS_SPECIFICATION.md → trace/ (WBS management)
IMPLEMENTATION_ROADMAP.md → trace/
OPENSPEC_PROPOSALS_INDEX.md → smartcp/
README_OPENSPEC_PROPOSALS.md → smartcp/
OPTIMIZED_PLAN_WITH_EXISTING_LIBS.md → pheno-sdk/
EXECUTION_CHECKLIST.md → trace/
```

### /docs/research/ (35 files)
```
database/ → pheno-sdk/docs/research/database/
routing/ → router/docs/research/
claude-integration/ → smartcp/docs/research/claude-integration/
proposals/ → smartcp/docs/research/proposals/
mcp-registry/ → smartcp/docs/research/mcp-registry/
discovery/ → smartcp/docs/research/discovery/
```

### /docs/guides/setup/ (6 files)
```
SETUP_GUIDE_LATEST.md → pheno-sdk/
DEPLOYMENT_GUIDE.md → atoms-mcp-prod/ or agentapi/
DEV_STATUS.md → pheno-sdk/
README_DEV.md → pheno-sdk/
DELIVERY_SUMMARY.md → trace/
LIBRARY_USAGE_GUIDE.md → pheno-sdk/
```

### /docs/ (7 summary files)
```
COMPREHENSIVE_RESEARCH_CATALOG_COMPLETE.md → trace/
RESEARCH_COMPLETE_FINAL_SUMMARY.md → trace/
RESEARCH_FINDINGS.md → trace/
ULTIMATE_MASTER_INDEX_COMPLETE.md → trace/
DOCUMENTATION_INFRASTRUCTURE_AUDIT_PLAN.md → trace/
DOCUMENTATION_INFRASTRUCTURE_MASTER_SUMMARY.md → trace/
EXECUTIVE_SUMMARY.md → trace/
```

---

## ✅ Root Should Contain ONLY This

```
/kush/
├── 4sgm/                    (project)
├── agentapi/                (project)
├── atoms-mcp-prod/          (project)
├── bloc/                    (project)
├── crun/                    (project)
├── dphi/                    (project)
├── kimaki/                  (project)
├── morph/                   (project)
├── pheno-sdk/               (project)
├── router/                  (project)
├── smartcp/                 (project)
├── task-tool/               (project)
├── task2/                   (project)
├── trace/                   (project)
├── usage/                   (project)
├── zen-mcp-server/          (project)
├── .github/                 (GitHub config)
├── .venv/                   (virtual env)
├── pyproject.toml           (root project config)
├── requirements.txt         (root dependencies)
├── mkdocs.yml              (documentation config - DELETE if cross-project)
├── Dockerfile              (container config)
└── (other essential config files)
```

---

## 🗑️ Delete (No Project Home)

These should be DELETED as they're meta-documentation of the move process:
- AUDIT_DOCUMENTS.md
- MOVE_EXECUTION_SUMMARY.md
- ROOT_FILE_AUDIT_AND_MOVE_PLAN.md
- ROOT_FILES_MOVE_CORRECTED.md
- ROOT_FILES_MOVE_TO_PROJECTS.md
- FINAL_CLEANUP_PLAN.md (this file)

OR move to `/archive/` if you want to preserve move history

---

## 📋 Execute Plan

### Step 1: Delete /docs/ folder
```bash
rm -rf /docs/
```

### Step 2: Move Audit Documents
```bash
# Option: Move to dphi (documentation keeper)
mv AUDIT_DOCUMENTS.md dphi/
mv MOVE_EXECUTION_SUMMARY.md dphi/
mv ROOT_FILE_AUDIT_AND_MOVE_PLAN.md dphi/
mv ROOT_FILES_MOVE_CORRECTED.md dphi/
mv ROOT_FILES_MOVE_TO_PROJECTS.md dphi/

# Or archive them
mv AUDIT_DOCUMENTS.md archive/
# ... etc
```

### Step 3: Verify Root
```bash
ls -1 | grep -E "\.md$|^[a-z]" | grep -v "^[.a-z]"
# Should only show project folders
```

---

## 🤔 Question: What are these folders?

Some root folders don't seem to be "projects" - they seem to be utilities:

| Folder | Purpose? | Should Keep? |
|--------|----------|--------------|
| **agent** | Empty (2 files) | ❓ Delete? |
| **archive** | Historical archive | ✅ Keep |
| **build** | Build artifacts | ? |
| **changes** | Change tracking | ✅ Keep (index of changes) |
| **claude-squad** | Multi-agent framework | ✅ Keep (project) |
| **config** | Shared config | ? Move to trace/ |
| **data** | Test/seed data | ? Move to trace/ |
| **example** | Examples | ? Move to trace/ |
| **hooks** | Git hooks | ✅ Keep (shared) |
| **infrastructure** | Shared infrastructure | ? Move to trace/ |
| **k8s** | Kubernetes configs | ? Move to trace/ |
| **opencode-openai-codex-auth** | Auth library | ✅ Keep (project) |
| **portfolio** | Portfolio project | ✅ Keep (project) |
| **scripts** | Shared scripts | ? Move to trace/ |
| **services** | Shared services | ? Move to trace/ |
| **templates** | Shared templates | ? Move to trace/ |
| **tests** | Root tests | ? Move to trace/ |
| **tmp** | Temporary | ✅ Delete |
| **usage** | CLI usage tracking | ✅ Keep (project) |
| **krystal** | ? Unknown | ❓ |
| **crun-gui** | GUI variant | Maybe merge with crun? |

---

## 🎯 Recommended Final Root Structure

```
/kush/
├── ACTUAL PROJECTS:
│   ├── 4sgm/
│   ├── agentapi/
│   ├── atoms-mcp-prod/
│   ├── bloc/
│   ├── claude-squad/
│   ├── crun/
│   ├── dphi/
│   ├── kimaki/
│   ├── morph/
│   ├── opencode-openai-codex-auth/
│   ├── pheno-sdk/
│   ├── portfolio/
│   ├── router/
│   ├── smartcp/
│   ├── task-tool/
│   ├── task2/
│   ├── trace/          (orchestration/meta project)
│   ├── usage/
│   └── zen-mcp-server/
│
├── SHARED INFRASTRUCTURE:
│   ├── .github/        (GitHub workflows)
│   ├── hooks/          (Git hooks)
│   ├── archive/        (Historical)
│   ├── changes/        (Change tracking)
│   └── .venv/          (Virtual environment)
│
├── CONFIG:
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── Dockerfile
│   └── (other root configs)
│
└── CLEANUP/DELETE:
    ├── tmp/            (DELETE)
    ├── agent/          (DELETE if empty)
    ├── build/          (DELETE if artifacts)
    ├── config/         (Move to trace/)
    ├── data/           (Move to trace/)
    ├── example/        (Move to trace/)
    ├── infrastructure/ (Move to trace/)
    ├── k8s/            (Move to trace/)
    ├── scripts/        (Move to trace/)
    ├── services/       (Move to trace/)
    ├── templates/      (Move to trace/)
    └── tests/          (Move to trace/)
```

---

## ⚠️ Critical Decision Needed

**To complete the cleanup, you need to decide:**

1. **What is `trace/`?**
   - Is it a meta-project for orchestration/planning?
   - Should it contain: config/, data/, scripts/, services/, templates/, tests/?

2. **What about utility folders?**
   - Should shared infrastructure go in a utility project?
   - Or stay at root but clearly marked as "shared"?

3. **Root Documentation:**
   - Should there be a root README.md explaining the structure?
   - Or should each project be self-documenting?

**Answer these, and I can execute the final cleanup!**

---

## 🎯 Immediate Action (No Decisions Needed)

If you just want to make root clean NOW:

```bash
# Delete cross-project docs folder
rm -rf /docs/

# Move audit files to archive (preserve them)
mv AUDIT_DOCUMENTS.md archive/
mv MOVE_EXECUTION_SUMMARY.md archive/
mv ROOT_FILE_AUDIT_AND_MOVE_PLAN.md archive/
mv ROOT_FILES_MOVE_CORRECTED.md archive/
mv ROOT_FILES_MOVE_TO_PROJECTS.md archive/
mv FINAL_CLEANUP_PLAN.md archive/

# Keep only essential root files
# AGENTS.md, CLAUDE.md should stay (project guidelines)
```

**Then root will only have projects + archive + .github + .venv + config files** ✅

---

## 🚀 Decision: Execute Immediate Action?

Shall I:
- ✅ Delete /docs/ folder?
- ✅ Archive the audit files?
- ✅ Clean up obvious artifacts (tmp/, build/)?
- ⏳ Wait for your guidance on utility folders (config/, data/, etc.)?

---

**Status:** Awaiting decision on utility folder organization
