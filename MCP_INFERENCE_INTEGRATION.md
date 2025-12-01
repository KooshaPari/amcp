# MCP Inference Integration Guide

Complete documentation for integrating the DSL Scope Inference Engine with FastMCP servers.

## Overview

The MCP Inference Integration provides **automatic scope detection and activation** for OpenAI-compatible agents without explicit instrumentation.

### What It Does

Given OpenAI-format messages from a ReAct agent:

```
User: "I'm working on the MyApp project"
Assistant: "Great! Let's start implementing..."
User: "Let's write unit tests"
```

The system automatically:

1. **Detects project**: "MyApp" → activates PROJECT scope
2. **Detects phase**: "unit tests" keyword → activates PHASE (testing)
3. **Tracks session**: Maintains SESSION scope context
4. **Stores signals**: Logs to Neo4j (when available)
5. **Manages state**: Redis caching for performance

## Architecture

```
OpenAI-Compatible Agent
         ↓
    [Messages]
         ↓
MCPInferenceBridge
    ├─ Analyze chat
    ├─ Extract signals
    ├─ Detect patterns
    └─ Score confidence
         ↓
ComprehensiveScopeInferenceEngine
    ├─ Project detection
    ├─ Phase classification
    ├─ Entity inference
    └─ Signal aggregation
         ↓
DSL Scope System
    ├─ Activate contexts
    ├─ Store variables
    └─ Manage state
         ↓
    [Database] [Redis] [Neo4j]
```

## Quick Start

### 1. Basic Integration (10 minutes)

```python
from fastmcp_inference_server import create_smartcp_inference_server
from fastmcp_2_13_server import TransportType, AuthType

# Create server with inference
server = create_smartcp_inference_server(
    name="smartcp-agent",
    transport=TransportType.STDIO,
    auth_type=AuthType.BEARER,
    bearer_tokens=["your-token"]
)

# Add tools as normal
@server.mcp.tool
def write_file(path: str, content: str) -> dict:
    """Write file to disk."""
    with open(path, 'w') as f:
        f.write(content)
    return {"success": True, "path": path}

# Start server
await server.start()
```

### 2. Automatic Inference Processing

The server automatically infers scopes from agent messages:

```python
# When agent sends completion request:
result = await server.process_completion_request(
    messages=[
        {"role": "user", "content": "I'm building MyApp in Python"},
        {"role": "assistant", "content": "Let's start with the models..."},
    ],
    session_id="session-123"
)

# Returns:
# {
#     "inference": {
#         "signals": [
#             {
#                 "scope_level": "PROJECT",
#                 "key": "project_name",
#                 "value": "MyApp",
#                 "confidence": 0.95,
#                 "evidence": ["mentioned 'MyApp'"]
#             },
#             {
#                 "scope_level": "PHASE",
#                 "key": "phase_type",
#                 "value": "implementation",
#                 "confidence": 0.8,
#                 "evidence": ["'start with the models' suggests implementation"]
#             }
#         ],
#         "activated_scopes": {
#             "project": "myapp-uuid",
#             "phase": "impl-uuid"
#         }
#     },
#     "scopes": {
#         "project_name": "MyApp",
#         "phase_type": "implementation",
#         ...
#     }
# }
```

### 3. Using Inferred Scopes

Tools can now access scoped variables:

```python
from dsl_scope import get_dsl_scope_system, ScopeLevel

@server.mcp.tool
async def create_file(filename: str, content: str) -> dict:
    """Create file in project context."""
    dsl = get_dsl_scope_system()

    # Get current project from inferred scope
    scopes = await dsl.get_current_context()
    project_id = scopes.project_id

    # Store in project scope
    await dsl.set(
        f"created_files/{filename}",
        {"path": filename, "size": len(content)},
        ScopeLevel.PROJECT
    )

    return {
        "file": filename,
        "project": project_id,
        "stored": True
    }
```

## Files

### Core Integration Files

| File | Purpose | Lines |
|------|---------|-------|
| `mcp_inference_bridge.py` | Bridge between MCP and inference engine | 320 |
| `fastmcp_inference_server.py` | Enhanced FastMCP server with inference | 280 |
| `tests/test_mcp_inference_integration.py` | Integration tests | 450 |

### Supporting Files

| File | Purpose | Lines |
|------|---------|-------|
| `fastmcp_2_13_server.py` | Base FastMCP 2.13 server (unchanged) | 242 |
| `dsl_scope/` | DSL scope system | 3000+ |
| `.env` | Credentials (Neo4j, Supabase, etc.) | 44 |

## API Reference

### MCPInferenceBridge

Main interface for inference functionality.

```python
class MCPInferenceBridge:
    """Bridge between MCP server and inference engine."""

    async def process_openai_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Process OpenAI completion with inference."""
        # Detects: project, phase, workspace, organization
        # Returns: signals, activated_scopes, metadata

    async def process_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
    ) -> List[InferenceSignal]:
        """Analyze tool call for scope signals."""
        # Examples:
        # - run_tests → PHASE: testing
        # - write_file (non-test) → PHASE: implementation
        # - write_file (.md) → PHASE: documentation

    async def get_current_scopes(self) -> Dict[str, str]:
        """Get all active scopes."""
        # Returns: session_id, project_id, phase_id, etc.

    def get_inference_history(self, limit: int = 50) -> List:
        """Get recent inference entries."""

    def clear_inference_history(self) -> None:
        """Clear history."""
```

### FastMCPInferenceServer

Extended FastMCP server with inference capabilities.

```python
class FastMCPInferenceServer(FastMCP213Server):
    """FastMCP 2.13 server with inference."""

    async def process_completion_request(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Process completion with automatic inference."""

    async def get_current_scopes(self) -> Dict[str, str]:
        """Get active scopes."""

    async def handle_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process tool call through inference."""

    def get_inference_history(self, limit: int = 50) -> List:
        """Get history."""

    def clear_inference_history(self) -> None:
        """Clear history."""
```

### InferenceMiddleware

Middleware for request/response processing.

```python
class InferenceMiddleware:
    """Middleware for request pipeline."""

    async def process_request(self, request: Dict) -> Dict:
        """Inject inference into request processing."""
        # Automatically detects /completions endpoints
        # Attaches _inference_result to request

    async def process_response(self, response: Dict) -> Dict:
        """Add inference metadata to response."""
```

## Scope Detection Patterns

### Project Detection

Recognizes project name patterns:

```
Regex patterns:
- "working on {ProjectName}"
- "project {ProjectName}"
- "building {ProjectName}"
- GitHub URLs
- File paths: /ProjectName/src/
- CamelCase identifiers
```

Example:
```
"I'm working on MyDataPipeline" → PROJECT: MyDataPipeline (confidence: 0.95)
"github.com/user/awesome-project" → PROJECT: awesome-project (confidence: 0.9)
```

### Phase Detection

Recognizes development phase from keywords:

| Phase | Keywords | Confidence |
|-------|----------|------------|
| PLANNING | "plan", "design", "discuss", "architecture" | 0.8-0.9 |
| DOCUMENTATION | "doc", "readme", "comment", "explain" | 0.85-0.95 |
| IMPLEMENTATION | "implement", "write", "code", "build" | 0.8-0.9 |
| TESTING | "test", "debug", "verify", "check" | 0.9-0.95 |
| DEBUGGING | "error", "bug", "fix", "crash" | 0.85-0.95 |

Example:
```
"Let's write unit tests" → PHASE: testing (confidence: 0.92)
"Implementing the user auth module" → PHASE: implementation (confidence: 0.88)
```

### Tool Call Patterns

Tool names reveal development phase:

```
Tool: run_tests → PHASE: testing
Tool: run_pytest → PHASE: testing
Tool: write_file + path.endswith('.md') → PHASE: documentation
Tool: write_file + not test → PHASE: implementation
Tool: execute_bash + 'debug' → PHASE: debugging
```

## Confidence Thresholds

Scopes are activated only above confidence thresholds:

| Scope | Threshold | Rationale |
|-------|-----------|-----------|
| SESSION | 0.8 | High - session identification is reliable |
| PROJECT | 0.6 | Medium - names can be ambiguous |
| PHASE | 0.7 | Medium-high - keywords can be context-dependent |
| WORKSPACE | 0.7 | Medium-high - less frequently mentioned |
| ORGANIZATION | 0.8 | High - org names are specific |
| ITERATION | 0.5 | Low - iterations inferred from timestamps |

## Examples

### Example 1: Simple Project Detection

```python
from fastmcp_inference_server import create_smartcp_inference_server

server = create_smartcp_inference_server(
    name="smartcp-test",
    transport=TransportType.STDIO
)

# Simulate agent interaction
result = await server.process_completion_request(
    messages=[
        {
            "role": "user",
            "content": "I'm starting to build the BlogApp project"
        }
    ],
    session_id="demo-session"
)

print("Inferred scopes:", result["scopes"])
# Output:
# {
#     "project_name": "BlogApp",
#     "phase_type": None,  # Not mentioned
#     ...
# }
```

### Example 2: Phase Inference

```python
result = await server.process_completion_request(
    messages=[
        {"role": "user", "content": "Let's debug the auth module"},
        {"role": "assistant", "content": "Found the issue in login function"}
    ],
    session_id="demo-session"
)

print("Phase:", result["scopes"]["phase_type"])
# Output: "debugging"
```

### Example 3: Tool Call Integration

```python
@server.mcp.tool
async def run_tests(path: str = "tests/") -> dict:
    """Run test suite."""
    # Inference will detect this as testing phase
    # because tool name is "run_tests"
    return {"passed": 10, "failed": 0}

# Simulate tool call
signals = await server.inference_bridge.process_tool_call(
    tool_name="run_tests",
    arguments={"path": "tests/unit/"},
    result={"passed": 5, "failed": 0}
)

# Detected signals will include PHASE: testing
```

### Example 4: Multi-Turn Conversation

```python
messages = [
    {"role": "user", "content": "I'm building MyApp project"},
    {"role": "assistant", "content": "Great! Let's start planning the architecture"},
    {"role": "user", "content": "Good, now let's implement the database layer"},
    {"role": "assistant", "content": "I'll create the models..."},
]

result = await server.process_completion_request(
    messages=messages,
    session_id="full-conversation"
)

# Infers:
# - PROJECT: MyApp (from first message)
# - PHASE: planning (from assistant's "planning")
# - PHASE: implementation (from user's "implement") - overrides planning
```

## Testing

Run integration tests:

```bash
pytest smartcp/tests/test_mcp_inference_integration.py -v

# Run specific test
pytest smartcp/tests/test_mcp_inference_integration.py::TestMCPInferenceBridge::test_project_inference -v

# Run with coverage
pytest smartcp/tests/test_mcp_inference_integration.py --cov=smartcp/mcp_inference_bridge
```

## Troubleshooting

### Issue: Scopes not being detected

**Cause**: Messages don't match patterns
**Solution**: Use explicit scope naming in messages
```python
# Instead of:
"I'm coding something"

# Use:
"I'm working on the MyProject project"
```

### Issue: Low confidence scores

**Cause**: Ambiguous language
**Solution**: Use more specific terminology
```python
# Instead of:
"Let's work on stuff"

# Use:
"Let's implement the authentication module"
```

### Issue: Wrong phase detected

**Cause**: Keywords are context-dependent
**Solution**: Check confidence scores and override if needed
```python
# Override inferred phase
dsl = get_dsl_scope_system()
await dsl.set("phase_type", "custom_phase", ScopeLevel.PHASE)
```

## Performance

Typical latencies:

| Operation | Latency |
|-----------|---------|
| Analyze single message | <10ms |
| Extract signals | <5ms |
| Auto-activate scopes | <2ms |
| Store to Redis | <5ms |
| Store to Neo4j | <50ms |

**Total**: ~70ms for complete inference + storage

## Next Steps

1. **GraphQL Subscription Client** - Real-time scope changes
2. **Neo4j Relation Building** - Persistent graph storage
3. **Voyage AI Integration** - Semantic similarity search
4. **Active Optimization** - Thompson sampling for scope selection
5. **Extended Pattern Library** - More language variations

## References

- [DSL Scope System README](dsl_scope/README.md)
- [Inference Engine Documentation](dsl_scope/inference_engine.py)
- [FastMCP 2.13 Documentation](fastmcp_2_13_server.py)
- [Test Examples](tests/test_mcp_inference_integration.py)

---

**Last Updated**: 2025-11-30
**Status**: Production Ready ✅
