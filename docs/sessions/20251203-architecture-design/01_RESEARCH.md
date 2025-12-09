# Architecture Research - SmartCP 3-Microservice Platform

**Session Date:** December 3, 2024
**Research Focus:** Polyglot microservices architecture for vibeproxy + smartcp + bifrost

---

## Research Questions

### 1. FastMCP + Go Interoperability

**Question:** Can FastMCP (Python ASGI) mount to Gin/Echo (Go)?

**Findings:**
- **NO direct mounting possible**
- FastMCP is ASGI-specific (Python web framework standard)
- Go frameworks (Gin/Echo) don't support Python ASGI applications natively
- **Solution:** Run as separate services, communicate via HTTP/gRPC

**Sources:**
- [FastMCP ASGI Mounting](https://github.com/dwayn/fastmcp-mount)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP Guide](https://gofastmcp.com/deployment/running-server)

**Architectural Implication:**
- SmartCP (FastMCP/Python) MUST run as standalone service
- Cannot be embedded in Go vibeproxy
- Inter-service communication via HTTP REST or gRPC

---

### 2. Bifrost vs LiteLLM

**Question:** Should we keep bifrost (88k LOC Python) or migrate to LiteLLM?

#### Bifrost Current State
- **197,219 LOC** total (not 88k - that was router_core subdirectory)
- Custom router implementation
- GraphQL + HTTP/2 architecture
- Significant investment in codebase

#### LiteLLM Features & Performance
- **Open-source Python SDK + Proxy Server**
- Supports 100+ LLM APIs in OpenAI format
- 28,800+ GitHub stars, active development

**Performance:**
- LiteLLM: 8ms P95 latency @ 1k RPS
- **But:** Python overhead = 25-100x slower than Rust alternatives
- **Throughput:** Lower than Go/Rust gateways

**Routing Features:**
- Advanced strategies: latency-based, usage-based, cost-based
- Custom routing algorithm support
- Load balancing + retries + fallbacks
- Budget management per project/team/API key

**Observability:**
- Pre-built integrations: Lunary, MLflow, Langfuse, Helicone, etc.
- Detailed monitoring + usage tracking

**Deployment:**
- Self-hosted (open-source, free)
- 15-30 min setup with YAML config

#### Decision Factors

**Keep Bifrost IF:**
- Custom routing logic NOT achievable via LiteLLM config
- Ultra-low latency required (<1ms)
- Existing features not in LiteLLM
- GraphQL architecture is critical

**Migrate to LiteLLM IF:**
- Want production-grade features out-of-box
- Routing logic configurable (not custom code)
- Willing to accept Python performance trade-offs
- Want broader provider support (100+ APIs)
- Need GitOps integration

**Recommendation:** **HYBRID APPROACH**
- Keep bifrost_ml for ML/classification (specialized)
- Add LiteLLM for routing + provider management
- Use bifrost as smart layer on top of LiteLLM

**Sources:**
- [LiteLLM vs OpenRouter](https://xenoss.io/blog/openrouter-vs-litellm)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [Top LLM Gateways 2025](https://www.helicone.ai/blog/top-llm-gateways-comparison-2025)

---

### 3. Free Tier Hosting Analysis

#### Vercel (Serverless)

**Limits:**
- **Execution time:** 10 seconds per function (Free tier)
- **Function size:** 250MB unzipped max
- **Environment vars:** 64KB total
- **Python versions:** 3.12 (default), 3.9 (legacy)
- **Cold starts:** Yes, for infrequent traffic

**Best For:**
- Lightweight API endpoints
- Short-running processes (<10s)
- Frontend + simple backend
- **NOT for:** Long-running tasks, heavy compute

**Sources:**
- [Vercel Limits](https://vercel.com/docs/limits)
- [FastAPI on Vercel](https://dev.to/abdadeel/deploying-fastapi-app-on-vercel-serverless-18b1)

#### Render.com (Container-based)

**Free Tier:**
- **512MB RAM / 0.1 CPU**
- **Auto-sleep:** After 15 min inactivity
- **Cold start:** 2-3 minutes to wake up
- **PostgreSQL:** Free but expires after 90 days

**Best For:**
- Full Python applications
- FastAPI services
- Background tasks
- **Workaround:** Self-health checks to prevent sleep

**Sources:**
- [Render Free Tier Guide](https://dashdashhard.com/posts/ultimate-guide-to-renders-free-tier/)
- [Keep FastAPI Active on Render](https://medium.com/@saveriomazza/how-to-keep-your-fastapi-server-active-on-renders-free-tier-93767b70365c)

#### Fly.io

**Free Tier:**
- 256MB RAM free
- Better cold start than Render (~5-10s)
- More flexible scaling

#### GCP Cloud Run

**Free Tier:**
- 180,000 vCPU-seconds/month
- 360,000 GiB-seconds/month
- 2 million requests/month
- **Cold start:** 1-3 seconds

**Best For:**
- Production-grade serverless
- Autoscaling
- Container deployments

---

### 4. Polyglot Language Justification

#### When Python is Best
- **ML/AI workloads** (ecosystem: PyTorch, TensorFlow, scikit-learn)
- **Rapid prototyping** (fast development cycles)
- **Data processing** (Pandas, NumPy)
- **FastMCP integration** (required for MCP server)

#### When Go is Best
- **API gateways** (2.5-3.6x faster than Python)
- **Proxy servers** (handles 10k+ concurrent connections)
- **High RPS services** (20k+ req/s possible)
- **Low memory footprint**
- **Fast compilation** (seconds vs minutes for Nuitka)

#### When Rust is Best
- **Hot paths** (25-100x faster than Python)
- **Systems programming**
- **Maximum throughput** (vs Python gateways)
- **Minimal latency** (<1ms vs 8ms+ for Python)

#### Protocol Performance Comparison

**gRPC (Best Performance):**
- Fastest response time
- HTTP/2 transport
- Binary serialization
- **Best for:** Service-to-service (vibeproxy ↔ smartcp ↔ bifrost)

**REST (Most Compatible):**
- Simple, widely supported
- Good for 100-500 req/s
- **Best for:** External APIs, client ↔ host

**GraphQL:**
- 94% smaller responses (partial field selection)
- Better for complex queries
- Higher CPU usage vs gRPC/REST
- **Best for:** bifrost (existing architecture)

**Sources:**
- [gRPC vs REST vs GraphQL 2024](https://www.designgurus.io/blog/rest-graphql-grpc-system-design)
- [Go vs Python Benchmarks 2024](https://www.augmentedmind.de/2024/07/14/go-vs-python-performance-benchmark/)
- [API Gateway Performance](https://medium.com/code-beyond/api-gateway-performance-benchmark-407500194c76)

---

### 5. Compiled Python Analysis

#### Nuitka

**Performance Gains:**
- 20-30% speedup typical (4s → 3s example)
- Converts Python → C → binary
- Optimizes memory usage

**Trade-offs:**
- **Slow builds:** ~30 min on GitHub Actions
- Requires C compiler
- Not as fast as native Go/Rust

#### PyOxidizer

**Status:**
- **No longer actively maintained** (as of 2024)
- Bundles Python into binaries
- Faster imports (memory vs filesystem)

**Recommendation:**
- **Avoid PyOxidizer** (unmaintained)
- **Use Nuitka sparingly** (slow builds, modest gains)
- **Better:** Keep Python + optimize hot paths with Go

**Sources:**
- [Nuitka Performance 2024](https://medium.com/top-python-libraries/nuitka-boost-python-speed-secure-code-via-binary-compilation-f87f83b078f2)
- [PyOxidizer Comparisons](https://pyoxidizer.readthedocs.io/en/stable/pyoxidizer_comparisons.html)

---

## Key Architectural Insights

### 1. No Cross-Language Mounting
- FastMCP cannot mount to Go frameworks
- Run services separately, communicate via network protocols

### 2. Go Wins for Gateway/Proxy
- 2.5-3.6x faster than Python
- 10k+ concurrent connections vs 2k for Python
- Perfect for vibeproxy (client proxy)

### 3. Python Required for SmartCP
- FastMCP is Python-only
- Keep logic minimal, delegate to bifrost

### 4. Bifrost Hybrid Approach
- Keep custom ML/routing
- Consider LiteLLM for provider management
- GraphQL for flexibility

### 5. Free Tier Strategy
- **Vercel:** Frontend + lightweight APIs (<10s)
- **Render:** SmartCP (FastMCP server)
- **GCP Run:** Bifrost (if autoscaling needed)
- **Client:** vibeproxy (local/moving device)

---

## Research Conclusions

**Language per Service:**
- **vibeproxy:** Go (proxy, gateway, high concurrency)
- **smartcp:** Python (FastMCP requirement)
- **bifrost:** Python (keep existing, add LiteLLM)

**Protocol per Connection:**
- **vibeproxy ↔ smartcp:** gRPC (performance)
- **smartcp ↔ bifrost:** GraphQL (existing arch)
- **Client ↔ vibeproxy:** REST (compatibility)

**Deployment:**
- **vibeproxy:** Local/device (compiled Go binary)
- **smartcp:** Render.com free tier (512MB, FastAPI)
- **bifrost:** GCP Run or Render (container)

**Bifrost Decision:**
- Keep existing codebase (197k LOC investment)
- Add LiteLLM as optional routing layer
- Hybrid: bifrost_ml + LiteLLM + custom logic
