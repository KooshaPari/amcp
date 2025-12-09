# SmartCP – Epic / PRD Index

**Purpose:** connect SmartCP core + SmartCP router to the unified
Epics/PRDs in this repo.

- Canonical backlog: `plans/012-epics-backlog.md`
- Canonical architecture: `docs/reference/UNIFIED_ARCHITECTURE.md`
- Epic PRDs: `docs/unified-specifications/E*.md`

---

## 1. Epic Mapping for SmartCP

| Epic | Name                                    | Canonical PRD                                                                 | SmartCP Scope (local)                                           |
|------|-----------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------|
| E3   | ML Routing Brain                        | `../../docs/unified-specifications/E3_ROUTING_BRAIN_PRD.md`                  | `smartcp/router/`, `smartcp/optimization/model_router.py`       |
| E5   | Tool Routing & Context Folding          | `../../docs/unified-specifications/E5_TOOL_ROUTING_CONTEXT_PRD.md`           | `smartcp/router/`, `smartcp/mcp_tool_*`, `smartcp/middleware_system.py` |
| E8   | Capability Registry & Semantic Profiles | `../../docs/unified-specifications/E8_CAPABILITY_REGISTRY_PRD.md`            | `smartcp/neo4j_storage_adapter.py`, `smartcp/vector_graph_db.py`|
| E9   | Deep Research & Knowledge Base          | `../../docs/unified-specifications/E9_DEEP_RESEARCH_KB_PRD.md`               | `smartcp/hierarchical_memory.py`, `smartcp/learning_system.py`  |
| E10  | Planner / Blackboard Orchestration      | `../../docs/unified-specifications/E10_PLANNER_BLACKBOARD_PRD.md`            | Planner/blackboard not yet implemented; see DSL + learning code |
| E11  | Observability & Telemetry               | `../../docs/unified-specifications/E11_OBSERVABILITY_TELEMETRY_PRD.md`       | Logging/metrics hooks in SmartCP router and services            |

---

## 2. Local Documentation Anchors

- SmartCP docs index: `smartcp/docs/README.md`
- SmartCP reference index: `smartcp/docs/reference/SMARTCP_MASTER_INDEX.md`
- Router docs index: `smartcp/router/CONSOLIDATION_INDEX.md` (and related files)

Use this file to jump from **Epics/PRDs → concrete SmartCP code and docs**.

