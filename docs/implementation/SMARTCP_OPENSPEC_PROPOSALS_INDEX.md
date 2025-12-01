# SmartCP OpenSpec Proposals Index

**Project:** SmartCP - Advanced MCP Framework  
**Date:** 2025-11-21  
**Status:** PROPOSAL PHASE  
**Base Reference:** python-proto-ref (Code Execution Mode)

## Overview

SmartCP is an advanced MCP framework built on FastMCP 2.13 that extends the python-proto-ref implementation with:
- Multi-transport support (stdio, SSE, HTTP)
- Advanced authentication (OAuth, Bearer, Env, Custom)
- Full bash environment access
- Hierarchical memory & persistence
- Multi-language executors (Python, Go, TypeScript)
- Advanced tool discovery (RAG, semantic, FTS, BM25)
- MCP registry integration
- Live tool management & lifecycle

## Proposals

### Core Infrastructure
- **PROPOSAL_01**: FastMCP 2.13 Upgrade & Composition Patterns
- **PROPOSAL_02**: Multi-Transport & Authentication Layer
- **PROPOSAL_03**: Bash Environment & System Integration

### Execution & Concurrency
- **PROPOSAL_04**: Multi-Language Executors (Python, Go, TS)
- **PROPOSAL_05**: Hierarchical Memory & Persistence
- **PROPOSAL_06**: Async/Sync/Parallel Execution Model

### Tool Discovery & Management
- **PROPOSAL_07**: Advanced Tool Discovery (RAG + Semantic + FTS)
- **PROPOSAL_08**: MCP Registry Integration & Automation
- **PROPOSAL_09**: Tool Lifecycle Management (Create, Extend, Reload)

### Advanced Features
- **PROPOSAL_10**: Filesystem Integration & Concurrency
- **PROPOSAL_11**: Live Tool Management & Server Control
- **PROPOSAL_12**: Agent Automation & Elicitation

## Implementation Phases

**Phase 1:** Core infrastructure (Proposals 01-03)  
**Phase 2:** Execution layer (Proposals 04-06)  
**Phase 3:** Discovery & management (Proposals 07-09)  
**Phase 4:** Advanced features (Proposals 10-12)

## Key Improvements Over python-proto-ref

| Feature | python-proto-ref | SmartCP |
|---------|------------------|---------|
| Transport | stdio only | stdio, SSE, HTTP |
| Auth | None | OAuth, Bearer, Env, Custom |
| Bash | No | Full environment |
| Memory | Ephemeral | Hierarchical persistent |
| Languages | Python only | Python, Go, TypeScript |
| Discovery | Basic | RAG + Semantic + FTS |
| Registry | Manual | Automated integration |
| Tool Mgmt | Static | Dynamic lifecycle |

---

See individual proposal files for detailed specifications.

