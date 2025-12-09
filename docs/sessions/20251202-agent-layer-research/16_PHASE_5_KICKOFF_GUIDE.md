# Phase 5 Implementation Kickoff Guide
**Status:** Ready for Week 1 Launch
**Date:** December 2, 2025
**Duration:** 8 weeks (4 feature teams)

---

## Quick Start (Week 0 - Preparation)

### 1. Development Environment Setup (2 hours)

```bash
# Clone and setup
cd smartcp
git checkout main
git pull origin main

# Setup Python environment
python3.10 -m venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Verify setup
python cli.py --help
python cli.py test run --scope unit  # Should pass Phase 3/4 tests

# Optional: Install additional Phase 5 dependencies
uv pip install "langraph==0.0.30"  # For orchestration (optional)
uv pip install "pytest-asyncio"     # For async tests
uv pip install "docker"             # For containerization
```

### 2. Create Feature Branches (Team Leads)

```bash
# Team 1: Core 1 + Core 2 (Agent Framework + Context Management)
git checkout -b phase5-core1-core2

# Team 2: Core 3 + Core 4 (APIs)
git checkout -b phase5-core3-core4

# Team 3: Core 5 (Terminal UI)
git checkout -b phase5-core5-ui

# Team 4: Core 6 (Integration & Testing)
git checkout -b phase5-core6-integration
```

### 3. Directory Structure for Phase 5

```
src/smartcp/
├── agents/                          # NEW: Core 1 (Agent Framework)
│   ├── __init__.py
│   ├── base.py                      # Abstract agent base class
│   ├── types.py                     # Agent types and enums
│   ├── exceptions.py                # Agent-specific exceptions
│   ├── factory.py                   # Agent instantiation factory
│   ├── coordinator.py               # Multi-agent coordination
│   ├── pool.py                      # Agent resource pooling
│   └── health.py                    # Health checking
│
├── context/                         # NEW: Core 2 (Context Management)
│   ├── __init__.py
│   ├── project.py                   # Project abstraction
│   ├── manager.py                   # CWD and state management
│   ├── inference.py                 # CWD inference algorithms
│   └── state.py                     # State snapshots/persistence
│
├── api/                             # ENHANCED: Core 3 + Core 4
│   ├── routes/
│   │   ├── agents/                  # NEW: Agent-optimized API
│   │   │   ├── __init__.py
│   │   │   ├── control.py           # Agent control endpoints
│   │   │   ├── tools.py             # Tool invocation API
│   │   │   ├── sessions.py          # Session management
│   │   │   └── streaming.py         # Streaming support
│   │   ├── openai/                  # ENHANCED: LLM-compatible API
│   │   │   ├── __init__.py
│   │   │   ├── chat.py              # Chat completions endpoint
│   │   │   ├── models.py            # Model listing
│   │   │   └── compat.py            # Compatibility layer
│   │   └── ...
│   └── middleware/
│       ├── authentication.py
│       ├── error_handling.py
│       └── rate_limiting.py
│
├── ui/                              # NEW: Core 5 (Terminal UI)
│   ├── __init__.py
│   ├── app.py                       # Main Ink.js app
│   ├── components/
│   │   ├── chat.tsx                 # Chat interface
│   │   ├── agent_status.tsx         # Agent monitor
│   │   ├── tool_panel.tsx           # Tool execution
│   │   └── logs.tsx                 # Log viewer
│   └── styles/
│       └── theme.ts
│
├── server.py                        # UPDATED: Server entrypoint (Phase 5)
├── main.py                          # UPDATED: CLI entrypoint
└── ...
```

### 4. Initial Project Structure (Run Once)

```bash
# Create agent layer directories
mkdir -p src/smartcp/{agents,context,ui}

# Create __init__.py files
touch src/smartcp/agents/__init__.py
touch src/smartcp/context/__init__.py
touch src/smartcp/ui/__init__.py

# Create test directories
mkdir -p tests/unit/{agents,context,api}
mkdir -p tests/integration/agents
```

### 5. GitHub Issue/PR Template (Team Leads)

Each Core should have:
- **Epic Issue**: Core overview and acceptance criteria
- **Task Issues**: Breakdown by task (Task 1.1, 1.2, etc.)
- **PR Reviews**: Team code reviews before merging to main

---

## Team Structure & Responsibilities

### Team 1: Agent Framework & Orchestration (Weeks 1-3)

**Lead:** [Name]
**Members:** 3-4 engineers
**Focus:** Cores 1 + 2

**Week 1:**
- Task 1.1: Base agent classes
- Task 1.2: Agent factory
- Task 1.3: Resource pooling
- Testing & code review

**Week 2:**
- Task 1.4: Lifecycle management
- Task 1.5: State persistence
- Task 1.6: Integration tests
- Code freeze for Core 1

**Week 3:**
- Task 2.1-2.5: Context management
- CWD inference & testing
- Handoff to Team 2

### Team 2: API Layers (Weeks 3-5)

**Lead:** [Name]
**Members:** 2-3 engineers
**Focus:** Cores 3 + 4

**Week 3:**
- Design API contracts (review Phase 5 plan)
- Setup FastAPI routers
- Begin Core 3 (Agent API)

**Week 4:**
- Task 3.1-3.6: Complete Agent API
- Task 4.1-4.5: LLM-compatible API
- Compatibility testing

**Week 5:**
- Integration with Core 1 + 2
- Streaming support
- Error handling

### Team 3: Terminal UI (Weeks 5-7)

**Lead:** [Name]
**Members:** 2-3 engineers
**Focus:** Core 5

**Week 5:**
- Ink.js environment setup
- Component architecture design
- Begin chat component

**Week 6:**
- Agent status monitor
- Tool execution panel
- Log viewer

**Week 7:**
- Performance optimization
- UX polish
- Integration tests

### Team 4: Integration & Testing (Weeks 7-8)

**Lead:** [Name]
**Members:** 2-3 engineers
**Focus:** Core 6

**Week 7:**
- SWE Bench integration
- Multi-agent coordination tests
- Performance baseline

**Week 8:**
- End-to-end testing
- Documentation
- Production readiness

---

## Daily Standups & Syncs

### Daily Standup (15 min, 10:00 AM)

**Format:** Each team lead reports
- What we completed yesterday
- What we're doing today
- Blockers or help needed

**Location:** [Zoom link]
**Attendees:** All team leads + stakeholders

### Weekly Sync (1 hour, Friday 2:00 PM)

**Agenda:**
1. Weekly progress review (20 min)
2. Cross-team dependencies (15 min)
3. Blockers & escalations (15 min)
4. Next week planning (10 min)

**Owner:** Project manager / Phase 5 lead

### Code Review Process

1. **Task completion**: Create PR when task done
2. **Team code review**: At least 1 team member
3. **Integration review**: Tech lead or PM (for cross-team)
4. **Merge**: Only after all reviews approved + tests passing

---

## Testing Strategy

### Unit Tests (Per Task)

- Minimum 80% coverage
- Use `pytest` + `pytest-asyncio` for async
- Run before every commit

```bash
python cli.py test run --scope unit
```

### Integration Tests (Per Core)

- Test interactions between components
- Use in-memory implementations where possible
- Run after core completion

```bash
python cli.py test run --scope integration
```

### Performance Tests (Phase 6+)

- SWE Bench baseline (Week 7, Core 6)
- Memory profiling
- Load testing
- Latency benchmarks

```bash
python cli.py test run --scope performance
```

---

## Documentation Requirements

### Per Task

- Inline code comments (complex logic only)
- Docstrings for public functions/classes
- Type annotations (all parameters and returns)

### Per Core (Completion)

- Architecture doc: How the core works
- API doc: If applicable (Cores 3, 4, 5)
- Integration guide: How to use from other cores

### Phase 5 Completion

- Deployment guide
- Configuration reference
- Troubleshooting guide

---

## CI/CD & Testing Gates

### Pre-Commit Hooks

```bash
# Format check (Ruff)
python cli.py format --check

# Lint check
python cli.py lint check

# Type check
python cli.py types check

# Unit tests (optional, but recommended)
python cli.py test run --scope unit
```

### PR Checks (GitHub Actions)

1. ✅ Lint + Format
2. ✅ Type checking
3. ✅ Unit tests (80%+ coverage)
4. ✅ Integration tests (if applicable)
5. ✅ Build success

### Merge Requirements

- ✅ All PR checks passing
- ✅ At least 1 team review approval
- ✅ All conversations resolved
- ✅ Branch up-to-date with main

---

## Dependency Management

### External Dependencies (Phase 5)

```python
# Required
fastapi>=0.100.0
pydantic>=2.0
asyncio-contextmanager
pytest>=7.0
pytest-asyncio

# Optional (for orchestration)
langraph>=0.0.30  # DAG-based workflows

# Optional (for containerization)
docker>=6.0

# Optional (for observability)
langfuse>=2.0  # Integrate in Core 6
```

### Adding New Dependencies

1. Add to `pyproject.toml` or `requirements-phase5.txt`
2. Run `uv pip install -e ".[dev]"`
3. Document in Phase 5 setup
4. Get approval from tech lead

---

## Progress Tracking

### Burndown Chart Template

```
Week 1: Expected 75 hours complete (out of 300)
Week 2: Expected 150 hours complete
Week 3: Expected 187 hours complete
Week 4: Expected 225 hours complete
Week 5: Expected 255 hours complete
Week 6: Expected 280 hours complete
Week 7: Expected 295 hours complete
Week 8: Expected 300 hours complete (DONE)
```

### Status Dashboard

- GitHub Projects board (Kanban: Todo → In Progress → Review → Done)
- Weekly velocity tracking
- Blocker log
- Risk register

---

## Risk Mitigation During Implementation

### If Behind Schedule

1. **Parallelize cores** (e.g., Teams 2/3 start early)
2. **Reduce scope** (cut UI polish, move to Phase 6)
3. **Add resources** (cross-train additional engineers)
4. **Extend timeline** (negotiate with stakeholders)

### If Technical Blocker Found

1. **Escalate immediately** (don't wait for standup)
2. **Engage tech lead** for architectural guidance
3. **Adjust plan** if fundamental assumption invalid
4. **Document decision** in 05_KNOWN_ISSUES.md

### If Performance Issues

1. **Profile early** (Week 2, not Week 8)
2. **Benchmark against targets** (per Core)
3. **Adjust architecture** if needed
4. **SWE Bench baseline** in Week 7 (gives early warning)

---

## Success Criteria (Per Core)

### Core 1: Agent Framework
- ✅ 100 agents spawn in <30 seconds
- ✅ Each agent init <200ms
- ✅ 80%+ test coverage
- ✅ Health checks passing
- ✅ No memory leaks (24h test)

### Core 2: Context Management
- ✅ CWD inference >95% accuracy
- ✅ State snapshots working
- ✅ Multi-project support
- ✅ File operations scoped correctly

### Core 3 & 4: APIs
- ✅ Agent API fully functional
- ✅ OpenAI compatibility tests passing
- ✅ Streaming support working
- ✅ Session management reliable

### Core 5: Terminal UI
- ✅ Responsive (<100ms p99)
- ✅ Supports 50+ concurrent agents
- ✅ All components working
- ✅ UX polished

### Core 6: Integration
- ✅ End-to-end working
- ✅ SWE Bench baseline established
- ✅ >80% test coverage
- ✅ Production ready

---

## Reference Materials

- **Phase 5 Plan:** `13_PHASE_5_DETAILED_IMPLEMENTATION_PLAN.md` (task breakdown)
- **Epics & Stories:** `14_EPICS_FUNCTIONAL_REQUIREMENTS_USER_STORIES.md` (acceptance criteria)
- **Architecture:** `12_ARCHITECTURE_DECISIONS.md` (rationale for decisions)
- **CLAUDE.md:** Repository working contract

---

## Contact & Escalation

**Phase 5 Lead:** [Name]
**Tech Lead:** [Name]
**Project Manager:** [Name]
**Escalation Slack Channel:** #phase5-agent-layer

---

**Ready to Start?** Review this guide, confirm team assignments, setup environments, and let's begin Week 1!

Last updated: December 2, 2025 05:10 UTC
