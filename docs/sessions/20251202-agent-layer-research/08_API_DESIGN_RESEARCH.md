# Agent Layer API Design Research

**Session:** 20251202-agent-layer-research
**Research Stream:** E1-E5 (API Design & Architecture)
**Timeline:** Day 3-4 of Phase 4 Research
**Status:** Complete
**Last Updated:** 2025-12-02

---

## Executive Summary

This document presents comprehensive research on dual-API architecture for the Agent Layer, covering:
1. **OpenAI API Compatibility** (E1) - Full specification mapping and compatibility requirements
2. **Agent-Optimized API Design** (E2) - Agentic control surfaces and multi-agent coordination
3. **Session & State Management** (E3) - Lifecycle patterns and persistence strategies
4. **Authentication & Authorization** (E4) - Security model and RBAC design
5. **Message Protocol Design** (E5) - Request/response structures and streaming semantics

**Key Finding:** Dual-API approach enables both LLM compatibility (via OpenAI-compatible endpoints) and advanced agentic features (via agent-optimized endpoints) without compromising either use case.

---

## Table of Contents

1. [E1: OpenAI API Compatibility Research](#e1-openai-api-compatibility-research)
2. [E2: Agent-Optimized API Design](#e2-agent-optimized-api-design)
3. [E3: Session & State Management](#e3-session--state-management)
4. [E4: Authentication & Authorization](#e4-authentication--authorization)
5. [E5: Message Protocol Design](#e5-message-protocol-design)
6. [Integration Architecture](#integration-architecture)
7. [Implementation Recommendations](#implementation-recommendations)
8. [References & Sources](#references--sources)

---

## E1: OpenAI API Compatibility Research

### Overview

Full OpenAI Chat Completions API compatibility ensures drop-in replacement capability for existing LLM applications while enabling gradual migration to agent-optimized features.

### Core Endpoints Required

#### 1. POST /v1/chat/completions

**Purpose:** Primary endpoint for chat-based interactions compatible with OpenAI SDK.

**Request Structure:**
```json
{
  "model": "claude-sonnet-4-5",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false,
  "temperature": 1.0,
  "max_tokens": 1000,
  "top_p": 1.0,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0,
  "stop": null,
  "n": 1,
  "tools": [],
  "tool_choice": "auto",
  "response_format": {"type": "text"}
}
```

**Response Structure (Non-Streaming):**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1699896916,
  "model": "claude-sonnet-4-5",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 10,
    "total_tokens": 30
  }
}
```

#### 2. Streaming Response Format

**When `stream: true`:**

Responses sent as Server-Sent Events (SSE):

```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1699896916,"model":"claude-sonnet-4-5","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1699896916,"model":"claude-sonnet-4-5","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1699896916,"model":"claude-sonnet-4-5","choices":[{"index":0,"delta":{"content":"!"},"finish_reason":"stop"}]}

data: [DONE]
```

**Key Streaming Parameters:**
- `stream: true` - Enables SSE streaming
- `latency_tier` - Options: 'auto', 'default', 'flex' (for scale tier customers)

### Tool/Function Calling Support

#### Tool Definition Format

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_current_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "The city and state, e.g. San Francisco, CA"
            },
            "unit": {
              "type": "string",
              "enum": ["celsius", "fahrenheit"]
            }
          },
          "required": ["location"]
        },
        "strict": true
      }
    }
  ],
  "tool_choice": "auto"
}
```

#### Tool Call Response

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "get_current_weather",
              "arguments": "{\"location\":\"San Francisco, CA\",\"unit\":\"celsius\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

#### Tool Call Response Handling

Client adds tool result to conversation:

```json
{
  "messages": [
    ...,
    {
      "role": "tool",
      "tool_call_id": "call_abc123",
      "content": "{\"temperature\": 22, \"unit\": \"celsius\", \"description\": \"Sunny\"}"
    }
  ]
}
```

### Structured Outputs

**When `strict: true` in function definition:**
- Guarantees arguments match JSON Schema exactly
- Model generates only valid parameters
- No need for validation layer

### Response Format Options

```json
{
  "response_format": {
    "type": "json_object"  // or "text"
  }
}
```

### OpenAI Compatibility Layer Requirements

**Must Support:**
1. All standard chat completion parameters
2. Function/tool calling with streaming
3. Multiple tool calls per response
4. Structured outputs with strict mode
5. Standard error codes and formats
6. Usage tracking (tokens)
7. Stop sequences
8. Temperature/top_p/frequency_penalty/presence_penalty
9. Max tokens limiting
10. Multi-turn conversations

**Mapping Challenges:**
- Claude → OpenAI parameter translation
- Model name aliasing
- Token counting differences
- Streaming format differences
- Error code mapping

---

## E2: Agent-Optimized API Design

### Philosophy

Agent-optimized APIs prioritize **autonomy, orchestration, and stateful workflows** over simple request-response patterns. Key principles:

1. **Direct Tool Invocation** - Agents call tools directly without LLM mediation
2. **Sub-Agent Spawning** - Hierarchical agent delegation
3. **Context/Working Directory** - Persistent workspace state
4. **Streaming & Real-Time Updates** - Continuous feedback loops
5. **Multi-Agent Coordination** - Parallel and sequential agent orchestration

### Core Agent API Endpoints

#### 1. POST /v1/agents/execute

**Purpose:** Execute agent with full control over workflow, tools, and sub-agents.

**Request:**
```json
{
  "agent_id": "agen-01",
  "task": "Analyze codebase and generate test coverage report",
  "context": {
    "workspace_id": "ws-123",
    "working_directory": "/projects/myapp",
    "user_id": "usr-456",
    "session_id": "sess-789"
  },
  "tools": [
    "workspace_read",
    "workspace_write",
    "code_analysis",
    "test_generation"
  ],
  "sub_agents": {
    "enabled": true,
    "max_depth": 3,
    "allowed_agents": ["test_specialist", "code_analyzer"]
  },
  "streaming": {
    "enabled": true,
    "events": ["tool_call", "thought", "progress", "result"]
  },
  "constraints": {
    "max_duration_seconds": 300,
    "max_tool_calls": 50,
    "max_sub_agents": 5
  }
}
```

**Response (Streaming):**
```
event: agent_started
data: {"agent_id":"agen-01","task_id":"task-abc","started_at":"2025-12-02T10:00:00Z"}

event: thought
data: {"content":"Analyzing project structure...","confidence":0.9}

event: tool_call
data: {"tool":"workspace_read","args":{"path":"/src"},"tool_call_id":"tc-001"}

event: tool_result
data: {"tool_call_id":"tc-001","result":{"files":["app.py","utils.py"],"count":2}}

event: progress
data: {"step":"Analysis","progress":0.5,"message":"Found 50 files, analyzing..."}

event: sub_agent_spawned
data: {"sub_agent_id":"agen-02","parent":"agen-01","task":"Generate unit tests for app.py"}

event: result
data: {"task_id":"task-abc","status":"completed","output":{"coverage":85,"report_url":"..."}}

event: done
data: {"task_id":"task-abc","duration_seconds":120,"tokens_used":5000}
```

#### 2. POST /v1/agents/tools/invoke

**Purpose:** Direct tool invocation without LLM decision-making.

**Request:**
```json
{
  "tool_name": "workspace_read",
  "arguments": {
    "workspace_id": "ws-123",
    "path": "/src/components"
  },
  "context": {
    "user_id": "usr-456",
    "session_id": "sess-789"
  }
}
```

**Response:**
```json
{
  "tool_call_id": "tc-123",
  "tool_name": "workspace_read",
  "result": {
    "files": [
      {"name": "Button.tsx", "size": 1024, "modified": "2025-12-01T10:00:00Z"},
      {"name": "Input.tsx", "size": 2048, "modified": "2025-12-01T11:00:00Z"}
    ],
    "count": 2
  },
  "execution_time_ms": 45,
  "status": "success"
}
```

#### 3. POST /v1/agents/spawn

**Purpose:** Spawn sub-agent for delegated task.

**Request:**
```json
{
  "parent_agent_id": "agen-01",
  "agent_type": "test_specialist",
  "task": "Generate unit tests for Button component",
  "context": {
    "workspace_id": "ws-123",
    "file_path": "/src/components/Button.tsx",
    "test_framework": "jest"
  },
  "tools": ["code_read", "test_write"],
  "return_control": "on_completion"
}
```

**Response:**
```json
{
  "sub_agent_id": "agen-02",
  "parent_agent_id": "agen-01",
  "status": "spawned",
  "estimated_duration_seconds": 60,
  "streaming_url": "/v1/agents/agen-02/stream"
}
```

#### 4. GET /v1/agents/{agent_id}/stream

**Purpose:** Subscribe to agent event stream (SSE).

**Response Stream:**
```
event: connected
data: {"agent_id":"agen-01","session_id":"sess-789"}

event: thought
data: {"content":"Planning approach..."}

event: tool_call
data: {...}

event: error
data: {"code":"TOOL_TIMEOUT","message":"Tool execution exceeded 30s"}
```

#### 5. POST /v1/agents/{agent_id}/interrupt

**Purpose:** Interrupt running agent (pause, stop, or redirect).

**Request:**
```json
{
  "action": "pause",  // or "stop", "redirect"
  "reason": "User requested pause",
  "redirect_task": null  // optional new task
}
```

#### 6. GET /v1/agents/{agent_id}/state

**Purpose:** Get current agent state and context.

**Response:**
```json
{
  "agent_id": "agen-01",
  "status": "running",
  "current_step": "analysis",
  "progress": 0.65,
  "context": {
    "workspace_id": "ws-123",
    "working_directory": "/projects/myapp",
    "variables": {
      "file_count": 50,
      "test_coverage": 75
    }
  },
  "tool_calls": 25,
  "sub_agents": [
    {"sub_agent_id": "agen-02", "status": "completed"}
  ],
  "started_at": "2025-12-02T10:00:00Z",
  "elapsed_seconds": 120
}
```

### Multi-Agent Coordination Patterns

#### Pattern 1: Sequential Delegation

```json
{
  "orchestration": {
    "type": "sequential",
    "agents": [
      {
        "agent_type": "code_analyzer",
        "task": "Analyze codebase structure"
      },
      {
        "agent_type": "test_generator",
        "task": "Generate tests based on analysis",
        "depends_on": ["code_analyzer"]
      },
      {
        "agent_type": "test_runner",
        "task": "Execute tests and report",
        "depends_on": ["test_generator"]
      }
    ]
  }
}
```

#### Pattern 2: Parallel Execution

```json
{
  "orchestration": {
    "type": "parallel",
    "agents": [
      {
        "agent_type": "linter",
        "task": "Run linting checks"
      },
      {
        "agent_type": "type_checker",
        "task": "Run type checking"
      },
      {
        "agent_type": "security_scanner",
        "task": "Run security scan"
      }
    ],
    "wait_for": "all",  // or "first", "any"
    "aggregate_results": true
  }
}
```

#### Pattern 3: Supervisor Pattern

```json
{
  "orchestration": {
    "type": "supervisor",
    "supervisor_agent": "task_coordinator",
    "worker_agents": [
      "code_analyzer",
      "test_generator",
      "doc_generator"
    ],
    "strategy": "dynamic_allocation"
  }
}
```

### Working Directory & Context Management

```json
{
  "context": {
    "workspace_id": "ws-123",
    "working_directory": "/projects/myapp",
    "environment": {
      "language": "typescript",
      "framework": "react",
      "test_framework": "jest"
    },
    "memory": {
      "short_term": {
        "recent_files": [...],
        "recent_errors": [...]
      },
      "long_term": {
        "project_conventions": [...],
        "test_patterns": [...]
      }
    },
    "permissions": {
      "read": ["/**"],
      "write": ["/tests/**"],
      "execute": ["/scripts/**"]
    }
  }
}
```

---

## E3: Session & State Management

### Session Lifecycle

#### 1. Session Creation

```
POST /v1/sessions

Request:
{
  "user_id": "usr-456",
  "workspace_id": "ws-123",
  "session_type": "agent",  // or "chat", "workflow"
  "ttl_seconds": 3600,
  "persistence": "redis"  // or "memory", "postgres"
}

Response:
{
  "session_id": "sess-789",
  "created_at": "2025-12-02T10:00:00Z",
  "expires_at": "2025-12-02T11:00:00Z",
  "state_url": "/v1/sessions/sess-789/state"
}
```

#### 2. Session State Structure

```json
{
  "session_id": "sess-789",
  "user_id": "usr-456",
  "workspace_id": "ws-123",
  "created_at": "2025-12-02T10:00:00Z",
  "last_activity_at": "2025-12-02T10:15:00Z",
  "expires_at": "2025-12-02T11:00:00Z",
  "conversation_history": [
    {
      "role": "user",
      "content": "Analyze the codebase",
      "timestamp": "2025-12-02T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "I'll analyze the codebase...",
      "timestamp": "2025-12-02T10:00:05Z",
      "tool_calls": [...]
    }
  ],
  "context": {
    "working_directory": "/projects/myapp",
    "active_agents": ["agen-01", "agen-02"],
    "variables": {
      "project_type": "typescript-react",
      "test_coverage": 85
    }
  },
  "metadata": {
    "total_tool_calls": 25,
    "total_tokens": 5000,
    "total_cost_usd": 0.15
  }
}
```

#### 3. State Persistence Strategies

**Option 1: In-Memory (Fast, Volatile)**
- Use: Short-lived sessions, development
- Storage: Python dict, TTLCache
- Pros: Fast, simple
- Cons: Lost on restart, not distributed

**Option 2: Redis (Fast, Distributed)**
- Use: Production sessions, distributed systems
- Storage: Redis with TTL
- Pros: Fast, distributed, automatic expiration
- Cons: Additional infrastructure

**Option 3: PostgreSQL (Persistent, Queryable)**
- Use: Long-term sessions, audit trail
- Storage: PostgreSQL JSONB
- Pros: Persistent, queryable, auditable
- Cons: Slower than Redis

**Hybrid Approach (Recommended):**
```
- Redis: Active session state (hot data)
- PostgreSQL: Session history, audit trail (cold data)
- Automatic migration: Redis → PostgreSQL after expiration
```

#### 4. Session API Endpoints

```
POST   /v1/sessions                    # Create session
GET    /v1/sessions/{session_id}       # Get session metadata
GET    /v1/sessions/{session_id}/state # Get full session state
PATCH  /v1/sessions/{session_id}       # Update session (extend TTL, etc.)
DELETE /v1/sessions/{session_id}       # End session
POST   /v1/sessions/{session_id}/checkpoint  # Create checkpoint
GET    /v1/sessions/{session_id}/checkpoints # List checkpoints
POST   /v1/sessions/{session_id}/restore     # Restore from checkpoint
```

### Multi-Turn Conversation Handling

#### Conversation State Management

```json
{
  "conversation": {
    "session_id": "sess-789",
    "turn_count": 5,
    "messages": [
      {
        "turn": 1,
        "role": "user",
        "content": "Analyze codebase",
        "timestamp": "2025-12-02T10:00:00Z"
      },
      {
        "turn": 1,
        "role": "assistant",
        "content": "I'll analyze...",
        "tool_calls": [...],
        "timestamp": "2025-12-02T10:00:05Z"
      },
      {
        "turn": 2,
        "role": "user",
        "content": "Generate tests",
        "timestamp": "2025-12-02T10:01:00Z"
      }
    ],
    "context_window": {
      "max_tokens": 200000,
      "current_tokens": 5000,
      "truncation_strategy": "sliding_window"
    }
  }
}
```

#### Context Window Management

**Strategy 1: Sliding Window**
```
Keep most recent N messages
Automatically drop oldest messages when limit reached
```

**Strategy 2: Importance-Based Pruning**
```
Assign importance scores to messages
Keep high-importance messages (system prompts, key decisions)
Prune low-importance messages when needed
```

**Strategy 3: Summarization**
```
Periodically summarize conversation history
Replace old messages with summary
Maintain key facts and decisions
```

### Working Directory Tracking

#### Directory State

```json
{
  "working_directory": {
    "session_id": "sess-789",
    "current_path": "/projects/myapp",
    "history": [
      {
        "path": "/projects",
        "timestamp": "2025-12-02T10:00:00Z",
        "reason": "session_start"
      },
      {
        "path": "/projects/myapp",
        "timestamp": "2025-12-02T10:00:10Z",
        "reason": "cd_command"
      }
    ],
    "file_watches": [
      {
        "path": "/projects/myapp/src/**/*.ts",
        "events": ["modified", "created", "deleted"],
        "callback_url": "/v1/events/file_changed"
      }
    ],
    "permissions": {
      "read": ["/projects/**"],
      "write": ["/projects/myapp/**"],
      "execute": ["/projects/myapp/scripts/**"]
    }
  }
}
```

### Memory Integration Strategies

#### Short-Term Memory (Session-Scoped)

```json
{
  "short_term_memory": {
    "session_id": "sess-789",
    "capacity": 100,
    "items": [
      {
        "key": "recent_files",
        "value": ["app.py", "utils.py"],
        "timestamp": "2025-12-02T10:15:00Z",
        "ttl_seconds": 300
      },
      {
        "key": "recent_errors",
        "value": ["TypeError in line 45"],
        "timestamp": "2025-12-02T10:14:00Z",
        "ttl_seconds": 600
      }
    ]
  }
}
```

#### Long-Term Memory (User/Workspace-Scoped)

```json
{
  "long_term_memory": {
    "user_id": "usr-456",
    "workspace_id": "ws-123",
    "facts": [
      {
        "key": "project_conventions",
        "value": "Use PascalCase for components",
        "confidence": 0.95,
        "learned_at": "2025-11-01T10:00:00Z",
        "reinforced_count": 25
      },
      {
        "key": "test_patterns",
        "value": "Use Jest for unit tests",
        "confidence": 1.0,
        "learned_at": "2025-10-15T10:00:00Z",
        "reinforced_count": 100
      }
    ],
    "storage": "vector_db"  // for semantic retrieval
  }
}
```

---

## E4: Authentication & Authorization

### Authentication Model

#### 1. API Key Authentication

**Structure:**
```
Authorization: Bearer sk_live_abc123xyz789
```

**Key Types:**
```
- sk_live_*   : Production keys (full access)
- sk_test_*   : Development keys (sandbox only)
- sk_admin_*  : Admin keys (full system access)
```

**Key Management:**
```
POST   /v1/api-keys              # Create API key
GET    /v1/api-keys              # List API keys
GET    /v1/api-keys/{key_id}     # Get API key details
DELETE /v1/api-keys/{key_id}     # Revoke API key
PATCH  /v1/api-keys/{key_id}     # Update API key (rate limits, scopes)
```

**Request:**
```json
{
  "name": "Production API Key",
  "scopes": ["agents:execute", "tools:invoke", "sessions:manage"],
  "rate_limit": {
    "requests_per_minute": 60,
    "requests_per_hour": 1000
  },
  "ip_whitelist": ["203.0.113.0/24"],
  "expires_at": "2026-12-01T00:00:00Z"
}
```

**Response:**
```json
{
  "key_id": "key-123",
  "key": "sk_live_abc123xyz789",
  "name": "Production API Key",
  "scopes": ["agents:execute", "tools:invoke", "sessions:manage"],
  "created_at": "2025-12-02T10:00:00Z",
  "expires_at": "2026-12-01T00:00:00Z",
  "last_used_at": null
}
```

#### 2. JWT Token Authentication

**Structure:**
```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Token Claims:**
```json
{
  "iss": "https://api.smartcp.ai",
  "sub": "usr-456",
  "aud": "smartcp-api",
  "exp": 1733227200,
  "iat": 1733140800,
  "scopes": ["agents:execute", "tools:invoke"],
  "workspace_id": "ws-123",
  "tenant_id": "tenant-abc"
}
```

**Token Endpoint:**
```
POST /v1/auth/token

Request:
{
  "grant_type": "client_credentials",
  "client_id": "client-123",
  "client_secret": "secret-xyz",
  "scope": "agents:execute tools:invoke"
}

Response:
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "agents:execute tools:invoke"
}
```

### Role-Based Access Control (RBAC)

#### Role Hierarchy

```
Owner
  ├─ Admin
  │   ├─ Developer
  │   │   ├─ Viewer
  │   │   └─ Agent (machine identity)
  │   └─ Operator
  └─ Billing
```

#### Permission Matrix

| Resource | Owner | Admin | Developer | Operator | Viewer | Agent |
|----------|-------|-------|-----------|----------|--------|-------|
| agents:execute | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| agents:manage | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| tools:invoke | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| tools:create | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| sessions:read | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| sessions:manage | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| workspaces:read | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| workspaces:write | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| billing:read | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| billing:manage | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| admin:full | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |

#### Scope Definitions

```json
{
  "scopes": {
    "agents:execute": {
      "description": "Execute agents",
      "resources": ["POST /v1/agents/execute", "GET /v1/agents/{id}/stream"]
    },
    "agents:manage": {
      "description": "Manage agent configurations",
      "resources": ["POST /v1/agents", "PUT /v1/agents/{id}", "DELETE /v1/agents/{id}"]
    },
    "tools:invoke": {
      "description": "Invoke tools",
      "resources": ["POST /v1/agents/tools/invoke"]
    },
    "tools:create": {
      "description": "Create custom tools",
      "resources": ["POST /v1/tools", "PUT /v1/tools/{id}"]
    },
    "sessions:manage": {
      "description": "Manage sessions",
      "resources": ["POST /v1/sessions", "DELETE /v1/sessions/{id}"]
    },
    "workspaces:write": {
      "description": "Write to workspaces",
      "resources": ["POST /v1/workspaces/{id}/files", "PUT /v1/workspaces/{id}/files"]
    }
  }
}
```

### User/Tenant Isolation

#### Multi-Tenancy Model

```
Tenant (Organization)
  ├─ Workspaces
  │   ├─ Workspace 1
  │   │   ├─ Sessions
  │   │   ├─ Agents
  │   │   └─ Files
  │   └─ Workspace 2
  └─ Users
      ├─ User 1 (Owner)
      ├─ User 2 (Admin)
      └─ User 3 (Developer)
```

#### Isolation Strategy

**Database Level:**
```sql
-- All tables have tenant_id and workspace_id
CREATE TABLE sessions (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  workspace_id UUID NOT NULL,
  user_id UUID NOT NULL,
  ...
  CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
  CONSTRAINT fk_workspace FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

-- Row-level security
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON sessions
  USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

**API Level:**
```python
@app.middleware("http")
async def tenant_isolation_middleware(request: Request, call_next):
    # Extract tenant from API key or JWT
    tenant_id = extract_tenant_from_auth(request)

    # Set tenant context for query filters
    request.state.tenant_id = tenant_id
    request.state.workspace_id = extract_workspace(request)

    return await call_next(request)
```

### Resource Quota Enforcement

#### Quota Types

```json
{
  "quotas": {
    "tenant_id": "tenant-abc",
    "plan": "pro",
    "limits": {
      "requests_per_minute": 1000,
      "requests_per_hour": 10000,
      "requests_per_day": 100000,
      "concurrent_agents": 10,
      "max_session_duration_seconds": 3600,
      "max_tool_calls_per_session": 1000,
      "storage_gb": 100,
      "total_tokens_per_month": 10000000
    },
    "usage": {
      "requests_this_minute": 50,
      "requests_this_hour": 500,
      "requests_this_day": 5000,
      "concurrent_agents": 3,
      "storage_used_gb": 25,
      "tokens_used_this_month": 250000
    }
  }
}
```

#### Rate Limiting Strategy

**Per-Endpoint Rate Limits:**
```
GET  /v1/chat/completions         : 60/min, 1000/hr
POST /v1/agents/execute           : 30/min, 500/hr
POST /v1/agents/tools/invoke      : 100/min, 2000/hr
GET  /v1/sessions/{id}/state      : 120/min, 5000/hr
```

**Rate Limit Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1733140920
X-RateLimit-Retry-After: 30
```

**Rate Limit Response:**
```
HTTP/1.1 429 Too Many Requests
Retry-After: 30

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry after 30 seconds.",
    "details": {
      "limit": 60,
      "remaining": 0,
      "reset_at": "2025-12-02T10:15:00Z"
    }
  }
}
```

### Security Best Practices

#### 1. API Key Security
- Generate with crypto.randomBytes(32)
- Store hashed (SHA-256 + salt)
- Prefix-based key types (sk_live_, sk_test_)
- Automatic rotation (optional, configurable)
- IP whitelisting support
- Revocation audit trail

#### 2. JWT Security
- Use RS256 (asymmetric) for distributed systems
- Short expiration (15-60 minutes)
- Refresh token rotation
- Token revocation list (Redis)
- Audience validation
- Issuer validation

#### 3. Transmission Security
- TLS 1.3 only
- Perfect Forward Secrecy (PFS)
- HTTP Strict Transport Security (HSTS)
- Certificate pinning (mobile/desktop clients)

#### 4. Request Validation
- Schema validation (Pydantic)
- Input sanitization
- SQL injection prevention
- XSS prevention
- CSRF protection

---

## E5: Message Protocol Design

### Request/Response Structure

#### Standard Request Format

```json
{
  "version": "1.0",
  "request_id": "req-abc123",
  "timestamp": "2025-12-02T10:00:00Z",
  "endpoint": "/v1/agents/execute",
  "auth": {
    "type": "bearer",
    "token": "sk_live_abc123xyz789"
  },
  "headers": {
    "X-Request-ID": "req-abc123",
    "X-Tenant-ID": "tenant-abc",
    "X-Workspace-ID": "ws-123",
    "Content-Type": "application/json"
  },
  "body": {
    // Endpoint-specific payload
  }
}
```

#### Standard Response Format

**Success Response:**
```json
{
  "success": true,
  "request_id": "req-abc123",
  "response_id": "res-xyz789",
  "timestamp": "2025-12-02T10:00:05Z",
  "data": {
    // Endpoint-specific data
  },
  "metadata": {
    "execution_time_ms": 450,
    "tokens_used": 150,
    "cost_usd": 0.001
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "request_id": "req-abc123",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid tool name: 'invalid_tool'",
    "details": {
      "field": "tool_name",
      "expected": "string matching pattern ^[a-z_]+$",
      "received": "invalid_tool"
    },
    "trace_id": "trace-123",
    "timestamp": "2025-12-02T10:00:05Z"
  }
}
```

### Streaming Semantics

#### Server-Sent Events (SSE) Protocol

**Connection Establishment:**
```
GET /v1/agents/{agent_id}/stream
Accept: text/event-stream
Authorization: Bearer sk_live_abc123xyz789

HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**Event Format:**
```
event: <event_type>
id: <event_id>
data: <json_payload>
retry: <retry_ms>

```

**Event Types:**
```
- connected        : Connection established
- agent_started    : Agent execution started
- thought          : Agent reasoning/planning
- tool_call        : Tool invocation
- tool_result      : Tool execution result
- progress         : Progress update
- sub_agent_spawned: Sub-agent created
- result           : Final result
- error            : Error occurred
- done             : Stream complete
```

**Example Stream:**
```
event: connected
id: 1
data: {"session_id":"sess-789","agent_id":"agen-01"}

event: agent_started
id: 2
data: {"task_id":"task-abc","started_at":"2025-12-02T10:00:00Z"}

event: thought
id: 3
data: {"content":"Analyzing project structure...","confidence":0.9}

event: tool_call
id: 4
data: {"tool":"workspace_read","args":{"path":"/src"},"tool_call_id":"tc-001"}

event: tool_result
id: 5
data: {"tool_call_id":"tc-001","result":{"files":["app.py"],"count":1},"duration_ms":45}

event: progress
id: 6
data: {"step":"Analysis","progress":0.5,"total_steps":4}

event: result
id: 7
data: {"task_id":"task-abc","status":"completed","output":{"coverage":85}}

event: done
id: 8
data: {"task_id":"task-abc","duration_seconds":120}
```

#### Streaming Options

**Chunked Transfer Encoding:**
```
Transfer-Encoding: chunked
Content-Type: application/json

<chunk_size_hex>\r\n
<chunk_data>\r\n
<chunk_size_hex>\r\n
<chunk_data>\r\n
0\r\n
\r\n
```

**WebSocket (Alternative):**
```
WebSocket /v1/agents/{agent_id}/ws

Client → Server:
{"type":"subscribe","events":["thought","tool_call","result"]}

Server → Client:
{"event":"thought","data":{...}}
{"event":"tool_call","data":{...}}
{"event":"result","data":{...}}
```

### Error Handling

#### Error Code Taxonomy

```
4xx Client Errors:
  400 BAD_REQUEST
    - VALIDATION_ERROR
    - INVALID_REQUEST_FORMAT
    - MISSING_REQUIRED_FIELD

  401 UNAUTHORIZED
    - INVALID_API_KEY
    - EXPIRED_TOKEN
    - MISSING_AUTHENTICATION

  403 FORBIDDEN
    - INSUFFICIENT_PERMISSIONS
    - QUOTA_EXCEEDED
    - RESOURCE_ACCESS_DENIED

  404 NOT_FOUND
    - AGENT_NOT_FOUND
    - SESSION_NOT_FOUND
    - TOOL_NOT_FOUND

  409 CONFLICT
    - SESSION_ALREADY_EXISTS
    - AGENT_ALREADY_RUNNING

  429 TOO_MANY_REQUESTS
    - RATE_LIMIT_EXCEEDED

5xx Server Errors:
  500 INTERNAL_SERVER_ERROR
    - UNHANDLED_EXCEPTION
    - DATABASE_ERROR

  502 BAD_GATEWAY
    - UPSTREAM_SERVICE_ERROR

  503 SERVICE_UNAVAILABLE
    - MAINTENANCE_MODE
    - OVERLOADED

  504 GATEWAY_TIMEOUT
    - AGENT_TIMEOUT
    - TOOL_TIMEOUT
```

#### Error Response Schema

```json
{
  "success": false,
  "error": {
    "code": "TOOL_TIMEOUT",
    "message": "Tool execution exceeded 30 second timeout",
    "details": {
      "tool_name": "code_analysis",
      "timeout_seconds": 30,
      "elapsed_seconds": 35
    },
    "trace_id": "trace-abc123",
    "timestamp": "2025-12-02T10:00:35Z",
    "request_id": "req-xyz789",
    "documentation_url": "https://docs.smartcp.ai/errors/TOOL_TIMEOUT"
  }
}
```

### Versioning Strategy

#### URL-Based Versioning (Primary)

```
/v1/agents/execute
/v1/chat/completions
/v2/agents/execute  (future)
```

#### Header-Based Versioning (Secondary)

```
API-Version: 2025-12-02
```

**Version Policy:**
- Major versions: Breaking changes (v1 → v2)
- Date-based versions: Feature additions (2025-12-02)
- Deprecated endpoints: 6-month sunset period
- Version lifecycle: documented at /v1/versions

#### Backward Compatibility

**Additive Changes (Non-Breaking):**
- New optional fields
- New endpoints
- New event types
- New error codes (with fallback)

**Breaking Changes (Requires New Version):**
- Removing fields
- Changing field types
- Changing response structure
- Removing endpoints
- Changing authentication

---

## Integration Architecture

### Dual-API Architecture Diagram

```
                     ┌─────────────────────────────────────┐
                     │         API Gateway                 │
                     │  (Authentication, Rate Limiting)    │
                     └───────────────┬─────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
         ┌──────────▼──────────┐         ┌──────────▼──────────┐
         │  OpenAI-Compatible  │         │  Agent-Optimized    │
         │      Endpoints      │         │     Endpoints       │
         │                     │         │                     │
         │ /v1/chat/completions│         │ /v1/agents/execute  │
         │ /v1/completions     │         │ /v1/agents/tools/*  │
         │ /v1/embeddings      │         │ /v1/agents/spawn    │
         └──────────┬──────────┘         └──────────┬──────────┘
                    │                               │
         ┌──────────▼──────────┐         ┌──────────▼──────────┐
         │  Compatibility      │         │  Agent Orchestrator │
         │     Layer           │         │                     │
         │ - Format translation│         │ - Direct tool calls │
         │ - Model mapping     │         │ - Sub-agent spawn   │
         │ - Token counting    │         │ - State management  │
         └──────────┬──────────┘         └──────────┬──────────┘
                    │                               │
                    └────────────────┬──────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │      Core Services              │
                    │                                 │
                    │ - Tool Registry                 │
                    │ - Session Manager               │
                    │ - Model Router                  │
                    │ - Memory Service                │
                    │ - Workspace Service             │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │    Infrastructure               │
                    │                                 │
                    │ - PostgreSQL (persistent state) │
                    │ - Redis (session cache)         │
                    │ - Vector DB (embeddings)        │
                    │ - S3 (file storage)             │
                    └─────────────────────────────────┘
```

### Request Flow Examples

#### Example 1: OpenAI-Compatible Chat Request

```
1. Client Request:
   POST /v1/chat/completions
   {
     "model": "claude-sonnet-4-5",
     "messages": [{"role":"user","content":"Hello"}],
     "stream": true
   }

2. API Gateway:
   - Validate API key
   - Check rate limits
   - Extract tenant/workspace

3. Compatibility Layer:
   - Translate to internal format
   - Map model name
   - Set up streaming

4. Core Services:
   - Load session state (if exists)
   - Route to model service
   - Execute request

5. Response Stream:
   SSE events → OpenAI format → Client
```

#### Example 2: Agent-Optimized Execution

```
1. Client Request:
   POST /v1/agents/execute
   {
     "agent_id": "agen-01",
     "task": "Analyze codebase",
     "tools": ["workspace_read"],
     "streaming": {"enabled": true}
   }

2. API Gateway:
   - Validate JWT token
   - Check permissions (agents:execute)
   - Extract tenant/workspace

3. Agent Orchestrator:
   - Create/restore session
   - Initialize agent context
   - Set up tool access

4. Execution Loop:
   - Agent plans approach
   - Calls tools directly (no LLM mediation)
   - Spawns sub-agents if needed
   - Streams progress events

5. Response Stream:
   SSE events → Agent format → Client
```

### Shared Infrastructure

#### Session Manager (Unified)

```python
class SessionManager:
    """Unified session management for both API types."""

    def __init__(self, redis: Redis, postgres: PostgreSQL):
        self.redis = redis
        self.postgres = postgres

    async def create_session(
        self,
        user_id: str,
        workspace_id: str,
        session_type: str  # "chat" or "agent"
    ) -> Session:
        """Create session in Redis with automatic persistence to PostgreSQL."""
        ...

    async def get_session(self, session_id: str) -> Session:
        """Get session from Redis (hot) or PostgreSQL (cold)."""
        ...

    async def update_session(self, session_id: str, updates: dict):
        """Update session state in Redis, async persist to PostgreSQL."""
        ...
```

#### Tool Registry (Unified)

```python
class ToolRegistry:
    """Unified tool registry for both LLM tool calls and direct agent calls."""

    async def register_tool(self, tool: ToolDefinition):
        """Register tool with both OpenAI schema and internal schema."""
        ...

    async def invoke_tool(
        self,
        tool_name: str,
        args: dict,
        context: ExecutionContext
    ) -> ToolResult:
        """Execute tool (works for both API types)."""
        ...

    def get_openai_schema(self, tool_name: str) -> dict:
        """Get OpenAI-compatible tool schema."""
        ...

    def get_agent_schema(self, tool_name: str) -> dict:
        """Get agent-optimized tool schema."""
        ...
```

---

## Implementation Recommendations

### Phase 1: Foundation (Week 1-2)

**Deliverables:**
1. ✅ API Gateway with authentication
2. ✅ Session manager (Redis + PostgreSQL)
3. ✅ Basic OpenAI /v1/chat/completions endpoint
4. ✅ Error handling framework
5. ✅ Rate limiting infrastructure

**Code Structure:**
```
src/api/
  gateway/
    auth.py           # Authentication middleware
    rate_limiter.py   # Rate limiting
  openai/
    chat.py           # /v1/chat/completions
    compat.py         # Format translation
  agents/
    (placeholder)
  services/
    session_manager.py
    tool_registry.py
  models/
    requests.py
    responses.py
```

### Phase 2: Agent API (Week 3-4)

**Deliverables:**
1. ✅ Agent execution endpoint (/v1/agents/execute)
2. ✅ Direct tool invocation
3. ✅ SSE streaming infrastructure
4. ✅ Sub-agent spawning
5. ✅ Context/working directory management

**Code Structure:**
```
src/api/
  agents/
    execute.py        # /v1/agents/execute
    tools.py          # /v1/agents/tools/*
    spawn.py          # /v1/agents/spawn
    stream.py         # SSE streaming
  services/
    agent_orchestrator.py
    working_directory.py
```

### Phase 3: Advanced Features (Week 5-6)

**Deliverables:**
1. ✅ Multi-agent orchestration patterns
2. ✅ Memory integration (short/long-term)
3. ✅ Advanced session management (checkpoints, restore)
4. ✅ RBAC enforcement
5. ✅ Quota management

### Phase 4: Production Hardening (Week 7-8)

**Deliverables:**
1. ✅ Performance optimization
2. ✅ Monitoring and observability
3. ✅ Load testing
4. ✅ Documentation
5. ✅ Security audit

### Technology Stack

**API Framework:**
- FastAPI (async, high performance, OpenAPI docs)
- Pydantic (request/response validation)
- Starlette (ASGI foundation)

**Streaming:**
- SSE via `asyncio` + `StreamingResponse`
- WebSocket support via `fastapi.WebSocket`

**Session Storage:**
- Redis (hot sessions, TTL-based expiration)
- PostgreSQL (cold sessions, audit trail)
- Valkey (Redis alternative, optional)

**Authentication:**
- JWT (jose library, RS256)
- API keys (SHA-256 hashed)
- OAuth2 (optional, via Supabase)

**Rate Limiting:**
- slowapi (decorator-based)
- Redis-backed counters

**Monitoring:**
- Prometheus metrics
- OpenTelemetry tracing
- Structured logging (structlog)

### Key Design Decisions

#### 1. SSE vs WebSocket for Streaming

**Decision: SSE (Primary), WebSocket (Optional)**

**Rationale:**
- SSE simpler to implement and debug
- Built-in reconnection and event IDs
- HTTP-based (easier firewalls/proxies)
- Sufficient for server-to-client streaming
- WebSocket as opt-in for bidirectional needs

#### 2. Session Storage Strategy

**Decision: Hybrid (Redis + PostgreSQL)**

**Rationale:**
- Redis for fast active session access
- PostgreSQL for persistence and audit trail
- Automatic promotion/demotion based on activity
- Best of both worlds (speed + durability)

#### 3. API Versioning

**Decision: URL-based + Date headers**

**Rationale:**
- URL versioning clear and explicit
- Date headers for minor versions
- Easy routing and deprecation
- Industry standard

#### 4. Authentication Model

**Decision: API keys + JWT**

**Rationale:**
- API keys for service-to-service
- JWT for user-to-service
- Both standards-based
- Flexible for different use cases

#### 5. Tool Calling Approach

**Decision: Unified registry, dual schemas**

**Rationale:**
- Single tool implementation
- OpenAI schema for /v1/chat/completions
- Agent schema for /v1/agents/execute
- Reduces code duplication

---

## References & Sources

### E1: OpenAI API Compatibility

1. [Azure OpenAI in Microsoft Foundry Models REST API reference](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/reference?view=foundry-classic)
2. [How do I Stream OpenAI's completion API? - Stack Overflow](https://stackoverflow.com/questions/73547502/how-do-i-stream-openais-completion-api)
3. [OpenAI — APIs : Stream it for faster response | by Amarjit Jha | Medium](https://jha-amarjit.medium.com/openai-apis-stream-it-for-faster-response-b4a88b50ae52)
4. [OpenAI API chat/completions endpoint — OpenVINO™ documentation](https://docs.openvino.ai/2024/openvino-workflow/model-server/ovms_docs_rest_api_chat.html)
5. [Function calling - OpenAI API](https://platform.openai.com/docs/guides/function-calling)
6. [Function Calling in the OpenAI API | OpenAI Help Center](https://help.openai.com/en/articles/8555517-function-calling-in-the-openai-api)

### E2: Agent-Optimized API Design

1. [LLM Agent Orchestration: A Step by Step Guide | IBM](https://www.ibm.com/think/tutorials/llm-agent-orchestration-with-langchain-and-granite)
2. [Orchestrating multiple agents - OpenAI Agents SDK](https://openai.github.io/openai-agents-python/multi_agent/)
3. [LLM Orchestration in 2025: Frameworks + Best Practices | Generative AI Collaboration Platform](https://orq.ai/blog/llm-orchestration)
4. [9 Best LLM Orchestration Frameworks for Agents and RAG - ZenML Blog](https://www.zenml.io/blog/best-llm-orchestration-frameworks)
5. [Design multi-agent orchestration with reasoning using Amazon Bedrock](https://aws.amazon.com/blogs/machine-learning/design-multi-agent-orchestration-with-reasoning-using-amazon-bedrock-and-open-source-frameworks/)

### E3: Session & State Management

1. [If REST applications are supposed to be stateless, how do you manage sessions? - Stack Overflow](https://stackoverflow.com/questions/3105296/if-rest-applications-are-supposed-to-be-stateless-how-do-you-manage-sessions)
2. [Stateful vs Stateless Architecture - Redis](https://redis.io/glossary/stateful-vs-stateless-architectures/)
3. [All Differences Between Stateless VS Stateful API - Apidog](https://apidog.com/blog/stateless-vs-stateful-api/)
4. [Stateful vs. Stateless Architecture - GeeksforGeeks](https://www.geeksforgeeks.org/system-design/stateful-vs-stateless-architecture/)
5. [Stateless REST API: Advantages of Statelessness in REST](https://restfulapi.net/statelessness/)

### E4: Authentication & Authorization

1. [API Key Management: Ultimate Guide 2024](https://bestaiagents.org/blog/api-key-management-ultimate-guide-2024/)
2. [Securing Rate Limit Actions with JSON Web Tokens (JWT) - Solo.io](https://www.solo.io/blog/tutorial-securing-rate-limit-actions-with-json-web-tokens-jwt/)
3. [The Ultimate Guide to API Keys - OpenReplay](https://blog.openreplay.com/ultimate-guide-to-api-keys/)
4. [The subtle art of API Rate-Limiting - Zuplo](https://zuplo.com/blog/2023/05/02/subtle-art-of-rate-limiting-an-api)
5. [API key vs JWT - which authentication to use and when - Software Engineering Stack Exchange](https://softwareengineering.stackexchange.com/questions/419533/api-key-vs-jwt-which-authentication-to-use-and-when)
6. [Top 7 API authentication methods and how to use them — WorkOS](https://workos.com/blog/api-authentication-methods)

### E5: Message Protocol Design

1. [WebSockets vs Server-Sent Events (SSE) - Ably](https://ably.com/blog/websockets-vs-sse)
2. [WebSockets vs. Server-Sent events/EventSource - Stack Overflow](https://stackoverflow.com/questions/5195452/websockets-vs-server-sent-events-eventsource)
3. [WebSockets vs Server-Sent-Events vs Long-Polling vs WebRTC vs WebTransport - RxDB](https://rxdb.info/articles/websockets-sse-polling-webrtc-webtransport.html)
4. [Server-Sent Events vs WebSockets – How to Choose - FreeCodeCamp](https://www.freecodecamp.org/news/server-sent-events-vs-websockets/)
5. [Using server-sent events - Web APIs | MDN](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)

---

## Next Steps

1. **Immediate (Day 3-4):**
   - ✅ Complete API design research (this document)
   - ⏭️ Review with team for feedback
   - ⏭️ Finalize dual-API architecture

2. **Short-term (Week 1-2):**
   - Implement Phase 1 foundation
   - Set up API gateway infrastructure
   - Build OpenAI-compatible endpoints
   - Deploy development environment

3. **Medium-term (Week 3-6):**
   - Implement agent-optimized endpoints
   - Build multi-agent orchestration
   - Integrate session and memory systems
   - Comprehensive testing

4. **Long-term (Week 7-8):**
   - Production hardening
   - Security audit
   - Performance optimization
   - Documentation and training

---

**Document Status:** ✅ Complete
**Reviewed By:** API Design Agent (Phase 4 Research)
**Approval Status:** Pending Team Review
**Implementation Ready:** Yes
