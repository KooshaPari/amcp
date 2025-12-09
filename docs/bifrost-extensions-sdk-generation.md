# Bifrost Extensions - SDK Code Generation Pipeline

**Status**: Planning Phase
**Owner**: SmartCP Team
**Target**: Post-Phase 5.1

---

## Vision

Once `bifrost_extensions` is stable and production-ready, create an automated code generation pipeline that produces multi-language SDKs from a canonical source:

```
bifrost_extensions/ (Python)
    ↓ Extract API schema
    ↓ Generate via OpenAPI/GraphQL schema
    ├→ Python SDK (pip)
    ├→ Go SDK (pkg.go.dev)
    ├→ Rust SDK (crates.io)
    ├→ TypeScript/JavaScript SDK (npm)
    └→ (More languages as needed)
```

---

## Current State

**bifrost_extensions** (Python):
- Exports: `GatewayClient`, `RoutingStrategy`, Models, Exceptions
- Location: `bifrost_extensions/client/gateway.py`
- Status: Phase 4, Week 1+ (development ongoing)
- Dependencies: router_core, pydantic, opentelemetry, httpx

**What it does**:
- Model routing (cost/performance/speed optimized)
- Tool routing
- Classification
- Usage tracking
- Circuit breaker, retry, rate limiting

---

## Implementation Strategy

### Phase 1: Stabilize & Document (Weeks 1-2)

1. **API Stability**
   - Lock down `GatewayClient` interface
   - Finalize request/response models in `bifrost_extensions/models.py`
   - Ensure backwards compatibility commitment

2. **Generate OpenAPI/GraphQL Schema**
   ```bash
   # From Pydantic models
   python scripts/generate_schema.py bifrost_extensions/ > bifrost-extensions-schema.openapi.json

   # Or GraphQL schema
   python scripts/generate_graphql_schema.py bifrost_extensions/ > bifrost-extensions.graphql
   ```

3. **Document Public API**
   - Create `docs/API_REFERENCE.md` with:
     - All public classes and methods
     - Request/response examples
     - Error codes
     - Rate limits
     - Authentication flows

### Phase 2: Set Up Code Generation (Weeks 3-4)

1. **Choose Generation Framework**

   **Option A: OpenAPI Generator** (Recommended)
   ```bash
   # Supports Python, Go, Rust, TypeScript/JavaScript, Ruby, PHP, etc.
   npx @openapitools/openapi-generator-cli generate \
     -i bifrost-extensions-schema.openapi.json \
     -g python \
     -o sdks/python
   ```

   **Option B: Smithy** (AWS-style)
   - More opinionated, better for RPC-style APIs
   - Good for multi-service ecosystems

   **Option C: Custom Codegen** (if API is too specialized)
   - Jinja2 templates + Python for full control
   - Best if API doesn't fit standard OpenAPI/GraphQL

2. **Directory Structure**
   ```
   bifrost-extensions/
   ├── python/        # bifrost-extensions on PyPI
   ├── go/           # github.com/YOUR_ORG/bifrost-extensions-go
   ├── rust/         # bifrost-extensions on crates.io
   ├── typescript/   # @yourorg/bifrost-extensions on npm
   ├── codegen/      # Templates and generation scripts
   └── Makefile      # make generate-all
   ```

3. **CI/CD Pipeline**
   ```yaml
   # .github/workflows/generate-sdks.yml
   on:
     push:
       paths:
         - 'bifrost_extensions/**'
         - 'docs/API_REFERENCE.md'
         - 'codegen/**'

   jobs:
     generate:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Generate SDKs
           run: make generate-all
         - name: Push to SDK repos
           run: |
             git -C sdks/python push origin main
             git -C sdks/go push origin main
             git -C sdks/rust push origin main
             git -C sdks/typescript push origin main
   ```

### Phase 3: Release & Distribution (Weeks 5-6)

1. **Python SDK** (PyPI)
   ```bash
   # sdks/python/setup.py
   python -m build
   twine upload dist/*
   ```

2. **Go SDK** (pkg.go.dev)
   ```go
   // Go modules auto-discovery
   // Push to GitHub, pkg.go.dev auto-indexes
   go get github.com/YOUR_ORG/bifrost-extensions-go@latest
   ```

3. **Rust SDK** (crates.io)
   ```bash
   cargo publish
   ```

4. **TypeScript SDK** (npm)
   ```bash
   npm publish
   ```

---

## Schema Definition Strategy

### Option 1: Generate from Python (Recommended for now)

```python
# scripts/generate_schema.py
from bifrost_extensions.models import (
    GatewayClient,
    RoutingRequest,
    RoutingResponse,
    RoutingStrategy,
)
from pydantic.json_schema import model_json_schema

# Generate OpenAPI from Pydantic models
schema = {
    "openapi": "3.1.0",
    "info": {
        "title": "Bifrost Extensions API",
        "version": "1.0.0"
    },
    "paths": {
        "/route": {
            "post": {
                "requestBody": model_json_schema(RoutingRequest),
                "responses": {
                    "200": model_json_schema(RoutingResponse)
                }
            }
        }
    }
}
```

### Option 2: Manual GraphQL Schema (Future)

```graphql
# bifrost-extensions.graphql
type Query {
  # Health check
  health: HealthStatus!
}

type Mutation {
  # Route request to optimal model
  route(request: RoutingRequestInput!): RoutingResponse!

  # Route tool selection
  routeTool(action: String!, tools: [String!]!): ToolRoutingDecision!

  # Classify prompt
  classify(prompt: String!): ClassificationResult!
}

input RoutingRequestInput {
  messages: [Message!]!
  strategy: RoutingStrategy!
  constraints: JSON
}

enum RoutingStrategy {
  COST_OPTIMIZED
  PERFORMANCE_OPTIMIZED
  SPEED_OPTIMIZED
  BALANCED
  PARETO
}

type RoutingResponse {
  model: ModelInfo!
  confidence: Float!
  reasoning: String
}
```

---

## Generated SDK Features (by Language)

### Python
```python
from bifrost_extensions import GatewayClient, RoutingStrategy

client = GatewayClient(api_key="...")
response = await client.route(
    messages=[{"role": "user", "content": "..."}],
    strategy=RoutingStrategy.COST_OPTIMIZED
)
```

### Go
```go
import "github.com/YOUR_ORG/bifrost-extensions-go"

client := bifrostextensions.NewGatewayClient("api_key")
response, err := client.Route(ctx, &bifrostextensions.RoutingRequest{
    Messages: [...],
    Strategy: bifrostextensions.RoutingStrategyCostOptimized,
})
```

### Rust
```rust
use bifrost_extensions::GatewayClient;

let client = GatewayClient::new("api_key")?;
let response = client.route(&RoutingRequest {
    messages: vec![...],
    strategy: RoutingStrategy::CostOptimized,
}).await?;
```

### TypeScript
```typescript
import { GatewayClient, RoutingStrategy } from "@yourorg/bifrost-extensions";

const client = new GatewayClient({ apiKey: "..." });
const response = await client.route({
  messages: [...],
  strategy: RoutingStrategy.CostOptimized,
});
```

---

## Dependencies & Tools

| Tool | Purpose | Status |
|------|---------|--------|
| OpenAPI Generator | Multi-language code generation | ✅ Available |
| Pydantic JSON Schema | Python → OpenAPI | ✅ Native |
| OpenAPI Spec 3.1 | Standard API definition | ✅ Stable |
| GitHub Actions | CI/CD for generation | ✅ Available |
| PyPI, npm, crates.io | Package hosting | ✅ Available |

---

## Timeline

- **Week 1-2**: Stabilize API, generate schema
- **Week 3-4**: Set up code generation, create templates
- **Week 5-6**: Generate SDKs, release to package registries
- **Week 7+**: Maintain SDKs, respond to feedback

**Total**: ~7 weeks to production SDKs in 4 languages

---

## Recommendations

1. **Start with Python + TypeScript**
   - Python: Internal use, can auto-update from canonical
   - TypeScript: Web/Node.js clients, fastest to market

2. **Use OpenAPI 3.1 as canonical format**
   - Most tool support
   - Easy to generate Pydantic models from it
   - Standard in industry

3. **Automate generation in CI/CD**
   - On every schema change, regenerate and test SDKs
   - Auto-publish to registries when version bumped

4. **Maintain breaking change policy**
   - Semantic versioning across all SDKs
   - Changelog consistency
   - Deprecation warnings before breaking changes

5. **Create SDK-specific documentation**
   - Language-specific quickstarts
   - Error handling patterns per language
   - Examples for common use cases

---

## References

- OpenAPI Generator: https://openapi-generator.tech/
- Pydantic JSON Schema: https://docs.pydantic.dev/latest/concepts/json_schema/
- Smithy: https://smithy.io/
- Go pkg.go.dev: https://pkg.go.dev/
- npm: https://www.npmjs.com/
- crates.io: https://crates.io/

