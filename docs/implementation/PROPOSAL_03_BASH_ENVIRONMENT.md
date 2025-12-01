# PROPOSAL 03: Bash Environment & System Integration

**Status:** PROPOSED  
**Priority:** P0 (Critical)  
**Effort:** 2 weeks  
**Dependencies:** PROPOSAL_01

## Problem Statement

Current implementation restricts agents to Python-only execution. Many tasks require:
- Shell commands (grep, sed, awk, etc.)
- System utilities (curl, jq, etc.)
- Package management (apt, brew, etc.)
- File system operations
- Process management

## Solution Overview

Provide full bash environment access with:
1. **Bash Executor** - Execute arbitrary bash commands
2. **Command Whitelisting** - Security controls
3. **Environment Variables** - Hierarchical config
4. **Process Management** - Background jobs, signals
5. **Filesystem Access** - Safe directory operations

## Architecture

```
┌──────────────────────────────────────┐
│      Bash Environment Manager        │
├──────────────────────────────────────┤
│  Command Executor                    │
│  ├─ Command validation               │
│  ├─ Whitelist/blacklist              │
│  ├─ Timeout enforcement              │
│  └─ Output capture                   │
├──────────────────────────────────────┤
│  Environment Management              │
│  ├─ Variable hierarchy               │
│  ├─ Secret masking                   │
│  ├─ Path management                  │
│  └─ Persistence                      │
├──────────────────────────────────────┤
│  Process Management                  │
│  ├─ Background jobs                  │
│  ├─ Signal handling                  │
│  ├─ Resource limits                  │
│  └─ Cleanup                          │
└──────────────────────────────────────┘
```

## Core Components

### 1. Bash Executor
```python
class BashExecutor:
    """Execute bash commands safely"""
    
    async def execute(
        self,
        command: str,
        timeout: int = 30,
        cwd: str = None,
        env: dict = None
    ) -> ExecutionResult
    
    async def execute_background(
        self,
        command: str,
        job_id: str
    ) -> Job
    
    async def kill_job(self, job_id: str)
    async def list_jobs(self) -> List[Job]
```

### 2. Command Validation
```python
class CommandValidator:
    """Validate commands against policies"""
    
    def is_allowed(self, command: str) -> bool
    def get_allowed_commands(self) -> List[str]
    def add_whitelist(self, pattern: str)
    def add_blacklist(self, pattern: str)
```

### 3. Environment Manager
```python
class EnvironmentManager:
    """Manage bash environment variables"""
    
    def set_variable(self, name: str, value: str, scope: str)
    def get_variable(self, name: str) -> str
    def list_variables(self, scope: str) -> dict
    def mask_secret(self, name: str)
    def persist_variables(self)
```

## Security Model

### Command Whitelisting
```yaml
bash:
  security:
    mode: whitelist  # whitelist | blacklist | permissive
    
    whitelist:
      - grep
      - sed
      - awk
      - curl
      - jq
      - find
      - ls
      - cat
      - head
      - tail
      - wc
      
    blacklist:
      - rm -rf /
      - sudo
      - su
      - passwd
```

### Environment Scopes
```
Global (system-wide)
  ↓
User (per-user)
  ↓
Session (per-execution)
  ↓
Local (per-command)
```

## Implementation Plan

### Phase 1: Basic Executor (Week 1)
- [ ] Bash executor implementation
- [ ] Command validation
- [ ] Output capture
- [ ] Timeout handling
- [ ] Unit tests

### Phase 2: Environment & Jobs (Week 1.5)
- [ ] Environment manager
- [ ] Variable hierarchy
- [ ] Background job support
- [ ] Signal handling
- [ ] Integration tests

### Phase 3: Security & Hardening (Week 2)
- [ ] Whitelist/blacklist
- [ ] Secret masking
- [ ] Resource limits
- [ ] Audit logging
- [ ] Security tests

## Benefits

✅ Full system access  
✅ Unix tool integration  
✅ Complex workflows  
✅ Better performance  
✅ Familiar paradigm  

## Success Criteria

- [ ] Execute 100+ bash commands
- [ ] Background jobs working
- [ ] Environment persistence
- [ ] Security policies enforced
- [ ] Performance benchmarks met

---

**Next:** PROPOSAL_04 (Multi-Language Executors)

