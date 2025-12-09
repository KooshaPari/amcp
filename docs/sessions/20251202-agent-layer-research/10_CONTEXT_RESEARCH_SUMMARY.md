# Context & Working Directory Management - Executive Summary
**Stream G Research - Quick Reference**
**Date:** December 2, 2025

---

## TL;DR

**Research complete for all 5 areas (G1-G5).** Ready for implementation.

**Key Recommendations:**
1. **Project Detection**: Git + package.json/pyproject.toml markers
2. **CWD Strategy**: Per-agent explicit paths (never `os.chdir()`)
3. **File Monitoring**: Watchdog library (cross-platform)
4. **State Persistence**: Event sourcing + incremental checkpoints
5. **Sandboxing**: gVisor for production (Docker for dev)

---

## G1: Project Abstraction

**What we learned:**
- Projects defined by Git root + package manager files
- Monorepos detected via `workspaces` field
- VS Code scans with `git.autoRepositoryDetection`

**What we're building:**
```python
class Project:
    root: Path
    type: ProjectType  # PYTHON, NODE, RUST, GO, MONOREPO, etc.
    git_repo: Optional[Path]
    subprojects: List[Project]  # For monorepos
```

**Implementation:**
- `ProjectDetector` scans upward for `.git/`
- Identifies type from `package.json`, `pyproject.toml`, etc.
- Caches results for performance

---

## G2: CWD Inference & Management

**What we learned:**
- `os.chdir()` is **process-wide**, breaks multi-threading
- Race conditions inevitable without locking
- Best practice: **explicit absolute paths**

**What we're building:**
```python
class AgentWorkspace:
    agent_id: str
    current_cwd: Path
    project: Optional[Project]
    path_resolver: PathResolver

    def resolve_path(self, relative_path: str) -> Path:
        """Always resolve relative to agent's CWD"""
```

**Implementation:**
- Per-agent workspace with isolated CWD
- Never call `os.chdir()` globally
- Infer CWD from message context ("cd X", file paths, project root)
- Thread-safe via separate workspace per agent

---

## G3: File System Integration

**What we learned:**
- Atomic renames most reliable for atomicity
- `fcntl` locking survives crashes
- Watchdog library: cross-platform file monitoring (inotify, FSEvents, etc.)
- Transaction logs enable rollback

**What we're building:**
```python
class SafeFileSystem:
    async def write(path, content):
        # 1. Write to temp file
        # 2. fsync to disk
        # 3. Atomic rename

    async def watch(path, callback):
        # Watchdog observer

    async def begin_transaction():
        # Track operations for rollback
```

**Implementation:**
- Atomic write-rename pattern
- fcntl-based file locking
- Watchdog for change monitoring
- Operation log for undo/rollback

---

## G4: State Persistence

**What we learned:**
- **Event sourcing** = complete audit trail + replay
- **Checkpoints** reduce recovery time
- **Incremental** snapshots most efficient
- Crash-consistent faster, application-consistent safer

**What we're building:**
```python
class CheckpointManager:
    event_store: EventStore  # Append-only log

    async def create_checkpoint(agent_id, state):
        # Full state snapshot (compressed)

    async def recover_agent(agent_id):
        # 1. Load last checkpoint
        # 2. Replay events since checkpoint
        # 3. Reconstruct current state
```

**Implementation:**
- Event store (append-only JSON log)
- Periodic checkpoints (every 5 min or 100 events)
- gzip compression for snapshots
- Event replay for recovery

---

## G5: Sandboxing & Isolation

**What we learned:**
- Docker = good isolation, easy to use, 5% overhead
- gVisor = better isolation, userspace kernel, 10-15% overhead
- Kata = best isolation, full VM, 15-20% overhead, 150-300ms startup
- Firecracker = serverless-optimized, 100-200ms startup

**Comparison:**

| Technology | Startup | Overhead | Security | Use Case |
|-----------|---------|----------|----------|----------|
| Docker | 50-100ms | 5% | Low | Development |
| **gVisor** | **50-100ms** | **10-15%** | **Medium** | **Production** ⭐ |
| Kata | 150-300ms | 15-20% | High | Maximum security |
| Firecracker | 100-200ms | 10-15% | High | Serverless |

**What we're building:**
```python
class SandboxManager:
    async def create_sandbox(agent_id, workspace):
        # Runtime: Docker (dev) or gVisor (prod)
        # Security: seccomp + capabilities + readonly root
        # Resources: 512MB RAM, 1 CPU, 1GB disk
        # Network: disabled by default
```

**Implementation:**
- Docker for development (fast iteration)
- gVisor for production (balanced security + performance)
- Resource limits enforced (memory, CPU, disk)
- Network isolation (disabled by default)

---

## Architecture Overview

```
Agent Layer
├── WorkspaceManager (per-agent CWD tracking)
│   ├── ProjectDetector (Git + package managers)
│   └── PathResolver (explicit path resolution)
│
├── SafeFileSystem (atomic ops + monitoring)
│   ├── AtomicOperations (write-rename pattern)
│   ├── FileLocking (fcntl-based)
│   ├── FileMonitor (Watchdog integration)
│   └── TransactionLog (undo/rollback)
│
├── CheckpointManager (state persistence)
│   ├── EventStore (append-only log)
│   ├── Snapshots (incremental checkpoints)
│   └── Recovery (checkpoint + event replay)
│
└── SandboxManager (isolation)
    ├── DockerSandbox (development)
    ├── GVisorSandbox (production)
    └── ResourceLimits (memory, CPU, disk)
```

---

## Implementation Priority

### Week 1: Core Context (G1 + G2)
✅ Project detection (Git, package managers)
✅ Workspace manager (per-agent CWD)
✅ Path resolution (explicit absolute paths)
✅ CWD inference (from message context)

### Week 2: File System (G3)
✅ Atomic file operations (write-rename)
✅ File locking (fcntl)
✅ File monitoring (Watchdog)
✅ Transaction support (begin/commit/rollback)

### Week 3: Persistence (G4)
✅ Event store (append-only log)
✅ Checkpoint manager (snapshots)
✅ Recovery mechanism (replay events)
✅ State serialization (pickle + gzip)

### Week 4: Sandboxing (G5)
✅ Docker sandbox (base implementation)
✅ gVisor integration (production runtime)
✅ Resource limits (memory, CPU, disk)
✅ Security hardening (seccomp, capabilities)

---

## Performance Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Project detection | <100ms | Fast agent startup |
| CWD inference | <50ms | Real-time path resolution |
| Atomic file write | <10ms | Minimal overhead |
| Checkpoint creation | <1s | Frequent snapshots |
| Sandbox startup (gVisor) | <200ms | Quick agent spawn |
| Sandbox startup (Kata) | <500ms | Acceptable for security |

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Multi-threaded CWD conflicts | High | Never use `os.chdir()`, explicit paths |
| Concurrent file writes | High | fcntl locking + atomic rename |
| Checkpoint failures | Medium | Event sourcing fallback |
| Sandbox escapes | High | gVisor/Kata for production |
| File descriptor exhaustion | Medium | Connection pooling + limits |
| Memory leaks | Medium | Periodic agent restarts + monitoring |

---

## Technology Stack

**Core:**
- Python 3.10+ (async/await support)
- Watchdog (file monitoring)
- Docker (base isolation)
- Git (repository detection)

**Production:**
- gVisor (sandboxing runtime)
- Redis (optional: shared state)
- PostgreSQL (optional: persistent event store)

**Optional:**
- Kata Containers (maximum isolation)
- Firecracker (serverless optimization)

---

## Key Design Decisions

1. **No global CWD**: Per-agent workspaces, explicit path resolution
2. **Event sourcing**: Complete audit trail, easy replay/recovery
3. **Incremental checkpoints**: Balance performance + recovery speed
4. **gVisor for production**: Best security/performance trade-off
5. **Watchdog for monitoring**: Battle-tested, cross-platform

---

## Next Steps

1. ✅ Complete research (all 5 areas documented)
2. ⏳ Review findings with team
3. ⏳ Begin Phase 1 implementation (Week 1)
4. ⏳ Write integration tests
5. ⏳ Performance benchmarks
6. ⏳ Production deployment guide

---

## Full Documentation

See [`10_CONTEXT_RESEARCH.md`](./10_CONTEXT_RESEARCH.md) for complete research findings with:
- Detailed analysis for each area (G1-G5)
- Code examples and implementations
- Architecture diagrams
- Comparison matrices
- Web research sources
- Implementation checklists

**Status:** ✅ Research Complete
**Ready for:** Phase 1 Implementation
**Estimated Timeline:** 4 weeks (parallel with other streams)
