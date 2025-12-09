# Proposal 3: Full Bash Environment & Concurrency Support

**ID:** PROPOSAL-003  
**Title:** Provide Full Bash Environment with Hierarchical Memory/Persistence  
**Status:** DRAFT  
**Priority:** P1  
**Effort:** 45 story points  
**Timeline:** 3-4 weeks

## Problem Statement

Current implementation limits agent to Python code execution. This prevents:
- Shell command execution (grep, sed, awk, etc.)
- System utilities (curl, jq, etc.)
- Complex bash paradigms (pipes, redirects, loops)
- Parallel execution patterns
- Persistent state across executions

## Solution Overview

Provide agents with:
1. **Full Bash Access** - Execute arbitrary shell commands
2. **Hierarchical Memory** - Variables, state persistence across contexts
3. **Concurrency Support** - Sync, async, parallel execution
4. **Filesystem Interaction** - Read/write with safety guardrails
5. **Process Management** - Background jobs, process control

## Architecture

### Execution Context
```python
class ExecutionContext:
    id: str  # Unique context ID
    parent_id: Optional[str]  # Parent context for hierarchy
    variables: Dict[str, Any]  # Persistent variables
    working_dir: Path
    environment: Dict[str, str]
    
class ContextManager:
    def create_context(parent: Optional[ExecutionContext]) -> ExecutionContext
    def get_context(context_id: str) -> ExecutionContext
    def set_variable(context_id: str, key: str, value: Any)
    def get_variable(context_id: str, key: str) -> Any
```

### Bash Executor
```python
class BashExecutor:
    async def execute(
        command: str,
        context: ExecutionContext,
        timeout: int = 30,
        parallel: bool = False
    ) -> ExecutionResult
    
    async def execute_parallel(
        commands: List[str],
        context: ExecutionContext
    ) -> List[ExecutionResult]
```

### Memory Hierarchy
```
Global Context
├── Session Context (user session)
│   ├── Task Context (specific task)
│   │   ├── Step Context (execution step)
│   │   └── Step Context
│   └── Task Context
└── Session Context
```

## Features

### 1. Bash Commands
- Full shell syntax support
- Pipes, redirects, background jobs
- Command substitution
- Variable expansion

### 2. Persistent Variables
```bash
# Set variable in context
set_var("API_KEY", "secret123")

# Access in subsequent commands
curl -H "Authorization: Bearer $API_KEY" https://api.example.com
```

### 3. Concurrency Patterns
```python
# Sequential
result1 = await bash("command1")
result2 = await bash("command2")

# Parallel
results = await bash_parallel([
    "command1",
    "command2",
    "command3"
])

# Async
task = bash_async("long_running_command")
# ... do other work ...
result = await task.wait()
```

### 4. Filesystem Safety
- Sandboxed working directory
- Read-only system paths
- Temporary file cleanup
- Quota enforcement

### 5. Process Management
```python
class ProcessManager:
    async def start_background(command: str) -> ProcessHandle
    async def list_processes() -> List[ProcessInfo]
    async def kill_process(pid: int)
    async def get_output(handle: ProcessHandle) -> str
```

## Implementation Phases

### Phase 1: Bash Executor (Week 1-2)
- [ ] Implement bash execution engine
- [ ] Add command validation
- [ ] Implement timeout handling
- [ ] Add output capture

### Phase 2: Context Management (Week 2)
- [ ] Implement context hierarchy
- [ ] Add variable persistence
- [ ] Implement context switching
- [ ] Add context cleanup

### Phase 3: Concurrency (Week 3)
- [ ] Implement parallel execution
- [ ] Add async support
- [ ] Implement process management
- [ ] Add job control

### Phase 4: Safety & Testing (Week 4)
- [ ] Sandbox implementation
- [ ] Security hardening
- [ ] Comprehensive testing
- [ ] Documentation

## Security Considerations

- Rootless container execution
- Capability dropping
- Read-only root filesystem
- Network isolation
- Resource limits (CPU, memory, PIDs)
- Audit logging

## Testing Strategy

- Unit tests for executor
- Integration tests for context management
- E2E tests for concurrency patterns
- Security tests for sandbox escape
- Performance tests for parallel execution

## Success Criteria

- [ ] Full bash support functional
- [ ] Context hierarchy working
- [ ] Parallel execution tested
- [ ] Filesystem safety verified
- [ ] <50ms context switch overhead
- [ ] Zero sandbox escapes in security audit

## Related Proposals

- Proposal 4: Multi-Language Executors (extends this)
- Proposal 6: Tool Management (uses bash for tool control)

