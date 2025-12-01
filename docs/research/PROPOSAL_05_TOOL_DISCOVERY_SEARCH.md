# Proposal 5: Advanced Tool Discovery & Search

**ID:** PROPOSAL-005  
**Title:** Implement RAG/Semantic/Keyword Search for Tool Discovery  
**Status:** DRAFT  
**Priority:** P1  
**Effort:** 40 story points  
**Timeline:** 3-4 weeks  
**Depends On:** Proposal 1 (FastMCP 2.13)

## Problem Statement

Current tool discovery is manual and context-heavy. This prevents:
- Automatic tool discovery from MCP registry
- Semantic search across tool documentation
- Keyword-based tool filtering
- Dynamic tool installation
- Context-efficient tool selection

## Solution Overview

Implement multi-modal tool discovery:
1. **MCP Registry Integration** - Discover tools from official registry
2. **Semantic Search** - Vector embeddings for intelligent discovery
3. **Keyword Search** - BM25/FTS for fast filtering
4. **RAG Pipeline** - Retrieve relevant tools with context
5. **Auto-Installation** - Discover and install tools on demand

## Architecture

### Tool Discovery Engine
```python
class ToolDiscoveryEngine:
    async def discover_from_registry(
        query: str,
        limit: int = 10
    ) -> List[ToolMetadata]
    
    async def semantic_search(
        query: str,
        limit: int = 10
    ) -> List[ToolMetadata]
    
    async def keyword_search(
        query: str,
        limit: int = 10
    ) -> List[ToolMetadata]
    
    async def install_tool(
        tool_id: str,
        config: ToolConfig
    ) -> ToolHandle
```

### Search Strategies

#### 1. MCP Registry Integration
```python
class MCPRegistryClient:
    async def search(query: str) -> List[RegistryEntry]
    async def get_tool_metadata(tool_id: str) -> ToolMetadata
    async def get_installation_config(tool_id: str) -> InstallConfig
    
    # Registry endpoints
    # GET /api/v1/tools/search?q=<query>
    # GET /api/v1/tools/<id>
    # GET /api/v1/tools/<id>/install
```

#### 2. Semantic Search (Vector Embeddings)
```python
class SemanticSearchEngine:
    async def index_tools(tools: List[Tool])
    async def search(query: str, limit: int) -> List[SearchResult]
    
    # Uses embeddings for:
    # - Tool descriptions
    # - Tool names
    # - Tool capabilities
    # - Example usage
```

#### 3. Keyword Search (BM25/FTS)
```python
class KeywordSearchEngine:
    async def index_tools(tools: List[Tool])
    async def search(query: str, limit: int) -> List[SearchResult]
    
    # Fast filtering on:
    # - Tool names
    # - Keywords/tags
    # - Categories
    # - Descriptions
```

#### 4. RAG Pipeline
```python
class ToolRAGPipeline:
    async def retrieve_relevant_tools(
        user_query: str,
        context: ExecutionContext,
        limit: int = 5
    ) -> List[ToolMetadata]
    
    async def generate_tool_recommendations(
        user_query: str,
        retrieved_tools: List[ToolMetadata]
    ) -> List[ToolRecommendation]
```

## Implementation Phases

### Phase 1: Registry Integration (Week 1)
- [ ] Implement MCP registry client
- [ ] Add registry search API
- [ ] Implement tool metadata caching
- [ ] Add installation config retrieval

### Phase 2: Semantic Search (Week 2)
- [ ] Implement embedding generation
- [ ] Add vector store (Pinecone/Weaviate)
- [ ] Implement semantic search
- [ ] Add relevance ranking

### Phase 3: Keyword Search (Week 2-3)
- [ ] Implement BM25 indexing
- [ ] Add FTS support
- [ ] Implement keyword search
- [ ] Add filtering/faceting

### Phase 4: RAG & Auto-Install (Week 3-4)
- [ ] Implement RAG pipeline
- [ ] Add tool recommendations
- [ ] Implement auto-installation
- [ ] Add dependency resolution

## Configuration Example

```yaml
tool_discovery:
  registry:
    enabled: true
    url: "https://registry.modelcontextprotocol.io"
    cache_ttl: 3600
    
  semantic_search:
    enabled: true
    embedding_model: "text-embedding-3-small"
    vector_store: "pinecone"
    
  keyword_search:
    enabled: true
    engine: "bm25"
    
  auto_install:
    enabled: true
    auto_approve: false
    max_tools: 50
```

## Search Examples

### Semantic Search
```
Query: "I need to analyze CSV files"
Results:
1. pandas-mcp (0.95 relevance)
2. data-processing-mcp (0.87)
3. file-system-mcp (0.72)
```

### Keyword Search
```
Query: "github issues"
Results:
1. github-mcp
2. github-issues-mcp
3. issue-tracker-mcp
```

### RAG Pipeline
```
User: "Help me migrate data from Jira to GitHub"
Retrieved Tools:
1. jira-mcp (retrieve)
2. github-mcp (retrieve)
3. data-transform-mcp (retrieve)

Recommendations:
1. Use jira-mcp to export issues
2. Transform with data-transform-mcp
3. Import to github-mcp
```

## Testing Strategy

- Unit tests for each search engine
- Integration tests with registry
- E2E tests for discovery workflows
- Performance tests for search latency
- Accuracy tests for relevance ranking

## Success Criteria

- [ ] Registry integration working
- [ ] Semantic search functional
- [ ] Keyword search fast (<100ms)
- [ ] RAG pipeline accurate
- [ ] Auto-installation tested
- [ ] <500ms end-to-end discovery

## Related Proposals

- Proposal 1: FastMCP 2.13 (prerequisite)
- Proposal 6: Tool Management (uses discovery)

