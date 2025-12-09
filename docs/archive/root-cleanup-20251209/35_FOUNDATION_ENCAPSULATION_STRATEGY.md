# Foundation Encapsulation Strategy

**Document Version:** 1.0
**Date:** 2025-12-02
**Status:** Planning - Phase 4 & 4.5

---

## Executive Summary

This document outlines the strategic plan to encapsulate two critical foundation components:

1. **Phase 4: Bifrost Extensions SDK** - Smart LLM Gateway (router/router_core/)
2. **Phase 4.5: SmartCP SDK** - MCP Tool Server (thin frontend)

**Goal:** Create production-ready, stable SDKs that agent-cli and other consumers can depend on, enabling autonomous agent development while maintaining clean architectural boundaries.

**Timeline:** 4-5 weeks total before agent-cli development can begin

**Critical Success Factors:**
- Clean API boundaries with minimal surface area
- Zero backwards compatibility burden (greenfield SDK design)
- Production-grade testing and documentation
- Clear separation of concerns (routing intelligence vs tool execution)

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Phase 4: Bifrost Extensions SDK](#2-phase-4-bifrost-extensions-sdk)
3. [Phase 4.5: SmartCP SDK](#3-phase-45-smartcp-sdk)
4. [Integration Architecture](#4-integration-architecture)
5. [Migration Strategy](#5-migration-strategy)
6. [Testing Strategy](#6-testing-strategy)
7. [Timeline & Milestones](#7-timeline--milestones)
8. [Risk Assessment](#8-risk-assessment)
9. [Success Criteria](#9-success-criteria)

---

## 1. Current State Analysis

### 1.1 Router/Router_Core Assessment

**Current Structure:**
```
router/router_core/
├── adapters/          # 21 modules - Provider integrations
├── analysis/          # 13 modules - Analytics & insights
├── application/       # 13 modules - High-level services
├── classification/    # 8 modules - Request classification
├── cost/              # 7 modules - Cost optimization
├── domain/            # 11 modules - Domain models
├── metrics/           # 9 modules - Performance tracking
├── prediction/        # 25 modules - ML prediction
├── routing/           # 32 modules - Core routing logic
├── ml_classifiers/    # 10 modules - ML classification
└── [35+ other modules across 49 directories]

Total: ~359 Python files
```

**Key Capabilities:**
- **Model Routing:** Cost-optimized, quality-aware, latency-aware routing
- **Tool Routing:** Determines which MCP tool to invoke for a given action
- **Classification:** Request intent classification (code, reasoning, creative, etc.)
- **Cost Optimization:** Real-time cost estimation and budget management
- **Performance Tracking:** Metrics collection and analysis
- **Provider Abstraction:** OpenRouter, OpenAI, Anthropic, local models
- **Fallback Handling:** Automatic failover and retry logic

**Pain Points:**
- **Massive surface area:** 359 files, unclear entry points
- **Circular dependencies:** Deep interdependencies between modules
- **No clear SDK boundary:** Everything is exposed, nothing is encapsulated
- **Testing complexity:** Integration tests require full stack
- **Documentation gaps:** Internal docs, no external API reference

### 1.2 MCP Infrastructure Assessment

**Current Structure:**
```
smartcp/
├── fastmcp_auth_provider.py       # Auth for MCP servers
├── mcp_registry.py                # Server registry
├── mcp_server_discovery.py        # Discovery service
├── mcp_custom_builder.py          # Custom server builder
├── mcp_lifecycle_manager.py       # Lifecycle management
├── mcp_hot_reload.py              # Hot reload support
├── mcp_lazy_loader.py             # Lazy loading
├── mcp_tool_composer.py           # Tool composition
├── mcp_inference_bridge.py        # Inference integration
├── mcp_real_registry.py           # Production registry
├── router/router_core/mcp/        # MCP integration in router
│   ├── mcp_tool_router.py         # Tool routing logic
│   └── mcp_tools_registry.py      # Tool registry
└── python-proto-ref/              # FastMCP prototype
```

**Key Capabilities:**
- **Stdio + HTTP:** Dual-protocol MCP server
- **Tool Discovery:** Automatic tool detection and registration
- **Tool Execution:** Parameterized tool invocation
- **Tool Composition:** Multi-tool workflows
- **Auth Integration:** FastMCP auth provider
- **Hot Reload:** Development workflow support
- **Registry:** Tool and server registration

**Pain Points:**
- **Scattered functionality:** MCP code across multiple files and directories
- **No clear SDK:** Entry points unclear for external consumers
- **Tight coupling:** MCP routing logic embedded in router_core
- **Duplication:** Multiple registries, discovery mechanisms
- **Testing gaps:** Integration tests require full deployment

### 1.3 Current Integration Pattern (Anti-Pattern)

```python
# ❌ CURRENT: Direct imports, tight coupling
from router_core.application.routing_service import RoutingService
from router_core.routing.registry import ModelRegistry
from router_core.classification.unified_classifier import UnifiedClassifier
from router_core.mcp.mcp_tool_router import MCPToolRouter
from mcp_registry import MCPRegistry
from mcp_lifecycle_manager import MCPLifecycleManager

# Agent tries to use these directly → nightmare
routing_service = RoutingService(...)  # 12 constructor params
classifier = UnifiedClassifier(...)    # 8 constructor params
tool_router = MCPToolRouter(...)       # 6 constructor params
```

**Problems:**
- Exposes internal implementation details
- No versioning or stability guarantees
- Breaking changes ripple to consumers
- Impossible to test in isolation
- No clear upgrade path

---

## 2. Phase 4: Bifrost Extensions SDK

**Duration:** 3-4 weeks
**Goal:** Production-ready Smart LLM Gateway SDK

### 2.1 SDK Design Philosophy

**Principles:**
1. **Minimal Surface Area:** Expose only what consumers need
2. **Stable Contracts:** API versioning, deprecation policy
3. **Zero Internal Leakage:** Hide router_core implementation
4. **Composable:** Modular components with clear boundaries
5. **Testable:** Mock-friendly, dependency-injectable
6. **Well-Documented:** API reference, tutorials, examples

### 2.2 Public API Design

#### Core Client

```python
# bifrost/__init__.py
from bifrost.client import GatewayClient
from bifrost.types import (
    RoutingStrategy,
    RoutingResult,
    ModelRecommendation,
    ToolRecommendation,
)
from bifrost.config import GatewayConfig

__all__ = [
    "GatewayClient",
    "RoutingStrategy",
    "RoutingResult",
    "ModelRecommendation",
    "ToolRecommendation",
    "GatewayConfig",
]
```

#### GatewayClient API

```python
from bifrost import GatewayClient, RoutingStrategy, GatewayConfig
from typing import AsyncIterator

# Initialize client
config = GatewayConfig(
    api_key="sk-...",
    default_strategy=RoutingStrategy.COST_OPTIMIZED,
    budget_usd=100.0,
    enable_metrics=True,
)
client = GatewayClient(config)

# --- USE CASE 1: Model Routing ---
# Simple routing (auto-detect strategy)
result = await client.route(
    prompt="Analyze this code for bugs",
    context={"code": "..."}
)
print(result.model_id)        # "claude-sonnet-4"
print(result.provider)        # "anthropic"
print(result.cost_usd)        # 0.003
print(result.reasoning)       # "Selected for code analysis quality"

# Explicit strategy
result = await client.route(
    prompt="Quick question: what's 2+2?",
    strategy=RoutingStrategy.FAST_CHEAP
)

# With constraints
result = await client.route(
    prompt="Long document analysis",
    strategy=RoutingStrategy.QUALITY,
    constraints={
        "max_cost_usd": 0.01,
        "max_latency_ms": 2000,
        "provider_preference": ["anthropic", "openai"],
    }
)

# --- USE CASE 2: Tool Routing ---
# Determine which tool to use
tool_result = await client.route_tool(
    action="search web for latest Python releases",
    available_tools=["web_search", "browser", "file_read"],
    context={"previous_results": [...]}
)
print(tool_result.tool_name)       # "web_search"
print(tool_result.parameters)      # {"query": "Python releases 2024"}
print(tool_result.confidence)      # 0.95

# --- USE CASE 3: Classification ---
# Classify request intent
classification = await client.classify(
    prompt="Write a Python script to parse CSV files"
)
print(classification.intent)       # "code_generation"
print(classification.complexity)   # "medium"
print(classification.tags)         # ["python", "data", "scripting"]

# --- USE CASE 4: Streaming ---
# Stream LLM response
async for chunk in client.stream(
    prompt="Explain quantum computing",
    strategy=RoutingStrategy.QUALITY
):
    print(chunk.content, end="")

# --- USE CASE 5: Batch Routing ---
# Optimize batch of requests
batch_results = await client.route_batch(
    requests=[
        {"prompt": "Quick math question"},
        {"prompt": "Complex code review"},
        {"prompt": "Creative story writing"},
    ],
    strategy=RoutingStrategy.BALANCED
)

# --- USE CASE 6: Cost Estimation ---
# Estimate cost before execution
estimate = await client.estimate_cost(
    prompt="Long prompt...",
    model_id="claude-sonnet-4"
)
print(estimate.input_cost_usd)
print(estimate.output_cost_usd)
print(estimate.total_cost_usd)

# --- USE CASE 7: Model Discovery ---
# Find models matching criteria
models = await client.discover_models(
    capabilities=["code", "reasoning"],
    max_cost_per_1k_tokens=0.01,
    min_context_length=100_000,
)
for model in models:
    print(model.id, model.provider, model.cost_per_1k)
```

#### Strategy Enum

```python
from enum import Enum

class RoutingStrategy(str, Enum):
    """Routing strategy for model selection."""

    # Primary strategies
    COST_OPTIMIZED = "cost_optimized"    # Minimize cost while meeting quality threshold
    QUALITY = "quality"                  # Best quality regardless of cost
    FAST_CHEAP = "fast_cheap"           # Minimize latency and cost
    BALANCED = "balanced"                # Balance cost, quality, latency

    # Advanced strategies
    BUDGET_AWARE = "budget_aware"       # Stay within budget constraints
    PROVIDER_SPECIFIC = "provider_specific"  # Prefer specific provider
    CAPABILITY_MATCH = "capability_match"    # Match model capabilities to task

    # Experimental
    ADAPTIVE = "adaptive"                # Learn from past performance
    ENSEMBLE = "ensemble"                # Multi-model consensus
```

#### Result Types

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

@dataclass
class RoutingResult:
    """Result of model routing decision."""

    # Model selection
    model_id: str                        # "claude-sonnet-4"
    provider: str                        # "anthropic"
    subprovider: Optional[str] = None    # "deepinfra" (for OpenRouter)

    # Cost & performance
    estimated_cost_usd: float = 0.0      # Estimated cost
    actual_cost_usd: Optional[float] = None  # Actual cost (after execution)
    estimated_latency_ms: float = 0.0    # Estimated latency
    actual_latency_ms: Optional[int] = None  # Actual latency

    # Decision metadata
    strategy_used: str = "cost_optimized"
    reasoning: str = ""                  # Human-readable explanation
    confidence: float = 1.0              # 0.0 - 1.0
    alternatives: List[str] = None       # Other models considered

    # Classification info
    classification: Optional[Dict[str, Any]] = None

    # Execution info (populated after execution)
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None


@dataclass
class ToolRecommendation:
    """Result of tool routing decision."""

    tool_name: str                       # "web_search"
    parameters: Dict[str, Any]           # {"query": "...", "max_results": 5}
    confidence: float = 1.0              # 0.0 - 1.0
    reasoning: str = ""                  # Why this tool
    alternatives: List[str] = None       # Other tools considered
    execution_priority: int = 1          # For multi-tool workflows


@dataclass
class ModelRecommendation:
    """Model metadata for discovery."""

    id: str
    provider: str
    display_name: str
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
    context_length: int
    capabilities: List[str]              # ["code", "reasoning", "vision"]
    latency_p50_ms: float
    quality_score: float                 # 0.0 - 1.0
```

### 2.3 Internal Architecture

**Package Structure:**
```
bifrost/
├── __init__.py                  # Public API exports
├── client.py                    # GatewayClient implementation
├── config.py                    # Configuration management
├── types.py                     # Public types (RoutingStrategy, etc.)
├── errors.py                    # Exception classes
├── _internal/                   # Internal implementation (hidden)
│   ├── routing/                 # Routing engine
│   │   ├── engine.py            # Core routing logic
│   │   ├── strategies/          # Strategy implementations
│   │   ├── registry.py          # Model registry
│   │   └── selector.py          # Model selection
│   ├── classification/          # Request classification
│   │   ├── classifier.py        # Unified classifier
│   │   └── intent_detector.py
│   ├── cost/                    # Cost management
│   │   ├── estimator.py
│   │   └── optimizer.py
│   ├── metrics/                 # Performance tracking
│   │   ├── collector.py
│   │   └── tracker.py
│   ├── adapters/                # Provider adapters
│   │   ├── base.py
│   │   ├── openrouter.py
│   │   ├── anthropic.py
│   │   └── openai.py
│   └── utils/                   # Internal utilities
├── testing/                     # Testing utilities
│   ├── mocks.py                # Mock implementations
│   └── fixtures.py             # Test fixtures
└── docs/                        # SDK documentation
    ├── quickstart.md
    ├── api_reference.md
    ├── strategies.md
    └── examples/
```

**Key Principles:**
1. **_internal/** is private:** Never import from `bifrost._internal.*`
2. **Versioned API:** Breaking changes require major version bump
3. **Stable types:** Public types frozen once released
4. **Adapter pattern:** Provider implementations hidden behind stable interfaces

### 2.4 Migration from router_core

**Extraction Strategy:**

**Step 1: Identify Core Components**
```bash
# Map current router_core modules to SDK structure
router_core/application/routing_service.py → bifrost/_internal/routing/engine.py
router_core/classification/unified_classifier.py → bifrost/_internal/classification/classifier.py
router_core/cost/estimator.py → bifrost/_internal/cost/estimator.py
router_core/routing/registry.py → bifrost/_internal/routing/registry.py
router_core/adapters/ → bifrost/_internal/adapters/
router_core/metrics/ → bifrost/_internal/metrics/
```

**Step 2: Create Thin Facade**
```python
# bifrost/client.py
from bifrost._internal.routing.engine import RoutingEngine
from bifrost._internal.classification.classifier import Classifier
from bifrost._internal.cost.estimator import CostEstimator
from bifrost.types import RoutingStrategy, RoutingResult
from bifrost.config import GatewayConfig

class GatewayClient:
    """Public client for Bifrost Gateway.

    This is the ONLY public entry point.
    """

    def __init__(self, config: GatewayConfig):
        self._config = config
        # Internal components (hidden from consumers)
        self._engine = RoutingEngine(config)
        self._classifier = Classifier(config)
        self._estimator = CostEstimator(config)

    async def route(
        self,
        prompt: str,
        strategy: RoutingStrategy = None,
        **kwargs
    ) -> RoutingResult:
        """Route request to optimal model.

        Args:
            prompt: User prompt
            strategy: Routing strategy (defaults to config)
            **kwargs: Additional routing parameters

        Returns:
            RoutingResult with model selection and metadata

        Raises:
            RoutingError: If routing fails
            ConfigError: If configuration invalid
        """
        strategy = strategy or self._config.default_strategy

        # Classify request
        classification = await self._classifier.classify(prompt)

        # Route to optimal model
        decision = await self._engine.route(
            prompt=prompt,
            classification=classification,
            strategy=strategy,
            **kwargs
        )

        # Return public result type
        return RoutingResult.from_internal(decision)
```

**Step 3: Consolidate Dependencies**
```python
# bifrost/_internal/routing/engine.py
# Consolidate logic from multiple router_core modules

from typing import Protocol
from bifrost.types import RoutingStrategy
from bifrost._internal.routing.registry import ModelRegistry
from bifrost._internal.routing.selector import ModelSelector
from bifrost._internal.cost.optimizer import CostOptimizer

class RoutingEngine:
    """Internal routing engine (not exposed to consumers)."""

    def __init__(self, config):
        self._registry = ModelRegistry(config)
        self._selector = ModelSelector(config)
        self._optimizer = CostOptimizer(config)

    async def route(self, prompt, classification, strategy, **kwargs):
        # Get candidate models
        candidates = await self._registry.get_candidates(
            capabilities=classification.required_capabilities,
            constraints=kwargs.get("constraints", {})
        )

        # Select optimal model
        if strategy == RoutingStrategy.COST_OPTIMIZED:
            selected = await self._optimizer.select_cheapest(
                candidates,
                quality_threshold=classification.min_quality
            )
        elif strategy == RoutingStrategy.QUALITY:
            selected = await self._selector.select_best_quality(candidates)
        elif strategy == RoutingStrategy.FAST_CHEAP:
            selected = await self._selector.select_fastest_cheapest(candidates)
        else:
            selected = await self._selector.select_balanced(candidates)

        return selected
```

**Step 4: Gradual Migration**
```python
# Week 1: Extract core routing
bifrost/_internal/routing/

# Week 2: Extract classification & cost
bifrost/_internal/classification/
bifrost/_internal/cost/

# Week 3: Extract adapters & metrics
bifrost/_internal/adapters/
bifrost/_internal/metrics/

# Week 4: Testing & documentation
bifrost/testing/
bifrost/docs/
```

### 2.5 Non-Agent Use Cases

**Critical:** Bifrost must support general LLM gateway use, not just agent routing.

**Use Cases:**
1. **Direct LLM Invocation:** Application wants cheapest model for known task
2. **Multi-Tenant Routing:** Different routing strategies per org/user
3. **Cost-Aware Applications:** Stay within budget, optimize spend
4. **Quality-Critical Applications:** Always use best model for specific domain
5. **Latency-Sensitive Applications:** Real-time chat, low-latency requirements
6. **Provider Failover:** Automatic fallback when provider unavailable
7. **A/B Testing:** Route traffic between models for experimentation

**Example: Direct Application Use**
```python
# Web application using Bifrost for cost-optimized chat
from bifrost import GatewayClient, RoutingStrategy

client = GatewayClient(config)

# User chat message → route to cheapest model
result = await client.route(
    prompt=user_message,
    strategy=RoutingStrategy.FAST_CHEAP,
    constraints={"max_cost_usd": 0.005}  # Penny per message
)

# Execute with selected model
response = await llm_client.complete(
    model=result.model_id,
    provider=result.provider,
    prompt=user_message
)

# Track actual cost
await client.record_execution(
    result=result,
    actual_cost_usd=response.cost,
    actual_latency_ms=response.latency_ms
)
```

---

## 3. Phase 4.5: SmartCP SDK

**Duration:** 2-3 weeks (overlaps with Phase 4 weeks 3-4)
**Goal:** Production-ready MCP Tool Server SDK

### 3.1 SDK Design Philosophy

**Principles:**
1. **Thin Frontend:** SmartCP delegates intelligence to Bifrost
2. **Tool Execution Only:** Focus on MCP protocol, tool invocation, composition
3. **Stdio + HTTP:** Support both protocols seamlessly
4. **Minimal Routing Logic:** Only tool discovery, no model routing
5. **FastMCP Integration:** Leverage FastMCP for MCP protocol
6. **Composable Tools:** Support multi-tool workflows

### 3.2 Public API Design

#### Core Components

```python
# smartcp/__init__.py
from smartcp.server import MCPServer
from smartcp.client import ToolClient
from smartcp.types import (
    Tool,
    ToolParameter,
    ToolResult,
    ExecutionMode,
)
from smartcp.config import MCPConfig

__all__ = [
    "MCPServer",
    "ToolClient",
    "Tool",
    "ToolParameter",
    "ToolResult",
    "ExecutionMode",
    "MCPConfig",
]
```

#### MCPServer API

```python
from smartcp import MCPServer, MCPConfig
from bifrost import GatewayClient  # For tool routing

# --- USE CASE 1: Start MCP Server (stdio) ---
config = MCPConfig(
    name="my-tools",
    version="1.0.0",
    mode="stdio",  # or "http"
    port=8000,  # for HTTP mode
)
server = MCPServer(config)

# Register tools
@server.tool
async def file_read(path: str) -> dict:
    """Read file contents."""
    with open(path) as f:
        return {"content": f.read()}

@server.tool
async def web_search(query: str, max_results: int = 5) -> dict:
    """Search web."""
    results = await search_api(query, max_results)
    return {"results": results}

# Start server
await server.start()  # Blocks, handles stdio/HTTP requests

# --- USE CASE 2: HTTP Server with Auth ---
config = MCPConfig(
    name="secure-tools",
    mode="http",
    port=8000,
    auth_enabled=True,
    auth_provider="jwt",  # or "api_key"
)
server = MCPServer(config)

# Require auth for all tools
@server.tool(requires_auth=True)
async def sensitive_operation(data: str) -> dict:
    """Perform sensitive operation."""
    # User context available from auth
    user_id = server.current_user.id
    return await perform_operation(user_id, data)

await server.start()

# --- USE CASE 3: Tool Discovery ---
# Server automatically exposes tool metadata
# Client can discover via:
# - stdio: list_tools command
# - HTTP: GET /tools

# Tools are auto-documented from docstrings
```

#### ToolClient API

```python
from smartcp import ToolClient, ExecutionMode
from bifrost import GatewayClient

# --- USE CASE 1: Execute Single Tool ---
client = ToolClient(server_url="http://localhost:8000")

# Discover available tools
tools = await client.list_tools()
print(tools)  # [Tool(name="file_read", ...), Tool(name="web_search", ...)]

# Execute tool
result = await client.execute_tool(
    tool_name="file_read",
    parameters={"path": "README.md"}
)
print(result.output)  # {"content": "..."}

# --- USE CASE 2: Tool Routing (with Bifrost) ---
# Delegate tool selection to Bifrost
gateway = GatewayClient(bifrost_config)
tool_client = ToolClient(server_url="http://localhost:8000")

# Ask Bifrost which tool to use
recommendation = await gateway.route_tool(
    action="search for Python documentation",
    available_tools=await tool_client.list_tools()
)

# Execute recommended tool
result = await tool_client.execute_tool(
    tool_name=recommendation.tool_name,
    parameters=recommendation.parameters
)

# --- USE CASE 3: Tool Composition (Multi-Tool Workflow) ---
# Execute multiple tools in sequence
workflow_result = await tool_client.execute_workflow([
    {"tool": "web_search", "params": {"query": "Python async"}},
    {"tool": "file_write", "params": {"path": "notes.txt", "content": "$prev.results"}},
])

# --- USE CASE 4: Batch Execution ---
# Execute multiple tools in parallel
results = await tool_client.execute_batch([
    {"tool": "file_read", "params": {"path": "file1.txt"}},
    {"tool": "file_read", "params": {"path": "file2.txt"}},
    {"tool": "file_read", "params": {"path": "file3.txt"}},
])

# --- USE CASE 5: Streaming Tool Results ---
# For long-running tools
async for chunk in tool_client.execute_stream(
    tool_name="large_file_process",
    parameters={"path": "huge_file.csv"}
):
    print(chunk.progress)  # {"rows_processed": 1000, "total": 100000}
```

#### Tool Registration Patterns

```python
from smartcp import MCPServer, ToolParameter
from typing import List

server = MCPServer(config)

# --- Pattern 1: Simple Function Tool ---
@server.tool
async def add_numbers(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

# --- Pattern 2: Complex Tool with Validation ---
@server.tool(
    parameters=[
        ToolParameter(name="query", type="string", required=True),
        ToolParameter(name="max_results", type="integer", default=5),
        ToolParameter(name="language", type="string", enum=["en", "es", "fr"]),
    ]
)
async def advanced_search(query: str, max_results: int = 5, language: str = "en"):
    """Advanced web search."""
    # Parameter validation automatic
    results = await search_api(query, max_results, language)
    return {"results": results, "count": len(results)}

# --- Pattern 3: Tool with Dependencies ---
@server.tool(requires_auth=True, rate_limit="10/minute")
async def rate_limited_tool(data: str):
    """Tool with rate limiting."""
    # Auth + rate limit enforced automatically
    return await process(data)

# --- Pattern 4: Dynamic Tool Registration ---
# Load tools from configuration
for tool_config in load_tool_configs():
    server.register_tool(
        name=tool_config.name,
        handler=create_handler(tool_config),
        parameters=tool_config.parameters
    )
```

### 3.3 Internal Architecture

**Package Structure:**
```
smartcp/
├── __init__.py                  # Public API exports
├── server.py                    # MCPServer implementation
├── client.py                    # ToolClient implementation
├── config.py                    # Configuration
├── types.py                     # Public types
├── errors.py                    # Exceptions
├── _internal/                   # Internal implementation
│   ├── protocol/                # MCP protocol handling
│   │   ├── stdio_handler.py
│   │   └── http_handler.py
│   ├── registry/                # Tool registry
│   │   ├── tool_registry.py
│   │   └── schema_builder.py
│   ├── execution/               # Tool execution
│   │   ├── executor.py
│   │   ├── validator.py
│   │   └── composition.py       # Multi-tool workflows
│   ├── auth/                    # Authentication
│   │   ├── provider.py
│   │   ├── jwt_provider.py
│   │   └── api_key_provider.py
│   └── utils/
├── integrations/                # External integrations
│   ├── bifrost.py              # Bifrost integration for tool routing
│   └── fastmcp.py              # FastMCP wrapper
└── docs/
    ├── quickstart.md
    ├── tool_development.md
    └── deployment.md
```

### 3.4 Integration with Bifrost

**Key Principle:** SmartCP delegates tool routing to Bifrost, focuses on execution.

```python
# smartcp/integrations/bifrost.py
from bifrost import GatewayClient
from smartcp.types import Tool
from typing import List, Dict, Any

class BifrostToolRouter:
    """Integration layer for Bifrost tool routing."""

    def __init__(self, gateway_client: GatewayClient):
        self._gateway = gateway_client

    async def recommend_tool(
        self,
        action: str,
        available_tools: List[Tool],
        context: Dict[str, Any] = None
    ) -> dict:
        """Ask Bifrost which tool to use.

        Args:
            action: Natural language action description
            available_tools: List of available tools
            context: Additional context for routing

        Returns:
            {"tool_name": str, "parameters": dict, "confidence": float}
        """
        return await self._gateway.route_tool(
            action=action,
            available_tools=[t.name for t in available_tools],
            context=context
        )
```

**Usage Pattern:**
```python
from smartcp import ToolClient
from bifrost import GatewayClient
from smartcp.integrations.bifrost import BifrostToolRouter

# Setup
gateway = GatewayClient(bifrost_config)
tool_client = ToolClient(mcp_server_url)
router = BifrostToolRouter(gateway)

# Agent workflow
action = "find recent Python releases"
available_tools = await tool_client.list_tools()

# Bifrost recommends tool
recommendation = await router.recommend_tool(action, available_tools)

# SmartCP executes tool
result = await tool_client.execute_tool(
    tool_name=recommendation["tool_name"],
    parameters=recommendation["parameters"]
)
```

### 3.5 Migration from Current MCP Infrastructure

**Consolidation Strategy:**

**Step 1: Consolidate MCP Files**
```bash
# Merge scattered MCP functionality into SDK
mcp_registry.py → smartcp/_internal/registry/tool_registry.py
mcp_server_discovery.py → smartcp/_internal/registry/discovery.py
mcp_lifecycle_manager.py → smartcp/_internal/lifecycle.py
mcp_tool_composer.py → smartcp/_internal/execution/composition.py
mcp_inference_bridge.py → smartcp/integrations/bifrost.py (remove inference, delegate to Bifrost)
fastmcp_auth_provider.py → smartcp/_internal/auth/provider.py
router_core/mcp/mcp_tool_router.py → DELETE (move to Bifrost)
```

**Step 2: Remove Routing Logic from SmartCP**
```python
# ❌ OLD: SmartCP tries to route tools internally
class MCPToolRouter:
    def select_tool(self, action: str) -> str:
        # Complex routing logic...
        pass

# ✅ NEW: SmartCP delegates to Bifrost
class ToolClient:
    async def execute_with_routing(
        self,
        action: str,
        gateway_client: GatewayClient
    ) -> ToolResult:
        # Ask Bifrost which tool
        recommendation = await gateway_client.route_tool(
            action=action,
            available_tools=await self.list_tools()
        )

        # Execute recommended tool
        return await self.execute_tool(
            tool_name=recommendation.tool_name,
            parameters=recommendation.parameters
        )
```

**Step 3: Simplify Server Implementation**
```python
# smartcp/server.py
from fastmcp import FastMCP
from smartcp.config import MCPConfig
from smartcp._internal.protocol.stdio_handler import StdioHandler
from smartcp._internal.protocol.http_handler import HTTPHandler
from smartcp._internal.registry.tool_registry import ToolRegistry

class MCPServer:
    """MCP server supporting stdio and HTTP."""

    def __init__(self, config: MCPConfig):
        self._config = config
        self._registry = ToolRegistry()

        # Choose protocol handler
        if config.mode == "stdio":
            self._handler = StdioHandler(self._registry, config)
        else:
            self._handler = HTTPHandler(self._registry, config)

    def tool(self, func=None, **kwargs):
        """Decorator to register tool."""
        def decorator(f):
            self._registry.register(f, **kwargs)
            return f

        if func:
            return decorator(func)
        return decorator

    async def start(self):
        """Start server."""
        await self._handler.start()
```

---

## 4. Integration Architecture

### 4.1 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Agent CLI                            │
│  (autonomous agent executor - to be built in Phase 5)       │
└─────────────┬───────────────────────────┬───────────────────┘
              │                           │
              │ uses                      │ uses
              ▼                           ▼
    ┌─────────────────┐         ┌─────────────────┐
    │  Bifrost SDK    │         │   SmartCP SDK   │
    │  (gateway)      │◄────────│   (tools)       │
    └─────────────────┘ delegates└─────────────────┘
              │         routing         │
              │                         │
              │                         │
    ┌─────────▼─────────┐     ┌────────▼────────┐
    │  LLM Providers    │     │  MCP Tools      │
    │  (OpenRouter,     │     │  (file ops,     │
    │   Anthropic, etc) │     │   web search)   │
    └───────────────────┘     └─────────────────┘
```

### 4.2 Clear Responsibilities

**Bifrost SDK:**
- ✅ Model routing (cost, quality, latency optimization)
- ✅ Tool routing (which tool to invoke)
- ✅ Classification (intent detection)
- ✅ Cost optimization
- ✅ Provider abstraction
- ✅ Performance metrics
- ❌ Tool execution (delegates to SmartCP)
- ❌ MCP protocol (delegates to SmartCP)

**SmartCP SDK:**
- ✅ MCP server (stdio + HTTP)
- ✅ Tool registration
- ✅ Tool execution
- ✅ Tool composition (multi-tool workflows)
- ✅ Parameter validation
- ✅ Auth integration
- ❌ Tool routing (delegates to Bifrost)
- ❌ Model selection (delegates to Bifrost)

**Agent CLI (Phase 5):**
- ✅ Autonomous execution
- ✅ Task planning
- ✅ Multi-step workflows
- ✅ Memory management
- ✅ Uses Bifrost for LLM routing
- ✅ Uses SmartCP for tool execution
- ❌ Direct LLM access (via Bifrost)
- ❌ Direct MCP protocol (via SmartCP)

### 4.3 Integration Patterns

**Pattern 1: Agent Workflow**
```python
from bifrost import GatewayClient, RoutingStrategy
from smartcp import ToolClient

# Agent initialization
gateway = GatewayClient(bifrost_config)
tool_client = ToolClient(mcp_server_url)

# Agent execution loop
async def agent_step(task: str):
    # 1. Ask Bifrost for model
    model_result = await gateway.route(
        prompt=f"Plan how to: {task}",
        strategy=RoutingStrategy.QUALITY
    )

    # 2. Execute LLM (via Bifrost)
    plan = await llm_client.complete(
        model=model_result.model_id,
        prompt=f"Plan how to: {task}"
    )

    # 3. Ask Bifrost which tool to use
    tool_result = await gateway.route_tool(
        action=plan.next_action,
        available_tools=await tool_client.list_tools()
    )

    # 4. Execute tool (via SmartCP)
    tool_output = await tool_client.execute_tool(
        tool_name=tool_result.tool_name,
        parameters=tool_result.parameters
    )

    # 5. Ask Bifrost for reflection
    reflection = await gateway.route(
        prompt=f"Reflect on result: {tool_output}",
        strategy=RoutingStrategy.FAST_CHEAP
    )

    return {"plan": plan, "tool_output": tool_output, "reflection": reflection}
```

**Pattern 2: Direct Application Use (No Agent)**
```python
from bifrost import GatewayClient, RoutingStrategy

# Application using Bifrost for cost-optimized routing
gateway = GatewayClient(config)

# User request
result = await gateway.route(
    prompt=user_query,
    strategy=RoutingStrategy.COST_OPTIMIZED
)

# Execute with selected model
response = await llm_client.complete(
    model=result.model_id,
    prompt=user_query
)
```

**Pattern 3: SmartCP Standalone (MCP Server)**
```python
from smartcp import MCPServer

# Deploy MCP server independently
server = MCPServer(config)

@server.tool
async def my_tool(param: str) -> dict:
    return {"result": param}

await server.start()  # Runs as stdio or HTTP server
```

---

## 5. Migration Strategy

### 5.1 Phased Approach

**Phase 4A: Bifrost Core (Week 1-2)**
- Extract routing engine from router_core
- Create GatewayClient facade
- Implement RoutingStrategy enum
- Basic model routing working

**Phase 4B: Bifrost Advanced (Week 3-4)**
- Tool routing API
- Classification integration
- Cost optimization
- Metrics & observability
- Documentation & examples

**Phase 4.5A: SmartCP Core (Week 3-4, overlaps)**
- Consolidate MCP files
- Create MCPServer (stdio + HTTP)
- Tool registration & discovery
- Basic execution working

**Phase 4.5B: SmartCP Integration (Week 5)**
- Bifrost integration for tool routing
- Tool composition workflows
- Auth & security
- Documentation & examples

### 5.2 Backwards Compatibility Strategy

**Critical Decision: NO backwards compatibility**

**Rationale:**
- Fresh start, clean slate
- No legacy baggage
- Greenfield SDK design
- Agent-cli is new, no existing consumers

**Migration Path:**
```python
# Old code (router_core direct use)
from router_core.application.routing_service import RoutingService

service = RoutingService(...)  # Complex constructor
result = service.route(...)     # Internal types

# New code (Bifrost SDK)
from bifrost import GatewayClient

client = GatewayClient(config)  # Simple config
result = await client.route(...) # Stable public types
```

**No Shims, No Adapters:**
- Delete old code paths
- Update all callers simultaneously
- Document breaking changes
- Provide migration guide

### 5.3 Testing During Migration

**Strategy: Parallel Testing**

**Step 1: Extract with Tests**
```python
# Week 1: Extract routing engine
router_core/application/routing_service.py
    → bifrost/_internal/routing/engine.py
    + tests/test_routing_engine.py (extracted from router_core tests)
```

**Step 2: Test Both Old & New**
```python
# Week 2: Ensure parity
@pytest.mark.parametrize("implementation", ["old", "new"])
async def test_routing_parity(implementation):
    if implementation == "old":
        result = await old_routing_service.route(...)
    else:
        result = await new_gateway_client.route(...)

    # Same result
    assert result.model_id == expected_model
```

**Step 3: Remove Old**
```python
# Week 3: Delete old after new proven
rm -rf router_core/application/routing_service.py
# Update all imports to bifrost
```

---

## 6. Testing Strategy

### 6.1 Bifrost Testing

**Unit Tests:**
```python
# tests/bifrost/test_gateway_client.py
import pytest
from bifrost import GatewayClient, RoutingStrategy
from bifrost.testing.mocks import MockRoutingEngine

@pytest.fixture
def mock_client():
    config = GatewayConfig(api_key="test")
    client = GatewayClient(config)
    client._engine = MockRoutingEngine()  # Inject mock
    return client

async def test_cost_optimized_routing(mock_client):
    result = await mock_client.route(
        prompt="test",
        strategy=RoutingStrategy.COST_OPTIMIZED
    )
    assert result.model_id == "gpt-3.5-turbo"  # Cheapest
    assert result.strategy_used == "cost_optimized"

async def test_quality_routing(mock_client):
    result = await mock_client.route(
        prompt="complex code review",
        strategy=RoutingStrategy.QUALITY
    )
    assert result.model_id == "claude-sonnet-4"  # Best
    assert result.confidence > 0.9
```

**Integration Tests:**
```python
# tests/bifrost/integration/test_live_routing.py
@pytest.mark.integration
async def test_live_routing_cost_optimized():
    # Real config, real providers
    client = GatewayClient(real_config)

    result = await client.route(
        prompt="Quick question: what's 2+2?",
        strategy=RoutingStrategy.COST_OPTIMIZED
    )

    # Should route to cheapest model
    assert result.estimated_cost_usd < 0.001
    assert result.model_id in CHEAP_MODELS
```

**Performance Tests:**
```python
# tests/bifrost/performance/test_routing_latency.py
@pytest.mark.performance
async def test_routing_latency():
    client = GatewayClient(config)

    start = time.time()
    result = await client.route(prompt="test")
    latency_ms = (time.time() - start) * 1000

    # Routing should be fast (<50ms)
    assert latency_ms < 50
```

### 6.2 SmartCP Testing

**Unit Tests:**
```python
# tests/smartcp/test_server.py
import pytest
from smartcp import MCPServer, MCPConfig

@pytest.fixture
def server():
    config = MCPConfig(name="test", mode="stdio")
    return MCPServer(config)

async def test_tool_registration(server):
    @server.tool
    async def test_tool(x: int) -> int:
        return x * 2

    tools = await server.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "test_tool"

async def test_tool_execution(server):
    @server.tool
    async def add(a: int, b: int) -> int:
        return a + b

    result = await server.execute_tool("add", {"a": 2, "b": 3})
    assert result.output == 5
```

**Integration Tests:**
```python
# tests/smartcp/integration/test_stdio_protocol.py
@pytest.mark.integration
async def test_stdio_server():
    # Start server in subprocess
    proc = await asyncio.create_subprocess_exec(
        "python", "-m", "smartcp.server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE
    )

    # Send MCP commands
    proc.stdin.write(b'{"method": "list_tools"}\n')
    response = await proc.stdout.readline()

    # Verify response
    data = json.loads(response)
    assert "tools" in data
```

**End-to-End Tests:**
```python
# tests/integration/test_bifrost_smartcp.py
@pytest.mark.e2e
async def test_full_workflow():
    # Setup both SDKs
    gateway = GatewayClient(bifrost_config)
    tool_client = ToolClient(mcp_server_url)

    # Workflow: Bifrost routes tool, SmartCP executes
    action = "search for Python documentation"

    # 1. Bifrost recommends tool
    recommendation = await gateway.route_tool(
        action=action,
        available_tools=await tool_client.list_tools()
    )

    # 2. SmartCP executes
    result = await tool_client.execute_tool(
        tool_name=recommendation.tool_name,
        parameters=recommendation.parameters
    )

    # 3. Verify
    assert result.success
    assert "python" in result.output["results"][0].lower()
```

### 6.3 Test Coverage Goals

**Bifrost:**
- Unit: >90% coverage
- Integration: Key routing strategies tested with real providers
- Performance: Routing latency <50ms, classification <100ms
- Load: Handle 1000 req/s

**SmartCP:**
- Unit: >85% coverage
- Integration: Stdio + HTTP protocols tested
- Performance: Tool execution overhead <10ms
- Load: Handle 100 concurrent tool executions

---

## 7. Timeline & Milestones

### 7.1 Detailed Schedule

**Week 1: Bifrost Core Extraction**
- Day 1-2: Create bifrost/ package structure
- Day 3-4: Extract routing engine from router_core
- Day 5: GatewayClient facade, basic routing working
- **Milestone:** `await client.route(prompt)` works

**Week 2: Bifrost Strategies & Classification**
- Day 1-2: Implement RoutingStrategy variants
- Day 3-4: Extract classification logic
- Day 5: Cost estimation & optimization
- **Milestone:** All routing strategies functional

**Week 3: Bifrost Tool Routing & SmartCP Start**
- Day 1-2: Tool routing API (`route_tool`)
- Day 3-4: SmartCP package structure, consolidate MCP files
- Day 5: MCPServer stdio mode working
- **Milestone:** `await gateway.route_tool(...)` works
- **Milestone:** SmartCP server starts, registers tools

**Week 4: Bifrost Polish & SmartCP HTTP**
- Day 1-2: Bifrost metrics, observability, docs
- Day 3-4: SmartCP HTTP mode, auth integration
- Day 5: Tool composition workflows
- **Milestone:** Bifrost production-ready
- **Milestone:** SmartCP dual-protocol working

**Week 5: Integration & Testing**
- Day 1-2: Bifrost ↔ SmartCP integration
- Day 3-4: End-to-end testing
- Day 5: Documentation, examples, migration guide
- **Milestone:** Both SDKs production-ready, tested, documented

### 7.2 Milestones & Deliverables

**Milestone 1 (End Week 1): Bifrost Core**
- ✅ Package structure created
- ✅ GatewayClient working
- ✅ Basic routing (cost_optimized) functional
- ✅ Unit tests passing
- 📦 **Deliverable:** bifrost-0.1.0 (alpha)

**Milestone 2 (End Week 2): Bifrost Complete**
- ✅ All routing strategies implemented
- ✅ Classification integrated
- ✅ Cost optimization working
- ✅ Integration tests passing
- 📦 **Deliverable:** bifrost-0.2.0 (beta)

**Milestone 3 (End Week 3): SmartCP Core + Bifrost Tool Routing**
- ✅ Tool routing API (`route_tool`)
- ✅ SmartCP package structure
- ✅ MCPServer stdio mode
- ✅ Tool registration & discovery
- 📦 **Deliverable:** bifrost-0.3.0, smartcp-0.1.0 (alpha)

**Milestone 4 (End Week 4): Both SDKs Feature-Complete**
- ✅ Bifrost: metrics, docs, examples
- ✅ SmartCP: HTTP mode, auth, composition
- ✅ Both: integration tests passing
- 📦 **Deliverable:** bifrost-0.9.0, smartcp-0.9.0 (RC)

**Milestone 5 (End Week 5): Production-Ready**
- ✅ Full integration testing
- ✅ Documentation complete
- ✅ Migration guide
- ✅ Performance validated
- 📦 **Deliverable:** bifrost-1.0.0, smartcp-1.0.0 (GA)

### 7.3 Parallel Workstreams

**Weeks 1-2:** Bifrost only (serial)
**Weeks 3-4:** Bifrost + SmartCP (parallel)
**Week 5:** Integration (collaborative)

**Team Allocation:**
- 1 developer: Bifrost (weeks 1-5)
- 1 developer: SmartCP (weeks 3-5)
- Testing: Shared (week 5)

---

## 8. Risk Assessment

### 8.1 Technical Risks

**Risk 1: Scope Creep in router_core**
- **Impact:** HIGH
- **Probability:** MEDIUM
- **Description:** 359 files in router_core, unclear boundaries
- **Mitigation:**
  - Start with minimal extraction (routing engine only)
  - Incrementally add features
  - Strict API freeze after beta
  - Document what's NOT included

**Risk 2: Breaking Changes During Migration**
- **Impact:** MEDIUM
- **Probability:** LOW
- **Description:** Changing internal router_core during extraction
- **Mitigation:**
  - Freeze router_core changes during Phase 4
  - Parallel testing (old vs new)
  - Feature flag for gradual rollout

**Risk 3: Performance Regression**
- **Impact:** HIGH
- **Probability:** LOW
- **Description:** SDK abstraction adds latency
- **Mitigation:**
  - Performance benchmarks (routing <50ms)
  - Zero-copy where possible
  - Async/await throughout
  - Load testing before GA

**Risk 4: Incomplete MCP Consolidation**
- **Impact:** MEDIUM
- **Probability:** MEDIUM
- **Description:** MCP code scattered across many files
- **Mitigation:**
  - Comprehensive file audit (week 3)
  - Delete old code after migration
  - No backwards compatibility shims

**Risk 5: Bifrost-SmartCP Coupling**
- **Impact:** MEDIUM
- **Probability:** MEDIUM
- **Description:** SmartCP becomes dependent on Bifrost internals
- **Mitigation:**
  - Clear integration interface (`route_tool` only)
  - SmartCP optional Bifrost integration
  - Both SDKs independently usable

### 8.2 Schedule Risks

**Risk 6: Optimistic Timeline**
- **Impact:** HIGH
- **Probability:** MEDIUM
- **Description:** 4-5 weeks is aggressive for 359-file refactor
- **Mitigation:**
  - Buffer week built into estimate
  - Reduce scope if needed (defer metrics, advanced strategies)
  - Parallel workstreams (week 3-4)

**Risk 7: Testing Delays**
- **Impact:** MEDIUM
- **Probability:** MEDIUM
- **Description:** Integration testing might uncover issues
- **Mitigation:**
  - Start testing early (week 2)
  - Continuous integration
  - Dedicated testing week (week 5)

### 8.3 Product Risks

**Risk 8: Agent-CLI Blocked**
- **Impact:** CRITICAL
- **Probability:** LOW
- **Description:** SDKs not ready, agent-cli can't start
- **Mitigation:**
  - Weekly demos of SDK progress
  - Alpha releases for early feedback
  - Prioritize core functionality over polish

**Risk 9: Non-Agent Use Cases Neglected**
- **Impact:** MEDIUM
- **Probability:** MEDIUM
- **Description:** Focus on agent use cases, ignore general gateway use
- **Mitigation:**
  - Document non-agent examples
  - Test general routing scenarios
  - Validate with potential non-agent users

### 8.4 Mitigation Summary

| Risk | Impact | Prob | Mitigation Status |
|------|--------|------|-------------------|
| Scope Creep | HIGH | MED | ✅ Minimal extraction plan |
| Breaking Changes | MED | LOW | ✅ Parallel testing |
| Performance | HIGH | LOW | ✅ Benchmarks defined |
| MCP Consolidation | MED | MED | ⚠️ Needs file audit |
| SDK Coupling | MED | MED | ✅ Clear integration interface |
| Optimistic Timeline | HIGH | MED | ⚠️ Buffer week, scope reduction plan |
| Testing Delays | MED | MED | ✅ Early testing, CI |
| Agent-CLI Blocked | CRIT | LOW | ✅ Weekly demos, alpha releases |
| Non-Agent Neglect | MED | MED | ⚠️ Needs validation |

---

## 9. Success Criteria

### 9.1 Functional Requirements

**Bifrost SDK:**
- ✅ `GatewayClient.route()` routes to optimal model
- ✅ `GatewayClient.route_tool()` recommends tool
- ✅ `GatewayClient.classify()` detects intent
- ✅ All `RoutingStrategy` variants working
- ✅ Cost estimation accurate (±10%)
- ✅ Provider fallback automatic
- ✅ Streaming support for long responses
- ✅ Batch routing for multiple requests

**SmartCP SDK:**
- ✅ `MCPServer.start()` runs stdio server
- ✅ `MCPServer.start()` runs HTTP server
- ✅ Tool registration via decorator
- ✅ Tool discovery (list_tools)
- ✅ Tool execution with parameter validation
- ✅ Tool composition (multi-tool workflows)
- ✅ Auth integration (JWT, API key)
- ✅ Bifrost integration for tool routing

### 9.2 Non-Functional Requirements

**Performance:**
- ✅ Routing latency <50ms (p95)
- ✅ Classification latency <100ms (p95)
- ✅ Tool execution overhead <10ms
- ✅ Handle 1000 req/s (Bifrost)
- ✅ Handle 100 concurrent tools (SmartCP)

**Quality:**
- ✅ >90% unit test coverage (Bifrost)
- ✅ >85% unit test coverage (SmartCP)
- ✅ All integration tests passing
- ✅ Performance benchmarks passing
- ✅ Zero critical bugs in beta

**Documentation:**
- ✅ API reference (auto-generated)
- ✅ Quickstart guide
- ✅ Strategy guide (Bifrost)
- ✅ Tool development guide (SmartCP)
- ✅ 5+ examples per SDK
- ✅ Migration guide from router_core

**Developer Experience:**
- ✅ `pip install bifrost` works
- ✅ `pip install smartcp` works
- ✅ Hello World in <10 lines
- ✅ Type hints throughout
- ✅ Clear error messages
- ✅ Works with Python 3.10+

### 9.3 Acceptance Criteria

**Phase 4 Complete (Bifrost):**
```python
# This code works, is tested, and documented
from bifrost import GatewayClient, RoutingStrategy

client = GatewayClient(config)

# Model routing
result = await client.route(
    prompt="Analyze this code",
    strategy=RoutingStrategy.COST_OPTIMIZED
)

# Tool routing
tool = await client.route_tool(
    action="search web",
    available_tools=["web_search", "browser"]
)

# Classification
classification = await client.classify(prompt="...")

# Streaming
async for chunk in client.stream(prompt="..."):
    print(chunk.content)
```

**Phase 4.5 Complete (SmartCP):**
```python
# This code works, is tested, and documented
from smartcp import MCPServer, ToolClient

# Server
server = MCPServer(config)

@server.tool
async def my_tool(param: str) -> dict:
    return {"result": param}

await server.start()

# Client
client = ToolClient(server_url)
result = await client.execute_tool("my_tool", {"param": "test"})
```

**Integration Complete:**
```python
# This works end-to-end
from bifrost import GatewayClient
from smartcp import ToolClient

gateway = GatewayClient(bifrost_config)
tool_client = ToolClient(mcp_server_url)

# Bifrost routes tool
recommendation = await gateway.route_tool(
    action="search web",
    available_tools=await tool_client.list_tools()
)

# SmartCP executes
result = await tool_client.execute_tool(
    tool_name=recommendation.tool_name,
    parameters=recommendation.parameters
)
```

### 9.4 Go/No-Go Criteria for Agent-CLI

**Agent-CLI can start Phase 5 when:**
- ✅ Bifrost 1.0.0 released (GA)
- ✅ SmartCP 1.0.0 released (GA)
- ✅ All acceptance criteria met
- ✅ Performance benchmarks passing
- ✅ Integration tests passing
- ✅ Documentation complete
- ✅ Migration guide published
- ✅ Zero critical bugs

**If not met by Week 5:**
- ⚠️ Release 0.9 (RC) with known limitations
- ⚠️ Agent-CLI starts with RC, accepts instability
- ⚠️ Commit to 1.0 within 2 weeks

---

## 10. Next Steps

### 10.1 Immediate Actions (This Week)

**Day 1-2:**
- [ ] Create bifrost/ package skeleton
- [ ] Create smartcp/ package skeleton
- [ ] Set up CI/CD for both SDKs
- [ ] Create GitHub repos (or monorepo structure)

**Day 3-4:**
- [ ] Audit router_core/ (identify extraction targets)
- [ ] Audit MCP files (consolidation targets)
- [ ] Write migration plan (detailed file mapping)
- [ ] Set up testing framework

**Day 5:**
- [ ] Kick off Week 1 extraction (routing engine)
- [ ] Create project tracking (Milestone 1 tasks)
- [ ] Schedule weekly demos

### 10.2 Decision Points

**Week 1 End:**
- ✅ Is GatewayClient.route() working?
- ❌ If no: reduce scope, focus on single strategy

**Week 2 End:**
- ✅ Are all strategies working?
- ❌ If no: defer advanced strategies (ensemble, adaptive)

**Week 3 End:**
- ✅ Is tool routing working?
- ✅ Is SmartCP server starting?
- ❌ If no: extend timeline, shift agent-cli start

**Week 4 End:**
- ✅ Are both SDKs feature-complete?
- ❌ If no: cut features, focus on core

**Week 5 End:**
- ✅ Are all tests passing?
- ✅ Is documentation complete?
- ❌ If no: release RC, delay 1.0

### 10.3 Open Questions

**For Product Team:**
1. Are there non-agent use cases we must support? (web app routing, CLI tools, etc.)
2. What's minimum viable feature set for Bifrost 1.0?
3. Can we defer metrics/observability to 1.1?
4. Should SDKs be separate repos or monorepo?

**For Engineering:**
1. How to version SDKs independently?
2. Should we support Python 3.9 or only 3.10+?
3. What's the deprecation policy for breaking changes?
4. How to handle provider API changes (OpenRouter, etc.)?

**For Testing:**
1. Do we need load testing before 1.0?
2. What's acceptable performance regression vs current?
3. Should we test on Mac M1, Linux, Windows?

---

## Appendices

### A. File Mapping (router_core → bifrost)

```
router_core/application/routing_service.py
    → bifrost/_internal/routing/engine.py

router_core/classification/unified_classifier.py
    → bifrost/_internal/classification/classifier.py

router_core/cost/estimator.py
    → bifrost/_internal/cost/estimator.py

router_core/routing/registry.py
    → bifrost/_internal/routing/registry.py

router_core/routing/routellm_router.py
    → bifrost/_internal/routing/strategies/routellm.py

router_core/adapters/providers/
    → bifrost/_internal/adapters/

router_core/metrics/
    → bifrost/_internal/metrics/

router_core/domain/
    → bifrost/_internal/types/ (internal types)
```

### B. MCP File Consolidation

```
mcp_registry.py
mcp_server_discovery.py
mcp_lifecycle_manager.py
    → smartcp/_internal/registry/

mcp_tool_composer.py
    → smartcp/_internal/execution/composition.py

mcp_inference_bridge.py
    → DELETE (use Bifrost integration instead)

fastmcp_auth_provider.py
    → smartcp/_internal/auth/provider.py

router_core/mcp/mcp_tool_router.py
    → DELETE (move to Bifrost)

router_core/mcp/mcp_tools_registry.py
    → smartcp/_internal/registry/tool_registry.py
```

### C. Example Projects

**Bifrost Examples:**
1. Cost-optimized chat application
2. Quality-focused code review
3. Multi-strategy AB testing
4. Budget-aware API gateway
5. Provider failover demo

**SmartCP Examples:**
1. File operations MCP server
2. Web search MCP server
3. HTTP MCP server with auth
4. Multi-tool workflow demo
5. Bifrost integration demo

### D. References

- FastMCP Documentation: https://github.com/jlowin/fastmcp
- MCP Specification: https://spec.modelcontextprotocol.io/
- OpenRouter API: https://openrouter.ai/docs
- Anthropic SDK: https://github.com/anthropics/anthropic-sdk-python
- Pydantic: https://docs.pydantic.dev/

---

**Document Status:** DRAFT v1.0
**Last Updated:** 2025-12-02
**Next Review:** After Week 1 (routing engine extraction complete)
