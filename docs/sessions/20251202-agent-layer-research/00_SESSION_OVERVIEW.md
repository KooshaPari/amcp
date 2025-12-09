# Agent Layer Research & Architecture Planning
**Session:** 20251202-agent-layer-research
**Phase:** 4 (Agent Layer Architecture & Framework Selection)
**Status:** Planning & Research Initialization

---

## Session Goals

1. **Complete comprehensive research** on agent frameworks, patterns, and existing implementations
2. **Design Agent Layer architecture** that separates concerns (agentic orchestration vs LLM inference)
3. **Select or design optimal frameworks** for:
   - Agent orchestration and control
   - Terminal CLI interface for AI agents
   - Multi-agent scaling (50-200 agents, ideally 1k+)
4. **Define API contracts** for both agent-optimized and LLM-compatible endpoints
5. **Plan migration path** from research to implementation (Phase 5)

## Architecture Context

```
AI Agent Civilization (Startup-Scale)
│
├── Brain Layer (Phase 3: COMPLETE ✅)
│   ├── Episodic Memory (52 tests passing)
│   ├── Semantic Memory (facts, relationships)
│   ├── Working Memory (context, frames)
│   └── Integration with PreActPlanner
│
├── Agent Layer (Phase 4: THIS SESSION)
│   ├── Agent Orchestration Framework
│   ├── Agentic Control Surface
│   ├── Sub-agent Coordination
│   ├── Tool Orchestration (via smartcp)
│   ├── Working Directory / Project Context Management
│   └── Memory Integration
│
├── Tools Layer (Parallel: smartcp - infinite tool fabric)
│   └── Smart Code Processor (tools, plugins, extensions)
│
└── Presentation Layer (Phase 5)
    ├── API Server (Agent-optimized + LLM-compatible)
    ├── Terminal CLI (TUI-based)
    ├── SDK (programmatic)
    └── Web Interface (future)
```

## Key Challenges to Address

### 1. **CWD/Working Directory Translation Problem**
- Claude Code / Factory Droid don't send CWD natively
- Agent layer needs to infer/manage project context
- Must track working directories, project state, file changes
- Solution: Context manager, state tracker, project abstraction

### 2. **Scale & Resource Optimization**
- Current CLI agents: 5-50GB memory, high CPU, too many open files
- Target: Support 50-200 concurrent agents (1k ideal)
- Challenges: Memory pooling, file descriptor limits, CPU scheduling
- Solutions: Container/VM isolation, memory sharing, lazy loading

### 3. **MCP & Sub-agent Support**
- Factory Droid: Excellent CLI, broken MCP/subagents
- Claude Code: Working subagents, slower TUI
- Need: Robust, scalable MCP integration + subagent orchestration

### 4. **API Duality**
- Agent API: Direct agentic control, full feature set
- LLM API: Mimics OpenAI-compatible interface for integration with existing tools
- Must present both without feature duplication

### 5. **Quality Metrics**
- Brain layer optimization: Complete, accurate, precise, fast, cheap
- Agent layer optimization: Orchestrate behaviors, shape responses, manage context
- Need: Grounding strategies, hallucination prevention, accuracy validation

## Research Streams (Can Be Parallelized)

### Stream A: Framework & Library Research
- [ ] LangChain ecosystem (core, agents, memory, tools)
- [ ] LangGraph (control flow, branching, parallelization)
- [ ] LangChain DeepAgents (hierarchy, planning)
- [ ] LangFuse (observability, monitoring, evaluation)
- [ ] Related: AutoGen, CrewAI, Phidata, Pydantic AI

### Stream B: Existing CLI Agent Analysis
- [ ] Factory Droid (excellent CLI, broken MCP)
- [ ] Claude Code (good subagents, slow TUI)
- [ ] Auggie (codebse indexing, search)
- [ ] Cursor (snappy CLI, limited exposure)
- [ ] Codex (reliable UI, written in Rust)
- [ ] Other OSS agents (Aider, Continue, etc)
- [ ] Reverse engineering, pattern extraction

### Stream C: SWE Bench & Validation
- [ ] SWE Bench benchmark structure
- [ ] Current state of art results
- [ ] Integration with our harness (Harbor)
- [ ] CLI agent performance on SWE Bench
- [ ] Evaluation metrics and scoring

### Stream D: Terminal UI Frameworks
- [ ] Ink.js ecosystem (React-like TUI)
- [ ] Ratatui (Rust-based TUI, high performance)
- [ ] Textual (Python TUI, modern)
- [ ] Bubbletea (Go TUI, snappy)
- [ ] Other options (Blessed, Urwid, etc)

### Stream E: API Patterns & Standards
- [ ] OpenAI API compatibility layer design
- [ ] Agent API specification (native control)
- [ ] Message protocol design
- [ ] Session management patterns
- [ ] Authentication & authorization

### Stream F: Multi-Agent Orchestration
- [ ] Sub-agent patterns and architectures
- [ ] Hierarchical vs flat structures
- [ ] Agent communication protocols
- [ ] Resource pooling and sharing
- [ ] Failure handling and recovery

### Stream G: Working Directory & Context Management
- [ ] Project abstraction models
- [ ] CWD tracking and inference
- [ ] File system integration
- [ ] State management (changed files, etc)
- [ ] Sandboxing and isolation

### Stream H: Performance & Optimization
- [ ] Memory pooling strategies
- [ ] File descriptor management
- [ ] CPU scheduling for agents
- [ ] Lazy loading and initialization
- [ ] Container/VM orchestration options

## Key Questions to Answer

1. **Framework selection:**
   - Should we build on LangChain/LangGraph or build our own?
   - What's the right level of abstraction?
   - Can we avoid vendor lock-in?

2. **Architecture:**
   - How do we cleanly separate agent control from LLM inference?
   - What's the agentic control surface look like?
   - How do we handle CWD/context?

3. **Scale:**
   - What's the bottleneck at 200+ agents?
   - How do we pool resources effectively?
   - What infrastructure do we need?

4. **Quality:**
   - How do we ground agent reasoning?
   - How do we detect/prevent hallucination?
   - What validation strategies work?

5. **Integration:**
   - How does agent layer talk to brain layer?
   - How do we expose both APIs cleanly?
   - How does Claude Code integrate?

## Success Criteria

- [ ] Comprehensive research of all 8 streams complete
- [ ] Architecture decisions documented with rationale
- [ ] Framework selection with trade-off analysis
- [ ] API contracts defined (both agent + LLM)
- [ ] Detailed implementation plan created
- [ ] Risk assessment and mitigation strategies
- [ ] Performance targets established
- [ ] Scalability model validated (at least to 200 agents)

---

## Next Steps

1. **Create detailed research plan** (03_RESEARCH_PLAN.md)
2. **Launch parallel research streams** via multi-agent orchestration
3. **Compile findings** from each stream
4. **Architecture synthesis** (04_ARCHITECTURE_DECISIONS.md)
5. **Implementation planning** (05_IMPLEMENTATION_PLAN.md)
6. **Go/No-go decision** for Phase 5 implementation

---

## Session Artifacts

- `00_SESSION_OVERVIEW.md` (this file) - High-level goals and context
- `01_RESEARCH_STREAMS.md` - Detailed breakdown of each research area
- `02_EXISTING_AGENTS_ANALYSIS.md` - Comparison and analysis of existing CLI agents
- `03_FRAMEWORK_EVALUATION.md` - LangChain, LangGraph, alternatives comparison
- `04_ARCHITECTURE_DECISIONS.md` - Design decisions with rationale
- `05_API_SPECIFICATION.md` - Both agent-optimized and LLM-compatible APIs
- `06_IMPLEMENTATION_PLAN.md` - Detailed WBS for Phase 5
- `07_KNOWN_ISSUES.md` - Current blockers and constraints

