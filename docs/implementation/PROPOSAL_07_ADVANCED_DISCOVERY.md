# PROPOSAL 07: Advanced Tool Discovery (RAG + Semantic + FTS)

**Status:** PROPOSED  
**Priority:** P1 (High)  
**Effort:** 3 weeks  
**Dependencies:** PROPOSAL_01

## Problem Statement

Current discovery is basic. Production needs:
- Semantic search (vector embeddings)
- Full-text search (BM25, keyword)
- RAG (Retrieval-Augmented Generation)
- Fuzzy matching
- Tool recommendations

## Solution Overview

Implement multi-modal discovery:

```
┌──────────────────────────────────────┐
│    Advanced Discovery Engine         │
├──────────────────────────────────────┤
│  Semantic Search                     │
│  ├─ Vector embeddings                │
│  ├─ Similarity matching              │
│  └─ Semantic ranking                 │
├──────────────────────────────────────┤
│  Full-Text Search                    │
│  ├─ BM25 ranking                     │
│  ├─ Keyword extraction               │
│  └─ Phrase matching                  │
├──────────────────────────────────────┤
│  RAG Pipeline                        │
│  ├─ Document retrieval               │
│  ├─ Context ranking                  │
│  └─ Answer generation                │
└──────────────────────────────────────┘
```

## Core Components

### 1. Semantic Search
```python
class SemanticSearcher:
    """Vector-based tool discovery"""
    
    async def embed_tool(self, tool: Tool) -> Vector
    async def search(self, query: str, limit: int) -> List[Tool]
    async def similar_tools(self, tool_id: str) -> List[Tool]
    def build_index(self, tools: List[Tool])
```

### 2. Full-Text Search
```python
class FullTextSearcher:
    """Keyword-based discovery"""
    
    def index_tool(self, tool: Tool)
    def search(self, query: str, limit: int) -> List[Tool]
    def extract_keywords(self, text: str) -> List[str]
    def rank_results(self, results: List[Tool]) -> List[Tool]
```

### 3. RAG Pipeline
```python
class RAGPipeline:
    """Retrieval-Augmented Generation"""
    
    async def retrieve(self, query: str) -> List[Document]
    async def rank(self, docs: List[Document]) -> List[Document]
    async def generate_answer(self, query: str, docs: List) -> str
    async def explain_recommendation(self, tool: Tool) -> str
```

## Search Strategies

### Strategy 1: Semantic
```python
# Find tools by meaning
results = await discovery.semantic_search(
    "upload file to cloud storage",
    limit=5
)
# Returns: [S3Upload, GCSUpload, AzureBlob, ...]
```

### Strategy 2: Full-Text
```python
# Find tools by keywords
results = await discovery.fulltext_search(
    "file upload cloud",
    limit=5
)
# Returns: [S3Upload, GCSUpload, ...]
```

### Strategy 3: Hybrid
```python
# Combine semantic + FTS
results = await discovery.hybrid_search(
    "upload file to cloud storage",
    semantic_weight=0.6,
    fts_weight=0.4,
    limit=5
)
```

### Strategy 4: RAG
```python
# Generate recommendations with explanation
results = await discovery.rag_search(
    "I need to store user data securely",
    limit=3
)
# Returns: [(tool, explanation), ...]
```

## Implementation Plan

### Phase 1: Full-Text Search (Week 1)
- [ ] BM25 implementation
- [ ] Keyword extraction
- [ ] Indexing
- [ ] Tests

### Phase 2: Semantic Search (Week 2)
- [ ] Embedding model
- [ ] Vector indexing
- [ ] Similarity search
- [ ] Tests

### Phase 3: RAG & Hybrid (Week 3)
- [ ] RAG pipeline
- [ ] Hybrid search
- [ ] Ranking algorithms
- [ ] Integration tests

## Benefits

✅ Better tool discovery  
✅ Semantic understanding  
✅ Faster searches  
✅ Relevant results  
✅ User guidance  

## Success Criteria

- [ ] All search modes working
- [ ] Semantic accuracy >85%
- [ ] FTS performance <100ms
- [ ] RAG explanations helpful
- [ ] Integration tests passing

---

**Next:** PROPOSAL_08 (MCP Registry)

