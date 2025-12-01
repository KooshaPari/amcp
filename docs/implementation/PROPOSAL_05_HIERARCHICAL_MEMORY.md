# PROPOSAL 05: Hierarchical Memory & Persistence

**Status:** PROPOSED  
**Priority:** P1 (High)  
**Effort:** 2 weeks  
**Dependencies:** PROPOSAL_01

## Problem Statement

Current implementation has ephemeral state. Production needs:
- Persistent variables across executions
- Hierarchical scoping (global, session, local)
- Sync/async/parallel execution coordination
- State recovery on failure
- Audit trail

## Solution Overview

Implement hierarchical memory system:

```
┌──────────────────────────────────────┐
│    Hierarchical Memory System        │
├──────────────────────────────────────┤
│  Global Scope (persistent)           │
│  ├─ System variables                 │
│  ├─ Configuration                    │
│  └─ Shared state                     │
├──────────────────────────────────────┤
│  Session Scope (per-session)         │
│  ├─ User context                     │
│  ├─ Temporary data                   │
│  └─ Execution history                │
├──────────────────────────────────────┤
│  Local Scope (per-execution)         │
│  ├─ Function variables               │
│  ├─ Temporary results                │
│  └─ Execution context                │
└──────────────────────────────────────┘
```

## Core Components

### 1. Memory Manager
```python
class MemoryManager:
    """Hierarchical memory management"""
    
    def set(self, key: str, value: Any, scope: str)
    def get(self, key: str, scope: str = None) -> Any
    def delete(self, key: str, scope: str)
    def list_keys(self, scope: str) -> List[str]
    def clear_scope(self, scope: str)
```

### 2. Persistence Layer
```python
class PersistenceLayer:
    """Persist memory to storage"""
    
    async def save(self, scope: str, data: dict)
    async def load(self, scope: str) -> dict
    async def backup(self, scope: str)
    async def restore(self, scope: str, backup_id: str)
```

### 3. Sync Coordinator
```python
class SyncCoordinator:
    """Coordinate sync/async/parallel execution"""
    
    async def acquire_lock(self, key: str) -> Lock
    async def wait_for(self, key: str, timeout: int)
    async def notify(self, key: str)
    async def barrier(self, count: int)
```

## Storage Backends

### 1. File System (Default)
```
~/.smartcp/
├─ global/
│  ├─ variables.json
│  ├─ config.yaml
│  └─ state.db
├─ sessions/
│  ├─ session_1/
│  │  ├─ variables.json
│  │  └─ history.log
│  └─ session_2/
└─ backups/
```

### 2. Redis (Optional)
- Fast access
- Distributed coordination
- Pub/sub support

### 3. PostgreSQL (Optional)
- Structured queries
- ACID guarantees
- Audit trail

## Implementation Plan

### Phase 1: Memory Manager (Week 1)
- [ ] Scope hierarchy
- [ ] Variable storage
- [ ] Lookup logic
- [ ] Tests

### Phase 2: Persistence (Week 1.5)
- [ ] File backend
- [ ] Backup/restore
- [ ] Migration support
- [ ] Tests

### Phase 3: Coordination (Week 2)
- [ ] Lock management
- [ ] Barrier support
- [ ] Pub/sub
- [ ] Integration tests

## Benefits

✅ State persistence  
✅ Concurrent execution  
✅ Failure recovery  
✅ Audit trail  
✅ Distributed support  

## Success Criteria

- [ ] All scopes working
- [ ] Persistence functional
- [ ] Concurrent access safe
- [ ] Backup/restore tested
- [ ] Performance acceptable

---

**Next:** PROPOSAL_06 (Async/Sync/Parallel)

