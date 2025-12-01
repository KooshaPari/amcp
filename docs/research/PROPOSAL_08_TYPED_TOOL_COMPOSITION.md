# Proposal 8: Typed Tool Composition & Piping

**ID:** PROPOSAL-008  
**Title:** Implement Typed Tool Composition with Automatic Piping  
**Status:** DRAFT  
**Priority:** P1  
**Effort:** 45 story points  
**Timeline:** 3-4 weeks  
**Depends On:** Proposals 1, 5, 6

## Problem Statement

Current tool system lacks:
- Automatic output-to-input piping
- Type safety for tool composition
- Schema compatibility validation
- Automatic data transformation
- Composition discovery and optimization

## Solution Overview

Implement typed tool composition enabling:
1. **Type-Safe Piping** - Validate output→input compatibility
2. **Composition Operators** - Pipe, parallel, conditional, sequence
3. **Auto-Transformation** - Convert between schemas
4. **Composition Discovery** - Find compatible tool chains
5. **Optimization** - Choose best composition paths

## Architecture

### Enhanced Tool Definition
```python
class TypedTool:
    name: str
    description: str
    input_schema: JSONSchema  # REQUIRED
    output_schema: JSONSchema  # REQUIRED (new)
    
    # Composition metadata
    compatible_inputs: List[str]
    compatible_outputs: List[str]
    transformations: Dict[str, Callable]
    
    # Performance metadata
    avg_latency_ms: float
    success_rate: float
    cost_per_call: float
```

### Composition Operators
```python
# Pipe: tool1 output → tool2 input
result = await (tool1 | tool2).execute(data)

# Parallel: execute both, combine results
results = await (tool1 & tool2).execute(data)

# Conditional: if condition, use tool2
result = await (tool1 >> tool2).execute(data)

# Sequence: tool1 → tool2 → tool3
result = await (tool1 >> tool2 >> tool3).execute(data)
```

### Type Validation
```python
class CompositionValidator:
    def validate_pipe(
        source: TypedTool,
        target: TypedTool
    ) -> ValidationResult:
        """Check if source output matches target input"""
        # Check type compatibility
        # Check required fields
        # Identify transformations needed
        # Return compatibility score
```

### Schema Transformer
```python
class SchemaTransformer:
    def transform(
        data: Any,
        source_schema: JSONSchema,
        target_schema: JSONSchema
    ) -> Any:
        """Auto-transform data between schemas"""
        # Extract relevant fields
        # Rename fields if needed
        # Convert types
        # Validate result
```

## Features

### 1. Type-Safe Piping
```python
# Automatic validation
search_tool | filter_tool  # ✅ Compatible
search_tool | delete_tool  # ❌ Incompatible (error)

# With transformation
search_tool | transform_tool  # Auto-transform if possible
```

### 2. Composition Operators
```python
# Sequential
pipeline = search | transform | analyze
result = await pipeline.execute(query)

# Parallel
results = await (search & filter).execute(data)

# Conditional
result = await (search >> (validate >> save)).execute(data)
```

### 3. Auto-Discovery
```python
# Find tools that can follow search
compatible = await composition_engine.find_compatible(
    tool="search",
    position="after"
)
# Returns: [transform, filter, analyze, ...]

# Find optimal path
path = await composition_engine.find_optimal_path(
    start="search",
    end="report",
    metric="latency"  # or "cost", "reliability"
)
```

### 4. Composition Templates
```python
# Define reusable patterns
search_transform_analyze = (
    search_tool | transform_tool | analyze_tool
)

# Reuse with different inputs
result1 = await search_transform_analyze.execute(query1)
result2 = await search_transform_analyze.execute(query2)
```

## Implementation Phases

### Phase 1: Enhanced Schemas (Week 1)
- [ ] Add output_schema to all tools
- [ ] Add compatibility metadata
- [ ] Implement schema validation

### Phase 2: Composition Operators (Week 2)
- [ ] Implement pipe operator
- [ ] Implement parallel operator
- [ ] Implement conditional operator
- [ ] Add error handling

### Phase 3: Auto-Transformation (Week 2-3)
- [ ] Implement schema transformer
- [ ] Add type coercion
- [ ] Add field mapping
- [ ] Handle edge cases

### Phase 4: Discovery & Optimization (Week 3-4)
- [ ] Find compatible tools
- [ ] Optimize composition paths
- [ ] Add composition suggestions
- [ ] Performance tracking

## Configuration Example

```yaml
tool_composition:
  enabled: true
  
  validation:
    strict: true
    auto_transform: true
    
  operators:
    pipe: true
    parallel: true
    conditional: true
    
  discovery:
    enabled: true
    max_depth: 5
    
  optimization:
    enabled: true
    metric: "latency"  # or "cost", "reliability"
```

## Testing Strategy

- Unit tests for type validation
- Integration tests for composition
- E2E tests for complex pipelines
- Performance tests for overhead
- Compatibility tests for transformations

## Success Criteria

- [ ] All tools have output schemas
- [ ] Type validation working
- [ ] Composition operators functional
- [ ] Auto-transformation working
- [ ] Discovery finding compatible tools
- [ ] <50ms composition overhead
- [ ] Full test coverage

## Related Proposals

- Proposal 5: Tool Discovery (enhanced by this)
- Proposal 6: Tool Management (uses composition)
- Proposal 7: Claude Skills (defines compositions)

