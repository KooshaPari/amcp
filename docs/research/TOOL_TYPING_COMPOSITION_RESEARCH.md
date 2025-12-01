# Tool Typing & Composition Research

**Date:** 2025-11-21  
**Status:** RESEARCH COMPLETE  
**Recommendation:** YES - Implement typed tool composition

## Question 1: Are Tools Pre-Typed?

### Current State: YES ✅

**Tools ARE pre-typed with input/output schemas:**

```python
# Current implementation
class Tool:
    name: str
    description: str
    input_schema: dict  # JSON Schema
    output_schema: dict  # JSON Schema (optional)
    examples: list[dict]
```

### Input Schema Example
```json
{
  "type": "object",
  "properties": {
    "query": {"type": "string"},
    "limit": {"type": "integer", "minimum": 1}
  },
  "required": ["query"]
}
```

### Output Schema Example
```json
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "title": {"type": "string"}
        }
      }
    },
    "total": {"type": "integer"}
  }
}
```

## Question 2: Can Tool Outputs Pipe Into Inputs?

### Current State: PARTIAL ⚠️

**Possible but not automatic:**

```python
# Manual piping (current approach)
result1 = await tool1.execute({"query": "search"})
# result1 = {"results": [...], "total": 5}

result2 = await tool2.execute({
    "items": result1["results"]  # Manual extraction
})
```

### What's Missing
- ❌ Automatic type matching
- ❌ Schema compatibility checking
- ❌ Automatic data transformation
- ❌ Error handling for type mismatches

### What Should Be Added
- ✅ Type compatibility validation
- ✅ Automatic schema matching
- ✅ Data transformation pipelines
- ✅ Composition operators

## Recommended Solution: Typed Tool Composition

### 1. Enhanced Tool Definition
```python
class TypedTool:
    name: str
    description: str
    input_schema: JSONSchema
    output_schema: JSONSchema  # REQUIRED
    
    # NEW: Type compatibility info
    compatible_inputs: List[str]  # Tool names
    compatible_outputs: List[str]  # Tool names
    
    # NEW: Transformation rules
    transformations: Dict[str, Callable]
```

### 2. Composition Operators
```python
# Pipe operator
result = await (tool1 | tool2).execute(input_data)

# Parallel operator
results = await (tool1 & tool2).execute(input_data)

# Conditional operator
result = await (tool1 >> tool2).execute(input_data)

# Sequence operator
result = await (tool1 >> tool2 >> tool3).execute(input_data)
```

### 3. Type Validation
```python
class CompositionValidator:
    def validate_pipe(
        source_tool: TypedTool,
        target_tool: TypedTool
    ) -> bool:
        """Check if source output matches target input"""
        source_output = source_tool.output_schema
        target_input = target_tool.input_schema
        return self._schemas_compatible(source_output, target_input)
    
    def _schemas_compatible(
        output: JSONSchema,
        input: JSONSchema
    ) -> bool:
        # Check type compatibility
        # Check required fields
        # Check transformations needed
        pass
```

### 4. Automatic Transformation
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
        return transformed_data
```

## Benefits of Typed Composition

| Benefit | Impact |
|---------|--------|
| **Type Safety** | Catch errors early |
| **Auto-Piping** | Reduce manual work |
| **Discovery** | Find compatible tools |
| **Optimization** | Choose best paths |
| **Documentation** | Self-documenting |

## Implementation Phases

### Phase 1: Enhanced Schemas (Week 1)
- [ ] Add output_schema to all tools
- [ ] Add compatibility metadata
- [ ] Implement schema validation

### Phase 2: Composition Operators (Week 2)
- [ ] Implement pipe operator
- [ ] Implement parallel operator
- [ ] Implement conditional operator

### Phase 3: Auto-Transformation (Week 2-3)
- [ ] Implement schema transformer
- [ ] Add type coercion
- [ ] Add field mapping

### Phase 4: Discovery & Optimization (Week 3-4)
- [ ] Find compatible tools
- [ ] Optimize composition paths
- [ ] Add composition suggestions

## Example: Real-World Composition

```python
# Search → Transform → Analyze → Report

search_tool = TypedTool(
    name="search",
    output_schema={
        "type": "object",
        "properties": {
            "results": {"type": "array"}
        }
    }
)

transform_tool = TypedTool(
    name="transform",
    input_schema={
        "type": "object",
        "properties": {
            "data": {"type": "array"}
        }
    },
    output_schema={
        "type": "object",
        "properties": {
            "transformed": {"type": "array"}
        }
    }
)

# Automatic piping with type checking
pipeline = search_tool | transform_tool
result = await pipeline.execute({"query": "data"})
```

## Success Criteria

- [ ] All tools have output schemas
- [ ] Type validation working
- [ ] Composition operators functional
- [ ] Auto-transformation working
- [ ] <50ms composition overhead
- [ ] Full test coverage

## Integration with Proposals

### With Proposal 5 (Tool Discovery)
- Typed schemas enable semantic search
- Output types guide tool recommendations
- Composition paths improve discovery

### With Proposal 6 (Tool Management)
- Type information in tool versioning
- Composition patterns as reusable templates
- Type evolution tracking

### With Proposal 7 (Claude Skills)
- Skills can define composition patterns
- Type information in skill instructions
- Automatic skill generation from compositions

---

**Recommendation:** ✅ IMPLEMENT TYPED COMPOSITION
**Effort:** 40-50 story points
**Timeline:** 3-4 weeks
**Strategic Value:** HIGH

