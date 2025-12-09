# Session Overview: Bifrost Business Logic Extraction

**Date:** 2025-12-02
**Goal:** Extract business logic from SmartCP MCP frontend and move it to Bifrost backend

## Objectives

1. **Identify ALL business logic in SmartCP** (~13,498 LOC currently)
   - Tool routing logic (ArchRouter)
   - Semantic search and discovery
   - ML/classification (MLX integration)
   - Direct database access (PostgreSQL, Memgraph, Qdrant, Valkey)
   - Tool registry management

2. **Design Bifrost GraphQL API**
   - Create comprehensive GraphQL schema
   - Design queries, mutations, subscriptions
   - Document inputs/outputs and contracts

3. **Move logic to Bifrost (Go backend)**
   - Implement routing service
   - Implement search/discovery service
   - Implement ML classification service
   - Implement tool registry service
   - Wire to existing router_core

4. **Refactor SmartCP to thin MCP frontend**
   - Replace local logic with BifrostClient GraphQL calls
   - Remove database dependencies
   - Remove ML dependencies
   - Target: <1000 LOC total

5. **Verify delegation and testing**
   - All SmartCP operations delegate to Bifrost
   - No business logic remains in SmartCP
   - Tests pass with new architecture
   - Performance maintained or improved

## Success Criteria

- [ ] SmartCP LOC <1000 (excluding tests)
- [ ] All intelligence moved to Bifrost backend
- [ ] GraphQL API working correctly
- [ ] No regression in functionality
- [ ] Tests passing
- [ ] Documentation updated

## Key Decisions

### Architecture Pattern
**Decision:** Use GraphQL for SmartCP ↔ Bifrost communication
**Rationale:**
- Already have GraphQL subscription client in SmartCP
- Supports queries, mutations, subscriptions
- Type-safe schema
- Better than REST for complex data requirements
- Supports real-time updates via subscriptions

### Service Decomposition
**Decision:** Create 4 core services in Bifrost
1. **ToolRoutingService** - ML-based routing decisions
2. **ToolRegistryService** - Tool/route discovery and management
3. **SemanticSearchService** - Vector search and discovery
4. **ExecutionService** - Tool execution coordination

**Rationale:**
- Clean separation of concerns
- Each service has single responsibility
- Easy to test and maintain
- Aligns with existing router_core structure

### Data Flow
**SmartCP (MCP Frontend)** → GraphQL → **Bifrost (Backend Services)** → Database/ML

## ARUs (Assumptions, Risks, Uncertainties)

### Assumptions
- Bifrost supports GraphQL (need to verify/add)
- MLX models can be called from Go (or use Python microservice)
- Existing router_core can be extended
- Performance acceptable with network hop

### Risks
- Latency increase from network calls (MITIGATION: caching, connection pooling)
- MLX model integration complexity (MITIGATION: Python microservice if needed)
- Large refactor scope (MITIGATION: incremental migration)

### Uncertainties
- Best way to integrate MLX from Go backend
- Optimal caching strategy
- GraphQL schema design details

## Links
- Main issue: Extract business logic from SmartCP
- Related: Router core architecture
- Related: Bifrost API design
