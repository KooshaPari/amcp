# Versioning and Compatibility Strategy

**Document Status**: Research & Strategy  
**Created**: 2025-12-02  
**Session**: Agent Layer Research  
**Purpose**: Define versioning strategy, compatibility guarantees, and migration patterns for agent SDK evolution

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Versioning Strategy](#versioning-strategy)
3. [Backward Compatibility Policy](#backward-compatibility-policy)
4. [API Evolution Patterns](#api-evolution-patterns)
5. [Interoperability Standards](#interoperability-standards)
6. [Migration Framework](#migration-framework)
7. [Deprecation Policy](#deprecation-policy)
8. [Standards Compliance](#standards-compliance)
9. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

### Key Decisions

**Versioning Approach**: Hybrid Semantic + Calendar Versioning
- **Core SDK**: Semantic Versioning (X.Y.Z) for API stability
- **Platform Release**: Calendar Versioning (YYYY.MM.PATCH) for deployment tracking
- **Rationale**: Balance API contract guarantees (SemVer) with predictable release cadence (CalVer)

**Compatibility Guarantee**: 12-Month Minimum Support Window
- Major versions: 12 months minimum support after successor release
- Minor versions: Supported until next major version
- Security patches: Backported for all supported major versions
- **Rationale**: Industry standard provides adequate migration time while limiting maintenance burden

**Breaking Change Policy**: Forward-Only with Migration Tools
- NO backward compatibility shims in production code
- Automated migration tools provided for each major version
- Comprehensive migration guides with code examples
- Optional feature flags for gradual rollout (removed after migration period)
- **Rationale**: Clean codebase architecture, reduced technical debt, automated migration support

**Standards Compliance**: MCP + OpenAI Compatibility Layer
- Native MCP protocol support
- OpenAI-compatible API layer (conversion boundary)
- Support for emerging standards (A2A, agents.json)
- **Rationale**: Maximize interoperability while maintaining native protocol advantages

---

## Versioning Strategy

### 1. Hybrid Versioning Model

#### Core SDK Versioning (Semantic)

```yaml
Format: MAJOR.MINOR.PATCH

MAJOR:
  - Breaking API changes
  - Removed deprecated features
  - Incompatible behavior changes
  - Example: 1.0.0 → 2.0.0

MINOR:
  - New backward-compatible features
  - New tools, capabilities, endpoints
  - Enhanced functionality
  - Performance improvements
  - Example: 1.0.0 → 1.1.0

PATCH:
  - Bug fixes
  - Security patches
  - Documentation updates
  - Performance optimizations (no API change)
  - Example: 1.1.0 → 1.1.1

Pre-release:
  - Alpha: 1.0.0-alpha.1 (internal testing)
  - Beta: 1.0.0-beta.1 (public preview)
  - RC: 1.0.0-rc.1 (release candidate)
```

#### Platform Release Versioning (Calendar)

```yaml
Format: YYYY.MM.PATCH

YYYY: Year of release (2025)
MM: Month of release (01-12)
PATCH: Incremental patch in that month

Examples:
  - 2025.01.0: January 2025 initial release
  - 2025.01.1: January 2025 patch 1
  - 2025.02.0: February 2025 release

Use Cases:
  - Cloud platform deployments
  - Enterprise SaaS releases
  - Marketing-aligned releases
  - LTS (Long Term Support) releases
```

#### Version Coordination

```python
# pyproject.toml
[project]
name = "pheno-agents"
version = "2.0.0"  # SDK version (SemVer)

[project.metadata]
platform_version = "2025.01.0"  # Platform release (CalVer)
sdk_version = "2.0.0"  # SDK contract version

# Runtime version detection
from pheno_agents import __version__, __platform_version__

print(f"SDK: {__version__}")  # "2.0.0"
print(f"Platform: {__platform_version__}")  # "2025.01.0"
```

**Benefits**:
- SemVer: Clear API contract guarantees for library consumers
- CalVer: Marketing alignment, predictable release cadence
- Combined: Best of both worlds - stability + transparency

**Sources**:
- [Semantic Versioning 2.0.0](https://semver.org/)
- [SemVer vs. CalVer: Choosing the Best Versioning Strategy](https://sensiolabs.com/blog/2025/semantic-vs-calendar-versioning)
- [From 1.0.0 to 2025.4: Making sense of software versioning](https://workos.com/blog/software-versioning-guide)

---

### 2. Version Lifecycle

```
┌─────────────┬──────────────┬───────────────┬─────────────┐
│   Alpha     │    Beta      │  Release      │  Sunset     │
│  (Internal) │  (Public)    │  (Stable)     │  (EOL)      │
└─────────────┴──────────────┴───────────────┴─────────────┘
     │              │               │              │
     v              v               v              v
  Unstable      Preview         Supported      Deprecated
  (No SLA)   (Best effort)    (Full support)  (Security only)
     
Timeline:
- Alpha: 1-2 months (internal testing)
- Beta: 1-2 months (public preview, no SLA)
- Stable: 12+ months (full support)
- Deprecated: 6-12 months (security patches only)
- EOL: No support

Support Windows:
┌─────────────────────────────────────────────────────────┐
│ v1.0.0 ──────────────────────────── EOL                │
│        └─ v1.1.0 ────────────── EOL                     │
│                                                          │
│             v2.0.0 ──────────────────────────── Active  │
│                    └─ v2.1.0 ────────────── Active      │
│                                                          │
│                          v3.0.0 ────────── Active       │
│                                 └─ v3.1.0 ─ Active      │
└─────────────────────────────────────────────────────────┘
  Y1          Y2          Y3          Y4          Y5
  
Legend:
━━━ = Full support (features + bugfixes + security)
─── = Security support only
EOL = End of life (no support)
```

**Support Policy**:
- **Full Support**: Latest major + minor versions
- **Security Support**: Previous major version for 12 months
- **Best Effort**: Beta releases (public feedback, no SLA)
- **No Support**: Alpha releases, EOL versions

---

## Backward Compatibility Policy

### 1. Breaking vs Non-Breaking Changes

#### Non-Breaking Changes (MINOR/PATCH)

```python
# ✅ ALLOWED: Add optional parameters with defaults
async def create_entity(
    name: str,
    description: str,
    entity_type: str = "generic",  # New optional param
    metadata: dict = None  # New optional param
) -> Entity:
    ...

# ✅ ALLOWED: Add new fields to responses
class EntityResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: datetime
    # New fields with defaults
    entity_type: str = "generic"
    metadata: dict = Field(default_factory=dict)

# ✅ ALLOWED: Add new methods to classes
class AgentSDK:
    def create_agent(self, config: AgentConfig) -> Agent:
        ...
    
    # New method
    def create_agent_async(self, config: AgentConfig) -> Awaitable[Agent]:
        ...

# ✅ ALLOWED: Add new error codes (clients should handle unknown codes)
class ErrorCodes:
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    # New error code
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"

# ✅ ALLOWED: Extend enums (if clients handle unknown values)
class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    # New status
    PAUSED = "paused"
```

#### Breaking Changes (MAJOR)

```python
# ❌ BREAKING: Remove parameters
async def create_entity(
    name: str,
    # description: str  # REMOVED - breaks existing callers
) -> Entity:
    ...

# ❌ BREAKING: Change parameter types
async def create_entity(
    name: str,
    description: dict  # Changed from str to dict
) -> Entity:
    ...

# ❌ BREAKING: Remove response fields
class EntityResponse(BaseModel):
    id: str
    name: str
    # description: str  # REMOVED - breaks clients expecting this field

# ❌ BREAKING: Change response types
async def get_entity(id: str) -> list[Entity]:  # Changed from Entity to list[Entity]
    ...

# ❌ BREAKING: Rename methods/classes
class AgentSDK:
    # create_agent renamed to make_agent - breaks existing code
    def make_agent(self, config: AgentConfig) -> Agent:
        ...

# ❌ BREAKING: Change behavior without API change
async def create_entity(name: str) -> Entity:
    # Old: Creates immediately
    # New: Queues for background creation
    # Breaks clients expecting synchronous creation
    ...
```

#### Deprecation Without Breaking

```python
# ✅ RECOMMENDED: Deprecate with compatibility shim
from warnings import warn

def create_agent(self, config: AgentConfig) -> Agent:
    warn(
        "create_agent is deprecated, use create_agent_async instead. "
        "Will be removed in v3.0.0",
        DeprecationWarning,
        stacklevel=2
    )
    # Compatibility shim - maintains old behavior
    return asyncio.run(self.create_agent_async(config))

async def create_agent_async(self, config: AgentConfig) -> Agent:
    # New implementation
    ...
```

**Sources**:
- [API Backwards Compatibility Best Practices](https://zuplo.com/learning-center/api-versioning-backward-compatibility-best-practices)
- [Best practices for API backwards compatibility - Stack Overflow](https://stackoverflow.com/questions/10716035/best-practices-for-api-backwards-compatibility)

---

### 2. Compatibility Guarantees

```yaml
Guaranteed Compatibility:
  - Public API surface (documented, typed)
  - Response formats (field additions only)
  - Error codes (additions, not removals)
  - Configuration schema (optional field additions)
  
NOT Guaranteed:
  - Internal/private APIs (prefixed with _)
  - Undocumented behavior
  - Performance characteristics
  - Resource consumption patterns
  - Exact error messages (codes are stable, text may change)

Example:
  Public API:
    ✅ pheno_agents.create_agent()
    ✅ pheno_agents.AgentConfig
    ✅ pheno_agents.Agent.run()
  
  Private API (no compatibility guarantee):
    ❌ pheno_agents._internal.registry
    ❌ pheno_agents.utils._helper_func
    ❌ pheno_agents.core._BaseAgent (internal base class)
```

---

## API Evolution Patterns

### 1. Feature Flags for Gradual Rollout

```python
# Use feature flags during migration period ONLY
# Remove after migration window closes

from pheno_agents import AgentSDK, FeatureFlags

sdk = AgentSDK(
    features=FeatureFlags(
        use_async_api=True,  # Enable new async patterns
        strict_validation=False,  # Gradual opt-in to strict mode
        legacy_compat=True  # Temporary compat mode
    )
)

# After migration period (12 months), remove flags:
# - use_async_api becomes default
# - strict_validation becomes default
# - legacy_compat removed entirely

# Implementation
class FeatureFlags(BaseModel):
    use_async_api: bool = True  # Default to new behavior
    strict_validation: bool = False  # Opt-in during migration
    legacy_compat: bool = False  # Disabled by default
    
    def __post_init__(self):
        if self.legacy_compat:
            warn(
                "legacy_compat will be removed in v3.0.0",
                DeprecationWarning
            )
```

**Migration Timeline**:
```
v2.0.0: Feature flag introduced (default=False)
v2.1.0: Feature flag default changes (default=True)
v2.5.0: Feature flag deprecated (warns if explicitly set)
v3.0.0: Feature flag removed (new behavior is only behavior)
```

**Sources**:
- [Feature flags for Python](https://launchdarkly.com/feature-flags-python/)
- [Database Migrations with Feature Flags](https://www.harness.io/blog/database-migration-with-feature-flags)

---

### 2. Expand-Contract Migration Pattern

```python
# Phase 1: EXPAND - Support both old and new
class EntityConfig(BaseModel):
    # Old field (deprecated)
    type: Optional[str] = Field(None, deprecated=True)
    
    # New field
    entity_type: str = "generic"
    
    @validator("entity_type", pre=True, always=True)
    def migrate_type_field(cls, v, values):
        # Automatic migration from old to new
        if v is None and "type" in values:
            return values["type"]
        return v

# Phase 2: DEPRECATE - Warn users
def create_entity(config: EntityConfig) -> Entity:
    if config.type is not None:
        warn(
            "EntityConfig.type is deprecated, use entity_type instead. "
            "Support for 'type' will be removed in v3.0.0",
            DeprecationWarning
        )

# Phase 3: CONTRACT - Remove old field (breaking change, new major version)
class EntityConfig(BaseModel):
    entity_type: str = "generic"
    # 'type' field removed
```

**Timeline**:
```
v2.0.0: Add entity_type (expand)
v2.1.0: Deprecate type field (contract warning)
v2.x.x: Both fields supported (migration period)
v3.0.0: Remove type field (contract)
```

---

### 3. Versioned Endpoints (API Gateway Pattern)

```python
# Support multiple API versions simultaneously via routing

# v1 endpoint (deprecated)
@router.post("/v1/agents")
async def create_agent_v1(config: AgentConfigV1) -> AgentResponseV1:
    warn("API v1 is deprecated, use /v2/agents", DeprecationWarning)
    # Convert v1 request to v2 internally
    v2_config = convert_v1_to_v2(config)
    v2_response = await create_agent_v2(v2_config)
    # Convert v2 response to v1 format
    return convert_v2_to_v1(v2_response)

# v2 endpoint (current)
@router.post("/v2/agents")
async def create_agent_v2(config: AgentConfigV2) -> AgentResponseV2:
    # New implementation
    ...

# Deprecation headers
@router.post("/v1/agents")
async def create_agent_v1(response: Response, ...):
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Wed, 01 Jan 2026 00:00:00 GMT"
    response.headers["Link"] = "</docs/migration/v1-to-v2>; rel=\"deprecation\""
    ...
```

**Deprecation Response Headers**:
```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Wed, 01 Jan 2026 00:00:00 GMT
Link: </docs/migration/v1-to-v2>; rel="deprecation"
Content-Type: application/json
```

**Sources**:
- [API Versioning Best Practices 2024](https://liblab.com/blog/api-versioning-best-practices)
- [Atlassian REST API policy](https://developer.atlassian.com/platform/marketplace/atlassian-rest-api-policy/)

---

## Interoperability Standards

### 1. Model Context Protocol (MCP) Native Support

```python
# Native MCP server implementation
from fastmcp import FastMCP

mcp = FastMCP(
    name="pheno-agents",
    version="2.0.0",
    description="Pheno Agent SDK MCP Server"
)

@mcp.tool
async def create_agent(
    config: dict,
    context: Context
) -> dict:
    """Create a new agent instance."""
    # Native MCP implementation
    agent = await agent_service.create(config, user_id=context.user_id)
    return {
        "success": True,
        "agent_id": agent.id,
        "status": agent.status
    }

@mcp.resource("agent://{agent_id}")
async def get_agent(agent_id: str, context: Context) -> str:
    """Get agent by ID."""
    agent = await agent_service.get(agent_id, user_id=context.user_id)
    return agent.model_dump_json()

# MCP server capabilities
mcp.list_tools()  # Advertise available tools
mcp.call_tool("create_agent", {...})  # Execute tool
mcp.get_resource("agent://123")  # Fetch resource
```

**MCP Protocol Compliance**:
- ✅ Tool discovery and execution
- ✅ Resource management
- ✅ Prompt templates
- ✅ Authentication and authorization
- ✅ Error handling and retries

**Sources**:
- [Model Context Protocol - OpenAI Agents SDK](https://openai.github.io/openai-agents-python/mcp/)
- [Understanding Model Context Protocol (MCP)](https://python.useinstructor.com/blog/2025/03/27/understanding-model-context-protocol-mcp/)
- [OpenAI and Microsoft Support Model Context Protocol](https://cloudwars.com/ai/openai-and-microsoft-support-model-context-protocol-mcp-ushering-in-unprecedented-ai-agent-interoperability/)

---

### 2. OpenAI API Compatibility Layer

```python
# OpenAI-compatible API endpoints (conversion boundary)
@router.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest
) -> ChatCompletionResponse:
    """OpenAI-compatible chat completions endpoint."""
    # Convert OpenAI format to internal format
    internal_request = convert_openai_to_internal(request)
    
    # Execute with native agent system
    result = await agent_service.run(internal_request)
    
    # Convert response back to OpenAI format
    return convert_internal_to_openai(result)

# Format conversion utilities
def convert_openai_to_internal(req: ChatCompletionRequest) -> AgentRequest:
    return AgentRequest(
        messages=req.messages,
        model=req.model,
        tools=[convert_openai_tool(t) for t in req.tools or []],
        metadata={"openai_compat": True}
    )

def convert_internal_to_openai(res: AgentResponse) -> ChatCompletionResponse:
    return ChatCompletionResponse(
        id=res.id,
        choices=[{
            "message": {"role": "assistant", "content": res.content},
            "finish_reason": res.finish_reason
        }],
        model=res.model,
        usage=res.usage
    )
```

**Compatibility Guarantees**:
- ✅ OpenAI Chat Completions API
- ✅ OpenAI Assistants API subset
- ✅ OpenAI Function Calling
- ⚠️ Best-effort compatibility (documented limitations)
- ❌ OpenAI Embeddings, Moderation (out of scope)

---

### 3. Framework Integration Adapters

```python
# LangChain integration adapter
from langchain.agents import Agent as LangChainAgent

class PhenoLangChainAdapter(LangChainAgent):
    """Wrap Pheno agent as LangChain agent."""
    
    def __init__(self, pheno_agent: Agent):
        self.agent = pheno_agent
    
    def _call(self, inputs: dict) -> dict:
        # Convert LangChain format to Pheno format
        result = asyncio.run(self.agent.run(inputs))
        return {"output": result.content}
    
    @property
    def _agent_type(self) -> str:
        return "pheno-agent"

# AutoGen integration adapter
from autogen import ConversableAgent as AutoGenAgent

class PhenoAutoGenAdapter(AutoGenAgent):
    """Wrap Pheno agent as AutoGen agent."""
    
    def __init__(self, pheno_agent: Agent, **kwargs):
        super().__init__(name=pheno_agent.name, **kwargs)
        self.agent = pheno_agent
    
    async def generate_reply(self, messages, sender, **kwargs):
        # Convert AutoGen messages to Pheno format
        result = await self.agent.run({"messages": messages})
        return result.content

# Usage
pheno_agent = sdk.create_agent(config)

# Use in LangChain
lc_agent = PhenoLangChainAdapter(pheno_agent)
lc_agent.run("Process this task")

# Use in AutoGen
ag_agent = PhenoAutoGenAdapter(pheno_agent)
await ag_agent.initiate_chat(other_agent, message="Hello")
```

**Adapter Guarantees**:
- ✅ Core functionality works
- ⚠️ Advanced features may have limitations
- 📖 Documented compatibility matrix

**Sources**:
- [Agent Protocol: Interoperability for LLM agents](https://blog.langchain.com/agent-protocol-interoperability-for-llm-agents/)
- [How to integrate LangGraph with AutoGen, CrewAI, and other frameworks](https://docs.langchain.com/langgraph-platform/autogen-integration)
- [Comparing Modern AI Agent Frameworks](https://www.aryaxai.com/article/comparing-modern-ai-agent-frameworks-autogen-langchain-openai-agents-crewai-and-dspy)

---

### 4. Standards Compliance Matrix

| Standard | Support Level | Notes |
|----------|---------------|-------|
| **MCP (Model Context Protocol)** | ✅ Native | Primary protocol, full support |
| **OpenAI Chat Completions** | ✅ Compatible | Via conversion layer |
| **OpenAI Assistants API** | ⚠️ Partial | Core features only |
| **OpenAI Function Calling** | ✅ Compatible | Full support |
| **A2A (Agent-to-Agent)** | 🔜 Planned | v2.5.0 target |
| **agents.json** | 🔜 Planned | v2.5.0 target |
| **LangChain** | ✅ Adapter | Via integration layer |
| **AutoGen** | ✅ Adapter | Via integration layer |
| **CrewAI** | ⚠️ Community | Community-maintained adapter |

**Legend**:
- ✅ Full support, tested, documented
- ⚠️ Partial support, documented limitations
- 🔜 Planned, roadmap item
- ❌ Not supported
- 📦 Community-maintained

---

## Migration Framework

### 1. Automated Migration Tools

```python
# Command-line migration utility
$ pheno-agents migrate --from 1.x --to 2.0

Analyzing codebase...
  ✓ Found 24 files using pheno-agents v1.x
  ✓ Detected 8 breaking changes requiring updates

Breaking changes:
  1. EntityConfig.type → EntityConfig.entity_type (12 occurrences)
  2. create_agent() → create_agent_async() (5 occurrences)
  3. Agent.run() return type changed (7 occurrences)

Apply automated fixes? [Y/n]: Y

Applying fixes...
  ✓ Updated EntityConfig.type → entity_type (12 files)
  ✓ Updated create_agent() → create_agent_async() (5 files)
  ✓ Added await to Agent.run() calls (7 files)
  ⚠ Manual review required for custom Agent subclasses (2 files)

Migration complete! 
  - 21 files updated automatically
  - 3 files require manual review (see migration-report.md)
  - Run tests to verify: python -m pytest

Next steps:
  1. Review changes: git diff
  2. Run tests: python -m pytest
  3. Read migration guide: https://docs.pheno.ai/migration/v1-to-v2
  4. Update dependencies: pip install pheno-agents>=2.0.0
```

#### Migration Tool Implementation

```python
# pheno_agents/cli/migrate.py
from ast import NodeTransformer, parse, unparse
from pathlib import Path

class V1ToV2Migrator(NodeTransformer):
    """AST transformer for v1 → v2 migration."""
    
    def visit_Call(self, node):
        # create_agent() → create_agent_async()
        if (hasattr(node.func, 'attr') and 
            node.func.attr == 'create_agent'):
            node.func.attr = 'create_agent_async'
            # Ensure call is awaited
            return ast.Await(value=node)
        return node
    
    def visit_Attribute(self, node):
        # EntityConfig.type → EntityConfig.entity_type
        if (hasattr(node, 'attr') and 
            node.attr == 'type' and
            self._is_entity_config(node)):
            node.attr = 'entity_type'
        return node

def migrate_file(path: Path) -> list[str]:
    """Migrate a single file."""
    warnings = []
    
    # Parse source
    source = path.read_text()
    tree = parse(source)
    
    # Apply transformations
    migrator = V1ToV2Migrator()
    new_tree = migrator.visit(tree)
    
    # Check for manual review items
    if has_custom_agent_subclass(tree):
        warnings.append(
            f"{path}: Custom Agent subclass requires manual review"
        )
    
    # Write transformed source
    new_source = unparse(new_tree)
    path.write_text(new_source)
    
    return warnings
```

**Sources**:
- [Migration Guides: Migrate AI SDK 4.0 to 5.0](https://ai-sdk.dev/docs/migration-guides/migration-guide-5-0)
- [Breaking Changes | Homey Apps SDK](https://apps.developer.homey.app/guides/how-to-breaking-changes)

---

### 2. Migration Guide Template

```markdown
# Migration Guide: v1.x → v2.0

## Overview

This guide covers migration from pheno-agents v1.x to v2.0.

**Timeline**: v2.0 released 2025-01-15, v1.x EOL 2026-01-15 (12 months)

**Key Changes**:
- Async-first API
- Renamed configuration fields
- New error handling patterns
- Improved type hints

**Estimated Migration Time**: 2-4 hours for typical project

---

## Automated Migration

```bash
# Install migration tool
pip install pheno-agents-migrate

# Run automated migration
pheno-agents migrate --from 1.x --to 2.0

# Review changes
git diff

# Test thoroughly
python -m pytest
```

---

## Breaking Changes

### 1. Async API (Breaking)

**Before (v1.x)**:
```python
from pheno_agents import AgentSDK

sdk = AgentSDK()
agent = sdk.create_agent(config)  # Synchronous
result = agent.run("Process this")  # Synchronous
```

**After (v2.0)**:
```python
from pheno_agents import AgentSDK

sdk = AgentSDK()
agent = await sdk.create_agent_async(config)  # Async
result = await agent.run("Process this")  # Async
```

**Migration**:
1. Add `async`/`await` to all agent operations
2. Update function signatures to `async def`
3. Use `asyncio.run()` for top-level calls

---

### 2. Configuration Changes (Breaking)

**Before (v1.x)**:
```python
config = EntityConfig(
    type="custom",  # Deprecated
    name="My Entity"
)
```

**After (v2.0)**:
```python
config = EntityConfig(
    entity_type="custom",  # New field name
    name="My Entity"
)
```

**Migration**:
- Automated: `pheno-agents migrate` handles this
- Manual: Replace `.type` with `.entity_type`

---

### 3. Error Handling (Breaking)

**Before (v1.x)**:
```python
try:
    result = agent.run(task)
except Exception as e:
    print(f"Error: {e}")
```

**After (v2.0)**:
```python
from pheno_agents.errors import AgentError, ToolError

try:
    result = await agent.run(task)
except ToolError as e:
    # Specific tool execution error
    print(f"Tool failed: {e.tool_name} - {e.message}")
except AgentError as e:
    # General agent error
    print(f"Agent error: {e.code} - {e.message}")
```

**Migration**:
- Update exception handling to catch specific error types
- Use error codes instead of parsing messages

---

## Testing Your Migration

```python
# Run existing tests
python -m pytest

# Run v2-specific tests
python -m pytest tests/test_v2_migration.py

# Check for deprecation warnings
python -W default::DeprecationWarning -m pytest

# Validate API compatibility
pheno-agents validate
```

---

## Gradual Migration Strategy

### Phase 1: Preparation (Week 1)
1. Review migration guide
2. Run automated migration tool
3. Review generated diff
4. Identify custom code requiring manual updates

### Phase 2: Testing (Week 2)
1. Update test suite
2. Run comprehensive tests
3. Fix any failures
4. Address deprecation warnings

### Phase 3: Deployment (Week 3)
1. Deploy to staging environment
2. Monitor for issues
3. Gradually roll out to production (feature flags)
4. Complete migration

---

## Support

- **Documentation**: https://docs.pheno.ai/migration/v1-to-v2
- **Migration Tool**: https://github.com/phenoai/migration-tools
- **Community Forum**: https://community.pheno.ai/migration
- **Support Email**: migration-support@pheno.ai

**Migration Support Period**: 12 months (until 2026-01-15)
```

---

## Deprecation Policy

### 1. Deprecation Timeline

```
┌─────────────────────────────────────────────────────────────┐
│ Deprecation Lifecycle                                       │
└─────────────────────────────────────────────────────────────┘

Phase 1: ANNOUNCEMENT (3-6 months before deprecation)
  - Update documentation with deprecation notice
  - Add @deprecated annotations to code
  - Email notification to affected users
  - Blog post announcing deprecation

Phase 2: DEPRECATION WARNINGS (release N+1)
  - Runtime warnings when deprecated features used
  - Migration guide published
  - Automated migration tool released
  - Response headers (API): Deprecation: true

Phase 3: COMPATIBILITY PERIOD (6-12 months)
  - Both old and new APIs supported
  - Gradually increase warning visibility
  - Monitor usage metrics
  - Proactive outreach to high-usage users

Phase 4: REMOVAL (release N+2, major version)
  - Deprecated features removed
  - Breaking change in new major version
  - Clear migration path documented
  - Old major version enters security-only support

Timeline Example:
  v1.5.0: Feature X announced as deprecated (Jun 2025)
  v1.6.0: Warnings added (Jul 2025)
  v2.0.0: Feature X removed (Jan 2026)
  v1.x.x: Security support until Jan 2027
```

### 2. Deprecation Communication Strategy

#### Multiple Channels (Critical)

```python
# 1. Code-level warnings
import warnings

def deprecated_function():
    warnings.warn(
        "deprecated_function() is deprecated and will be removed in v3.0.0. "
        "Use new_function() instead. "
        "See https://docs.pheno.ai/migration/deprecated-function",
        DeprecationWarning,
        stacklevel=2
    )

# 2. API response headers
@router.get("/v1/deprecated-endpoint")
async def deprecated_endpoint(response: Response):
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Wed, 01 Jun 2026 00:00:00 GMT"
    response.headers["Link"] = "</docs/migration>; rel=\"deprecation\""

# 3. Documentation annotations
@deprecated(version="2.0.0", reason="Use create_agent_async instead")
def create_agent(config: AgentConfig) -> Agent:
    ...

# 4. Type hints
from typing_extensions import deprecated

@deprecated("Use create_agent_async() instead")
def create_agent(config: AgentConfig) -> Agent:
    ...
```

#### Direct User Contact

```python
# Email notification to affected users
subject = "Action Required: Deprecated API Usage Detected"
body = f"""
Dear {user.name},

We've detected that your application is using deprecated Pheno Agents APIs:

Deprecated Features:
  - create_agent() (found in: {app.name})
  - EntityConfig.type field (12 occurrences)

Impact:
  - These features will be removed in v3.0.0 (Jan 2026)
  - Your application will break if not updated

Action Required:
  1. Review migration guide: {migration_url}
  2. Run automated migration: pheno-agents migrate
  3. Test thoroughly and deploy updated version
  4. Update dependencies: pip install pheno-agents>=2.0.0

Timeline:
  - Now: Deprecation warnings active
  - Jan 2026: Features removed (breaking change)
  - Migration support: migration-support@pheno.ai

Need Help?
  - Migration guide: {migration_url}
  - Support: migration-support@pheno.ai
  - Office hours: Thursdays 10am PT
"""

# Send email
await email_service.send(to=user.email, subject=subject, body=body)
```

#### Brownout Testing

```python
# Temporarily disable deprecated features to test user readiness
from datetime import datetime

async def brownout_check(feature: str) -> bool:
    """
    Brownout schedule for deprecated features.
    Temporarily disables features during low-traffic periods.
    """
    now = datetime.utcnow()
    
    # Brownout windows (increasing frequency)
    if feature == "create_agent_sync":
        # Week 1: 1 hour/week
        if now.weekday() == 2 and 2 <= now.hour < 3:  # Wed 2-3am UTC
            return True
        
        # Week 2: 2 hours/week
        if now.weekday() == 2 and 2 <= now.hour < 4:
            return True
        
        # Week 3: 4 hours/week
        if now.weekday() == 2 and 2 <= now.hour < 6:
            return True
    
    return False

@router.post("/v1/agents")
async def create_agent(request: Request):
    if await brownout_check("create_agent_sync"):
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Feature temporarily disabled (brownout testing)",
                "migration_url": "https://docs.pheno.ai/migration",
                "next_brownout": "2025-06-10T02:00:00Z"
            }
        )
    # Normal operation
    ...
```

**Sources**:
- [Best Practices for Deprecating an API](https://treblle.com/blog/best-practices-deprecating-api)
- [How to Smartly Sunset and Deprecate APIs](https://nordicapis.com/how-to-smartly-sunset-and-deprecate-apis/)
- [SDK deprecation timeline communication strategy](https://www.linkedin.com/advice/3/how-can-you-manage-api-feature-deprecation-ghjkf)

---

### 3. Deprecation Monitoring

```python
# Track usage of deprecated features
from prometheus_client import Counter

deprecated_usage = Counter(
    "deprecated_feature_usage",
    "Usage of deprecated features",
    ["feature", "user_id", "version"]
)

def track_deprecation(feature: str, user_id: str, version: str):
    deprecated_usage.labels(
        feature=feature,
        user_id=user_id,
        version=version
    ).inc()

# Alert if usage doesn't decline
if deprecated_usage.labels(feature="create_agent_sync").get() > 1000:
    alert_team(
        "Deprecated feature usage still high. "
        "Increase communication efforts."
    )

# Proactive outreach to high-usage users
top_users = get_top_deprecated_users(feature="create_agent_sync", limit=10)
for user in top_users:
    send_migration_assistance_email(user)
```

---

## Standards Compliance

### 1. OpenAI Compatibility

```python
# OpenAI-compatible endpoint implementation
@router.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    api_key: str = Header(None, alias="Authorization")
) -> ChatCompletionResponse:
    """
    OpenAI-compatible chat completions endpoint.
    
    Compatibility Level: FULL
    - Request format: OpenAI Chat Completions API
    - Response format: OpenAI Chat Completions API
    - Streaming: Supported (SSE format)
    - Function calling: Supported
    
    Limitations:
    - logprobs: Not supported (returns null)
    - logit_bias: Not supported (ignored)
    """
    # Validate API key
    user = await authenticate_openai_key(api_key)
    
    # Convert OpenAI request to internal format
    internal_request = AgentRequest(
        messages=request.messages,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        tools=[convert_openai_tool(t) for t in request.tools or []],
        metadata={"source": "openai_compat"}
    )
    
    # Execute with native agent
    result = await agent_service.run(internal_request)
    
    # Convert response to OpenAI format
    return ChatCompletionResponse(
        id=result.id,
        object="chat.completion",
        created=int(result.created_at.timestamp()),
        model=result.model,
        choices=[{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": result.content,
                "tool_calls": [
                    convert_internal_tool_call(tc)
                    for tc in result.tool_calls or []
                ]
            },
            "finish_reason": result.finish_reason,
            "logprobs": None  # Not supported
        }],
        usage={
            "prompt_tokens": result.usage.prompt_tokens,
            "completion_tokens": result.usage.completion_tokens,
            "total_tokens": result.usage.total_tokens
        }
    )

# Streaming support
@router.post("/v1/chat/completions", response_class=StreamingResponse)
async def chat_completions_stream(
    request: ChatCompletionRequest
) -> StreamingResponse:
    if not request.stream:
        return await chat_completions(request)
    
    async def event_stream():
        async for chunk in agent_service.run_stream(request):
            # Convert to OpenAI SSE format
            yield f"data: {convert_to_openai_chunk(chunk)}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )
```

**Compatibility Matrix**:
| OpenAI Feature | Support Level | Notes |
|----------------|---------------|-------|
| Chat Completions | ✅ Full | Complete compatibility |
| Streaming (SSE) | ✅ Full | OpenAI format |
| Function Calling | ✅ Full | Tools conversion |
| Vision (images) | ⚠️ Partial | Image URLs only |
| JSON mode | ✅ Full | Structured output |
| Logprobs | ❌ Not supported | Returns null |
| Logit bias | ❌ Not supported | Ignored |

---

### 2. MCP Protocol Compliance

```python
# MCP protocol implementation
from fastmcp import FastMCP
from fastmcp.server import MCPServer

mcp = FastMCP(
    name="pheno-agents",
    version="2.0.0",
    description="Pheno Agent SDK MCP Server",
    capabilities={
        "tools": True,
        "resources": True,
        "prompts": True,
        "sampling": False  # Not supported
    }
)

# Tool discovery
@mcp.list_tools
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="create_agent",
            description="Create a new agent instance",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "model": {"type": "string"},
                    "tools": {"type": "array"}
                },
                "required": ["name"]
            }
        ),
        # ... more tools
    ]

# Tool execution
@mcp.call_tool
async def call_tool(
    name: str,
    arguments: dict,
    context: Context
) -> ToolResult:
    """Execute a tool."""
    if name == "create_agent":
        agent = await agent_service.create(
            arguments,
            user_id=context.user_id
        )
        return ToolResult(
            content=[{"type": "text", "text": agent.model_dump_json()}],
            isError=False
        )
    
    raise ValueError(f"Unknown tool: {name}")

# Resource management
@mcp.list_resources
async def list_resources(context: Context) -> list[Resource]:
    """List available resources."""
    agents = await agent_service.list(user_id=context.user_id)
    return [
        Resource(
            uri=f"agent://{a.id}",
            name=a.name,
            mimeType="application/json"
        )
        for a in agents
    ]

@mcp.read_resource
async def read_resource(uri: str, context: Context) -> str:
    """Read a resource by URI."""
    if uri.startswith("agent://"):
        agent_id = uri.replace("agent://", "")
        agent = await agent_service.get(agent_id, user_id=context.user_id)
        return agent.model_dump_json()
    
    raise ValueError(f"Unknown resource: {uri}")
```

**MCP Compliance Checklist**:
- ✅ Tool discovery (list_tools)
- ✅ Tool execution (call_tool)
- ✅ Resource listing (list_resources)
- ✅ Resource reading (read_resource)
- ✅ Prompt templates (list_prompts, get_prompt)
- ✅ Authentication (context.user_id)
- ✅ Error handling (ToolResult.isError)
- ❌ Sampling (not supported)

---

### 3. Standards Roadmap

```yaml
Current (v2.0.0):
  - MCP 1.0 (native support)
  - OpenAI Chat Completions API (compatibility layer)
  - OpenAI Function Calling (full support)

Planned (v2.5.0 - Q2 2025):
  - A2A (Agent-to-Agent Protocol)
  - agents.json manifest format
  - Extended MCP capabilities

Future (v3.0.0 - Q4 2025):
  - Multi-modal tool support
  - Streaming tools
  - Advanced resource types

Under Consideration:
  - LangSmith protocol
  - Anthropic Computer Use API
  - Google Gemini Tools
```

---

## Implementation Roadmap

### Phase 1: Foundation (v2.0.0 - Q1 2025)

```yaml
Goals:
  - Establish versioning infrastructure
  - Implement deprecation framework
  - Create migration tooling

Deliverables:
  - Version detection and compatibility checks
  - Automated migration CLI tool
  - Migration guide template
  - Deprecation warning system

Success Criteria:
  - 80% of breaking changes automated
  - <24hr average migration time
  - Zero breaking changes in minor versions
```

### Phase 2: Standards (v2.5.0 - Q2 2025)

```yaml
Goals:
  - MCP protocol compliance
  - OpenAI compatibility layer
  - Framework adapters

Deliverables:
  - Native MCP server implementation
  - OpenAI API compatibility endpoint
  - LangChain/AutoGen adapters
  - A2A protocol support

Success Criteria:
  - 100% MCP core features
  - 90% OpenAI API compatibility
  - Framework adapter test coverage >80%
```

### Phase 3: Ecosystem (v3.0.0 - Q4 2025)

```yaml
Goals:
  - Multi-framework interoperability
  - Advanced standards support
  - Production-grade migration tools

Deliverables:
  - agents.json support
  - Enhanced migration automation
  - Cross-platform compatibility tests
  - Enterprise migration support

Success Criteria:
  - <4hr migration time (v2→v3)
  - Zero regression in compatibility tests
  - 95% automated migration coverage
```

---

## Appendix

### A. Version Detection

```python
# Runtime version detection
from pheno_agents import __version__, __platform_version__

def check_version_compatibility(required: str) -> bool:
    """Check if current version meets requirement."""
    from packaging.version import parse
    current = parse(__version__)
    required_version = parse(required)
    return current >= required_version

# Usage
if not check_version_compatibility("2.0.0"):
    raise RuntimeError("pheno-agents >= 2.0.0 required")

# CLI version check
$ pheno-agents --version
pheno-agents 2.0.0 (platform: 2025.01.0)
Python 3.11.5
```

### B. Compatibility Test Suite

```python
# tests/compatibility/test_openai_compat.py
import pytest
from openai import OpenAI
from pheno_agents import AgentSDK

def test_openai_chat_completions():
    """Test OpenAI compatibility."""
    # Use OpenAI SDK with Pheno backend
    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="pheno-test-key"
    )
    
    response = client.chat.completions.create(
        model="claude-sonnet-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    
    assert response.choices[0].message.content
    assert response.usage.total_tokens > 0

def test_function_calling():
    """Test OpenAI function calling compatibility."""
    client = OpenAI(base_url="http://localhost:8000/v1")
    
    response = client.chat.completions.create(
        model="claude-sonnet-4",
        messages=[{"role": "user", "content": "Get weather for SF"}],
        tools=[{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    }
                }
            }
        }]
    )
    
    assert response.choices[0].message.tool_calls
    assert response.choices[0].message.tool_calls[0].function.name == "get_weather"
```

### C. Migration Automation Examples

```python
# Example: Automated config migration
from pheno_agents.migration import ConfigMigrator

migrator = ConfigMigrator(from_version="1.x", to_version="2.0")

# Migrate single file
migrator.migrate_file("config.py")

# Migrate entire project
migrator.migrate_directory("src/")

# Generate migration report
report = migrator.generate_report()
print(report.summary())
# Output:
# Migration Report
# ----------------
# Files analyzed: 24
# Files updated: 21
# Manual review required: 3
# Breaking changes: 8
# Deprecation warnings: 12
```

### D. Further Reading

**Versioning**:
- [Semantic Versioning 2.0.0](https://semver.org/)
- [SemVer vs. CalVer: Choosing the Best Versioning Strategy](https://sensiolabs.com/blog/2025/semantic-vs-calendar-versioning)
- [API Versioning Best Practices 2024](https://liblab.com/blog/api-versioning-best-practices)

**Compatibility**:
- [API Backwards Compatibility Best Practices](https://zuplo.com/learning-center/api-versioning-backward-compatibility-best-practices)
- [Best practices for API backwards compatibility](https://stackoverflow.com/questions/10716035/best-practices-for-api-backwards-compatibility)
- [Atlassian REST API policy](https://developer.atlassian.com/platform/marketplace/atlassian-rest-api-policy/)

**Migration**:
- [Migration Guides: Migrate AI SDK 4.0 to 5.0](https://ai-sdk.dev/docs/migration-guides/migration-guide-5-0)
- [Breaking Changes | Homey Apps SDK](https://apps.developer.homey.app/guides/how-to-breaking-changes)
- [Database Migrations with Feature Flags](https://www.harness.io/blog/database-migration-with-feature-flags)

**Standards**:
- [Model Context Protocol - OpenAI Agents SDK](https://openai.github.io/openai-agents-python/mcp/)
- [Agent Protocol: Interoperability for LLM agents](https://blog.langchain.com/agent-protocol-interoperability-for-llm-agents/)
- [How to integrate LangGraph with AutoGen](https://docs.langchain.com/langgraph-platform/autogen-integration)

---

**End of Document**
