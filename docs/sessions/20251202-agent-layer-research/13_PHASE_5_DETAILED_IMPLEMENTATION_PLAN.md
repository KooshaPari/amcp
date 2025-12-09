# Phase 5: Detailed Implementation Plan
**Status:** Implementation Readiness
**Total Effort:** ~300 hours
**Timeline:** 8 weeks (4 feature teams × 2-4 engineers each)
**Start Date:** Ready to begin immediately

---

## Executive Summary

Phase 5 breaks down into 6 core infrastructure components, each with specific task breakdown, dependencies, and acceptance criteria. The implementation is organized into 8 weekly sprints with clear deliverables.

**Critical Path:** Core 1 (Agent Framework) → Core 2 (Context Management) → Core 3/4 (APIs) → Core 5 (UI) → Core 6 (Integration)

**Go/No-Go:** ✅ **GO** - All unknowns resolved in Phase 4 research. Ready for immediate implementation.

---

## Part 1: Core Component Breakdown

### Core 1: Agent Framework & Orchestration (60 hours, Weeks 1-2)

**Overview:** Foundation for multi-agent orchestration with resource pooling and lifecycle management.

**Deliverable:** Fully functional agent spawning, coordination, and lifecycle management. All tests passing (>80% coverage).

#### Task 1.1: Agent Base Classes & Interfaces (8 hours)

**Objective:** Define abstract interfaces and base classes for agent execution.

**Files to Create:**
- `src/agents/__init__.py` - Agent module exports
- `src/agents/base.py` - Base agent class (≤350 lines)
- `src/agents/types.py` - Agent types and enums
- `src/agents/exceptions.py` - Agent-specific exceptions

**Task Breakdown:**
1. Define `Agent` abstract base class with lifecycle methods
   - `async def initialize()` - Setup phase
   - `async def execute(request: AgentRequest) -> AgentResponse` - Main execution
   - `async def shutdown()` - Cleanup phase
   - `async def health_check() -> HealthStatus` - Liveness check

2. Define `AgentRequest` and `AgentResponse` Pydantic models
   - Request includes: agent_id, user_id, workspace_id, prompt, tools, parameters
   - Response includes: status, result, logs, metadata, duration, resource_usage

3. Define agent states: INITIALIZING, READY, RUNNING, PAUSED, SHUTDOWN, ERROR

4. Exception hierarchy: AgentError, AgentTimeoutError, AgentResourceError, etc.

**Acceptance Criteria:**
- All 3 agent state transitions work correctly
- Exception hierarchy properly typed
- Base class cannot be instantiated directly
- 100% test coverage for types and exceptions
- No circular imports

**Tests:** `tests/unit/agents/test_base.py` (50+ lines)

---

#### Task 1.2: Agent Spawning & Coordination (10 hours)

**Objective:** Implement agent factory and coordination primitives.

**Files to Create:**
- `src/agents/factory.py` - Agent instantiation factory
- `src/agents/coordinator.py` - Multi-agent coordination (≤350 lines)
- `src/agents/protocols.py` - Protocol definitions

**Task Breakdown:**
1. Implement `AgentFactory` class
   - `async def spawn(agent_type: str, config: AgentConfig) -> Agent`
   - Handles instantiation, dependency injection, initialization
   - Timeout: <200ms per agent spawn (measured)
   - Resource bounds: <100MB per agent init

2. Implement `Coordinator` class for multi-agent orchestration
   - Manages pool of active agents
   - Routes requests to agents
   - Handles agent communication via message bus
   - Max pool size: 200 agents (configurable)

3. Define coordination protocols
   - Agent-to-agent message format (JSON)
   - Event broadcast protocol
   - Result aggregation patterns (fan-out, map-reduce)

**Acceptance Criteria:**
- Spawn 100 agents in <30 seconds
- Each agent initialization <200ms
- Coordinator tracks agent health and readiness
- Message routing latency <10ms p99
- 80%+ test coverage

**Tests:** `tests/unit/agents/test_factory.py`, `tests/unit/agents/test_coordinator.py` (100+ lines total)

---

#### Task 1.3: Resource Pooling & Management (10 hours)

**Objective:** Share expensive resources across agents to prevent exhaustion.

**Files to Create:**
- `src/agents/resources.py` - Resource pool management (≤350 lines)
- `src/agents/pools/__init__.py` - Pool submodule
- `src/agents/pools/db_pool.py` - Database connection pooling
- `src/agents/pools/http_pool.py` - HTTP client pooling
- `src/agents/pools/tool_pool.py` - Tool instance caching

**Task Breakdown:**
1. Implement `ResourcePool` base class
   - `acquire(timeout: float = 10)` - Get resource with timeout
   - `release(resource)` - Return resource to pool
   - `drain()` - Graceful shutdown

2. Implement database connection pooling
   - Min: 5 connections, Max: 50 connections
   - Lazy initialization, reuse across agents
   - Health check every 60 seconds
   - Timeout: 30 seconds per connection

3. Implement HTTP client pooling
   - Reuse httpx.AsyncClient across agents
   - Connection limits: 20 concurrent per pool
   - Keep-alive: 30 seconds
   - Timeout: 30 seconds per request

4. Implement tool instance caching
   - Cache instantiated tools
   - TTL: 5 minutes (configurable)
   - LRU eviction if cache >100 items
   - Estimated speedup: 40x (from research)

**Acceptance Criteria:**
- 200 agents share single DB pool without contention
- HTTP connection reuse verified (measure socket count)
- Tool cache hit rate >80%
- Memory usage <2GB for 200 agents (vs 40GB unshared)
- 85%+ test coverage

**Tests:** `tests/unit/agents/test_resources.py` (120+ lines)

---

#### Task 1.4: Agent Lifecycle Management (8 hours)

**Objective:** Handle agent initialization, execution, and cleanup with proper error handling.

**Files to Create:**
- `src/agents/lifecycle.py` - Lifecycle state machine (≤350 lines)

**Task Breakdown:**
1. Implement lifecycle state machine
   - Transitions: INITIALIZING → READY → RUNNING → READY → SHUTDOWN
   - Error states: ERROR (recoverable), FAILED (unrecoverable)
   - State transition hooks for logging and metrics

2. Implement warm pooling
   - Pre-initialize agents during idle periods
   - Reduce startup latency from 2s to <100ms
   - Pool size: 10 agents (configurable)
   - Initialization batch size: 2 agents in parallel

3. Implement cleanup and termination
   - Graceful shutdown: wait for in-flight requests (timeout: 30s)
   - Force termination if timeout exceeded
   - Resource cleanup: close DB connections, HTTP clients, files
   - Logging: capture all cleanup errors

4. Health monitoring
   - Liveness check every 30 seconds
   - Recovery strategy: restart failed agents
   - Max restarts: 3 per hour (circuit breaker)

**Acceptance Criteria:**
- State transitions atomic and logged
- Warm pool reduces startup from 2s to <200ms
- Graceful shutdown completes in <60s
- Health checks detect failures within 60s
- 100% test coverage for state machine

**Tests:** `tests/unit/agents/test_lifecycle.py` (100+ lines)

---

#### Task 1.5: State Persistence (10 hours)

**Objective:** Persist agent state to survive restarts and enable recovery.

**Files to Create:**
- `src/agents/persistence.py` - State persistence layer (≤350 lines)
- `src/agents/checkpointing.py` - Checkpoint management

**Task Breakdown:**
1. Define agent state model
   - Agent metadata: id, type, config, created_at
   - Execution context: user_id, workspace_id, working_dir
   - Agent progress: current_step, completed_steps, results
   - Resource usage: memory, CPU, open_files

2. Implement checkpoint creation
   - Create checkpoint every N steps (N=5, configurable)
   - Atomic write: write to temp file, atomic rename
   - Compression: gzip if size >1MB
   - Retention: keep last 10 checkpoints per agent

3. Implement state recovery
   - On agent restart, load latest checkpoint
   - Verify checkpoint integrity (CRC check)
   - Resume from checkpoint or restart if corrupted
   - Logging: capture all recovery events

4. Implement cleanup
   - Delete old checkpoints after agent termination
   - Archive long-running agent states to cold storage (S3)

**Storage Schema (Supabase):**
```sql
CREATE TABLE agent_state (
    id UUID PRIMARY KEY,
    agent_id UUID UNIQUE NOT NULL,
    checkpoint_version INT,
    state JSONB NOT NULL,
    resource_usage JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE agent_checkpoints (
    id UUID PRIMARY KEY,
    agent_id UUID NOT NULL REFERENCES agent_state(agent_id),
    checkpoint_num INT,
    state BYTEA NOT NULL, -- gzipped
    size_bytes INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(agent_id, checkpoint_num)
);
```

**Acceptance Criteria:**
- Checkpoint creation <500ms
- State recovery <200ms
- Checkpoint size <10MB (including compression)
- Recovery from corruption works correctly
- 80%+ test coverage

**Tests:** `tests/unit/agents/test_persistence.py`, `tests/integration/test_agent_recovery.py` (150+ lines)

---

#### Task 1.6: Testing & Validation (14 hours)

**Objective:** Comprehensive test suite covering agent framework functionality and integration.

**Test Strategy:**

1. **Unit Tests** (70 test cases, ≤30 lines each)
   - Agent base class behavior
   - Factory spawn/destroy
   - Coordinator message routing
   - Resource pool acquire/release
   - Lifecycle state transitions
   - Persistence checkpoint creation/loading
   - Exception handling

2. **Integration Tests** (30 test cases)
   - Spawn 10 agents, execute parallel tasks
   - Resource pool under load (100+ concurrent requests)
   - Agent failure and recovery
   - Coordinator multi-agent communication
   - State persistence and recovery
   - Warm pool initialization

3. **Performance Tests** (10 benchmarks)
   - Agent spawn latency: target <200ms
   - Message routing: target <10ms
   - Resource pool contention: target <5% overhead
   - State persistence: target <500ms
   - Recovery time: target <200ms

**Files to Create:**
- `tests/unit/agents/test_*.py` - Unit tests (8 files, 400+ lines total)
- `tests/integration/agents/test_*.py` - Integration tests (4 files, 300+ lines total)
- `tests/performance/test_agents.py` - Performance benchmarks (100+ lines)

**Acceptance Criteria:**
- All 110 tests passing
- >80% code coverage (target >85%)
- No performance regressions from baseline
- All error cases tested
- Documented test strategy and coverage report

---

**Core 1 Summary:**
- **Total Files:** 12 new files (agent module complete)
- **Total Lines:** ~1500 production code, ~800 test code
- **Integration Points:** Depends on Phase 3 (PreActPlanner), will feed APIs in Core 3/4
- **Exit Criteria:** All tests passing, performance targets met, ready for API integration

---

### Core 2: Context & Working Directory Management (40 hours, Weeks 1-2)

**Overview:** Manage per-agent execution context without process-level `os.chdir()`.

**Deliverable:** Production-ready context manager with file operations, CWD tracking, and state persistence.

#### Task 2.1: Project Abstraction (8 hours)

**Objective:** Abstract filesystem, Git repos, and project metadata.

**Files to Create:**
- `src/context/__init__.py` - Context module exports
- `src/context/models.py` - Project and context data models
- `src/context/project.py` - Project detection and management (≤350 lines)
- `src/context/git_integration.py` - Git repository integration

**Task Breakdown:**
1. Define `Project` model
   - Root path (canonical, absolute)
   - Name, description, type (python, nodejs, rust, etc.)
   - Package manager (pip, npm, cargo, etc.)
   - Structure info: src/, tests/, package.json, pyproject.toml, etc.
   - Git metadata if applicable: remote, current_branch

2. Implement project detection
   - Walk directory tree looking for markers:
     - Git: `.git/` directory
     - Python: `pyproject.toml`, `setup.py`, `requirements.txt`, `poetry.lock`
     - Node.js: `package.json`, `package-lock.json`, `yarn.lock`
     - Rust: `Cargo.toml`
     - Monorepo: lerna.json, workspaces config
   - Detect correctly: prioritize closest marker
   - Cache results (TTL: 1 hour)

3. Implement Git integration
   - Get current branch
   - List commits (last 20)
   - Get file status (staged, unstaged, untracked)
   - Resolve file paths relative to repo root

**Acceptance Criteria:**
- Detect projects in <100ms (with cache)
- Monorepo detection works (multiple projects)
- Git integration handles non-repos gracefully
- 90%+ test coverage

---

#### Task 2.2: CWD Tracking & Inference (12 hours)

**Objective:** Track per-agent working directory without `os.chdir()`.

**Files to Create:**
- `src/context/cwd_manager.py` - CWD tracking per agent (≤350 lines)
- `src/context/path_resolver.py` - Path resolution helpers

**Task Breakdown:**
1. Implement `ContextState` dataclass
   - Current working directory (absolute path)
   - Project root (if in a project)
   - Relative path from project root
   - Git branch (if applicable)
   - Environment variables (PATH, PYTHONPATH, NODE_PATH, etc.)

2. Implement per-agent CWD tracking
   - Each agent has isolated ContextState
   - Stored in agent's persistent state (Core 1.5)
   - Inference on first request:
     - Check request headers for hint (x-cwd, x-workspace-id)
     - Look at request context (file paths)
     - Fall back to project root
   - Update on file operations (Task 2.3)

3. Implement path resolution
   - `resolve_path(relative_or_absolute_path) -> str` (absolute)
   - `relative_path(absolute_path) -> str` (relative to CWD)
   - Handle symlinks: resolve to canonical path
   - Handle `..` and `.` correctly
   - Verify paths don't escape project root (security)

4. Implement CWD stack
   - Save current CWD before tool invocation
   - Restore after tool completes
   - Handle nested tool calls correctly
   - Max stack depth: 10 (detect infinite loops)

**Acceptance Criteria:**
- CWD changes don't affect other agents (isolation)
- Path resolution works across 1000+ files
- Symlink handling correct
- Stack prevents infinite recursion
- 85%+ test coverage

---

#### Task 2.3: File System Integration (10 hours)

**Objective:** Safe file operations with change detection and atomic transactions.

**Files to Create:**
- `src/context/file_ops.py` - File operation helpers (≤350 lines)
- `src/context/file_watcher.py` - Change detection

**Task Breakdown:**
1. Implement safe file operations
   - `read_file(path: str) -> str` - Read with boundary checks
   - `write_file(path: str, content: str) -> None` - Atomic write
   - `delete_file(path: str) -> None` - Safe delete
   - `list_files(path: str, pattern: str) -> list[str]` - List with filtering
   - All operations verify path is within project

2. Implement atomic writes
   - Write to temp file: `{path}.tmp.{random}`
   - Sync to disk: `fsync(fd)`
   - Atomic rename: `rename(temp_file, final_path)`
   - On failure, clean up temp file
   - Timeout: 30s per operation

3. Implement file locking
   - Use fcntl (Unix) or msvcrt (Windows) for locks
   - Prevent concurrent writes to same file
   - Timeout: 10s acquisition, 60s hold max
   - Deadlock detection: max wait depth = 3

4. Implement change detection
   - Track file hash (SHA256) after each write
   - Detect external modifications (git checkout, etc.)
   - Notify agent of unexpected changes
   - Store change history (last 10 versions)

**Acceptance Criteria:**
- Atomic writes: verify no partial/corrupted files
- Concurrent writes to different files work
- Concurrent writes to same file fail gracefully
- Change detection catches all modifications
- 80%+ test coverage

---

#### Task 2.4: State Management (8 hours)

**Objective:** Persist and recover agent context state.

**Files to Create:**
- `src/context/state_store.py` - State persistence (≤350 lines)

**Task Breakdown:**
1. Implement event sourcing
   - All state changes logged as immutable events
   - Event schema: timestamp, agent_id, event_type, details, metadata
   - Store in PostgreSQL event log table
   - Replay events to recover state

2. Implement incremental snapshots
   - Full snapshot every 100 events
   - Incremental snapshot every 10 events (stores deltas)
   - Compression: gzip if >1MB
   - Cleanup: delete old snapshots (keep last 3)

3. Implement state recovery
   - Load latest snapshot (or full state from events)
   - Replay events since snapshot
   - Verify CWD is still valid (directory exists)
   - Fall back to project root if CWD invalid

**Storage Schema:**
```sql
CREATE TABLE context_events (
    id BIGSERIAL PRIMARY KEY,
    agent_id UUID NOT NULL,
    event_type TEXT NOT NULL,
    details JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_context_events_agent ON context_events(agent_id);
CREATE INDEX idx_context_events_time ON context_events(created_at);
```

**Acceptance Criteria:**
- Event logging: <10ms overhead
- Snapshot creation: <500ms
- Recovery from snapshot: <100ms
- State consistency verified
- 80%+ test coverage

---

#### Task 2.5: Testing & Validation (2 hours)

**Objective:** Core 2 testing for all components.

**Test Coverage:**
- Project detection (8 tests)
- CWD tracking (10 tests)
- Path resolution (12 tests)
- File operations (15 tests)
- Change detection (8 tests)
- State persistence (10 tests)
- Integration (5 tests)
- Total: ~70 tests

**Files to Create:**
- `tests/unit/context/` (5 test files, 300+ lines)
- `tests/integration/context/` (2 test files, 100+ lines)

**Acceptance Criteria:**
- All 70+ tests passing
- >80% code coverage
- No security issues (path escape attempts blocked)
- Performance targets met

---

**Core 2 Summary:**
- **Total Files:** 10 new files (context module complete)
- **Total Lines:** ~1200 production code, ~400 test code
- **Integration Points:** Feeds Agent Framework (Core 1), used by APIs (Core 3/4) and Tools (via smartcp)
- **Exit Criteria:** All tests passing, CWD isolation verified, ready for API integration

---

### Core 3: API Layer - Agent-Optimized API (50 hours, Week 3)

**Overview:** High-performance agent control API with direct tool invocation and sub-agent spawning.

**Deliverable:** Fully functional `/v1/agents/*` endpoints with streaming, tool execution, and session management.

#### Task 3.1: API Server Foundation (8 hours)

**Objective:** FastAPI application structure with middleware and request/response handling.

**Files to Create:**
- `src/api/__init__.py` - API module exports
- `src/api/server.py` - FastAPI app factory
- `src/api/middleware.py` - Request/response middleware
- `src/api/models.py` - Request/response models for agent API

**Task Breakdown:**
1. Create FastAPI application
   - CORS middleware (allow all origins for development, restrict for production)
   - Request logging (structured logging)
   - Error handling (consistent error responses)
   - Health check endpoint: `/health`, `/health/ready`, `/health/live`

2. Implement request middleware
   - Generate request_id (UUID)
   - Extract user_id from Authorization header
   - Extract workspace_id from x-workspace-id header
   - Inject dependencies (agent coordinator, services)
   - Timeout: 30s for all requests

3. Implement response middleware
   - Consistent response envelope (success, data, error)
   - Timing metadata (duration, timestamp)
   - Logging: log all requests/responses (structured)

4. Define agent API request/response models
   - `AgentExecuteRequest`: prompt, tools, parameters, cwd, timeout
   - `AgentExecuteResponse`: status, result, logs, metadata
   - `AgentSpawnRequest`: agent_type, config, parameters
   - `AgentSpawnResponse`: agent_id, status

**Acceptance Criteria:**
- Server starts in <1s
- Health checks respond in <10ms
- Middleware overhead <5ms
- Error responses consistent format
- Request logging structured and searchable

---

#### Task 3.2: Agent Control Endpoints (12 hours)

**Objective:** Core endpoints for agent execution and management.

**Files to Create:**
- `src/api/routes/agents.py` - Agent control routes (≤350 lines)

**Endpoint Definitions:**

**POST /v1/agents/execute** (Main execution endpoint)
```
Request:
  agent_id: str (optional, create new if not provided)
  prompt: str (required)
  tools: list[str] (optional, default all available)
  parameters: dict (optional, forwarded to agent)
  cwd: str (optional, will be inferred if not provided)
  timeout: float (optional, default 300s)
  stream: bool (optional, default false)

Response (non-streaming):
  agent_id: str
  status: "completed" | "failed" | "timeout" | "error"
  result: str (LLM output)
  logs: list[str] (execution logs)
  metadata:
    duration_ms: int
    tokens_used: int
    tools_called: list[str]
    errors: list[str]

Response (streaming):
  Server-Sent Events:
    event: "agent-start"
    event: "tool-call" (with tool_name, tool_input)
    event: "tool-result" (with tool_name, tool_result)
    event: "agent-output" (with text chunk)
    event: "agent-complete" (with final result)
    event: "agent-error" (with error message)
```

**POST /v1/agents/spawn** (Create sub-agent)
```
Request:
  agent_type: str (optional, default "claude-sonnet-4")
  config: dict (optional, agent configuration)
  parent_id: str (optional, establish parent-child relationship)

Response:
  agent_id: str
  status: "initializing" | "ready" | "error"
  metadata:
    created_at: str (ISO 8601)
    type: str
```

**GET /v1/agents/{agent_id}** (Get agent status)
```
Response:
  agent_id: str
  status: AgentStatus
  cwd: str
  created_at: str
  last_activity: str
  resource_usage:
    memory_mb: int
    cpu_percent: float
```

**POST /v1/agents/{agent_id}/kill** (Terminate agent)
```
Response:
  status: "terminated" | "error"
  message: str
```

**GET /v1/agents** (List agents)
```
Response:
  agents: list[AgentInfo]
  total: int
  active_count: int
```

**Acceptance Criteria:**
- All 5 endpoints implemented and tested
- Streaming works with SSE
- Error handling consistent
- Request validation tight (no invalid inputs pass)
- 80%+ code coverage

---

#### Task 3.3: Tool Invocation API (10 hours)

**Objective:** Direct tool calling from agent API.

**Files to Create:**
- `src/api/routes/tools.py` - Tool invocation routes (≤350 lines)

**Endpoint Definitions:**

**POST /v1/agents/{agent_id}/tools/{tool_name}** (Invoke tool directly)
```
Request:
  tool_name: str (from URL)
  parameters: dict (tool-specific parameters)
  timeout: float (optional, default 30s)

Response:
  status: "success" | "error"
  result: any (tool-specific)
  metadata:
    duration_ms: int
    tool_version: str
```

**GET /v1/tools** (List available tools)
```
Response:
  tools: list[ToolInfo]
  total: int

ToolInfo:
  name: str
  description: str
  parameters: dict (JSON schema)
  tags: list[str]
```

**GET /v1/tools/{tool_name}** (Get tool documentation)
```
Response:
  name: str
  description: str
  parameters: dict (JSON schema)
  examples: list[dict]
  tags: list[str]
```

**Acceptance Criteria:**
- Tool invocation latency <1s (including tool execution)
- Tool registry integrated with smartcp tools
- Error handling (missing tool, invalid params)
- Tool versioning supported
- 80%+ code coverage

---

#### Task 3.4: Session Management (8 hours)

**Objective:** Track agent sessions with state and billing.

**Files to Create:**
- `src/api/sessions.py` - Session management (≤350 lines)

**Task Breakdown:**
1. Implement session model
   - session_id (UUID)
   - agent_id (UUID)
   - user_id (UUID)
   - workspace_id (UUID)
   - created_at, updated_at
   - status: "active" | "paused" | "closed"
   - metadata: cwd, tools, parameters

2. Implement session storage
   - Hot storage: Redis (30 minute TTL)
   - Cold storage: PostgreSQL (permanent record)
   - Sync strategy: write-through (Redis + DB)
   - Query by session_id, user_id, agent_id

3. Implement session lifecycle
   - Create on first /agents/execute call
   - Reuse agent within session (maintain state)
   - Close when explicitly requested or timeout (1 hour idle)
   - Archive to cold storage on close

**Storage Schema:**
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    agent_id UUID NOT NULL,
    user_id UUID NOT NULL,
    workspace_id UUID NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_agent ON sessions(agent_id);
CREATE INDEX idx_sessions_workspace ON sessions(workspace_id);
```

**Acceptance Criteria:**
- Session reuse preserves agent state
- Hot/cold storage sync reliable
- Session cleanup works (TTL expiry)
- 80%+ code coverage

---

#### Task 3.5: Streaming & Real-Time (8 hours)

**Objective:** Server-Sent Events (SSE) for real-time updates.

**Files to Create:**
- `src/api/streaming.py` - SSE streaming implementation (≤350 lines)

**Task Breakdown:**
1. Implement SSE event stream
   - Content-Type: text/event-stream
   - Keep-alive: send comment every 30s
   - Events: agent-start, tool-call, tool-result, agent-output, agent-complete, agent-error
   - JSON payload in each event

2. Implement streaming for /agents/execute
   - Stream tool calls as they happen
   - Stream LLM output tokens as they arrive
   - Stream completion with full result
   - Support both streaming and non-streaming responses

3. Implement connection management
   - Timeout: 5 minute max stream duration (reconnect)
   - Cleanup: close connection if agent dies
   - Reconnection: client can resume with session_id

**Acceptance Criteria:**
- Stream latency <100ms per event
- No message loss during streaming
- Reconnection works without data loss
- 80%+ code coverage

---

#### Task 3.6: Testing & Documentation (4 hours)

**Objective:** Test suite and API documentation.

**Files to Create:**
- `tests/unit/api/test_agents.py` - Unit tests (100+ lines)
- `tests/integration/test_agents_api.py` - Integration tests (150+ lines)
- `docs/api/AGENT_API.md` - API documentation

**Test Coverage:**
- All 5 main endpoints
- Streaming endpoint
- Tool invocation
- Session management
- Error handling
- Authentication/authorization

**Documentation:**
- Complete endpoint reference (request/response)
- Authentication methods
- Error codes and handling
- Example workflows
- Rate limiting info

**Acceptance Criteria:**
- All tests passing (50+ tests)
- >80% API code coverage
- Documentation complete and accurate
- Ready for client integration

---

**Core 3 Summary:**
- **Total Files:** 8 new files (agent API complete)
- **Total Lines:** ~1000 production code, ~600 test code
- **Integration Points:** Feeds session management, uses Agent Framework (Core 1), Context (Core 2)
- **Exit Criteria:** All endpoints working, streaming verified, tests passing, documentation complete

---

### Core 4: API Layer - LLM-Compatible API (40 hours, Week 3-4)

**Overview:** OpenAI-compatible endpoints for seamless integration with existing tools.

**Deliverable:** `/v1/chat/completions` fully compatible with OpenAI client libraries.

#### Task 4.1: OpenAI-Compatible Interface (12 hours)

**Objective:** Implement OpenAI Chat API specification.

**Files to Create:**
- `src/api/routes/openai.py` - OpenAI-compatible endpoints (≤350 lines)
- `src/api/models/openai.py` - OpenAI request/response models

**Endpoint: POST /v1/chat/completions**

**Request (OpenAI format):**
```json
{
  "model": "claude-sonnet-4",
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ],
  "temperature": 0.7,
  "top_p": 1.0,
  "max_tokens": 2048,
  "stream": false,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "tool_name",
        "description": "Tool description",
        "parameters": {...}
      }
    }
  ],
  "tool_choice": "auto"
}
```

**Response (non-streaming):**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "claude-sonnet-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Response text",
        "tool_calls": [
          {
            "id": "call_123",
            "type": "function",
            "function": {
              "name": "tool_name",
              "arguments": "{...}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls" | "stop" | "length"
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150
  }
}
```

**Response (streaming - SSE):**
```
event: "start"
data: {"id": "chatcmpl-123"}

event: "delta"
data: {"delta": {"content": "text"}}

event: "tool_call"
data: {"tool_call": {"id": "call_123", "function": ...}}

event: "done"
data: [DONE]
```

**Task Breakdown:**
1. Parse OpenAI request format
   - Validate model name (support claude-sonnet-4, claude-opus, etc.)
   - Parse messages (validate role/content)
   - Handle tools array (convert to agent tools)
   - Handle tool_choice (auto, none, specific tool)

2. Execute agent with OpenAI semantics
   - Map OpenAI request to agent request
   - Execute agent
   - Capture tool calls and results
   - Map response back to OpenAI format

3. Handle streaming
   - Convert agent streaming events to OpenAI SSE format
   - Proper event types: start, delta, tool_call, done
   - Token counting for streaming

**Acceptance Criteria:**
- OpenAI client libraries work without modification
- Tool calling fully compatible
- Streaming works with openai-python
- Error responses match OpenAI format
- 80%+ endpoint coverage

---

#### Task 4.2: Message Protocol Mapping (8 hours)

**Objective:** Convert between OpenAI and agent message formats.

**Files to Create:**
- `src/api/converters/openai.py` - Message format converter (≤350 lines)

**Task Breakdown:**
1. Implement OpenAI → Agent conversion
   - Message: {role, content, tool_calls} → AgentRequest
   - Tools: OpenAI tool format → agent tool spec
   - Model selection: "claude-sonnet-4" → agent type
   - Parameters: temperature, top_p, max_tokens → agent parameters

2. Implement Agent → OpenAI conversion
   - AgentResponse → ChatCompletion format
   - Tool calls → tool_calls array
   - Token counts → usage object
   - Metadata → finish_reason

3. Implement error mapping
   - Agent errors → OpenAI error format
   - Error codes: invalid_request_error, server_error, etc.
   - Error messages: human-readable

**Acceptance Criteria:**
- Round-trip conversion preserves semantics
- All tool_call fields preserved
- Error mapping complete
- 90%+ code coverage

---

#### Task 4.3: Routing & Adaptation (8 hours)

**Objective:** Route requests to correct agent and adapt responses.

**Files to Create:**
- `src/api/routing.py` - Request routing logic (≤350 lines)

**Task Breakdown:**
1. Implement model routing
   - Map "gpt-4" → Claude for capability match
   - Map "gpt-3.5-turbo" → Claude Flash for cost
   - Support model aliasing via config
   - Default model: "claude-sonnet-4"

2. Implement capability adaptation
   - OpenAI: top_k not supported → ignore
   - OpenAI: parallel tool calls → map to sequential
   - OpenAI: function calling → map to tool use
   - Validate request against agent capabilities

3. Implement response adaptation
   - Ensure response format matches OpenAI spec exactly
   - Token counting accurate
   - Finish reason correct (tool_calls, stop, length, error)

**Acceptance Criteria:**
- Model aliasing works
- Capability adaptation transparent to client
- Response validation against OpenAI spec
- 85%+ code coverage

---

#### Task 4.4: Compatibility Testing (8 hours)

**Objective:** Comprehensive testing with OpenAI client libraries.

**Files to Create:**
- `tests/integration/test_openai_compatibility.py` - Compatibility tests (200+ lines)

**Test Coverage:**
- OpenAI Python client integration
- Chat completion requests
- Streaming requests
- Tool calling
- Error handling
- Token counting
- Model selection

**Example Test:**
```python
async def test_openai_client_chat_completion():
    client = openai.OpenAI(api_key="test", base_url="http://localhost:8000/v1")
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=100
    )
    assert response.choices[0].message.content
    assert response.usage.total_tokens > 0
```

**Acceptance Criteria:**
- OpenAI client works without modification
- All request types work (completion, streaming, tool-use)
- 95%+ client library compatibility
- Performance within 10% of OpenAI

---

**Core 4 Summary:**
- **Total Files:** 6 new files (OpenAI API complete)
- **Total Lines:** ~800 production code, ~400 test code
- **Integration Points:** Shares session/tool infrastructure with Core 3, uses Agent Framework (Core 1)
- **Exit Criteria:** OpenAI client libraries work, compatibility tests pass, ready for client integration

---

### Core 5: Terminal UI (60 hours, Weeks 4-5)

**Overview:** Interactive terminal interface for agent management and monitoring using Textual framework.

**Deliverable:** Production-ready TUI with responsive layout, real-time updates, and agent monitoring.

#### Task 5.1: Framework Setup & Theme (4 hours)

**Objective:** Textual application foundation with styling.

**Files to Create:**
- `src/tui/__init__.py` - TUI module exports
- `src/tui/app.py` - Textual application main
- `src/tui/styles.tcss` - Terminal CSS styling

**Task Breakdown:**
1. Initialize Textual application
   - Create App subclass with dark theme
   - Set up screen dimensions and layout
   - Configure key bindings (Ctrl+C, Ctrl+L, etc.)

2. Define color scheme
   - Background: dark blue (#1e1e2e)
   - Primary: cyan (#89dcff)
   - Accent: magenta (#ff57d8)
   - Success: green (#50fa7b)
   - Error: red (#ff5555)

3. Define component styles
   - Button, Input, Header, Footer styles
   - Responsive to terminal size
   - High contrast for accessibility

**Acceptance Criteria:**
- App starts and renders in <250ms
- Theme applies consistently
- Responsive to terminal resize

---

#### Task 5.2: Component Library (20 hours)

**Objective:** Reusable Textual components for agent management.

**Files to Create:**
- `src/tui/components/__init__.py` - Component exports
- `src/tui/components/agent_list.py` - Agent list widget (≤350 lines)
- `src/tui/components/agent_detail.py` - Agent detail panel (≤350 lines)
- `src/tui/components/executor.py` - Agent executor widget (≤350 lines)
- `src/tui/components/log_viewer.py` - Scrollable log display (≤350 lines)
- `src/tui/components/input_panel.py` - Command input panel (≤350 lines)

**Components:**

1. **AgentListWidget**
   - Display list of active agents
   - Columns: agent_id, status, cwd, memory_mb, cpu%
   - Sortable by columns
   - Selectable rows (highlight)
   - Refresh on model change

2. **AgentDetailWidget**
   - Show selected agent details
   - Tabs: Info, Logs, State, Tools
   - Real-time memory/CPU updates
   - Action buttons: Kill, Pause, Resume

3. **ExecutorWidget**
   - Input field for agent commands/prompts
   - Execute button
   - Real-time output display
   - Tool call visualization

4. **LogViewerWidget**
   - Scrollable log view
   - Filter by log level
   - Search within logs
   - Auto-scroll to bottom
   - Color-coded by level

5. **InputPanel**
   - Multi-line input
   - Command history (up/down)
   - Auto-complete (agent names, tools)
   - Submit with Ctrl+Enter

**Acceptance Criteria:**
- All 5 components render correctly
- Component interactions smooth
- No visual glitches or flicker
- Responsive to data updates
- 75%+ component code coverage

---

#### Task 5.3: Layout & Navigation (12 hours)

**Objective:** Responsive layout with navigation between screens.

**Files to Create:**
- `src/tui/screens/__init__.py` - Screen exports
- `src/tui/screens/main.py` - Main screen with sidebar (≤350 lines)
- `src/tui/screens/executor.py` - Agent executor screen (≤350 lines)
- `src/tui/screens/monitor.py` - System monitoring screen (≤350 lines)

**Layout 1: Main Screen (Default)**
```
┌─────────────────────────────────────────────────────┐
│ SmartCP Agent Dashboard                      [Q]uit │
├──────────────┬──────────────────────────────────────┤
│ Agents       │ Agent: agent-123                     │
│ ▸ agent-123  │ Status: RUNNING                      │
│   agent-456  │ Memory: 125 MB / 512 MB              │
│   agent-789  │ CPU: 45% (4 cores)                   │
│              │ CWD: /home/user/project              │
│              │ Created: 5 minutes ago                │
│              │                                       │
│              │ [Info] [Logs] [State] [Tools]        │
├──────────────┴──────────────────────────────────────┤
│ Command:                                             │
│ > run entity.create("My Entity")                     │
│ > _                                                  │
├──────────────────────────────────────────────────────┤
│ Output:                                              │
│ [2024-12-02 10:30:45] Agent started                 │
│ [2024-12-02 10:30:46] Tool called: entity_create    │
│ [2024-12-02 10:30:47] Result: success               │
└──────────────────────────────────────────────────────┘
```

**Layout 2: Executor Screen**
```
┌──────────────────────────────────────────────────────┐
│ SmartCP Agent Executor                    [ESC] Back │
├──────────────────────────────────────────────────────┤
│ Prompt:                                              │
│ ┌──────────────────────────────────────────────────┐ │
│ │ Create a new entity with the following details:  │ │
│ │ - Name: "Product Launch"                         │ │
│ │ - Description: "Q4 2024 product launch"          │ │
│ │                                                   │ │
│ │ _                                                │ │
│ └──────────────────────────────────────────────────┘ │
│ [Execute] [Clear] [Copy]                            │
├──────────────────────────────────────────────────────┤
│ Output:                                              │
│ [Tool] entity.create                                │ │
│ ├─ name: "Product Launch"                           │
│ ├─ description: "Q4 2024 product launch"            │
│ └─ [Executing...]                                   │
│ [Result] Success - entity_id: 550e8400-e29b...     │
│ [Output] Created entity with 2 relationships        │
└──────────────────────────────────────────────────────┘
```

**Layout 3: Monitor Screen**
```
┌──────────────────────────────────────────────────────┐
│ SmartCP System Monitor                   [ESC] Back  │
├──────────────────────────────────────────────────────┤
│ System Resources                   Refresh: 2s       │
│                                                       │
│ Memory:  [████████░░░░] 65% (4.2GB / 8GB)           │
│ CPU:     [██████░░░░░░] 40% (4 cores @ 2.4GHz)      │
│ Disk:    [█░░░░░░░░░░░] 5% (50GB used / 1TB)       │
│                                                       │
│ Agents: 12 active, 3 idle, 1 error                  │
│                                                       │
│ Agent Activity                                       │
│ ┌──────────────────────────────────────────────────┐ │
│ │ agent-123  RUNNING  125 MB   45% CPU             │ │
│ │ agent-456  IDLE      85 MB    0% CPU             │ │
│ │ agent-789  RUNNING  150 MB   70% CPU             │ │
│ │ agent-abc  ERROR    100 MB   15% CPU             │ │
│ │                                                   │ │
│ │ ↑ ↓ scroll │ [Refresh]                           │ │
│ └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

**Task Breakdown:**
1. Implement main screen layout
   - Sidebar: agent list with selection
   - Main panel: agent details (info, logs, state, tools)
   - Bottom panel: command input
   - Header: title bar with quit button
   - Footer: status line

2. Implement executor screen
   - Large prompt input area
   - Streaming output display
   - Tool call visualization
   - Result display with formatting

3. Implement monitor screen
   - System resource gauges
   - Agent list with resource usage
   - Real-time updates every 2s
   - Graph history (CPU, Memory over time)

4. Implement navigation
   - Tab key to switch between main/executor/monitor
   - Q to quit (with confirmation)
   - Esc to go back
   - Ctrl+L to clear screen

**Acceptance Criteria:**
- All 3 screens render correctly
- Navigation works smoothly
- Real-time updates visible
- Responsive to terminal resize
- No visual corruption

---

#### Task 5.4: Agent Monitoring (10 hours)

**Objective:** Real-time agent monitoring and interaction.

**Files to Create:**
- `src/tui/monitor.py` - Agent monitor/watcher (≤350 lines)
- `src/tui/state.py` - TUI state management

**Task Breakdown:**
1. Implement agent monitoring
   - Poll agent status every 1s
   - Fetch: status, memory, CPU, CWD, active tools
   - Update local state (no re-render if unchanged)
   - Detect agent death/errors and highlight

2. Implement log streaming
   - Subscribe to agent log events via SSE
   - Buffer logs in circular queue (1000 log lines max)
   - Display latest logs in log viewer
   - Filter by level (debug, info, warning, error)

3. Implement metrics display
   - Memory usage graph (last 5 minutes)
   - CPU usage graph (last 5 minutes)
   - Tool call frequency (last hour)
   - Request latency histogram

4. Implement agent control
   - Kill agent (with confirmation)
   - Pause/resume agent
   - Force restart
   - Clear logs

**Acceptance Criteria:**
- Monitoring latency <500ms
- Log streaming works without loss
- Metrics accurate and responsive
- Control operations work reliably
- 80%+ code coverage

---

#### Task 5.5: Responsive Design (8 hours)

**Objective:** TUI responsive to terminal size changes.

**Task Breakdown:**
1. Implement dynamic layout adjustment
   - Resize handler triggered on terminal resize
   - Reflow layout components
   - Maintain scroll positions in scrollable panels
   - Graceful degradation for small terminals (<80 cols)

2. Implement mobile-friendly version
   - Single-column layout for <100 columns
   - Collapsible panels
   - Full-screen executor/monitor
   - Touch-friendly (if supported)

3. Test across terminal sizes
   - 80x24 (minimal)
   - 120x40 (standard)
   - 200x50 (wide)
   - Verify no content loss

**Acceptance Criteria:**
- Resize works without crashes
- Content readable at all sizes
- No horizontal scrolling for >120 cols
- Performance acceptable on all sizes

---

#### Task 5.6: Testing & UX Polish (6 hours)

**Objective:** Polish UI and comprehensive testing.

**Files to Create:**
- `tests/integration/test_tui.py` - TUI integration tests (150+ lines)
- `docs/tui/USER_GUIDE.md` - User guide

**Test Coverage:**
- Component rendering
- Component interactions
- Layout responsiveness
- Screen navigation
- Real-time updates
- User input handling

**UX Polish:**
- Consistent spacing and alignment
- Helpful error messages
- Keyboard shortcuts documented
- Mouse support (if terminal supports)
- Performance optimization (no stuttering)

**User Guide:**
- Getting started
- Main screen walkthrough
- Executor screen walkthrough
- Monitor screen walkthrough
- Keyboard shortcuts
- Troubleshooting

**Acceptance Criteria:**
- All tests passing (50+ tests)
- >80% TUI code coverage
- User guide comprehensive
- Zero visual glitches
- Startup <500ms

---

**Core 5 Summary:**
- **Total Files:** 12 new files (TUI complete)
- **Total Lines:** ~2000 production code, ~600 test code
- **Integration Points:** Communicates with Agent API (Core 3), displays data from Core 1 + 2
- **Exit Criteria:** TUI functional, all screens working, responsive to resize, tests passing

---

### Core 6: Integration & Testing (50 hours, Weeks 6-8)

**Overview:** Integrate all components, brain layer compatibility, and comprehensive testing.

**Deliverable:** Production-ready system with full integration, SWE Bench evaluation, and deployment readiness.

#### Task 6.1: Brain Layer Integration (15 hours)

**Objective:** Connect Agent Layer to Phase 3 (Brain Layer) components.

**Task Breakdown:**
1. Integrate Memory System with Agent Framework
   - Each agent gets memory instance (from Core 1)
   - Episodic memory stores agent execution history
   - Semantic memory stores learned facts (tool behavior, common patterns)
   - Working memory for current context

2. Integrate PreActPlanner with Agents
   - Agent execution delegates planning to PreActPlanner
   - Capture planning outcomes in memory (episodic)
   - Use learned patterns from semantic memory
   - Store planning results for agent reflection

3. Implement agent-memory interface
   - `agent.memory.store_execution(task, outcome)`
   - `agent.memory.recall_similar_tasks(query)`
   - `agent.memory.get_working_memory() -> ExecutionContext`

4. Integration test: Full workflow
   - Start agent → plan → execute → store outcome → recall
   - Verify memory improves over time
   - Verify agent learns from past executions

**Acceptance Criteria:**
- Memory integration transparent to API callers
- Episodic memory captures all executions
- Semantic memory extraction works
- Learning improves agent performance (measured)
- 85%+ integration code coverage

---

#### Task 6.2: SmartCP Tool Integration (15 hours)

**Objective:** Integrate smartcp tool fabric into agent execution.

**Task Breakdown:**
1. Connect tool registry
   - Agent can call any smartcp tool
   - Tools return structured results
   - Tools can access agent's working directory (Core 2)
   - Tools integrated with memory system

2. Implement tool result capture
   - Store tool inputs/outputs
   - Capture execution time, errors
   - Feed results to agent for next decision

3. Implement tool caching (Core 1.3)
   - Tool result caching for identical inputs
   - Cache hit reduces latency from 500ms to <10ms
   - Cache invalidation on file changes

4. Implement tool error handling
   - Graceful failures (tool crash ≠ agent crash)
   - Error recovery: retry with backoff
   - Fallback mechanisms for critical tools

**Acceptance Criteria:**
- All smartcp tools accessible from agents
- Tool result caching working
- Error handling robust
- Tool latency <500ms (p95)
- 80%+ integration coverage

---

#### Task 6.3: Multi-Agent Coordination Tests (10 hours)

**Objective:** Comprehensive multi-agent orchestration testing.

**Files to Create:**
- `tests/integration/test_multi_agent.py` - Multi-agent tests (200+ lines)
- `tests/integration/test_agent_communication.py` - Agent communication tests (150+ lines)

**Test Scenarios:**

1. **Sequential Agents**
   - Agent A creates entity
   - Agent B reads entity created by A
   - Result: correct communication and state

2. **Parallel Agents**
   - 10 agents create entities in parallel
   - No race conditions or deadlocks
   - All agents complete successfully

3. **Hierarchical Agents**
   - Parent agent spawns 2 child agents
   - Child agents report results to parent
   - Parent aggregates results
   - Parent returns final result

4. **Agent Failure & Recovery**
   - One of 3 agents fails
   - Other agents detect failure
   - System recovers gracefully
   - Failed agent restarts and resumes

5. **Resource Sharing**
   - 200 agents share DB pool, HTTP pool, tool cache
   - No resource exhaustion
   - Performance degradation <20% vs single agent

**Acceptance Criteria:**
- All 5 scenarios pass
- 100+ total test cases
- No deadlocks or race conditions (verified with thread sanitizer)
- Resource usage stays <2GB
- All agents complete successfully

---

#### Task 6.4: Performance Testing (5 hours)

**Objective:** Benchmark agent performance and identify bottlenecks.

**Files to Create:**
- `tests/performance/test_agent_performance.py` - Performance benchmarks (100+ lines)

**Benchmarks:**

1. **Agent Spawn Latency**
   - Single agent: target <200ms
   - 100 agents parallel: target <5s total
   - Warm pool reuse: target <100ms

2. **Message Routing Latency**
   - Simple message: target <10ms (p99)
   - Complex message (3KB): target <15ms (p99)

3. **Tool Invocation Latency**
   - Tool call: target <500ms (p95, including execution)
   - Cached tool call: target <100ms

4. **Memory Usage**
   - Per-agent baseline: <100MB
   - 200 agents total: <2GB (vs 40GB unshared)
   - Memory growth rate: <10MB per 10 agents

5. **API Response Time**
   - /agents/execute: target <1s (p95)
   - /agents/{id}: target <100ms (p95)
   - /tools list: target <50ms

**Acceptance Criteria:**
- All performance targets met
- No performance regressions (compare against Phase 3)
- Bottlenecks identified and documented
- Optimization opportunities noted

---

#### Task 6.5: Documentation & Deployment (5 hours)

**Objective:** Complete documentation and deployment readiness.

**Files to Create:**
- `docs/deployment/DEPLOYMENT_GUIDE.md` - Deployment instructions
- `docs/deployment/CONFIGURATION.md` - Configuration reference
- `docs/integration/BRAIN_LAYER_INTEGRATION.md` - Brain layer integration
- `docs/integration/SMARTCP_INTEGRATION.md` - SmartCP tool integration
- `docs/architecture/AGENT_ARCHITECTURE.md` - Agent architecture overview

**Content:**

1. **Deployment Guide**
   - Docker deployment
   - Kubernetes deployment (with gVisor)
   - Configuration via environment variables
   - Database setup (Supabase)
   - Redis setup (session storage)

2. **Configuration Reference**
   - All environment variables
   - Performance tuning parameters
   - Resource limits
   - Feature flags

3. **Integration Guides**
   - How Brain Layer integrates with agents
   - How SmartCP tools are called
   - Memory system integration
   - Tool caching strategy

4. **Architecture Documentation**
   - Agent execution flow diagram
   - Component interaction diagram
   - Data flow diagram
   - Scaling model (50, 100, 200 agents)

**Acceptance Criteria:**
- Documentation complete
- All deployment steps documented
- Configuration options clear
- Integration flows documented
- Ready for ops team

---

**Core 6 Summary:**
- **Total Files:** 8 new files (integration complete)
- **Total Lines:** ~1200 production/test code
- **Integration Points:** Connects Phase 3, Phase 5 Core 1-5, SmartCP
- **Exit Criteria:** All components integrated, tests passing, documentation complete, production-ready

---

## Part 2: Implementation Timeline

### Week 1: Core 1 + Core 2 (Agent Framework + Context)
**Parallel Streams:**
- Team 1: Core 1.1-1.3 (Agent base, spawning, resource pooling)
- Team 2: Core 2.1-2.3 (Project abstraction, CWD, file ops)

**Daily Standup:**
- Status: tasks completed, blockers
- Review: pull requests, integration points
- Plan: next day's work

**End of Week Deliverables:**
- Functional agent spawning
- Resource pooling working
- Per-agent CWD isolation verified
- Atomic file operations tested

---

### Week 2: Core 1.4-1.6 + Core 2.4-2.5 (Lifecycle + State)
**Parallel Streams:**
- Team 1: Core 1.4-1.6 (Lifecycle, persistence, testing)
- Team 2: Core 2.4-2.5 (State management, testing)

**Integration Work:**
- Connect agent lifecycle to state persistence
- Verify state recovery on restart
- Performance testing (target <200ms agent startup)

**End of Week Deliverables:**
- Warm pooling reducing startup to <100ms
- State persistence and recovery working
- 100+ tests passing (Core 1 + Core 2)
- >80% code coverage

---

### Week 3: Core 3 (Agent API)
**Single Stream:**
- Team 1: Core 3.1-3.6 (API endpoints, streaming, testing)

**Parallel Effort:**
- Team 2: Begin Core 4.1-4.2 (OpenAI API foundation)

**Integration Work:**
- Connect Agent API to Agent Framework (Core 1)
- Implement session management
- Test streaming with agent execution

**End of Week Deliverables:**
- /v1/agents/execute fully functional
- Streaming working (SSE)
- Session management implemented
- 50+ API tests passing

---

### Week 4: Core 3.3-3.6 + Core 4 (Tool Invocation + OpenAI API)
**Parallel Streams:**
- Team 1: Core 3.3-3.6 continuation (tool invocation, remaining endpoints)
- Team 2: Core 4.1-4.4 (OpenAI API implementation, compatibility)

**Integration Work:**
- Tool invocation routed through smartcp
- OpenAI client library testing
- Session reuse across both API types

**End of Week Deliverables:**
- Tool invocation API working
- OpenAI chat completions endpoint working
- OpenAI Python client compatible
- 50+ tests for both APIs

---

### Week 5: Core 5.1-5.4 (TUI - Foundation + Components + Navigation + Monitoring)
**Single Stream:**
- Team 1: Core 5.1-5.4 (TUI framework, components, layout, monitoring)

**Parallel Effort:**
- Team 2: Begin Core 6.1 (Brain layer integration setup)

**Integration Work:**
- TUI communicates with Agent API (Core 3)
- Real-time agent monitoring via SSE
- Display logs, memory, CPU in real-time

**End of Week Deliverables:**
- TUI main screen working
- Agent list with selection
- Real-time monitoring
- Streaming output display

---

### Week 6: Core 5.5-5.6 + Core 6.1 (TUI Polish + Brain Integration)
**Parallel Streams:**
- Team 1: Core 5.5-5.6 (responsive design, testing, UX polish)
- Team 2: Core 6.1-6.2 (Brain layer + SmartCP tool integration)

**Integration Work:**
- TUI works on all terminal sizes
- Memory system feeding agents
- SmartCP tools callable from agents
- Brain layer + Agent layer integrated

**End of Week Deliverables:**
- TUI responsive and polished
- Brain layer integration working
- SmartCP tools integrated
- Full end-to-end execution: prompt → plan → execute → learn

---

### Week 7: Core 6.3-6.4 (Multi-Agent + Performance Testing)
**Parallel Streams:**
- Team 1: Core 6.3 (multi-agent coordination tests)
- Team 2: Core 6.4 (performance testing and optimization)

**Integration Work:**
- Verify 200 agents work without resource exhaustion
- Identify and fix bottlenecks
- Performance profiling (CPU, memory, latency)

**End of Week Deliverables:**
- 200 agents tested and working
- Performance targets met (or documented exceptions)
- All resource pooling verified
- Bottleneck analysis complete

---

### Week 8: Core 6.5 + Final Integration (Documentation + Deployment)
**Parallel Streams:**
- Team 1: Core 6.5 (documentation, deployment guides)
- Team 2: Final integration testing, bug fixes, performance tuning

**Integration Work:**
- End-to-end integration tests (full workflow)
- SWE Bench evaluation setup
- Deployment documentation
- Production readiness checklist

**End of Week Deliverables:**
- Documentation complete
- Deployment guide ready
- All 6 cores integrated and tested
- Ready for production deployment

---

## Part 3: Critical Path & Dependencies

### Dependency Graph:
```
Core 1 (Agent Framework)
  ↓
Core 2 (Context Management)
  ↓
Core 3 (Agent API) ────→ Core 4 (OpenAI API)
  ↓
Core 5 (TUI)
  ↓
Core 6 (Integration)
  ├→ Core 6.1 (Brain Layer Integration) → Core 3 (Brain + Agent integration)
  ├→ Core 6.2 (SmartCP Integration) → Core 3 (Tool integration)
  ├→ Core 6.3 (Multi-Agent Tests)
  └→ Core 6.4 (Performance Tests)
```

**Critical Path:** Core 1 → Core 2 → Core 3 → Core 5 → Core 6 (15 weeks if sequential, 8 weeks with parallelization)

**Parallelizable Streams:**
1. Core 1 + Core 2 (independent)
2. Core 3 + Core 4 (can start simultaneously after Core 1)
3. Core 5 (can start after Core 3 ready for testing)
4. Core 6 (waits for Core 1-5, but components can be integrated incrementally)

---

## Part 4: Success Criteria & Acceptance

### Phase 5 Success Criteria:

✅ **All 6 Core Components Implemented**
- Core 1: Agent framework fully functional
- Core 2: Context management working
- Core 3: Agent API with streaming
- Core 4: OpenAI-compatible API
- Core 5: TUI responsive and interactive
- Core 6: Full integration complete

✅ **Test Coverage: >80%**
- Unit tests: >85% coverage
- Integration tests: >75% coverage
- Performance tests: all targets met
- E2E tests: critical paths covered

✅ **Performance Targets:**
- Agent spawn: <200ms (single), <30s (100 parallel)
- API latency: <1s (p95)
- Tool invocation: <500ms (p95)
- Memory: <2GB for 200 agents
- TUI startup: <500ms

✅ **Integration Quality:**
- Phase 3 (Brain Layer) integrated seamlessly
- SmartCP tools fully accessible
- OpenAI client library compatibility
- Multi-agent orchestration verified

✅ **Production Readiness:**
- Documentation complete
- Deployment guide finalized
- Configuration documented
- Monitoring/observability in place
- Error handling comprehensive

---

## Part 5: Risk Mitigation

### High-Risk Areas:

1. **Multi-Agent Resource Contention (Week 7)**
   - Risk: OOM errors at 200 agents
   - Mitigation: Resource pooling (Core 1.3), incremental scaling tests
   - Contingency: Reduce max agents to 100, revisit pooling strategy

2. **OpenAI API Compatibility (Week 4)**
   - Risk: Client library incompatibilities
   - Mitigation: Early testing with openai-python, frequent compatibility checks
   - Contingency: Implement minimal compatibility layer

3. **TUI Responsiveness Under Load (Week 5-6)**
   - Risk: UI lag with 100+ active agents
   - Mitigation: Async updates, batching events, performance profiling
   - Contingency: Reduce update frequency, implement pagination

4. **Brain Layer Integration (Week 6)**
   - Risk: Memory system doesn't integrate cleanly with agents
   - Mitigation: Early architectural planning, incremental integration
   - Contingency: Implement adapter layer for compatibility

---

## Part 6: Deliverables Summary

**Total Implementation:**
- **Production Code:** ~6000 lines
- **Test Code:** ~4000 lines
- **Documentation:** ~3000 lines
- **Total Files:** 60+ new files
- **Test Coverage:** >80%
- **Timeline:** 8 weeks with 4 feature teams

**Ready for:**
- SWE Bench evaluation
- Production deployment
- Client integration (OpenAI library compatibility)
- Multi-tenant operation (50-200+ agents)
- Performance monitoring and optimization

---

## Execution Checklist

### Pre-Implementation (Day 0)
- [ ] Approve Phase 5 plan
- [ ] Form 4 feature teams (2-4 engineers each)
- [ ] Set up CI/CD pipeline
- [ ] Create Supabase tables and indexes
- [ ] Set up Redis for session storage
- [ ] Distribute work to teams

### Weekly Checkpoint
- [ ] Monday: Plan week, identify blockers from previous week
- [ ] Daily: Team standups (15 min each)
- [ ] Thursday: Integration testing across teams
- [ ] Friday: Review pull requests, merge to main

### End of Phase Celebration
- [ ] All 6 cores tested and integrated ✅
- [ ] Performance targets met ✅
- [ ] Documentation complete ✅
- [ ] Ready for production ✅
- [ ] Team retrospective and lessons learned ✅

---

**Status: READY FOR IMPLEMENTATION** 🚀

This plan provides the detailed roadmap for Phase 5. Each team can operate independently with clear interfaces and integration points. The 8-week timeline with parallelization is aggressive but achievable given the detailed Phase 4 research that resolved all major unknowns.

