# PROPOSAL 08: MCP Registry Integration & Automation

**Status:** PROPOSED  
**Priority:** P1 (High)  
**Effort:** 2 weeks  
**Dependencies:** PROPOSAL_01, PROPOSAL_07

## Problem Statement

Manual MCP server management is tedious:
- No centralized registry
- Manual installation
- Version management
- Dependency resolution
- Update coordination

## Solution Overview

Integrate with MCP registry for automated discovery and installation:

```
┌──────────────────────────────────────┐
│    MCP Registry Integration          │
├──────────────────────────────────────┤
│  Registry Client                     │
│  ├─ Search registry                  │
│  ├─ Fetch metadata                   │
│  └─ Version resolution               │
├──────────────────────────────────────┤
│  Installation Manager                │
│  ├─ Download packages                │
│  ├─ Dependency resolution            │
│  └─ Verification                     │
├──────────────────────────────────────┤
│  Update Manager                      │
│  ├─ Check updates                    │
│  ├─ Version pinning                  │
│  └─ Rollback support                 │
└──────────────────────────────────────┘
```

## Core Components

### 1. Registry Client
```python
class RegistryClient:
    """MCP registry interaction"""
    
    async def search(self, query: str) -> List[Package]
    async def get_package(self, name: str) -> Package
    async def list_versions(self, name: str) -> List[Version]
    async def get_metadata(self, name: str, version: str) -> dict
```

### 2. Installation Manager
```python
class InstallationManager:
    """Manage MCP server installation"""
    
    async def install(self, name: str, version: str = "latest")
    async def uninstall(self, name: str)
    async def upgrade(self, name: str)
    async def list_installed(self) -> List[InstalledPackage]
    async def verify_installation(self, name: str) -> bool
```

### 3. Dependency Resolver
```python
class DependencyResolver:
    """Resolve package dependencies"""
    
    async def resolve(self, package: Package) -> List[Package]
    async def check_conflicts(self, packages: List[Package]) -> List[Conflict]
    async def suggest_versions(self, package: Package) -> List[Version]
```

## Registry Schema

```yaml
package:
  name: github-mcp
  version: 1.2.3
  description: GitHub MCP server
  
  metadata:
    author: Anthropic
    license: MIT
    repository: https://github.com/anthropic-ai/mcp-server-github
    
  requirements:
    - python >= 3.10
    - fastmcp >= 2.13
    
  dependencies:
    - requests >= 2.28
    - pydantic >= 2.0
    
  tools:
    - name: search_issues
      description: Search GitHub issues
    - name: create_issue
      description: Create GitHub issue
      
  configuration:
    required:
      - github_token
    optional:
      - github_org
```

## Installation Workflow

```
1. User: smartcp install github-mcp
2. Registry: Search registry
3. Resolver: Resolve dependencies
4. Installer: Download packages
5. Verifier: Verify checksums
6. Loader: Load into SmartCP
7. Config: Update configuration
8. Test: Run smoke tests
```

## Implementation Plan

### Phase 1: Registry Client (Week 1)
- [ ] Registry API integration
- [ ] Search functionality
- [ ] Metadata fetching
- [ ] Tests

### Phase 2: Installation (Week 1.5)
- [ ] Download manager
- [ ] Dependency resolution
- [ ] Verification
- [ ] Tests

### Phase 3: Updates & Automation (Week 2)
- [ ] Update checking
- [ ] Version pinning
- [ ] Rollback support
- [ ] Integration tests

## Benefits

✅ Automated discovery  
✅ Easy installation  
✅ Dependency management  
✅ Version control  
✅ Community packages  

## Success Criteria

- [ ] Registry integration working
- [ ] Install/uninstall functional
- [ ] Dependency resolution correct
- [ ] Update mechanism tested
- [ ] Integration tests passing

---

**Next:** PROPOSAL_09 (Tool Lifecycle)

