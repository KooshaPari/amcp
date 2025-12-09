# SmartCP SDK Documentation

Complete documentation for SmartCP SDKs and APIs.

## Available SDKs

### [Bifrost Extensions SDK](./bifrost/)

Production-grade Python SDK for intelligent LLM routing, tool routing, and cost optimization.

**Status:** ✅ v1.0-alpha - Production Ready

**Features:**
- Model routing with 5 optimization strategies
- Cost and latency constraints
- Multi-tenant support
- OpenTelemetry integration
- Full type safety with Pydantic

**Quick Start:**
```python
from bifrost_extensions import GatewayClient, RoutingStrategy

client = GatewayClient()
response = await client.route(
    messages=[{"role": "user", "content": "Hello"}],
    strategy=RoutingStrategy.COST_OPTIMIZED
)
```

**Documentation:**
- [Quick Start & README](./bifrost/README.md)
- [Complete API Reference](./bifrost/api-reference.md)
- [Integration Guide](./bifrost/integration-guide.md) (FastAPI, Flask, Django, etc.)
- [Architecture & Design](./bifrost/architecture.md)
- [Examples](./bifrost/examples/)
- [OpenAPI Specification](./openapi/bifrost-api.yaml)

---

### [SmartCP SDK](./smartcp/)

**Status:** ⏳ Coming Soon - Documentation In Progress

FastMCP-based SDK for building MCP servers and tools.

**Planned Features:**
- MCP protocol integration
- Tool development framework
- BifrostClient integration
- GraphQL schema support
- Security and sandboxing

**Documentation (Planned):**
- MCP Protocol Guide
- Tool Development Guide
- FastMCP Server Setup
- BifrostClient Integration
- Security Best Practices

---

## OpenAPI Specifications

| API | Version | Status | Documentation |
|-----|---------|--------|---------------|
| [Bifrost API](./openapi/bifrost-api.yaml) | 1.0.0-alpha | ✅ Complete | OpenAPI 3.1 with examples |
| SmartCP MCP API | - | ⏳ Planned | Coming soon |

---

## Getting Started

### 1. Choose Your SDK

- **Bifrost Extensions**: For LLM routing and optimization → [Get Started](./bifrost/README.md)
- **SmartCP SDK**: For MCP server development → Coming Soon

### 2. Installation

```bash
# Bifrost Extensions
pip install bifrost-extensions  # Production (when published)
pip install -e .                 # Development

# SmartCP SDK
pip install smartcp-sdk          # Coming soon
```

### 3. First Steps

**Bifrost Extensions:**
1. [Quick Start](./bifrost/README.md#quick-start)
2. [Basic Examples](./bifrost/examples/01-basic-routing.md)
3. [Integration Guide](./bifrost/integration-guide.md)

**SmartCP SDK:**
- Documentation coming soon

---

## Documentation Structure

```
docs/sdk/
├── README.md                    # This file
├── bifrost/                     # Bifrost Extensions SDK
│   ├── README.md                # Main documentation
│   ├── api-reference.md         # Complete API reference
│   ├── integration-guide.md     # Framework integrations
│   ├── architecture.md          # System architecture
│   └── examples/                # Code examples
│       ├── 01-basic-routing.md
│       ├── 02-advanced-routing.md
│       ├── 03-tool-routing.md
│       └── 04-cost-optimization.md
├── smartcp/                     # SmartCP SDK (coming soon)
│   ├── README.md
│   ├── mcp-protocol.md
│   ├── tool-development.md
│   └── bifrost-integration.md
└── openapi/                     # OpenAPI specifications
    ├── bifrost-api.yaml
    └── smartcp-mcp.yaml
```

---

## Key Features by SDK

### Bifrost Extensions

| Feature | Status | Documentation |
|---------|--------|---------------|
| Model Routing | ✅ v1.0 | [API Reference](./bifrost/api-reference.md#route) |
| Tool Routing | ⏳ v1.1 | [API Reference](./bifrost/api-reference.md#route_tool) |
| Classification | ⏳ v1.1 | [API Reference](./bifrost/api-reference.md#classify) |
| Usage Tracking | ⏳ v1.2 | [API Reference](./bifrost/api-reference.md#get_usage) |
| Cost Optimization | ✅ v1.0 | [Examples](./bifrost/examples/) |
| Multi-Tenant | ✅ v1.0 | [Integration Guide](./bifrost/integration-guide.md#multi-tenant-applications) |

### SmartCP SDK

| Feature | Status | Documentation |
|---------|--------|---------------|
| MCP Protocol | ⏳ Planned | Coming soon |
| Tool Development | ⏳ Planned | Coming soon |
| FastMCP Integration | ⏳ Planned | Coming soon |
| GraphQL Schema | ⏳ Planned | Coming soon |
| Security Sandboxing | ⏳ Planned | Coming soon |

---

## Integration Examples

### Bifrost with FastAPI

```python
from fastapi import FastAPI, Depends
from bifrost_extensions import GatewayClient, RoutingStrategy

app = FastAPI()

def get_client() -> GatewayClient:
    return GatewayClient()

@app.post("/chat")
async def chat(
    messages: list[dict],
    client: GatewayClient = Depends(get_client)
):
    response = await client.route(
        messages=messages,
        strategy=RoutingStrategy.BALANCED
    )
    return {
        "model": response.model.model_id,
        "cost": response.model.estimated_cost_usd
    }
```

[More Examples →](./bifrost/integration-guide.md)

---

## API References

### Bifrost Extensions API

- **Base URL**: `https://api.bifrost.ai`
- **Authentication**: Bearer token
- **Version**: 1.0.0-alpha

**Endpoints:**
- `POST /v1/route` - Route to optimal model
- `POST /v1/route/tool` - Route to optimal tool
- `POST /v1/classify` - Classify prompt
- `GET /v1/usage` - Get usage statistics
- `GET /v1/health` - Health check

[Full OpenAPI Spec →](./openapi/bifrost-api.yaml)

---

## Support & Resources

### Documentation
- **Bifrost Extensions**: [Complete Guide](./bifrost/)
- **SmartCP SDK**: Coming Soon
- **API Reference**: [OpenAPI Specs](./openapi/)

### Community
- **GitHub Issues**: [Report bugs](https://github.com/yourorg/bifrost-extensions/issues)
- **Discussions**: [Ask questions](https://github.com/yourorg/bifrost-extensions/discussions)
- **Discord**: [Join community](https://discord.gg/smartcp)

### Development
- **Contributing**: See [CLAUDE.md](../../CLAUDE.md)
- **Changelog**: See individual SDK README files
- **Roadmap**: [GitHub Projects](https://github.com/yourorg/bifrost-extensions/projects)

---

## Version Matrix

| SDK | Version | Python | Status | Release Date |
|-----|---------|--------|--------|--------------|
| Bifrost Extensions | 1.0.0-alpha | 3.10+ | ✅ Active | 2025-12-02 |
| Bifrost Extensions | 1.1.0-beta | 3.10+ | ⏳ Planned | Q1 2026 |
| Bifrost Extensions | 1.2.0 | 3.10+ | ⏳ Planned | Q2 2026 |
| SmartCP SDK | - | 3.10+ | ⏳ Planned | TBD |

---

## Quick Navigation

**By Use Case:**
- [I want to optimize LLM costs](./bifrost/examples/04-cost-optimization.md)
- [I need to integrate with FastAPI](./bifrost/integration-guide.md#fastapi-integration)
- [I want to build MCP tools](./smartcp/) (coming soon)
- [I need to track usage](./bifrost/api-reference.md#get_usage)

**By Role:**
- [Developers](./bifrost/README.md#quick-start)
- [Architects](./bifrost/architecture.md)
- [DevOps](./bifrost/integration-guide.md#deployment-patterns)
- [Product Managers](./bifrost/README.md#features)

---

## License

All SDKs are released under the MIT License. See individual SDK directories for details.

---

## Updates

This documentation is actively maintained. Last updated: 2025-12-02

For the latest documentation, visit our [GitHub repository](https://github.com/yourorg/smartcp).
