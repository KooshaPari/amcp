# Phase 5 Revised Strategy: Agent Layer SDK Focus
**Status:** Updated based on strategic pivot + multi-agent research
**Date:** December 2, 2025 (Updated Session)
**Focus:** Agent Layer API/SDK, not UI layer

---

## Strategic Pivot Summary

### Original Plan
- 6 cores: Agent Framework → Context Mgmt → APIs → **Terminal UI** → Integration
- 300 hours total, 8 weeks, 4 feature teams
- Core 5 (Terminal UI): 60 hours on Ink.js-based presentation layer

### Revised Plan ✅
- **5 cores: Agent Framework → Context Mgmt → APIs → Integration**
- **Skip Core 5 (Terminal UI)** - Move to Phase 6 (separate concern)
- **Agent Layer becomes pure SDK** - Programmatic API, not presentation-focused
- **Time saved: ~60 hours** → Use for depth and robustness in Cores 1-4
- **External consumption model:** Claude Code (and other clients) consume Agent SDK via APIs

---

## Why This Makes Sense

### Current Architecture Model

```
┌──────────────────────────────────────────┐
│     Presentation Layer (Phase 6)         │
│  ┌──────────────────────────────────┐   │
│  │  Ratatui CLI / Web / Desktop     │   │
│  │  (Consumes Agent SDK APIs)       │   │
│  └──────────────────────────────────┘   │
└──────────────────────────────────────────┘
                    ↓↑
┌──────────────────────────────────────────┐
│  Agent Layer (Phase 5) - SDK Focus       │
│  ┌──────────────────────────────────┐   │
│  │  Core 1: Agent Framework         │   │
│  │  Core 2: Context Management      │   │
│  │  Core 3: Agent-Optimized API     │   │
│  │  Core 4: LLM-Compatible API      │   │
│  │  (Orchestration, isolation,      │   │
│  │   session mgmt, memory hooks)    │   │
│  └──────────────────────────────────┘   │
└──────────────────────────────────────────┘
                    ↓↑
┌──────────────────────────────────────────┐
│         Brain Layer (Phase 3 ✅)         │
│  (Semantic, episodic, working memory)    │
└──────────────────────────────────────────┘
                    ↓↑
┌──────────────────────────────────────────┐
│         Tools Layer (SmartCP)            │
│  (Tool discovery, execution, isolation)  │
└──────────────────────────────────────────┘
```

### Consumption Model (Real-World)

**Claude Code** (and other clients) use Agent SDK like this:

```python
# Claude Code example (external consumer)
from agent_sdk import AgentCoordinator, AgentConfig

# Initialize
coordinator = AgentCoordinator(config)

# Spawn agent for code review task
agent = await coordinator.spawn(
    agent_type="code_reviewer",
    config=AgentConfig(
        cwd="/project",
        tools=["file_read", "semantic_search", "git"],
        memory=True,
        isolation="gvisor"  # Sandboxed
    )
)

# Execute task via Agent SDK (not a UI)
response = await agent.execute(
    request=AgentRequest(
        prompt="Review this code and identify issues",
        tools=["analyze_code", "suggest_fix"],
        context={"selected_files": [...]}
    ),
    stream=True  # Streaming support
)

# Results back to Claude Code for presentation
async for chunk in response.stream:
    print(chunk.result)
```

**This is the focus.** The **SDK itself**, not how it gets displayed.

---

## Revised Phase 5 Scope

### 5 Core Components (Total: 240 hours, 6 weeks)

| Core | Component | Hours | Weeks | Purpose |
|------|-----------|-------|-------|---------|
| 1 | Agent Framework & Orchestration | 60 | 2 | Base classes, spawning, pooling, lifecycle |
| 2 | Context & Working Directory Mgmt | 40 | 1.5 | Project abstraction, CWD inference, state |
| 3 | Agent-Optimized API Layer | 50 | 2 | Native agent control surface (SDK) |
| 4 | LLM-Compatible API Layer | 40 | 1.5 | OpenAI-compatible wrapper (for ecosystem) |
| (Integration & Testing) | *Embedded in cores* | 50 | 1 | Brain layer hooks, SWE Bench baseline |
| **Total** | | **240** | **6 weeks** | **Pure SDK focus** |

### Removed: Core 5 (Terminal UI)

- ❌ 60 hours on Ratatui TUI components
- ✅ Defer to Phase 6 (presentation layer separate)
- ✅ Saves time, enables depth in Cores 1-4
- ✅ External clients (Claude Code) provide their own UI

---

## What Changes in Cores 1-4

### Core 1: Agent Framework (60h, Weeks 1-2)
**Same as before, but with more depth:**
- Event-driven lifecycle (not just state transitions)
- Rich observability hooks (tracing, metrics)
- Actor-model patterns (documented)
- Failure isolation via sandboxing patterns
- Session checkpointing for debugging

**Added sections (from multi-agent research):**
- Production patterns from LangChain, AutoGen
- Anti-patterns to avoid
- Performance benchmarks (spawn time, memory)
- Real code examples (async patterns)

### Core 2: Context Management (40h, Weeks 2-3)
**Same as before, but with usability focus:**
- CWD inference edge cases documented
- Project abstraction intuitive for SDK users
- File watching patterns (real implementations)
- State sync strategies (git-aware, monorepo support)
- Fallback strategies when inference fails

**Added sections:**
- Real project structure variations (Django, Node, Rust, Go)
- How Claude Code will use this API
- Multi-project orchestration patterns
- Undo/rollback via event sourcing

### Core 3: Agent-Optimized API (50h, Weeks 3-5)
**This is the core SDK surface.** Deep focus:
- Tool invocation semantics (sync vs async, streaming)
- Sub-agent spawning protocol
- Session management (multi-turn, checkpointing)
- Memory access API (semantic, episodic, working)
- Error handling (rich error codes, debugging info)

**From research:**
- Detailed comparison with Claude Agent SDK
- Tool invocation benchmarks (latency, throughput)
- Streaming protocol specification (event format)
- Examples: How to integrate with Brain layer
- Intuitive API design (reduce user mental load)

### Core 4: LLM-Compatible API (40h, Weeks 3-5)
**Pure compatibility layer (no new concerns):**
- Map Agent API ↔ OpenAI Chat format
- Tool calling translation
- Fallback handling
- Edge case coverage (documented)

---

## Integration Points (Embedded in Cores)

### Brain Layer Hooks (15h)

Instead of separate Core 6 task, embedded in Cores 1-3:

**In Core 1 (Agent Framework):**
- Memory access hooks: `on_before_tool()`, `on_after_tool()`, `on_completion()`
- Semantic memory queries (cache-aware)
- Episodic memory updates (logging, patterns)

**In Core 2 (Context):**
- Working memory frame updates
- Context window management
- State snapshots for episodic storage

**In Core 3 (Agent API):**
- `/agent/{id}/memory` endpoints
- Semantic search integration
- Pattern extraction triggers

### SmartCP Integration (15h)

**In Core 1:**
- Tool registry pattern (discover available tools)
- Tool execution timeout management
- Resource isolation (container, VM patterns)

**In Core 3:**
- Tool invocation API (calls SmartCP)
- Error handling from tool execution
- Streaming tool output to client

### Claude Code Compatibility (10h)

**Documentation + examples:**
- How Claude Code uses Agent SDK
- MCP integration (if needed)
- Session state visibility
- Tool discovery for Claude Code

### SWE Bench Baseline (10h)

**Week 5-6:**
- Run agents on SWE Bench
- Measure: Accuracy, latency, memory
- Identify gaps for Phase 6 optimization

---

## Timeline (Revised: 6 weeks instead of 8)

### Week 1: Foundation (Agent Framework Pt. 1)
**Team 1 (3-4 engineers)**
- Task 1.1-1.2: Base classes, factory
- Async patterns, event lifecycle
- Code review & integration tests

### Week 2: Acceleration (Agent Framework Pt. 2)
**Team 1 (continued)**
- Task 1.3-1.5: Pooling, lifecycle, state persistence
- Observability hooks (tracing, metrics)
- Production patterns from research
- **Core 1 complete, ready for handoff**

### Week 3: Branching (Core 2 + Core 3 Start)
**Team 1 + Team 2**
- Team 1: Core 2 (context management, CWD inference, edge cases)
- Team 2: Core 3 API design finalization, streaming protocol
- Integration planning (Brain layer hooks)

### Week 4: APIs (Core 3/4 Complete)
**Team 2 (2-3 engineers)**
- Task 3.1-3.5: Agent-optimized API fully functional
- Task 4.1-4.4: LLM-compatible API mapping
- Claude Code integration examples
- Performance benchmarks

### Week 5: Integration Phase 1
**Team 3 (2-3 engineers)**
- Brain layer integration (Core 1/2/3 hooks)
- SmartCP tool integration
- Multi-agent coordination tests
- Begin SWE Bench baseline

### Week 6: Integration Phase 2 + Polish
**Team 3 (continued)**
- SWE Bench baseline completion
- Documentation & examples
- Performance profiling
- Phase 6 handoff preparation
- **Phase 5 complete**

---

## Why This Strategy is Better

### 1. **Cleaner Separation of Concerns**
- Phase 5: Agent SDK (what agents DO)
- Phase 6: Presentation (how users SEE it)
- No conflation of API design with UI design

### 2. **Better SDK Design**
- Focused on **programmatic usability** (not visual UX)
- Intuitive for developers (Claude Code, other tools)
- Examples: How to spawn agents, use memory, invoke tools
- Clear error handling, debugging support

### 3. **Faster Time to Value**
- 6 weeks → delivery of working Agent SDK
- Claude Code can integrate immediately
- Real usage patterns (Claude Code) inform Phase 6 design

### 4. **Production-Grade Implementation**
- ~60 extra hours (freed by not doing UI)
- Directed to Core 1-4 robustness
- Better error handling, edge cases, observability
- Research-informed patterns (not MVP)

### 5. **Ratatui Move Makes Sense**
- Phase 6 focus: Pure TUI concerns
- Ratatui native performance benefits
- Dedicated team for presentation layer
- Not rushed alongside core SDK work

---

## Documentation Updates

### Files to Create/Update:

1. **19_PHASE_5_REVISED_STRATEGY.md** (this file)
   - Strategic pivot explanation
   - Scope changes (5 cores instead of 6)
   - Timeline revised (6 weeks instead of 8)

2. **Update 15_STAKEHOLDER_REVIEW_SUMMARY.md**
   - New recommendation: 6 weeks, 240 hours
   - SDK focus instead of full-stack
   - Faster delivery, better quality

3. **Update 17_PHASE_5_SPRINT_SCHEDULE.md**
   - Weeks 1-6 (not 1-8)
   - Embedded integration (no separate Core 6)
   - Team allocation: 3 teams (not 4)

4. **Enhance 13_PHASE_5_DETAILED_IMPLEMENTATION_PLAN.md**
   - Cores 1-5 become Cores 1-4
   - Add multi-agent research insights
   - Deepen acceptance criteria

5. **Create 18_AGENT_LAYER_SDK_DESIGN.md** (from research)
   - Comprehensive SDK specification
   - Code examples, integration patterns
   - Production patterns validated

6. **Update 12_ARCHITECTURE_DECISIONS.md**
   - Add: UI layer deferred to Phase 6
   - Add: SDK focus increases robustness
   - Ratatui selection (but Phase 6 scope)

---

## Resource Requirements (Revised)

### Team Size: 8-10 engineers (down from 10-13)

**Team 1: Core Framework & Context** (3 engineers)
- Weeks 1-3

**Team 2: Agent APIs** (2-3 engineers)
- Weeks 3-5

**Team 3: Integration & SWE Bench** (2-3 engineers)
- Weeks 5-6

### Skills Mix:
- Python async experts (critical)
- Database/session management
- API design (REST/async semantics)
- Performance profiling
- Testing (unit, integration, SWE Bench)

---

## Success Criteria (Revised)

### Phase 5 Sign-Off (Week 6):

✅ **Core 1: Agent Framework**
- Event-driven lifecycle working
- 200+ agents spawn in <30s
- Observability complete (tracing, metrics)
- Zero memory leaks (24h test)

✅ **Core 2: Context Management**
- CWD inference >95% accurate
- Multi-project support
- State snapshots/restore working

✅ **Core 3: Agent-Optimized API**
- Tool invocation working (sync/async/streaming)
- Sub-agent spawning working
- Session management complete
- Memory integration hooks in place

✅ **Core 4: LLM-Compatible API**
- OpenAI compatibility tests 95%+ passing
- Tool mapping working
- Error translation correct

✅ **Integration:**
- Brain layer hooks implemented
- SmartCP integration working
- SWE Bench baseline established (document accuracy %)
- Claude Code can consume SDK

✅ **Quality:**
- >80% test coverage
- Zero critical bugs
- Performance targets met
- Production patterns validated (from research)

---

## What Phase 6 Looks Like Now

### Phase 6: Presentation Layer + Optimization

**Cores (TBD in Phase 6):**
1. **Ratatui CLI** - Native, high-performance TUI for agent monitoring
2. **Web Dashboard** - Browser-based agent management
3. **SDK Documentation** - Examples, tutorials, API reference
4. **Performance Optimization** - SWE Bench improvement, cost reduction
5. **Extended Features** - Agent pool UI, advanced debugging tools

**Time:** 8-10 weeks (dedicated UI/optimization focus)
**Team:** 2-3 engineers on Ratatui, additional on web/optimization

---

## Risk Changes (Revised)

### Risk Reduction ✅

| Risk | Original | Revised | Mitigation |
|------|----------|---------|-----------|
| **Scope creep (UI)** | High | Low | Deferred to Phase 6 |
| **Time pressure** | Medium | Low | 6 weeks → breathing room |
| **Quality (SDK)** | Medium | Low | Extra hours for robustness |
| **Ratatui learning** | Medium | Low | Phase 6 dedicated team |

### Risk Increase ⚠️

| Risk | Original | Revised | Mitigation |
|------|----------|---------|-----------|
| **Phase 6 dependency** | Low | Medium | Clear API contracts in Phase 5 |
| **UI not ready for demo** | N/A | Medium | Phase 5 delivers working SDK, Phase 6 adds UI |

---

## Recommendation

### ✅ **REVISED GO FOR PHASE 5**

**Scope:** 5 cores (Agent Framework, Context, APIs) — pure SDK focus
**Timeline:** 6 weeks (compressed from 8)
**Effort:** 240 hours (focused, no UI distraction)
**Quality:** Enhanced by multi-agent research insights
**Delivery:** Agent SDK ready for Claude Code integration + external consumption

**Phase 5 Success = Production-grade Agent SDK**
**Phase 6 Success = Beautiful presentation layer + performance optimization**

---

**Next Steps:**
1. Update stakeholder summary with revised scope
2. Brief teams on strategic pivot (UI deferred)
3. Emphasize SDK design excellence (not UI)
4. Week 0: Environment setup + research review
5. Week 1: Phase 5 implementation begins

Let's build an excellent Agent SDK first. The pretty interface comes next.

Last updated: December 2, 2025 (Session Pivot)
