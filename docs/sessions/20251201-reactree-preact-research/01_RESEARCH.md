# ReAcTree + PreAct Research Findings

**Session**: 2024-12-01
**Topic**: Understanding ReAcTree and PreAct for SmartCP Phase 2 Implementation
**Status**: Complete

## Quick Summary

- **ReAcTree** = Hierarchical task planning with tree-structured decomposition (2x improvement over ReAct)
- **PreAct** = Prediction-enhanced planning (prediction → reasoning → action → reflection)
- **Not related**: Preact (React UI framework) - this is entirely AI/ML focused

## Key Findings

### ReAcTree (Hierarchical Task Planning)

**What it is**: Extension of ReAct that decomposes complex tasks into hierarchical subtasks within a tree structure.

**Core Components**:
1. **Agent Nodes**: LLM agents that handle specific subgoals
2. **Control Flow Nodes**: Manage execution order (sequence, parallel, conditional)
3. **Episodic Memory**: Goal-specific experiences as in-context examples
4. **Working Memory**: Shared state across all agent nodes

**Performance**:
- WAH-NL benchmark: 31% → 61% success rate (nearly 2x improvement)
- Qwen 2.5 72B model
- Submitted to ICLR 2025

**Why it matters for SmartCP**:
- Automatically breaks complex prompts into manageable pieces
- Prevents context overflow through memory systems
- Enables parallel execution of independent subgoals
- Adapts dynamically based on intermediate results

### PreAct (Prediction-Enhanced Planning)

**What it is**: Agent framework adding prediction step before planning.

**Flow**: Prediction → Reasoning → Action → Self-Reflection

**Key Innovation**: By predicting outcomes first, the LLM can provide more strategic and focused reasoning.

**Benefits**:
- Proactive strategy formulation (not just reactive)
- Error prevention through outcome forecasting
- Built-in self-reflection via prediction comparison
- Better composability with other techniques

**Publication**: Coling 2025 (code available on GitHub)

### Related Tree-Based Techniques

1. **LATS (Language Agent Tree Search)**
   - Adapts Monte Carlo Tree Search (MCTS) to language agents
   - 2x improvement on HotPotQA, +22.1% on WebShop
   - Uses LLM as value function

2. **Tree of Thoughts (ToT)**
   - Multiple reasoning paths explored simultaneously
   - Maintains tree of coherent thought sequences

3. **Forest-of-Thought (FoT)**
   - Integrates multiple reasoning trees
   - Sparse activation for computational efficiency

## Integration Architecture for SmartCP

```
Input Prompt
    ↓
[ReAcTree Planning] - Hierarchical decomposition
    ↓
[PreAct Prediction] - Forecast outcomes
    ↓
[Tree Search] - Explore reasoning paths (optional)
    ↓
[Memory Systems] - Episodic + Working memory
    ↓
Optimized Output
```

## Implementation Recommendations

### Phase 2 Priority Order

1. **PreAct (Weeks 1-2)** - LOW EFFORT, QUICK WINS
   - Add prediction step before existing reasoning
   - Implement self-reflection feedback loop
   - Integrate with current optimization pipeline

2. **ReAcTree (Weeks 3-6)** - MEDIUM EFFORT, HIGH IMPACT
   - Hierarchical decomposition for complex prompts
   - Agent node and control flow management
   - Episodic/working memory integration

3. **LATS/Tree Search (Weeks 7-12)** - HIGH EFFORT, SPECIALIZED
   - MCTS-based exploration of reasoning paths
   - Reward-guided search optimization
   - Multi-tree reasoning (FoT)

## Key Implementation Patterns

### Pattern 1: ReAcTree Decomposition
```python
# services/optimization/reactree_planner.py
class ReAcTreePlanner:
    async def decompose_prompt(prompt: str) -> AgentNode
    async def execute_tree(root_node: AgentNode) -> Dict
    async def _expand_node(node: AgentNode, depth: int) -> None
```

### Pattern 2: PreAct Prediction Layer
```python
# services/optimization/preact_predictor.py
class PreActPredictor:
    async def predict_and_plan(goal: str, context: Dict) -> Dict
    async def _predict_outcomes(goal: str, context: Dict) -> PredictionResult
    async def _reflect_on_plan(prediction, actions) -> Dict
```

### Pattern 3: Tree Search (LATS)
```python
# services/optimization/tree_search.py
class TreeSearchOptimizer:
    async def search(initial_state: Dict, goal: str) -> Dict
    async def _lats_search(root: TreeNode, goal: str) -> Dict
    async def _evaluate_state(node: TreeNode, goal: str) -> float
```

## Performance Considerations

### Memory Management
- **Challenge**: Exponential tree growth
- **Solutions**: Pruning, depth limiting, batch processing, vector store offloading

### Computational Cost
- **Challenge**: Multiple LLM calls per iteration
- **Solutions**: Caching, batching, smaller models for evaluation, early termination

### Latency Optimization
- **Challenge**: Sequential tree expansion is slow
- **Solutions**: Pre-expansion, asynchronous expansion, streaming results

## Testing Strategy

Key test cases to implement:
- Simple task decomposition
- Control flow coordination (parallel vs sequential)
- Episodic memory retrieval
- Prediction accuracy
- Tree search convergence
- Performance benchmarks

## Metrics to Track

- Tree depth (avg)
- Node count per prompt
- LLM cache hit rate
- Task success rate
- Latency (p50, p99)
- Prediction accuracy (PreAct predictions vs actual outcomes)
- Memory usage per optimization pass

## Sources

### ReAcTree
- [arXiv:2511.02424](https://arxiv.org/abs/2511.02424)
- [OpenReview](https://openreview.net/forum?id=KgKN7F0PyQ)

### PreAct
- [arXiv:2402.11534](https://arxiv.org/abs/2402.11534)
- [GitHub: Fu-Dayuan/PreAct](https://github.com/Fu-Dayuan/PreAct)

### LATS
- [arXiv:2310.04406](https://arxiv.org/pdf/2310.04406)

### Tree-Based Techniques
- [Tree of Thoughts Prompting Guide](https://www.promptingguide.ai/techniques/tot)
- [Forest-of-Thought: arXiv:2412.09078](https://arxiv.org/html/2412.09078v1)

## Next Steps

1. Create `services/optimization/reactree_planner.py` with basic decomposition
2. Add `services/optimization/preact_predictor.py` with prediction layer
3. Implement comprehensive test suite in `tests/unit/optimization/test_reactree.py`
4. Benchmark against current optimization pipeline
5. Document architectural integration points

