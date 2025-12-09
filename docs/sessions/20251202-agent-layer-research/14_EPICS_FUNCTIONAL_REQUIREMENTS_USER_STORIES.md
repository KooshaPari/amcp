# Phase 5: Epics, Functional Requirements & User Stories
**Maturity Level:** Enterprise
**Scope:** Complete Agent Layer implementation with Brain integration
**Total Story Points:** ~800 (estimated)
**Timeline:** 8 weeks (4 feature teams)

---

## Table of Contents
1. [Epic Overview](#epic-overview)
2. [Epic 1: Agent Orchestration & Lifecycle](#epic-1-agent-orchestration--lifecycle)
3. [Epic 2: Context & Workspace Management](#epic-2-context--workspace-management)
4. [Epic 3: Agent Control API](#epic-3-agent-control-api)
5. [Epic 4: LLM-Compatible API](#epic-4-llm-compatible-api)
6. [Epic 5: Agent Monitoring & Terminal UI](#epic-5-agent-monitoring--terminal-ui)
7. [Epic 6: Integration & System Hardening](#epic-6-integration--system-hardening)
8. [Functional Requirements Matrix](#functional-requirements-matrix)
9. [User Story Prioritization](#user-story-prioritization)
10. [Cross-Cutting Concerns](#cross-cutting-concerns)

---

## Epic Overview

| Epic | Description | Teams | Points | Weeks | Priority |
|------|-------------|-------|--------|-------|----------|
| **Epic 1** | Agent orchestration, spawning, lifecycle management | Team 1 | 120 | 2 | P0 (Critical) |
| **Epic 2** | Working directory isolation, file operations, state persistence | Team 2 | 100 | 2 | P0 (Critical) |
| **Epic 3** | High-performance agent control API with streaming | Team 1 | 110 | 2 | P0 (Critical) |
| **Epic 4** | OpenAI-compatible chat completions API | Team 2 | 80 | 2 | P1 (High) |
| **Epic 5** | Terminal UI for agent management and monitoring | Team 1 | 150 | 3 | P1 (High) |
| **Epic 6** | Brain layer integration, SWE Bench, deployment | Team 2 | 140 | 3 | P0 (Critical) |

---

# Epic 1: Agent Orchestration & Lifecycle

## Epic Goal
Enable reliable multi-agent orchestration with resource pooling, fault tolerance, and auto-scaling to support 50-200+ concurrent agents without resource exhaustion.

## Success Criteria
- [ ] Spawn 100 agents in <30 seconds
- [ ] Each agent uses <100MB memory (measured)
- [ ] Agent startup latency <200ms (warm pool)
- [ ] Resource pools (DB, HTTP, tools) prevent exhaustion at 200 agents
- [ ] Agent failures detected within 60 seconds
- [ ] Graceful shutdown in <60 seconds
- [ ] All tests passing (>85% coverage)
- [ ] Performance benchmarks within target

---

## User Stories

### Story 1.1: Agent Factory with Configuration
**As a** developer
**I want** to spawn agents with configurable types (claude-sonnet-4, claude-opus, etc.)
**So that** I can use optimal models for different tasks

**Acceptance Criteria:**
1. Factory accepts agent_type parameter (string)
2. Supports at least 3 model types (Sonnet, Opus, Haiku)
3. Custom configuration passed as dict (parameters, timeout, memory_limit)
4. Agent instantiation <200ms per agent
5. Factory validates config before instantiation
6. Detailed error messages on invalid config
7. Unit tests: 10+ test cases, >90% coverage

**Task Breakdown:**
- Create `AgentFactory` class with spawn method
- Define `AgentConfig` Pydantic model with validation
- Implement agent type registry (extensible for new types)
- Create unit tests for factory behavior
- Document supported agent types and parameters

**Depends On:** None
**Blocked By:** None
**Points:** 13

---

### Story 1.2: Agent Lifecycle State Machine
**As an** operator
**I want** agents to follow a clear lifecycle (INITIALIZING → READY → RUNNING → SHUTDOWN)
**So that** I can reliably predict agent state and detect problems

**Acceptance Criteria:**
1. Agent has atomic state transitions (no race conditions)
2. State machine allows: INITIALIZING → READY → {RUNNING, PAUSED} → READY → SHUTDOWN
3. ERROR state for recoverable failures (max 3 restarts/hour)
4. FAILED state for unrecoverable failures
5. State transition hooks for logging and metrics
6. No state transition without proper preconditions
7. Integration test: full lifecycle with 10 agents

**State Transitions Diagram:**
```
INITIALIZING → READY → RUNNING → READY → PAUSED
                 ↓                  ↓        ↓
                ERROR           SHUTDOWN   READY
                 ↓
            (restart)
```

**Task Breakdown:**
- Create `AgentState` enum with all states
- Implement state machine with precondition checking
- Add transition hooks for observability
- Create integration tests for all state paths
- Document state machine in code and docs

**Depends On:** Story 1.1
**Blocked By:** None
**Points:** 13

---

### Story 1.3: Agent Warm Pool for Fast Startup
**As a** performance engineer
**I want** agents pre-initialized in a warm pool
**So that** agent startup reduces from 2 seconds to <100ms

**Acceptance Criteria:**
1. Warm pool initialized at server startup
2. Pool size configurable (default: 10 agents)
3. Pool maintains ready agents (state = READY)
4. On agent request, reuse from pool or spawn new
5. Pool auto-replenishes asynchronously
6. Memory overhead: <1GB for 10-agent pool
7. Warm pool reduces P95 startup from 2s to <200ms
8. Benchmark: measure and verify startup improvement

**Performance Targets:**
- Cold start (no pool): 2000ms
- Warm pool reuse: <100ms
- Pool initialization: <5 seconds
- Memory per pooled agent: ~100MB

**Task Breakdown:**
- Create `WarmPool` class with async initialization
- Implement agent request routing (pool → spawn)
- Add metrics for pool utilization and reuse rate
- Create performance benchmark tests
- Document warm pool tuning parameters

**Depends On:** Story 1.1, 1.2
**Blocked By:** None
**Points:** 13

---

### Story 1.4: Resource Pooling (DB, HTTP, Tools)
**As a** capacity planner
**I want** shared resource pools for DB connections, HTTP clients, and tool instances
**So that** 200 agents don't consume 40GB memory (vs 2GB with pooling)

**Acceptance Criteria:**
1. Database connection pool: min 5, max 50 connections
   - All agents share single pool
   - Health check every 60 seconds
   - Timeout: 30 seconds per connection
   - Measure: 200 agents + shared pool = <500MB memory
2. HTTP client pool: reuse httpx.AsyncClient
   - Max 20 concurrent connections per pool
   - Keep-alive: 30 seconds
   - Connection reuse: >80% hit rate
   - Measure: socket count stable (not growing)
3. Tool instance cache: LRU cache with TTL
   - Max 100 items, evict oldest if exceeded
   - TTL: 5 minutes per tool
   - Cache hit rate: >80%
   - Measure: 40x speedup for cached tool calls (500ms → 10ms)
4. Resource exhaustion monitoring
   - Alert on pool saturation (>80% capacity)
   - Fallback: auto-scale pool (up to limits)
5. Integration test: 200 agents + resource pools = <2GB memory

**Task Breakdown:**
- Create `ResourcePool` base class
- Implement database connection pooling
- Implement HTTP client pooling (reuse)
- Implement tool instance cache (LRU + TTL)
- Create integration tests with 200 agents
- Add monitoring/metrics for pool usage
- Document resource pool tuning

**Depends On:** Story 1.1
**Blocked By:** None
**Points:** 21

---

### Story 1.5: Agent Failure Detection & Recovery
**As a** reliability engineer
**I want** failed agents detected and automatically restarted
**So that** system recovers from transient failures without operator intervention

**Acceptance Criteria:**
1. Health check every 30 seconds (liveness probe)
2. Failure detection latency: <60 seconds
3. Auto-restart strategy:
   - Max 3 restarts per hour (circuit breaker)
   - Exponential backoff: 1s, 2s, 4s
   - After 3rd failure: manual intervention required
4. Graceful degradation: failed agent doesn't crash orchestrator
5. Logging: all failure events with context
6. Integration test: inject failures, verify recovery
7. No duplicate restarts (restart lock)

**Failure Scenarios Tested:**
- OOM (out of memory)
- Crashed process
- Hung execution (timeout)
- External dependency failure (DB down, tool unavailable)
- Network partition

**Task Breakdown:**
- Implement liveness check (health endpoints)
- Implement restart logic with backoff
- Implement circuit breaker (max restarts/hour)
- Add comprehensive logging
- Create failure injection tests
- Document failure recovery strategy

**Depends On:** Story 1.2
**Blocked By:** None
**Points:** 13

---

### Story 1.6: Agent State Persistence & Recovery
**As an** operator
**I want** agent state persisted across restarts
**So that** long-running agents recover from crashes without losing progress

**Acceptance Criteria:**
1. State checkpoint creation every N steps (N=5, configurable)
2. Checkpoint latency: <500ms
3. Checkpoint size: <10MB (with compression)
4. Recovery on restart: load latest checkpoint, resume
5. Checkpoint integrity: CRC/checksum verification
6. Checkpoint retention: keep last 10 per agent
7. Archive old checkpoints: move to S3 after 7 days
8. Integration test: checkpoint + recovery + resume

**Checkpoint Data:**
- Agent metadata (id, type, config)
- Execution context (cwd, user_id, workspace_id)
- Progress (current_step, completed_steps)
- Intermediate results
- Resource usage stats

**Task Breakdown:**
- Define checkpoint data model (Pydantic)
- Implement checkpoint creation (atomic write)
- Implement checkpoint recovery (with integrity check)
- Implement cleanup (archival, retention)
- Create database tables (Supabase)
- Add integration tests with recovery
- Document checkpoint strategy

**Depends On:** Story 1.1, 1.2
**Blocked By:** None
**Points:** 13

---

### Story 1.7: Agent Pool Scaling to 200+ Agents
**As a** capacity engineer
**I want** validated scalability to 200+ concurrent agents
**So that** I can plan infrastructure with confidence

**Acceptance Criteria:**
1. Performance validated at: 50, 100, 200 agents
2. Metrics at each scale:
   - Memory: <2GB for 200 agents
   - CPU: <4 cores for 200 agents (2.2 GHz)
   - Open file descriptors: <1000 total
   - DB connections: <50 concurrent
3. Scalability model: overhead % = f(agent_count)
   - 50 agents: 91% efficiency
   - 100 agents: 85% efficiency
   - 200 agents: 73% efficiency
4. Bottleneck identification and documented
5. Load test results published

**Load Test Scenarios:**
- Ramp up: add 5 agents/sec until 200
- Sustained: run 200 agents for 5 minutes
- Stress: attempt 300 agents (should fail gracefully)
- Recovery: kill 50 agents, verify others continue
- Resource limit: verify alerts at 80% capacity

**Task Breakdown:**
- Create load testing harness (Python/k6)
- Implement monitoring/metrics collection
- Run load tests at 50, 100, 200 agent scales
- Identify bottlenecks (profiling)
- Document scalability characteristics
- Create public report of results

**Depends On:** Story 1.4, 1.5
**Blocked By:** Story 1.4
**Points:** 21

---

### Story 1.8: Multi-Agent Coordination Protocol
**As a** developer
**I want** agents to communicate and coordinate via reliable message bus
**So that** complex workflows with multiple agents work correctly

**Acceptance Criteria:**
1. Message format: JSON with schema validation
2. Message routing: agent_id → receive queue
3. Broadcast: one agent → multiple agents
4. Message bus: in-memory (Redis for distributed)
5. Delivery guarantee: at-least-once (idempotent handlers)
6. Message timeout: 30 seconds (auto-cleanup)
7. Unit test: routing, broadcast, timeout scenarios
8. Integration test: 3 agents coordinating task

**Message Types:**
- `agent.status_update` - periodic agent status
- `task.result` - sub-agent reporting result
- `task.subtask` - parent agent spawning sub-task
- `resource.request` - request access to shared resource
- `resource.grant` - grant resource access

**Task Breakdown:**
- Design message schema (Pydantic models)
- Implement message bus (in-memory queue)
- Implement routing (agent_id based)
- Implement broadcast (one → many)
- Add idempotency handling
- Create comprehensive tests
- Document protocol in code

**Depends On:** Story 1.1
**Blocked By:** None
**Points:** 13

---

## Epic 1 Summary
**Total Points:** 120
**Stories:** 8 user stories
**Key Deliverables:**
- Functional agent factory and lifecycle
- Resource pooling (40x memory savings)
- Warm pool (<100ms startup)
- Failure detection and recovery
- State persistence and recovery
- Validated scaling to 200+ agents
- Multi-agent coordination protocol

**Exit Criteria:**
- All 8 stories passing acceptance tests
- Performance benchmarks met
- >85% code coverage
- Load tests at 50, 100, 200 agents succeed
- Ready for integration with other epics

---

# Epic 2: Context & Workspace Management

## Epic Goal
Provide per-agent working directory isolation, file operations, and project context without global state, enabling safe multi-agent file access.

## Success Criteria
- [ ] Per-agent CWD isolation (no `os.chdir()`)
- [ ] Atomic file operations with <1% corruption rate
- [ ] File watching detects changes within 1 second
- [ ] Project detection works for Python, Node.js, Rust, monorepos
- [ ] State recovery from checkpoint <200ms
- [ ] File access restricted to project boundaries (security)
- [ ] All tests passing (>80% coverage)

---

## User Stories

### Story 2.1: Project Detection & Analysis
**As a** developer
**I want** the system to automatically detect project type and structure
**So that** agent operations are contextually aware

**Acceptance Criteria:**
1. Detects project type: Python, Node.js, Rust, Go, monorepo, unknown
2. Identifies root directory by checking:
   - Git repo (.git/)
   - Python (pyproject.toml, setup.py, poetry.lock)
   - Node.js (package.json, yarn.lock, package-lock.json)
   - Rust (Cargo.toml)
   - Monorepo (lerna.json, workspaces config)
3. Detection latency: <100ms (with caching, TTL 1 hour)
4. Handles non-repo directories gracefully
5. Extracts package manager info (pip, npm, cargo, etc.)
6. Lists source directories (src/, lib/, tests/, etc.)
7. Unit test: 20+ project types, >90% accuracy

**Supported Project Types:**
```
Python:     pyproject.toml, setup.py, Pipfile, poetry.lock, requirements.txt
JavaScript: package.json, yarn.lock, package-lock.json, pnpm-lock.yaml
Rust:       Cargo.toml, Cargo.lock
Go:         go.mod, go.sum
Monorepo:   lerna.json, workspaces field in package.json, pnpm-workspaces.yaml
Git:        .git/ directory (any language)
Unknown:    No markers found (fallback to current dir)
```

**Task Breakdown:**
- Create `ProjectDetector` class
- Implement marker-based detection (parallel file checks)
- Implement caching (Redis, 1-hour TTL)
- Extract package manager and dependencies
- Create comprehensive test suite (20+ projects)
- Document detection logic

**Depends On:** None
**Blocked By:** None
**Points:** 13

---

### Story 2.2: Per-Agent Working Directory Tracking
**As a** developer
**I want** each agent to have isolated CWD without `os.chdir()`
**So that** multiple agents can work in different directories simultaneously

**Acceptance Criteria:**
1. Each agent has `ContextState` (CWD, project_root, git_branch, env_vars)
2. CWD persisted in agent state (recovered on restart)
3. Inference on first request:
   - Check `x-cwd` header (client hint)
   - Check request context (file paths in prompt)
   - Fall back to project root
4. Path resolution: `resolve_path(relative_path) -> absolute_path`
5. Relative path conversion: `relative_path(absolute_path) -> str`
6. Symlink handling: resolve to canonical path
7. Security: paths don't escape project boundary
8. CWD stack: save/restore around tool calls (prevent leaks)
9. Integration test: 10 agents in different CWDs, no cross-pollution

**ContextState Data Model:**
```python
@dataclass
class ContextState:
    cwd: str                      # Absolute path
    project_root: str             # Project root (if detected)
    relative_cwd: str             # Relative to project root
    git_branch: str | None        # Current branch (if Git repo)
    git_remote: str | None        # Remote URL
    env_vars: dict[str, str]      # Environment variables
    timestamp: datetime           # Last updated
```

**Task Breakdown:**
- Design `ContextState` data model
- Implement `CWDManager` class
- Implement path resolution (absolute ↔ relative)
- Implement symlink resolution
- Implement boundary checking (security)
- Implement CWD stack for nested operations
- Create comprehensive tests (edge cases: symlinks, ../, .)
- Document isolation model

**Depends On:** Story 2.1
**Blocked By:** None
**Points:** 13

---

### Story 2.3: Safe File Operations with Atomicity
**As a** developer
**I want** file operations to be atomic and safe
**So that** concurrent agents don't corrupt files

**Acceptance Criteria:**
1. Read: `read_file(path) -> str` with boundary check
2. Write: `write_file(path, content)` atomic (temp → rename)
3. Delete: `delete_file(path)` with safety checks
4. List: `list_files(path, pattern)` with filtering
5. All operations verify path within project
6. Atomic write: write temp file → fsync → atomic rename
7. Crash safety: verify no partial files on failure
8. Concurrent writes: first write wins (or queue with mutex)
9. File locking: fcntl (Unix) / msvcrt (Windows)
10. Timeout: 30s per operation (configurable)
11. Integration test: concurrent writes, verify no corruption
12. Stress test: 10 agents writing different files simultaneously

**File Operation Behavior:**
```
write_file("/path/to/file.txt", "content"):
  1. Generate temp: "/path/to/.file.txt.tmp.{random}"
  2. Write to temp file
  3. fsync(fd) - ensure on disk
  4. Acquire lock on target
  5. Atomic rename: temp → target
  6. Release lock
  7. Return success or error

Failure scenarios:
  - Temp write fails → cleanup temp, raise error
  - fsync fails → cleanup temp, raise error
  - Rename fails → cleanup temp, raise error
  - Process crash → temp cleanup on recovery
```

**Task Breakdown:**
- Create `FileOps` class with safe operations
- Implement atomic write pattern
- Implement file locking (cross-platform)
- Implement boundary checking (security)
- Add timeout handling
- Create comprehensive tests (corruption scenarios)
- Add stress testing (concurrent writes)
- Document file operations

**Depends On:** Story 2.2
**Blocked By:** None
**Points:** 13

---

### Story 2.4: File Change Detection & Watching
**As a** developer
**I want** to detect when files change (externally or by agents)
**So that** agent can react to modifications

**Acceptance Criteria:**
1. Track file hash (SHA256) after each write
2. Detect external modifications (git checkout, external edit)
3. Change events: modify, create, delete
4. Detection latency: <1 second (using watchdog)
5. Change history: keep last 10 versions per file
6. Notify agent of unexpected changes
7. Integration test: modify file externally, agent detects

**Change Detection Strategy:**
```
After write operation:
  1. Compute SHA256 hash of file
  2. Store in agent state: {path: hash, timestamp}

Periodic scan (every 5 seconds):
  1. For each tracked file:
     a. Current hash = SHA256(file)
     b. Stored hash = agent_state[path].hash
     c. If different:
        - External modification detected
        - Log event
        - Notify agent (optional)
        - Update stored hash

Before read operation:
  1. Check if file hash changed
  2. If changed externally:
     a. Log warning
     b. Return current content (not cached)
     c. Update internal hash
```

**Task Breakdown:**
- Implement file hashing (SHA256)
- Implement watchdog-based file monitoring
- Implement change history storage
- Implement change event notification
- Create integration tests (external modifications)
- Document file watching strategy

**Depends On:** Story 2.3
**Blocked By:** None
**Points:** 13

---

### Story 2.5: Persistent Context State Management
**As an** operator
**I want** context state persisted across agent restarts
**So that** agent continues in same directory/context after recovery

**Acceptance Criteria:**
1. Event sourcing: all CWD changes logged as events
2. Event schema: {timestamp, agent_id, event_type, cwd, details}
3. Snapshots: full state every 100 events, incremental every 10 events
4. Compression: gzip if snapshot >1MB
5. Recovery: replay events to reconstruct state
6. CWD validation: verify directory still exists on recovery
7. Fallback: use project root if CWD invalid
8. Integration test: context persistence + recovery

**State Persistence Flow:**
```
Agent execution:
  CWD change → log event → update in-memory state

Every 10 events:
  Create incremental snapshot (deltas only)

Every 100 events:
  Create full snapshot (compress if >1MB)
  Prune old snapshots (keep last 3)

On agent restart:
  1. Load latest snapshot
  2. Replay events since snapshot
  3. Validate CWD (directory exists)
  4. If invalid: fallback to project_root
  5. Continue execution
```

**Storage Schema:**
```sql
CREATE TABLE context_events (
    id BIGSERIAL PRIMARY KEY,
    agent_id UUID NOT NULL,
    event_type TEXT NOT NULL,      -- "cwd_change", "env_update", etc.
    cwd TEXT,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE context_snapshots (
    id UUID PRIMARY KEY,
    agent_id UUID UNIQUE NOT NULL,
    snapshot_num INT,
    state BYTEA NOT NULL,          -- gzipped JSON
    size_bytes INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Task Breakdown:**
- Design event and snapshot schema
- Implement event sourcing (append-only log)
- Implement snapshot creation (full + incremental)
- Implement recovery (replay events)
- Implement validation and fallback
- Create database tables (Supabase)
- Add comprehensive tests
- Document persistence strategy

**Depends On:** Story 2.2, 2.4
**Blocked By:** None
**Points:** 13

---

### Story 2.6: Project Boundary Enforcement (Security)
**As a** security officer
**I want** agents restricted to project boundaries
**So that** they cannot access files outside the project

**Acceptance Criteria:**
1. All file paths validated against project_root
2. Reject paths that escape project (../../../etc/passwd)
3. Reject absolute paths outside project
4. Reject symlinks pointing outside project
5. Security test: attempted escapes fail with clear error
6. Logging: all escape attempts logged for audit
7. Error message: informative but not leaking paths

**Path Security Checks:**
```python
def secure_resolve(requested_path: str, project_root: str) -> str:
    """
    1. Resolve relative path: project_root + requested_path
    2. Canonicalize: resolve symlinks, ../, ./
    3. Verify: result starts with project_root
    4. Return: canonical path or raise SecurityError
    """
```

**Test Cases:**
- `../../../etc/passwd` → reject
- `/etc/passwd` → reject
- `./file.txt` → accept (in project)
- `subdir/file.txt` → accept (in project)
- symlink → /etc/passwd → reject
- symlink → ./file.txt → accept

**Task Breakdown:**
- Implement path security validation
- Implement symlink boundary checking
- Add audit logging
- Create comprehensive security tests
- Document security model

**Depends On:** Story 2.2, 2.3
**Blocked By:** None
**Points:** 13

---

### Story 2.7: Git Integration (Metadata & Status)
**As a** developer
**I want** agent aware of Git context (branch, remotes, status)
**So that** agents can make Git-aware decisions

**Acceptance Criteria:**
1. Detect Git repo and extract metadata
2. Current branch: `git_branch` from HEAD
3. Remote info: extract remote URL
4. File status: staged, unstaged, untracked (via git status)
5. Commit history: last 20 commits available
6. Integration with CWD tracking (update on checkout)
7. Cache: refresh on git operations (5-minute default TTL)
8. Unit test: Git operations, status detection
9. Integration test: agent switches branch, CWD context updated

**Git Metadata Captured:**
```python
@dataclass
class GitContext:
    repo_path: str          # .git directory location
    current_branch: str     # from HEAD
    remotes: dict[str, str] # {origin: url, ...}
    file_status: dict[str, str]  # {file: status, ...}
    last_commits: list[dict]  # [{hash, author, message, ...}]
    last_updated: datetime
```

**Task Breakdown:**
- Implement Git repo detection
- Implement Git metadata extraction (pygit2 or gitpython)
- Implement file status detection
- Implement caching with TTL
- Create comprehensive tests
- Document Git integration

**Depends On:** Story 2.1, 2.2
**Blocked By:** None
**Points:** 13

---

## Epic 2 Summary
**Total Points:** 100
**Stories:** 7 user stories
**Key Deliverables:**
- Automatic project detection (Python, Node.js, Rust, etc.)
- Per-agent CWD isolation (no `os.chdir()`)
- Atomic file operations with crash safety
- File change detection (<1s latency)
- Context state persistence and recovery
- Security boundary enforcement
- Git integration (branch, remote, status)

**Exit Criteria:**
- All 7 stories passing acceptance tests
- Multi-agent file access verified (no corruption)
- Security tests pass (no escapes)
- >80% code coverage
- Ready for integration with Agent APIs

---

# Epic 3: Agent Control API

## Epic Goal
Provide high-performance API for direct agent control with streaming output, tool invocation, and session management.

## Success Criteria
- [ ] POST /v1/agents/execute functional with streaming
- [ ] Agent API latency <1s (p95)
- [ ] Streaming latency <100ms per event
- [ ] Session management (reuse, cleanup)
- [ ] Tool invocation working (<500ms)
- [ ] >80% test coverage
- [ ] Load tests at 1000 req/min pass

---

## User Stories

### Story 3.1: Agent Execution Endpoint
**As a** API client
**I want** to execute an agent with a prompt
**So that** I can get results from the agent

**Acceptance Criteria:**
1. Endpoint: POST /v1/agents/execute
2. Request: agent_id (optional), prompt, tools (optional), parameters (optional), cwd (optional), timeout (optional)
3. Response: agent_id, status, result, logs, metadata (duration, tokens, tools_called)
4. Status codes: 200 (success), 400 (invalid request), 500 (server error)
5. Timeout default: 300s (configurable)
6. Result: LLM output text
7. Logs: execution logs (array of strings)
8. Metadata: timing, token counts, tools invoked
9. Unit test: basic execution, timeout, invalid input
10. Integration test: end-to-end with agent framework

**Request Format:**
```json
POST /v1/agents/execute
{
  "agent_id": "agent-123",        // optional, create new if omitted
  "prompt": "Create an entity...",
  "tools": ["entity.create", "entity.read"],  // optional, default all
  "parameters": {
    "temperature": 0.7,
    "top_p": 1.0
  },
  "cwd": "/home/user/project",    // optional, inferred if omitted
  "timeout": 300,
  "stream": false
}
```

**Response Format:**
```json
{
  "agent_id": "agent-123",
  "status": "completed",
  "result": "I've created the entity with ID 550e8400-e29b...",
  "logs": [
    "[2024-12-02T10:30:45] Agent started",
    "[2024-12-02T10:30:46] Tool: entity.create called",
    "[2024-12-02T10:30:47] Tool result: success"
  ],
  "metadata": {
    "duration_ms": 2500,
    "tokens_used": 350,
    "tools_called": ["entity.create"],
    "errors": []
  }
}
```

**Task Breakdown:**
- Create `/v1/agents/execute` endpoint
- Implement request validation (Pydantic)
- Implement agent execution orchestration
- Implement response formatting
- Create comprehensive tests
- Document endpoint behavior

**Depends On:** Epic 1
**Blocked By:** None
**Points:** 13

---

### Story 3.2: Streaming Agent Output (SSE)
**As a** real-time client
**I want** streaming output from agent execution
**So that** I see results immediately

**Acceptance Criteria:**
1. Streaming mode: `stream: true` in request
2. Response: Server-Sent Events (SSE)
3. Content-Type: text/event-stream
4. Events:
   - `agent-start`: agent initialized
   - `tool-call`: tool being invoked {tool_name, tool_input}
   - `tool-result`: tool result {tool_name, result}
   - `agent-output`: LLM output chunk {text}
   - `agent-complete`: final result {result, metadata}
   - `agent-error`: error occurred {error, code}
5. Keep-alive: send comment every 30s (connection stability)
6. Streaming latency: <100ms per event
7. No message loss
8. Connection timeout: 5 minutes (auto-reconnect)
9. Integration test: streaming with token-by-token output

**SSE Format:**
```
event: agent-start
data: {"agent_id": "agent-123", "timestamp": "2024-12-02T10:30:45Z"}

event: tool-call
data: {"tool_name": "entity.create", "tool_input": {"name": "Product"}}

event: tool-result
data: {"tool_name": "entity.create", "result": {"id": "550e8400-e29b"}}

event: agent-output
data: {"text": "I've created"}

event: agent-output
data: {"text": " the entity"}

event: agent-complete
data: {"result": "I've created the entity...", "metadata": {...}}
```

**Task Breakdown:**
- Implement SSE streaming handler
- Implement event queue for buffering
- Implement keep-alive (comment every 30s)
- Implement reconnection logic (client side)
- Create streaming tests
- Document streaming protocol

**Depends On:** Story 3.1
**Blocked By:** None
**Points:** 13

---

### Story 3.3: Agent Sub-Spawning (Hierarchical)
**As a** developer
**I want** agents to spawn child agents
**So that** I can create hierarchical workflows

**Acceptance Criteria:**
1. Parent agent can spawn sub-agents via API call
2. Request: `POST /v1/agents/spawn` with agent_type, config, parent_id
3. Response: agent_id, status, metadata
4. Sub-agents inherit parent's working_dir/context (unless overridden)
5. Sub-agents report results back to parent via message bus
6. Parent can wait for sub-agents or run async
7. Timeout: 60s for spawn operation
8. Integration test: parent spawns 2 child agents, waits for results

**Sub-Agent Spawning Flow:**
```
Parent agent executing:
  1. Call /v1/agents/spawn
  2. System creates child agent (inherits context)
  3. Return child agent_id
  4. Parent sends work to child
  5. Child reports results via message bus
  6. Parent aggregates results
  7. Parent continues with aggregated result
```

**Task Breakdown:**
- Create `/v1/agents/spawn` endpoint
- Implement sub-agent context inheritance
- Implement parent-child relationship tracking
- Implement result reporting (message bus)
- Create integration tests
- Document sub-agent patterns

**Depends On:** Epic 1, Story 3.1
**Blocked By:** None
**Points:** 13

---

### Story 3.4: Tool Invocation API
**As a** developer
**I want** to invoke tools directly from the API
**So that** I can use tools without going through agent execution

**Acceptance Criteria:**
1. Endpoint: POST /v1/agents/{agent_id}/tools/{tool_name}
2. Request: tool_name, parameters (tool-specific)
3. Response: status, result, metadata
4. Tool result: raw output from tool
5. Error handling: invalid tool, invalid parameters
6. Timeout: 30s per tool (configurable)
7. Integration test: invoke entity.create tool directly

**Tool Invocation Endpoints:**

**POST /v1/agents/{agent_id}/tools/{tool_name}**
```json
Request:
{
  "parameters": {
    "name": "My Entity",
    "type": "product"
  }
}

Response:
{
  "status": "success",
  "result": {
    "id": "550e8400-e29b",
    "name": "My Entity",
    "created_at": "2024-12-02T10:30:47Z"
  },
  "metadata": {
    "duration_ms": 125,
    "tool_version": "1.0.0"
  }
}
```

**GET /v1/tools**
```json
Response:
{
  "tools": [
    {
      "name": "entity.create",
      "description": "Create a new entity",
      "parameters": {...JSON Schema...},
      "tags": ["entity", "create"]
    }
  ],
  "total": 42
}
```

**GET /v1/tools/{tool_name}**
```json
Response:
{
  "name": "entity.create",
  "description": "Create a new entity with properties",
  "parameters": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "type": {"type": "string"}
    },
    "required": ["name"]
  },
  "examples": [
    {
      "input": {"name": "Product Launch", "type": "product"},
      "output": {"id": "550e8400-e29b"}
    }
  ]
}
```

**Task Breakdown:**
- Create `/v1/agents/{agent_id}/tools/{tool_name}` endpoint
- Implement tool registry integration
- Create `/v1/tools` listing endpoint
- Create `/v1/tools/{tool_name}` documentation endpoint
- Implement parameter validation (JSON Schema)
- Create comprehensive tests
- Document tool invocation

**Depends On:** Epic 1, Story 3.1
**Blocked By:** None
**Points:** 13

---

### Story 3.5: Session Management
**As an** API client
**I want** to maintain agent sessions for multi-turn conversations
**So that** agent state is preserved across requests

**Acceptance Criteria:**
1. Session created on first `/v1/agents/execute` request
2. Session ID returned in response
3. Subsequent requests use session_id to reuse agent
4. Session state: active, paused, closed
5. Session timeout: 1 hour idle (auto-close)
6. Session storage: Redis (hot) + PostgreSQL (cold)
7. Get session: GET /v1/sessions/{session_id}
8. List sessions: GET /v1/sessions?user_id=...
9. Close session: POST /v1/sessions/{session_id}/close
10. Integration test: multi-turn conversation in session

**Session Lifecycle:**
```
Request 1: POST /v1/agents/execute
  → No session_id provided
  → System creates new session
  → Creates/spawns agent
  → Returns session_id + result

Request 2: POST /v1/agents/execute?session_id=sess-123
  → Session found
  → Reuses existing agent
  → Preserves context and memory
  → Returns result

Request 3 (after 1 hour idle): POST with session_id
  → Session expired
  → System returns 410 Gone
  → Client creates new session
```

**Storage Schema:**
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    agent_id UUID NOT NULL,
    user_id UUID NOT NULL,
    workspace_id UUID NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    metadata JSONB,                    -- cwd, tools, parameters
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_agent ON sessions(agent_id);
```

**Task Breakdown:**
- Design session model (Pydantic)
- Implement session creation and retrieval
- Implement session reuse (agent reuse)
- Implement session timeout (1 hour idle)
- Implement hot/cold storage (Redis + DB)
- Create session endpoints (get, list, close)
- Add comprehensive tests
- Document session management

**Depends On:** Story 3.1
**Blocked By:** None
**Points:** 13

---

### Story 3.6: Agent Status & Monitoring Endpoints
**As an** operator
**I want** to query agent status and resource usage
**So that** I can monitor and debug agent behavior

**Acceptance Criteria:**
1. GET /v1/agents - list all agents
2. GET /v1/agents/{agent_id} - get agent details
3. GET /v1/agents/{agent_id}/logs - get agent logs
4. Response includes: status, memory, CPU, cwd, created_at, last_activity
5. Pagination support (limit, offset)
6. Real-time updates: memory and CPU measured at request time
7. Log filtering: by level (debug, info, warning, error)
8. Integration test: query agents, verify metrics

**Agent Status Response:**
```json
GET /v1/agents/agent-123
{
  "agent_id": "agent-123",
  "status": "running",
  "cwd": "/home/user/project",
  "created_at": "2024-12-02T10:30:00Z",
  "last_activity": "2024-12-02T10:35:15Z",
  "resource_usage": {
    "memory_mb": 125,
    "cpu_percent": 45,
    "open_files": 23
  },
  "tools": ["entity.create", "entity.read"],
  "session_count": 1,
  "uptime_seconds": 315
}
```

**Task Breakdown:**
- Create agent listing endpoint
- Create agent details endpoint
- Create log retrieval endpoint
- Implement real-time metrics collection
- Add pagination support
- Create comprehensive tests
- Document monitoring endpoints

**Depends On:** Story 3.1
**Blocked By:** None
**Points:** 13

---

### Story 3.7: API Testing & Documentation
**As a** developer
**I want** complete API documentation and test coverage
**So that** I can integrate with the API confidently

**Acceptance Criteria:**
1. OpenAPI/Swagger spec generated automatically
2. All endpoints documented (request, response, error codes)
3. Example requests and responses
4. Authentication and authorization documented
5. Rate limiting documented
6. Error codes with descriptions
7. Postman collection included
8. 50+ integration tests, >80% coverage
9. Load tests: 1000 req/min sustained
10. Documentation updated with each change

**Documentation Artifacts:**
- `docs/api/AGENT_API.md` - Full API reference
- `openapi.json` - OpenAPI spec (auto-generated)
- `docs/api/examples.md` - Usage examples
- Postman collection (importable)
- Swagger UI endpoint: `/v1/docs`

**Task Breakdown:**
- Auto-generate OpenAPI spec (FastAPI)
- Create comprehensive API documentation
- Create example requests and responses
- Create Postman collection
- Write 50+ integration tests
- Run load tests (1000 req/min)
- Create troubleshooting guide
- Set up API versioning strategy

**Depends On:** All stories 3.1-3.6
**Blocked By:** None
**Points:** 13

---

## Epic 3 Summary
**Total Points:** 110
**Stories:** 7 user stories
**Key Deliverables:**
- High-performance agent execution API
- Streaming SSE for real-time output
- Sub-agent spawning (hierarchical)
- Direct tool invocation
- Session management (multi-turn)
- Agent monitoring endpoints
- Complete API documentation and tests

**Exit Criteria:**
- All 7 stories passing acceptance tests
- API latency targets met (<1s p95)
- Streaming latency <100ms per event
- >80% test coverage
- Load tests at 1000 req/min pass
- OpenAPI spec generated and documented
- Ready for client integration

---

# Epic 4: LLM-Compatible API

## Epic Goal
Provide OpenAI-compatible Chat API endpoints so existing OpenAI client libraries and tools integrate seamlessly.

## Success Criteria
- [ ] POST /v1/chat/completions works with openai-python client
- [ ] Tool calling fully compatible
- [ ] Streaming compatible with openai-python streaming
- [ ] Error responses match OpenAI format
- [ ] Model selection transparent
- [ ] >90% test coverage with real OpenAI client
- [ ] Load tests at 500 req/min pass

---

## User Stories

### Story 4.1: OpenAI Chat Completions Endpoint
**As a** OpenAI user
**I want** to use /v1/chat/completions like OpenAI API
**So that** I can use existing openai-python code without changes

**Acceptance Criteria:**
1. Endpoint: POST /v1/chat/completions
2. Request format: identical to OpenAI Chat API
3. Response format: identical to OpenAI
4. Supports parameters: model, messages, temperature, top_p, max_tokens, stream
5. Model mapping: "gpt-4" → Claude for capability match
6. Handles tool_calls: format as function calls
7. Error responses: same format as OpenAI
8. Token counting: accurate usage reporting
9. Works with: openai-python, openai-js, curl, Postman
10. Integration test: openai.OpenAI client works unmodified

**Request Format (OpenAI standard):**
```json
POST /v1/chat/completions
{
  "model": "gpt-4",
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi!"}
  ],
  "temperature": 0.7,
  "top_p": 1.0,
  "max_tokens": 2048,
  "stream": false
}
```

**Response Format (OpenAI standard):**
```json
{
  "id": "chatcmpl-123abc",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 12,
    "total_tokens": 22
  }
}
```

**Task Breakdown:**
- Create `/v1/chat/completions` endpoint
- Implement request parsing (Pydantic validation)
- Implement message format conversion
- Implement model mapping
- Implement response formatting
- Implement token counting
- Create comprehensive tests
- Document compatibility

**Depends On:** None (can start in parallel)
**Blocked By:** None
**Points:** 13

---

### Story 4.2: Tool Calling Compatibility
**As a** developer
**I want** to use tool calling with OpenAI-compatible API
**So that** agents can call functions naturally

**Acceptance Criteria:**
1. Request: `tools` array in OpenAI format
2. Tool format: function object with name, description, parameters (JSON schema)
3. Response: `tool_calls` in message
4. Tool choice: "auto", "none", or specific tool name
5. Parallel tool calls: support multiple concurrent calls
6. Tool result: client sends back via message (role: "tool")
7. Automatic tool execution (optional): agent calls tools directly
8. Error handling: invalid tool, missing parameters
9. Integration test: end-to-end tool calling workflow

**Tool Calling Format:**
```json
Request with tools:
{
  "messages": [...],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "entity_create",
        "description": "Create a new entity",
        "parameters": {
          "type": "object",
          "properties": {
            "name": {"type": "string"},
            "type": {"type": "string"}
          },
          "required": ["name"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}

Response with tool calls:
{
  "choices": [
    {
      "message": {
        "tool_calls": [
          {
            "id": "call_123",
            "type": "function",
            "function": {
              "name": "entity_create",
              "arguments": "{\"name\": \"Product\", \"type\": \"product\"}"
            }
          }
        ]
      }
    }
  ]
}

Client sends result back:
{
  "messages": [
    {...previous messages...},
    {"role": "assistant", "tool_calls": [...above...]},
    {"role": "tool", "tool_call_id": "call_123", "content": "{\"id\": \"123\"}"}
  ]
}
```

**Task Breakdown:**
- Implement tools array parsing
- Implement tool schema validation (JSON schema)
- Implement tool_calls response formatting
- Implement tool execution (optional agent feature)
- Implement tool result processing
- Create comprehensive tests
- Document tool calling patterns

**Depends On:** Story 4.1
**Blocked By:** None
**Points:** 13

---

### Story 4.3: Streaming Compatibility
**As a** developer
**I want** streaming to work with OpenAI client libraries
**So that** I get real-time responses

**Acceptance Criteria:**
1. Stream parameter: `stream: true` in request
2. Response: SSE (Server-Sent Events) OpenAI format
3. Event format: `data: {"delta": ...}` (OpenAI standard)
4. Events:
   - `delta.content`: text chunk
   - `delta.tool_calls`: tool call information
   - `finish_reason`: stop, length, tool_calls
5. Works with: openai.OpenAI(stream=True)
6. Handles reconnection gracefully
7. Integration test: openai-python streaming works
8. Performance: <100ms latency per event

**Streaming Response Format:**
```
data: {"id":"chatcmpl-123","choices":[{"delta":{"role":"assistant"},"index":0}]}

data: {"id":"chatcmpl-123","choices":[{"delta":{"content":"Hello"},"index":0}]}

data: {"id":"chatcmpl-123","choices":[{"delta":{"content":" there"},"index":0}]}

data: {"id":"chatcmpl-123","choices":[{"delta":{},"finish_reason":"stop","index":0}]}

data: [DONE]
```

**Task Breakdown:**
- Implement OpenAI streaming format
- Implement delta events for content and tool calls
- Implement SSE endpoint for streaming
- Add streaming tests with openai-python
- Document streaming usage

**Depends On:** Story 4.1
**Blocked By:** None
**Points:** 13

---

### Story 4.4: Model Aliasing & Capability Adaptation
**As a** API user
**I want** model names to be flexible (gpt-4, gpt-3.5, etc.)
**So that** my code is portable across APIs

**Acceptance Criteria:**
1. Support model aliases: gpt-4 → claude-sonnet-4, gpt-3.5 → claude-opus, etc.
2. Model mapping configurable via environment variable
3. Capability matching: match OpenAI capability to Claude model
4. Fallback: unknown models use default (claude-sonnet-4)
5. Response includes actual model used (transparency)
6. Integration test: gpt-4 request → claude-sonnet-4 execution

**Model Mapping (Default):**
```python
MODEL_ALIASES = {
    "gpt-4": "claude-sonnet-4",           # High capability
    "gpt-4-turbo": "claude-sonnet-4",     # High capability
    "gpt-3.5-turbo": "claude-opus",       # Cost-optimized
    "gpt-3.5": "claude-opus",
}
```

**Capability Matching:**
```
gpt-4 (high capability) → claude-sonnet-4
  - Both: high intelligence, moderate speed, high cost
  - Context: 128k tokens
  - Tool calling: yes

gpt-3.5-turbo (low cost) → claude-opus
  - Both: fast inference, low cost
  - Context: 200k tokens
  - Tool calling: yes
```

**Task Breakdown:**
- Implement model aliasing configuration
- Implement capability matching logic
- Add configuration via environment variable
- Create comprehensive tests
- Document model mapping

**Depends On:** Story 4.1
**Blocked By:** None
**Points:** 13

---

### Story 4.5: Compatibility Testing with OpenAI Clients
**As a** QA engineer
**I want** comprehensive compatibility tests with real OpenAI libraries
**So that** users can trust the integration

**Acceptance Criteria:**
1. Test with openai-python (latest version)
2. Test with openai-js (TypeScript)
3. Test scenarios:
   - Simple chat completion
   - Streaming completion
   - Tool calling
   - Error handling
4. 50+ test cases
5. >90% test coverage
6. Performance within 10% of OpenAI API
7. Error responses match OpenAI format
8. Unit and integration tests

**Test Scenarios:**
```python
# Test 1: Simple completion with openai-python
client = openai.OpenAI(api_key="test", base_url="http://localhost:8000/v1")
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=100
)
assert response.choices[0].message.content

# Test 2: Streaming with openai-python
with client.chat.completions.create(
    model="gpt-4",
    messages=[...],
    stream=True
) as stream:
    for text in stream.text_stream:
        assert text

# Test 3: Tool calling with openai-python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[...],
    tools=[...],
    tool_choice="auto"
)
assert response.choices[0].message.tool_calls

# Test 4: Error handling
try:
    client.chat.completions.create(model="invalid-model")
except openai.BadRequestError:
    pass  # Expected
```

**Task Breakdown:**
- Set up openai-python and openai-js test clients
- Create 50+ compatibility test cases
- Test streaming, tool calling, errors
- Run performance comparison tests
- Document test results
- Create CI/CD integration tests

**Depends On:** Story 4.1, 4.2, 4.3
**Blocked By:** None
**Points:** 13

---

## Epic 4 Summary
**Total Points:** 80
**Stories:** 5 user stories
**Key Deliverables:**
- OpenAI-compatible /v1/chat/completions endpoint
- Tool calling fully compatible
- Streaming with OpenAI format
- Model aliasing and capability matching
- Comprehensive OpenAI client compatibility tests

**Exit Criteria:**
- All 5 stories passing acceptance tests
- openai-python and openai-js clients work unmodified
- Tool calling verified
- Streaming compatible
- >90% test coverage
- Error responses match OpenAI format exactly
- Ready for client integration

---

# Epic 5: Agent Monitoring & Terminal UI

## Epic Goal
Provide intuitive terminal interface for real-time agent monitoring, execution, and management.

## Success Criteria
- [ ] TUI starts in <500ms
- [ ] Real-time agent monitoring (update latency <1s)
- [ ] Responsive to terminal resize
- [ ] Agent execution in TUI working
- [ ] Log streaming visible
- [ ] System resource gauges
- [ ] >75% TUI code coverage
- [ ] Usable on 80x24 terminal

---

## User Stories

### Story 5.1: TUI Foundation & Component Library
**As a** operator
**I want** a responsive terminal interface for agent management
**So that** I can monitor and control agents in the CLI

**Acceptance Criteria:**
1. Built with Textual framework (Python)
2. Responsive to terminal resize (down to 80x24)
3. Color scheme: dark theme with good contrast
4. Performance: <500ms startup, <100ms per update
5. Component library: reusable widgets
6. Graceful degradation for small terminals
7. Support for mouse and keyboard input
8. >75% TUI code coverage

**Components:**
- AgentListWidget: filterable, sortable agent list
- AgentDetailWidget: agent details with tabs
- LogViewerWidget: scrollable log display
- InputPanel: command/prompt input with history
- StatusBar: system resource gauges
- ProgressBar: task progress visualization

**Task Breakdown:**
- Create Textual application structure
- Define color scheme and styles
- Create AgentListWidget with selection
- Create AgentDetailWidget with tabs
- Create LogViewerWidget with filtering
- Create InputPanel with history
- Create StatusBar with resource gauges
- Create comprehensive component tests

**Depends On:** Epic 1, 3
**Blocked By:** None
**Points:** 21

---

### Story 5.2: Real-Time Agent Monitoring
**As an** operator
**I want** real-time updates of agent status and resource usage
**So that** I can see what's happening right now

**Acceptance Criteria:**
1. Agent list updates every 1-2 seconds
2. Status display: INITIALIZING, READY, RUNNING, PAUSED, SHUTDOWN, ERROR
3. Memory usage: current MB / limit MB (gauge)
4. CPU usage: current % (gauge)
5. Uptime: display in human-readable format
6. Last activity: timestamp or "just now", "5 min ago", etc.
7. Open files: count of open file descriptors
8. Log streaming: latest logs visible in real-time
9. Color coding: green (healthy), yellow (warning), red (error)
10. Integration test: monitor 10 agents simultaneously

**Display Example:**
```
Active Agents: 12 | Memory: 1.2GB / 2GB | CPU: 35% | Uptime: 2h 15m

Agent ID      Status      Memory    CPU    CWD                Files
agent-123     RUNNING     125/512MB  45%   /home/user/proj    23
agent-456     READY        85/512MB   0%   /var/www/app       12
agent-789     PAUSED      100/512MB   5%   /tmp/test          18
agent-abc     ERROR        95/512MB  15%   (error)            (-)
```

**Task Breakdown:**
- Implement agent status polling (1-2s interval)
- Implement metric collection (memory, CPU, uptime)
- Implement real-time display updates
- Add log streaming integration
- Create color-coded status display
- Create integration tests
- Document monitoring strategy

**Depends On:** Story 5.1
**Blocked By:** None
**Points:** 21

---

### Story 5.3: Agent Executor Screen
**As a** developer
**I want** to execute agents directly from the TUI
**So that** I can interact with agents interactively

**Acceptance Criteria:**
1. Executor screen: large prompt input area
2. Prompt input: multi-line, editable, history navigation
3. Execute button: (Ctrl+Enter or button click)
4. Output display: streaming agent output
5. Tool call visualization: show tool name, input, result
6. Progress indicator: show execution status
7. Error display: show errors with stack trace (if applicable)
8. Result formatting: pretty-print structured results
9. Integration test: execute agent, see streaming output

**Executor Screen Layout:**
```
┌──────────────────────────────────────────────────┐
│ Agent: agent-123 | Status: RUNNING               │
├──────────────────────────────────────────────────┤
│ Prompt:                                          │
│ ┌──────────────────────────────────────────────┐ │
│ │ Create a new entity with the following:       │ │
│ │ - Name: "Product Launch"                      │ │
│ │ - Type: "product"                             │ │
│ │                                                │ │
│ │ _                                              │ │
│ └──────────────────────────────────────────────┘ │
│ [Execute] [Clear] [Copy] [Open Editor]           │
├──────────────────────────────────────────────────┤
│ Output:                                          │
│ [Tool] entity.create                             │
│ ├─ name: "Product Launch"                        │
│ ├─ type: "product"                               │
│ └─ [✓] Success - entity_id: 550e8400-e29b        │
│                                                   │
│ [Agent] I've created the product entity...       │
└──────────────────────────────────────────────────┘
```

**Task Breakdown:**
- Create executor screen component
- Implement prompt input (multi-line)
- Implement streaming output display
- Implement tool call visualization
- Implement error display
- Create integration tests
- Document executor usage

**Depends On:** Story 5.1, Epic 3
**Blocked By:** None
**Points:** 21

---

### Story 5.4: Multi-Screen Navigation
**As an** operator
**I want** to switch between different monitoring screens
**So that** I can see different aspects of the system

**Acceptance Criteria:**
1. Main screen: agent list + details (default)
2. Executor screen: agent execution interface
3. Monitor screen: system resource graphs
4. Navigation: Tab key or menu
5. Screen transitions: smooth, no flickering
6. Keyboard shortcuts: documented and intuitive
7. Back button: return to previous screen
8. Help screen: keyboard shortcuts and commands
9. Integration test: navigate between all screens

**Screen Navigation Map:**
```
Main Screen (agent list + details)
  ├─ Tab → Executor Screen (run agents)
  │   └─ Esc → Main
  ├─ Shift+Tab → Monitor Screen (graphs)
  │   └─ Esc → Main
  ├─ H → Help (keyboard shortcuts)
  │   └─ Esc → Main
  └─ Q → Quit (with confirmation)
```

**Task Breakdown:**
- Create screen manager for navigation
- Implement screen transitions
- Define keyboard shortcuts
- Create help screen
- Add keyboard shortcut documentation
- Create navigation tests
- Document all screens and shortcuts

**Depends On:** Story 5.1, 5.2, 5.3
**Blocked By:** None
**Points:** 13

---

### Story 5.5: Responsive Design & Small Terminals
**As a** terminal user
**I want** the TUI to work on small terminals (80x24)
**So that** I can use it on minimal setups

**Acceptance Criteria:**
1. Minimum supported: 80x24 terminal
2. Responsive: adjust layout based on terminal size
3. Collapse mode: single-column layout for <100 columns
4. Hide optional: hide non-critical panels if space limited
5. Horizontal scroll: fallback for content >terminal width
6. No truncation: show at least first N characters
7. Graceful degradation: still usable at minimum size
8. Integration test: render at 80x24, 120x40, 200x60 terminals

**Responsive Breakpoints:**
```
≤80 cols:      Single column, collapse all panels
81-120 cols:   Two columns, hide optional panels
121-160 cols:  Three columns, show all panels
>160 cols:     Full width, optimal layout
```

**Task Breakdown:**
- Implement responsive layout system
- Create responsive breakpoints
- Test on different terminal sizes
- Add scrolling for content overflow
- Create responsive tests
- Document terminal size requirements

**Depends On:** Story 5.1
**Blocked By:** None
**Points:** 13

---

### Story 5.6: TUI Testing & Polish
**As a** user
**I want** a polished, bug-free TUI
**So that** I can trust and enjoy using it

**Acceptance Criteria:**
1. No visual glitches or flicker
2. No crashes on resize or input
3. Color scheme consistent and accessible
4. Help text inline and clear
5. Error messages helpful (not cryptic)
6. Keyboard shortcuts intuitive
7. Performance: no lag on monitor updates
8. Accessibility: high contrast, readable fonts
9. 50+ integration tests
10. >75% TUI code coverage

**Testing Scenarios:**
- Resize terminal while agent executing
- Rapid navigation between screens
- Input invalid commands
- Receive rapid agent updates
- Stream large output
- Memory pressure (many agents)
- Keyboard input validation
- Error message display

**Task Breakdown:**
- Create comprehensive integration tests
- Test responsiveness and performance
- Test keyboard/mouse input edge cases
- Test accessibility (color contrast, font sizes)
- Create user guide with screenshots
- Polish UI details (spacing, alignment)
- Document keyboard shortcuts
- Create troubleshooting guide

**Depends On:** All story 5.* stories
**Blocked By:** None
**Points:** 21

---

## Epic 5 Summary
**Total Points:** 150
**Stories:** 6 user stories
**Key Deliverables:**
- Textual-based terminal UI
- Real-time agent monitoring
- Interactive agent executor
- Multi-screen navigation
- Responsive to small terminals
- Fully tested and polished

**Exit Criteria:**
- All 6 stories passing acceptance tests
- TUI works on 80x24 terminals
- Real-time monitoring verified (<1s latency)
- Agent execution working in TUI
- Streaming output visible
- >75% code coverage
- User guide complete
- Ready for production use

---

# Epic 6: Integration & System Hardening

## Epic Goal
Integrate all components (Agent Layer with Brain Layer), perform comprehensive testing, ensure SWE Bench readiness, and prepare for production deployment.

## Success Criteria
- [ ] Phase 3 (Brain) + Phase 5 (Agent) fully integrated
- [ ] SmartCP tools integrated and working
- [ ] SWE Bench evaluation setup complete
- [ ] 200-agent load test passes
- [ ] Multi-agent coordination verified
- [ ] Production documentation complete
- [ ] Deployment guide ready
- [ ] >80% overall test coverage

---

## User Stories

### Story 6.1: Brain Layer Integration
**As a** system architect
**I want** memory system integrated with agent orchestration
**So that** agents learn from past executions

**Acceptance Criteria:**
1. Agent has MemorySystem instance (from Phase 3)
2. Episodic memory: store agent execution history
   - Task, inputs, outputs, result, duration
   - Retrieve similar tasks for learning
3. Semantic memory: store learned facts
   - Common tool patterns (which tools work together)
   - Common errors and recovery strategies
   - Tool performance characteristics
4. Working memory: current execution context
   - Available tools, CWD, recent results
   - Task history (last 5 tasks in current session)
5. Memory integration points:
   - On task completion: store in episodic memory
   - On error: log failure for recovery learning
   - On initialization: load relevant semantic memory
   - On execution: consult working memory for context
6. Integration test: multi-turn agent session improves with memory

**Learning Flow:**
```
Agent execution 1:
  Task: "Create entity"
  → Episode stored in memory
  → Patterns extracted to semantic memory

Agent execution 2:
  Task: "Create related entities"
  → Recall similar episodes
  → Suggest tool sequences from semantic memory
  → Execute more efficiently
  → Store new patterns

Over time:
  Agent improves task completion rate
  Agent reduces tool invocation errors
  Agent finds optimal tool sequences
```

**Task Breakdown:**
- Integrate MemorySystem with Agent Framework
- Implement episodic storage interface
- Implement semantic learning from outcomes
- Implement working memory context
- Create integration tests
- Measure learning improvement
- Document memory integration

**Depends On:** Epic 1, Phase 3 (Brain Layer)
**Blocked By:** None
**Points:** 21

---

### Story 6.2: SmartCP Tool Integration
**As a** developer
**I want** to call any smartcp tool from an agent
**So that** agents have full access to code operations

**Acceptance Criteria:**
1. Agent tool registry includes all smartcp tools
2. Tool invocation: agent → smartcp tool
3. Tool result: structured, usable by agent
4. Tools can access agent's working directory
5. Tool errors handled gracefully (non-fatal)
6. Tool caching: cache tool results for identical inputs
   - Cache hit latency: <10ms (vs 500ms execution)
7. Tool integration test: call 10 different smartcp tools
8. Performance: tool latency <500ms (p95)

**Tool Integration Points:**
```
Agent execution:
  1. Parse tool calls from LLM
  2. Route to smartcp tool registry
  3. Execute tool with agent context (CWD, files)
  4. Capture tool result
  5. Return to agent
  6. Cache result (same inputs → same output)

Tool result caching:
  Input: {tool_name, parameters}
  Hash: SHA256({tool_name, parameters})
  Cache key: hash
  TTL: 5 minutes
  Speedup: 40x-50x for repeated operations
```

**Task Breakdown:**
- Create smartcp tool registry adapter
- Implement tool invocation routing
- Implement working directory passing to tools
- Implement tool result caching (LRU + TTL)
- Implement error handling (tool crash recovery)
- Create integration tests
- Measure tool performance

**Depends On:** Epic 1, Epic 3
**Blocked By:** None
**Points:** 21

---

### Story 6.3: Multi-Agent Coordination Tests
**As a** QA engineer
**I want** comprehensive multi-agent scenarios tested
**So that** I can verify coordination works correctly

**Acceptance Criteria:**
1. Sequential workflow: Agent A → Agent B → Agent C
   - A creates entity, B reads and updates, C deletes
   - Verify correct data flow
   - Verify no race conditions
2. Parallel workflow: 10 agents create entities simultaneously
   - Verify no ID collisions
   - Verify all succeed
   - Verify no corrupted data
3. Hierarchical workflow: Parent → 2 children → 4 grandchildren
   - Verify parent-child communication
   - Verify result aggregation
   - Verify timeout handling
4. Failure recovery: One agent in group fails
   - Others continue (no cascade)
   - Failed agent restarts
   - Results remain consistent
5. Resource contention: 100 agents accessing DB
   - Verify no connection exhaustion
   - Verify query latency stays <100ms
   - Verify resource pooling works
6. Load test: 200 agents, 5 minutes
   - Memory: <2GB
   - CPU: <4 cores
   - FDs: <1000
   - No crashes or deadlocks

**Test Scenarios:**
```
Scenario 1: Sequential
  Agent-A: create entity
  Agent-B: read, update
  Agent-C: delete
  Verify: data consistency across agents

Scenario 2: Parallel (10 agents)
  All create entities simultaneously
  Verify: no ID collisions, no corruption

Scenario 3: Hierarchical (1 parent, 2 children, 4 grandchildren)
  Parent spawns 2 children
  Each child spawns 2 grandchildren
  All return results to parent
  Parent aggregates and returns

Scenario 4: Failure Recovery
  Kill one of 3 executing agents
  Other 2 continue
  Failed agent restarts
  Overall task completes

Scenario 5: Resource Contention
  100 agents simultaneously query DB
  Measure: latency, connection count, CPU
  Verify: no exhaustion
```

**Task Breakdown:**
- Create multi-agent test scenarios
- Create failure injection (agent kill, timeout)
- Create load testing harness
- Implement resource monitoring
- Create comprehensive test report
- Document coordination patterns

**Depends On:** Epic 1
**Blocked By:** None
**Points:** 21

---

### Story 6.4: Performance Testing & Optimization
**As a** performance engineer
**I want** all performance targets verified
**So that** I can deploy with confidence

**Acceptance Criteria:**
1. Agent spawn latency: <200ms (measured)
2. Message routing: <10ms (p99)
3. Tool invocation: <500ms (p95)
4. API latency: <1s (p95)
5. Memory: <100MB per agent, <2GB for 200 agents
6. CPU: <4 cores for 200 agents
7. File descriptors: <1000 for 200 agents
8. Memory growth rate: linear, no leaks
9. Bottleneck identification and documented
10. Optimization opportunities documented for future

**Benchmarks to Run:**
```
Latency benchmarks:
  - Agent spawn (cold): 2000ms (baseline)
  - Agent spawn (warm): 100ms (warm pool)
  - Message routing: 5-10ms
  - Tool invocation: 100-500ms
  - API /execute: 500-2000ms
  - API /tools: 50-100ms

Resource benchmarks:
  - Single agent: 100MB memory
  - 50 agents: 5GB memory (5% overhead)
  - 100 agents: 10GB memory (10% overhead)
  - 200 agents: 20GB memory (20% overhead)
  - Memory growth: linear with agent count

Stress test:
  - 100 agents: 5 minute run
  - 200 agents: 5 minute run
  - Measure: memory, CPU, FDs, crashes

Optimization targets:
  - 200 agents: <2GB (40x reduction from unshared)
  - Tool cache hit: >80%
  - Memory footprint: <100MB per agent
```

**Task Breakdown:**
- Create load testing framework
- Run latency benchmarks
- Run resource benchmarks
- Run stress tests (100, 200, 300 agents)
- Identify bottlenecks
- Create optimization recommendations
- Document results in report
- Archive benchmark data for regression detection

**Depends On:** Epic 1
**Blocked By:** None
**Points:** 21

---

### Story 6.5: SWE Bench Integration & Evaluation
**As a** researcher
**I want** agent performance measured on SWE Bench
**So that** I can compare against other agents

**Acceptance Criteria:**
1. SWE Bench harness set up (using Harbor if available)
2. Evaluation script: run agent on benchmark problem
3. Metrics: success rate, time to solve, cost
4. Results reporting: structured output (JSON)
5. Baseline: run on 50 problems, establish baseline
6. Target: 15-20% success rate (vs 5-10% baseline)
7. Performance log: track improvements over time
8. Integration test: successful problem-solving demonstration

**SWE Bench Integration:**
```
Harness:
  1. Load problem from SWE Bench dataset
  2. Set up environment (clone repo, install deps)
  3. Create isolated workspace
  4. Give agent problem statement
  5. Let agent execute (timeout: 5 minutes)
  6. Check solution (run tests, verify diff)
  7. Record: success/failure, duration, tools used

Results format:
  {
    "problem_id": "django-123",
    "status": "success|failure|timeout",
    "duration_seconds": 45,
    "tools_used": ["entity.create", "file.read"],
    "tokens_consumed": 2500,
    "cost_usd": 0.15
  }

Reporting:
  Success rate: 15.2% (8/50 problems)
  Average time: 45 seconds
  Average cost: $0.15
  Common failure patterns: [...]
```

**Task Breakdown:**
- Set up SWE Bench evaluation harness
- Create problem solver script
- Implement metrics collection
- Run baseline evaluation (50 problems)
- Analyze results and failure patterns
- Create performance report
- Document evaluation methodology

**Depends On:** Epic 1, 3, 6.1, 6.2
**Blocked By:** None
**Points:** 21

---

### Story 6.6: Documentation & Deployment
**As an** operator
**I want** complete deployment guide and documentation
**So that** I can run the system in production

**Acceptance Criteria:**
1. Deployment guide: Docker, Kubernetes, bare metal
2. Configuration reference: all environment variables
3. Troubleshooting guide: common issues and solutions
4. Monitoring setup: Prometheus/Grafana integration
5. Logging setup: structured logging configuration
6. Scaling guide: how to scale to 200+ agents
7. Architecture documentation: system design overview
8. API documentation: complete OpenAPI spec
9. Integration guide: connecting Brain + Agent layers
10. Changelog: version history and breaking changes

**Documentation Artifacts:**
```
docs/deployment/
  ├── DEPLOYMENT_GUIDE.md        # Docker, K8s, bare metal
  ├── CONFIGURATION.md            # Environment variables
  ├── TROUBLESHOOTING.md          # Common issues
  ├── MONITORING.md               # Prometheus/Grafana
  ├── LOGGING.md                  # Structured logging
  ├── SCALING.md                  # Horizontal scaling
  └── security/
      └── SECURITY_GUIDE.md       # Security best practices

docs/architecture/
  ├── SYSTEM_OVERVIEW.md          # High-level architecture
  ├── COMPONENTS.md               # Component descriptions
  ├── DATA_FLOW.md                # Data flow diagrams
  ├── INTEGRATION.md              # Brain + Agent integration
  └── PERFORMANCE.md              # Performance characteristics

docs/api/
  ├── AGENT_API.md                # Agent control API
  ├── OPENAI_API.md               # OpenAI-compatible API
  ├── examples/                   # Example requests/responses
  └── openapi.json                # OpenAPI specification

docs/operations/
  ├── HEALTH_CHECKS.md            # Monitoring health
  ├── BACKUP_RECOVERY.md          # Backup and recovery
  ├── UPGRADE.md                  # Upgrade procedures
  └── INCIDENT_RESPONSE.md        # Incident response
```

**Task Breakdown:**
- Create deployment guide (Docker, K8s, bare metal)
- Create configuration reference
- Create troubleshooting guide (30+ scenarios)
- Create monitoring setup guide
- Create architecture documentation
- Create API documentation (OpenAPI)
- Create operational runbooks
- Create security guide

**Depends On:** All epics
**Blocked By:** None
**Points:** 21

---

## Epic 6 Summary
**Total Points:** 140
**Stories:** 6 user stories
**Key Deliverables:**
- Brain layer integration (memory + learning)
- SmartCP tool integration (full access)
- Multi-agent coordination tests (5 scenarios)
- Performance testing and optimization
- SWE Bench evaluation setup and baseline
- Complete deployment and operational documentation

**Exit Criteria:**
- All 6 stories passing acceptance tests
- Brain + Agent layers fully integrated
- 200-agent load test passes
- SWE Bench baseline established (15-20% target)
- All performance targets verified
- Documentation complete and reviewed
- Ready for production deployment

---

# Functional Requirements Matrix

## High-Level FRs

| ID | Requirement | Epic | Priority | Testability |
|---|---|---|---|---|
| **FR-1** | Multi-agent orchestration supporting 50-200+ concurrent agents | Epic 1 | P0 | Load test 200 agents |
| **FR-2** | Agent resource pooling (DB, HTTP, tools) preventing exhaustion | Epic 1 | P0 | Memory profile <2GB |
| **FR-3** | Per-agent working directory isolation without `os.chdir()` | Epic 2 | P0 | Multi-agent file ops verify isolation |
| **FR-4** | Atomic file operations with <1% corruption rate | Epic 2 | P0 | Concurrent write stress test |
| **FR-5** | Agent-optimized API with streaming SSE support | Epic 3 | P0 | API latency <1s (p95), stream <100ms |
| **FR-6** | OpenAI-compatible API working with openai-python | Epic 4 | P0 | Client library integration test |
| **FR-7** | Terminal UI for real-time agent monitoring | Epic 5 | P1 | Render test on 80x24 terminal |
| **FR-8** | Brain layer integration (episodic + semantic memory) | Epic 6 | P0 | Learning improves over tasks |
| **FR-9** | SmartCP tool integration (all tools callable) | Epic 6 | P0 | Call 10 different tool types |
| **FR-10** | SWE Bench evaluation capability | Epic 6 | P1 | Baseline evaluation 50+ problems |

## Detailed Functional Requirements

### FR-1: Multi-Agent Orchestration
```
Agents spawned: 50, 100, 200, 300
Agent startup latency:
  - Cold: <2000ms
  - Warm pool: <200ms
Agent lifecycle: INITIALIZING → READY → RUNNING → SHUTDOWN
Failure detection: <60s
Auto-recovery: max 3 retries/hour
Message routing: <10ms latency
Communication: event-driven via message bus
```

### FR-2: Resource Pooling
```
Database connections:
  - Pool size: 5-50 connections
  - Reuse rate: >80%
  - Health check: every 60s

HTTP clients:
  - Connection reuse: >80%
  - Max concurrent: 20 per pool

Tool instance cache:
  - Max size: 100 items
  - TTL: 5 minutes
  - Hit rate: >80%
  - Speedup: 40x-50x

Memory results (200 agents):
  - Unshared: 40GB
  - Pooled: 2GB (20x reduction)
  - Growth rate: linear
```

### FR-3: Working Directory Isolation
```
Per-agent context state:
  - CWD: current working directory (absolute)
  - Project root: detected automatically
  - Git branch: if applicable
  - Environment variables: isolated

Operations:
  - Path resolution: relative → absolute (with boundary check)
  - CWD stack: save/restore around tool calls
  - Symlink resolution: canonical paths
  - Security: no escape outside project_root

10 agents in different dirs: no cross-pollution verified
```

### FR-4: Atomic File Operations
```
Write safety:
  - Write to temp file: /path/.filename.tmp.{random}
  - Sync to disk: fsync(fd)
  - Atomic rename: temp → final
  - Corruption rate: <1% (measured)

Locking:
  - Concurrent reads: allowed
  - Concurrent writes: same file → 1st wins
  - Mutex: fcntl (Unix) / msvcrt (Windows)
  - Timeout: 30s per operation

Stress test: 10 agents writing different files → all succeed
```

### FR-5: Agent-Optimized API
```
Endpoints:
  - POST /v1/agents/execute → agent_id, result, logs
  - POST /v1/agents/spawn → sub-agent spawning
  - POST /v1/agents/{id}/tools/{name} → tool invocation
  - GET /v1/agents → agent listing
  - GET /v1/agents/{id} → agent status/metrics

Streaming:
  - Content-Type: text/event-stream
  - Events: agent-start, tool-call, tool-result, agent-output, agent-complete, agent-error
  - Latency: <100ms per event
  - Keep-alive: comment every 30s

Session management:
  - Create on first request
  - Reuse within session (state preservation)
  - Timeout: 1 hour idle
  - Storage: Redis (hot) + DB (cold)
```

### FR-6: OpenAI-Compatible API
```
Endpoint: POST /v1/chat/completions
Format: identical to OpenAI Chat API
Model aliasing: gpt-4 → claude-sonnet-4
Tool calling: full support with tool_calls array
Streaming: OpenAI SSE format
Error responses: match OpenAI exactly

Client compatibility:
  - openai-python: works unmodified
  - openai-js: works unmodified
  - curl: works with no client library
```

### FR-7: Terminal UI
```
Screens:
  - Main: agent list + details + command input
  - Executor: agent execution interface
  - Monitor: resource graphs (CPU, memory, FDs)

Updates:
  - Refresh rate: 1-2 seconds
  - Real-time monitoring latency: <1 second
  - Streaming output: live visualization

Responsiveness:
  - Minimum terminal: 80x24
  - Startup: <500ms
  - Update render: <100ms
  - Responsive to resize: no data loss

Interaction:
  - Keyboard shortcuts: documented
  - Mouse support: optional
  - Help: built-in (H key)
```

### FR-8: Brain Layer Integration
```
Memory types integrated:
  - Episodic: store execution history
  - Semantic: learn patterns and common errors
  - Working: current context (last 5 tasks)

Learning feedback:
  - On success: store in episodic, extract patterns
  - On failure: log error, suggest recovery
  - Over time: improve task completion rate

Integration test:
  - Multi-turn session: 10 tasks
  - Measure: time to solve, tool sequence optimization
  - Verify: learning improves metrics over session
```

### FR-9: SmartCP Tool Integration
```
Tool access:
  - All smartcp tools callable from agents
  - Tool result: structured, parsed by agent
  - Working directory: passed to tools
  - Error handling: non-fatal (agent continues)

Caching:
  - Cache tool results (same inputs → same output)
  - TTL: 5 minutes
  - Hit rate: >80%
  - Latency reduction: 500ms → <10ms

Tool categories tested:
  - File operations: read, write, delete
  - Code analysis: parse, lint, test
  - Git operations: commit, push, diff
  - Entity operations: create, read, update
  - Relationship operations: link, unlink
```

### FR-10: SWE Bench Evaluation
```
Baseline:
  - Run on 50 benchmark problems
  - Measure: success rate, time, cost
  - Target: 15-20% success (vs 5-10% baseline)

Metrics:
  - Success rate: % of solved problems
  - Average time: seconds to solve
  - Average cost: USD per problem
  - Tool usage: which tools most effective

Failure analysis:
  - Common failure patterns
  - Tool errors analysis
  - Timeout analysis
  - Optimization opportunities
```

---

# User Story Prioritization

## Priority Matrix

| Priority | Definition | Story Count | Effort |
|----------|---|---|---|
| **P0 - Critical** | Must have for MVP, blocks other work | 25 | 400 points |
| **P1 - High** | Important, enables value delivery | 15 | 280 points |
| **P2 - Medium** | Nice to have, good to have features | 8 | 120 points |

## P0 Stories (Critical Path)

**Execution Order:**
1. Epic 1, Story 1.1-1.4 (Agent framework foundation)
2. Epic 2, Story 2.1-2.3 (Context & file ops)
3. Epic 3, Story 3.1-3.2 (Agent API basic + streaming)
4. Epic 4, Story 4.1 (OpenAI endpoint)
5. Epic 1, Story 1.5-1.7 (Failure recovery, persistence, scaling)
6. Epic 6, Story 6.1-6.2 (Brain integration, SmartCP)

**Total P0 Points:** 400 (8 weeks with 4 teams = 50 points/week/team)

---

# Cross-Cutting Concerns

## Authentication & Authorization

**Requirement:** API requests authenticated, agents isolated by workspace

**Stories Affected:** Epic 3, Epic 4
**Implementation:**
- API key validation on all requests
- Extract workspace_id from headers
- Agents restricted to workspace (file access, DB queries)
- Admin vs user roles

---

## Observability & Monitoring

**Requirement:** Complete visibility into agent execution and system health

**Stories Affected:** All epics
**Implementation:**
- Structured logging (JSON format)
- Metrics: Prometheus endpoints
- Tracing: correlation IDs across requests
- Alerts: memory, CPU, error rate thresholds

---

## Error Handling & Recovery

**Requirement:** Graceful failure, no data corruption, clear error messages

**Stories Affected:** All epics
**Implementation:**
- Try-catch at component boundaries
- Error codes with descriptions
- Fallback mechanisms (circuit breaker)
- Automatic retries with exponential backoff

---

## Performance & Scalability

**Requirement:** Support 50-200+ agents without resource exhaustion

**Stories Affected:** Epic 1, 3, 6
**Implementation:**
- Resource pooling (DB, HTTP, tools)
- Connection limits and timeouts
- Async operations (not blocking)
- Load testing and benchmarking

---

## Security

**Requirement:** Prevent unauthorized access, contain agent execution

**Stories Affected:** Epic 2, 3
**Implementation:**
- Path boundary enforcement (no escape)
- API authentication and authorization
- Input validation (prevent injection)
- Sandboxing (optional: containers/VMs)

---

## Testing Strategy

**Requirement:** Comprehensive coverage, all functionality validated

**Stories Affected:** All epics
**Implementation:**
- Unit tests: >85% coverage per component
- Integration tests: >75% coverage
- End-to-end tests: critical workflows
- Load tests: scale to 200 agents
- Performance tests: latency and resource usage

---

# Success Metrics

## Phase 5 Completion Definition

| Metric | Target | Measurement |
|---|---|---|
| **All Epics Complete** | 6/6 epics done | Story acceptance tests passing |
| **Test Coverage** | >80% overall | Code coverage tool (pytest-cov) |
| **Performance** | All targets met | Benchmark test results |
| **Documentation** | 100% | All docs reviewed and published |
| **Team Velocity** | 50 points/week/team | Actual points completed |
| **Code Quality** | <5 bugs per epic | Defect tracking |
| **Go/No-Go Decision** | GO for production | Pass readiness criteria |

---

**Total Estimated Effort: 800 story points**
**Timeline: 8 weeks (4 feature teams × 2-4 engineers each)**
**Status: READY FOR EXECUTION** 🚀

