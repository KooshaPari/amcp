# Phase 4 Week 0 Kickstart: Foundation Encapsulation

**Session ID:** 20251202-foundation-encapsulation
**Phase:** Phase 4 - Bifrost + SmartCP SDK Encapsulation
**Timeline:** 4-5 weeks to stable foundation
**Date:** December 2, 2025
**Status:** 🚀 LAUNCHING NOW

---

## Quick Status

**Research Complete:** ✅
- Bifrost extensions audited (359 files, 88k LOC understood)
- SmartCP implementation audited (monolith identified)
- Codex CLI evaluated (don't fork, build Python)
- Foundation strategy designed (SDK architecture clear)

**Decision Made:** ✅
- Python+LangGraph for agent-cli (NOT Rust)
- Foundation-first approach (4-5 weeks before agent-cli)
- Bifrost SDK + SmartCP SDK encapsulation parallel tracks

**Ready to Build:** ✅ LET'S GO!

---

## Phase 4 Overview

### Two Parallel Tracks

**Track A: Bifrost SDK** (3-4 weeks)
- Encapsulate router/router_core/ into stable SDK
- Create `GatewayClient` public API
- Team: 2-3 engineers

**Track B: SmartCP SDK** (2-3 weeks, starts Week 3)
- Refactor to thin MCP frontend (<1000 LOC)
- Complete GraphQL integration with Bifrost
- Team: 2-3 engineers

**Total:** 4-5 weeks, 4-6 engineers

---

## Week 0 Checklist (This Week)

### Track 1: Team Assignment (Day 1)

- [ ] **Assign Bifrost Team Lead** (Senior Python engineer, async expertise)
- [ ] **Assign SmartCP Team Lead** (MCP protocol + GraphQL experience)
- [ ] **Assign 2-3 engineers to Bifrost team**
- [ ] **Assign 2-3 engineers to SmartCP team** (start Week 3)

### Track 2: Environment Setup (Days 1-2)

**Per Engineer:**
```bash
# Clone and setup
cd /Users/kooshapari/temp-PRODVERCEL/485/API/smartcp
source .venv/bin/activate  # Or create if needed

# Verify dependencies
pip install -r requirements.txt

# Verify router_core works
python -c "from router.router_core import RoutingService; print('✅ Bifrost imports working')"

# Verify SmartCP works
python -c "from fastmcp import FastMCP; print('✅ SmartCP imports working')"

# Run existing tests
pytest tests/ -v --tb=short
```

- [ ] All engineers have working Python environment
- [ ] All can import router/router_core/ successfully
- [ ] All can run existing tests

### Track 3: Documentation Review (Days 2-3)

**Required Reading (Bifrost Team):**
- [ ] `docs/sessions/20251202-bifrost-extensions-audit/32_BIFROST_EXTENSIONS_ARCHITECTURE_AUDIT.md`
- [ ] `docs/35_FOUNDATION_ENCAPSULATION_STRATEGY.md` (Bifrost SDK section)
- [ ] `router/router_core/NAMING_STANDARDS.md` (existing standards)

**Required Reading (SmartCP Team):**
- [ ] `docs/sessions/20251202-smartcp-audit/33_SMARTCP_MCP_IMPLEMENTATION_AUDIT.md`
- [ ] `docs/35_FOUNDATION_ENCAPSULATION_STRATEGY.md` (SmartCP SDK section)
- [ ] FastMCP 2.13 documentation

**Required Reading (All):**
- [ ] `docs/sessions/20251202-agent-layer-research/36_FOUNDATION_FIRST_STRATEGY.md`
- [ ] `CLAUDE.md` (agent contract)

### Track 4: Design Review (Days 3-4)

**Bifrost SDK API Design:**
```python
# Proposed GatewayClient API - Review & Feedback
from bifrost_extensions import GatewayClient, RoutingStrategy

client = GatewayClient()

# Model routing
response = await client.route(
    messages=[...],
    strategy=RoutingStrategy.COST_OPTIMIZED
)

# Tool routing
tool = await client.route_tool(
    action="search web",
    available_tools=[...]
)

# Classification
category = await client.classify(prompt="...")
```

- [ ] **API Review:** Team review proposed API
- [ ] **Feedback:** Collect suggestions for improvements
- [ ] **Finalize:** Lock API design before coding

**SmartCP SDK API Design:**
```python
# Proposed APIs - Review & Feedback
from smartcp import MCPServer, ToolClient, BifrostClient

# MCP Server
server = MCPServer(port=8000, bifrost_url="...")
await server.start()

# Tool Client
client = ToolClient()
result = await client.execute_tool(name="file_read", params={...})

# Bifrost Integration
bifrost = BifrostClient(graphql_url="...")
tools = await bifrost.query_tools(filters={...})
```

- [ ] **API Review:** Team review proposed API
- [ ] **GraphQL Schema:** Design Bifrost queries/mutations for SmartCP
- [ ] **Finalize:** Lock API design

### Track 5: Repository Setup (Day 4-5)

**Create SDK Package Structures:**

```bash
# Bifrost SDK package
mkdir -p bifrost_extensions/{routing,providers,config}
touch bifrost_extensions/__init__.py
touch bifrost_extensions/client.py
touch bifrost_extensions/models.py
touch bifrost_extensions/exceptions.py

# SmartCP SDK reorganization (Week 3)
# Will extract from existing mcp_*.py files

# Tests
mkdir -p tests/sdk/{bifrost,smartcp}
touch tests/sdk/bifrost/test_client.py
touch tests/sdk/smartcp/test_client.py
```

- [ ] Directory structure created
- [ ] Package __init__.py files created
- [ ] Test directories ready

### Track 6: Communication Setup (Day 5)

**Channels:**
- [ ] Create Slack channel: `#phase4-foundation`
- [ ] Schedule daily standups: 10 AM, 15 min (team leads)
- [ ] Schedule weekly syncs: Friday 2 PM, 1 hour (full team)
- [ ] Create GitHub Projects board for task tracking

**Documentation:**
- [ ] Create session folder: `docs/sessions/20251202-foundation-encapsulation/`
- [ ] Copy this kickstart document there
- [ ] Create `01_BIFROST_SDK_PROGRESS.md` (living doc)
- [ ] Create `02_SMARTCP_SDK_PROGRESS.md` (living doc)

---

## Week 1 Start (Monday)

### Bifrost Team Kickoff (9:00 AM)

**Monday Morning:**
- 9:00 AM: Team standup, assign Week 1 tasks
- 9:30 AM: Begin Task 1.1 (GatewayClient scaffold)

**Week 1 Goals:**
- ✅ GatewayClient class created with API surface
- ✅ Basic route() method working (single model)
- ✅ Pydantic request/response models
- ✅ Unit tests for route()
- ✅ OpenTelemetry spans added

**Week 1 Tasks:**
1. Create `bifrost_extensions/client.py` (GatewayClient)
2. Create `bifrost_extensions/models.py` (Request/Response models)
3. Implement `route()` method (basic, no strategies yet)
4. Add observability (OpenTelemetry)
5. Write unit tests (mock routing logic)
6. Initial documentation

---

## Success Criteria (Week 0 → Week 1)

**By Friday EOD:**
- ✅ Teams assigned and briefed
- ✅ All environments working
- ✅ All documentation reviewed
- ✅ API designs finalized
- ✅ Repository structure ready
- ✅ Communication channels active
- ✅ No blockers for Week 1 start

**Monday 9 AM (Week 1 Start):**
- ✅ Bifrost team begins Task 1.1
- ✅ Daily standups operational
- ✅ Phase 4 foundation work underway

---

## Quick Reference

### Key Documents
1. **This Kickstart:** `00_PHASE_4_WEEK_0_KICKSTART.md`
2. **Bifrost Audit:** `docs/sessions/20251202-bifrost-extensions-audit/32_BIFROST_EXTENSIONS_ARCHITECTURE_AUDIT.md`
3. **SmartCP Audit:** `docs/sessions/20251202-smartcp-audit/33_SMARTCP_MCP_IMPLEMENTATION_AUDIT.md`
4. **SDK Design:** `docs/35_FOUNDATION_ENCAPSULATION_STRATEGY.md`
5. **Overall Strategy:** `docs/sessions/20251202-agent-layer-research/36_FOUNDATION_FIRST_STRATEGY.md`

### Slack Channels
- `#phase4-foundation` - Main coordination
- `#phase4-blockers` - Escalations

### Key Contacts
- **Phase 4 Lead:** [Assign in Week 0]
- **Bifrost Team Lead:** [Assign in Week 0]
- **SmartCP Team Lead:** [Assign in Week 0]

---

**Status: READY FOR PHASE 4** ✅

**Let's build the foundation!** 🚀
