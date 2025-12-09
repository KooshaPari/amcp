# Agent Layer Phase 4: Evaluation Research

**Research Agent:** Evaluation Research Agent
**Date:** 2025-12-02
**Research Duration:** 12 hours (C1: 4h, C2: 4h, C3: 2h, C4: 2h)
**Status:** Complete

---

## Executive Summary

This document provides comprehensive research on SWE-Bench benchmarking, agent evaluation strategies, and validation frameworks for the Agent Layer Phase 4 development. The research covers four key streams:

1. **SWE-Bench Benchmark Structure** - Understanding the dataset, metrics, and evaluation methodology
2. **Current Agent Performance** - Analyzing SOTA results, success patterns, and failure modes
3. **Harbor Integration** - Designing evaluation infrastructure for our agents
4. **Validation Strategy** - Establishing quality assurance and safety frameworks

**Key Findings:**
- SWE-Bench provides 2,294 real GitHub issues across 12 Python repositories
- Current SOTA: 70.2% on SWE-Bench Verified (devlo), 26.3% on Lite (Aider)
- Multi-LLM ensemble and inference-time scaling are winning strategies
- Harbor framework enables scalable cloud-based agent evaluation
- Code correctness validation requires multi-layer safety checks

---

## C1: SWE-Bench Benchmark Structure (4h)

### 1.1 Dataset Composition

**Core Dataset:**
- **Total Instances:** 2,294 software engineering problems
- **Source:** Real GitHub issues and corresponding pull requests
- **Repositories:** 12 popular Python open-source projects
- **Construction Method:** Issue-Pull Request pairs with substantial filtering

**Dataset Variants:**

1. **SWE-Bench Full** (2,294 instances)
   - Original comprehensive benchmark
   - Complete set of verified Issue-PR pairs
   - Most challenging variant

2. **SWE-Bench Lite** (300 instances)
   - Curated subset for cost-effective evaluation
   - More accessible for rapid iteration
   - Representative sample of full benchmark

3. **SWE-Bench Verified** (500 instances)
   - Human-filtered subset
   - Higher quality annotations
   - More reliable ground truth
   - Current focus for SOTA comparisons

4. **SWE-Bench Multimodal**
   - Features issues with visual elements
   - Tests multi-modal understanding
   - Newer addition (2024)

5. **SWE-Bench Pro**
   - Private, previously unseen codebases
   - More realistic generalization measure
   - Commercial variant via Scale AI

**Data Quality:**
- Substantial filtering ensures solvability
- Real-world complexity maintained
- Post-PR behavior as reference solution
- Unit test verification available

### 1.2 Evaluation Metrics & Scoring Methodology

**Primary Metric: % Resolved**

The core metric representing percentage of instances where generated patch:
- Passes all relevant tests (fail-to-pass tests)
- Maintains existing functionality (pass-to-pass tests)
- Successfully resolves the described issue

**Evaluation Workflow:**

```
1. Setup
   └─> Docker environment for repository
   └─> Install dependencies
   └─> Checkout specific commit

2. Apply Patch
   └─> Apply model-generated patch
   └─> Handle merge conflicts
   └─> Validate syntax

3. Run Tests
   └─> Execute fail-to-pass tests (must pass)
   └─> Execute pass-to-pass tests (must not break)
   └─> Record test results

4. Determine Success
   └─> Issue Resolution: fail-to-pass tests pass
   └─> No Regressions: pass-to-pass tests continue passing
   └─> Both conditions required for "Resolved" status
```

**Additional Metrics:**

| Metric | Description | Purpose |
|--------|-------------|---------|
| Total Instances | Total problems in benchmark | Dataset size |
| Instances Submitted | Problems attempted | Coverage |
| Instances Completed | Patches generated | Completion rate |
| Instances Resolved | Tests passed, no regressions | Success rate |
| Instances Unresolved | Failed or broke tests | Failure analysis |
| Empty Patches | No changes generated | Agent failure |
| Instances with Errors | Execution errors | System issues |

**Stricter Criteria (SWE-Bench Pro):**

Two strict conditions for resolution:
1. **Issue Resolution**: fail-to-pass tests pass (bug fixed/feature implemented)
2. **No Regressions**: ALL pre-existing pass-to-pass tests continue passing

This prevents "solutions" that fix one thing but break others.

**Evaluation Environment:**

- **Containerization:** Fully containerized using Docker
- **Reproducibility:** Consistent across platforms
- **Isolation:** Each evaluation in separate container
- **Timeout:** Reasonable time limits per task
- **Resource Control:** Memory and CPU constraints

### 1.3 Difficulty Distribution

**Time-Based Categories (SWE-Bench Verified):**

| Category | Duration | Characteristics | Percentage |
|----------|----------|-----------------|------------|
| Trivial | < 15 min | Simple assertions, config changes | ~40% |
| Small | 15 min - 1 hr | Focused changes, single function | ~51% |
| Substantial | 1 - 4 hrs | Multiple functions/files, rewrites | ~8% |
| Complex | > 4 hrs | Esoteric issues, 100+ lines changed | ~1% |

**Key Insight:** 91% of SWE-Bench Verified tasks take < 1 hour for experienced developers.

**Complexity Metrics by Difficulty:**

| Metric | Easy → Hard | Observation |
|--------|-------------|-------------|
| Lines Changed | 11x increase | Most dramatic indicator |
| Files Modified | 2x increase | Modest growth |
| Hunks | 5x increase | Moderate correlation |

**Problem Categories:**

Distribution spans:
- Bug fixes (most common)
- Feature requests
- Performance optimizations
- Security updates
- UI/UX improvements
- Documentation corrections
- Test additions/fixes

**Repository Distribution:**

Tasks drawn from repositories like:
- Django (web framework)
- scikit-learn (ML library)
- matplotlib (plotting)
- pytest (testing framework)
- sympy (symbolic math)
- And 7+ others

This diversity ensures agents must handle various:
- Coding styles
- Domain knowledge requirements
- Project structures
- Testing frameworks

### 1.4 Current SOTA Results (2024)

**SWE-Bench Verified (500 instances):**

| Rank | System | Score | Key Innovation |
|------|--------|-------|----------------|
| 1 | devlo | 70.2% | Multi-LLM ensemble, regression testing |
| 2 | OpenHands | 66%+ | Critic model, solution selection |
| 3 | Harness AI | 60%+ | Top commercial offering |

**SWE-Bench Lite (300 instances):**

| Rank | System | Score | Approach |
|------|--------|-------|----------|
| 1 | Aider | 26.3% | Repository mapping, reliable editing |
| 2 | Various | 20-25% | Different strategies |

**SWE-Bench Full (2,294 instances):**

| Rank | System | Score | Notable |
|------|--------|-------|---------|
| 1 | Aider | 18.9% | SOTA on full benchmark |
| 2 | Claude Opus 4.1 | 17.8% | Private codebases |
| 3 | GPT-5 | 14.9% | Private codebases |

**Performance Gap Observation:**

Public codebases (potentially in training data):
- Claude Opus 4.1: 22.7%
- GPT-5: 23.1%

Private codebases (unseen):
- Claude Opus 4.1: 17.8% (-4.9%)
- GPT-5: 14.9% (-8.2%)

**Conclusion:** Private codebases provide more realistic generalization measure.

**Recent Milestones (2024):**

- May 2024: Aider achieves 26.3% on Lite
- June 2024: Aider achieves 18.9% on Full
- October 2024: SWE-Bench Multimodal introduced
- Late 2024: 70.2% on Verified (devlo)

### 1.5 Submission Process & Leaderboard

**Submission Requirements:**

1. **Model/Agent Details:**
   - System name and version
   - Base model(s) used
   - Inference configuration
   - Tool access provided

2. **Generated Patches:**
   - One patch per instance
   - Git diff format
   - Applies cleanly to target commit

3. **Evaluation Logs:**
   - Test execution logs
   - Error messages
   - Timing information

4. **Reproducibility:**
   - Code/configuration to reproduce
   - Docker images if custom
   - Dependency specifications

**Leaderboard Categories:**

- SWE-Bench Full
- SWE-Bench Lite
- SWE-Bench Verified
- SWE-Bench Multimodal
- SWE-Bench Multilingual (new)

Each tracks:
- % Resolved (primary)
- % Resolved + % Partial (with regressions)
- Submission date
- Model family
- Organization

---

## C2: Current Agent Performance (4h)

### 2.1 SOTA CLI Agents Analysis

**Top Performers:**

**1. Aider (Open Source)**
- **Scores:** 18.9% (Full), 26.3% (Lite)
- **Architecture:** Single-agent with optimized tools
- **Key Features:**
  - Repository mapping via AST analysis
  - Reliable LLM code editing
  - Git integration
  - Extensive prompting strategies

**Strategy:**
```
1. Repository Mapping
   └─> Static analysis of code AST
   └─> Call graph construction
   └─> Compact codebase summary

2. Code Editing
   └─> Precise diff generation
   └─> Integration checks
   └─> Style consistency

3. Regression Testing
   └─> PASS_TO_PASS validation
   └─> First to integrate regression testing
   └─> Later became standard practice
```

**2. OpenHands (formerly SWE-agent)**
- **Score:** 66%+ on Verified
- **Architecture:** Multi-agent with specialized roles
- **Innovation:** Critic model for solution selection

**Approach:**
```
Multi-Agent Structure:
├── Planner Agent
│   └─> Codebase research
│   └─> Strategy formation
├── Implementation Agent
│   └─> Code writing
│   └─> Tool execution
└── Reviewer Agent
    └─> Error checking
    └─> Test running
    └─> Change reflection
```

**3. devlo**
- **Score:** 70.2% on Verified (SOTA)
- **Key Innovation:** Multi-LLM ensemble

**Strategy:**
```
Hybrid Multi-LLM Approach:
1. Base agent sends inputs to 3 LLMs
2. Each produces independent solution
3. Agent assesses candidates
4. Produces final patch

Rationale:
- Non-overlapping training data
- Different inductive biases
- Diverse reasoning habits
- One model's miss = another's success
```

**4. Composio's SweKit**
- **Score:** 48.6% on benchmark
- **Technology:** LangGraph + LangSmith
- **Architecture:** Multi-agent specialization

**Agents:**
```
├── SWE ENGINEER (Manager)
│   └─> Task coordination
│   └─> Decision routing
├── CODE ANALYSIS
│   └─> In-depth code analysis
│   └─> Dependency mapping
└── EDITOR
    └─> Code modification
    └─> Test execution
```

**Tools Provided:**
- File editing and reading
- Git operations
- Code indexing
- LSP tools for comprehension

### 2.2 Performance by Problem Category

**Category Performance (Analysis):**

**Easy Tasks (< 15 min, ~40%):**
- Most models: 60-80% success
- Simple edits, clear context
- Models excel at obvious fixes

**Small Tasks (15 min - 1 hr, ~51%):**
- Most models: 30-50% success
- Requires understanding context
- Multiple possible solutions

**Substantial Tasks (1-4 hrs, ~8%):**
- Most models: 10-20% success
- Multi-file coordination
- Complex reasoning required

**Complex Tasks (> 4 hrs, ~1%):**
- Most models: 0-5% success
- Esoteric knowledge needed
- Large-scale refactoring

**Language Performance Differences:**

| Language | High Performers | Low Performers | Challenge |
|----------|----------------|----------------|-----------|
| Python | 30%+ resolve | Varies | Most training data |
| Go | 30%+ resolve | 15-20% | Good structure |
| JavaScript | 0-30% vary | 5-15% | Ecosystem complexity |
| TypeScript | 0-30% vary | 5-15% | Type system nuances |

**Key Insight:** JS/TS present more variable performance, likely due to:
- Complex build tooling
- Evolving best practices
- Framework diversity
- Type system subtleties

### 2.3 Error Analysis & Failure Modes

**LLM-as-Judge Analysis:**

Methodology:
- GPT-5 as automated judge
- 87% alignment with human categorization
- Random sample + heuristics
- Hand-curated failure patterns

**Failure Mode Categories:**

**1. Large Model Failures (e.g., Opus 4.1):**

| Failure Type | Description | Frequency | Impact |
|--------------|-------------|-----------|---------|
| Semantic Errors | Wrong logic, algorithm issues | High | Critical |
| Multi-file Coordination | Inconsistent changes across files | Medium | Major |
| Edge Case Handling | Missing corner cases | Medium | Moderate |

Characteristic: High-level reasoning errors despite good syntax.

**2. Small Model Failures (e.g., Qwen 3 32B):**

| Failure Type | Description | Frequency | Impact |
|--------------|-------------|-----------|---------|
| Syntax Errors | Invalid code generation | High | Blocking |
| Formatting Issues | Style/structure problems | High | Minor |
| Tool Misuse | Incorrect tool invocation | Medium | Major |
| Context Loss | Forgetting earlier decisions | Medium | Major |

Characteristic: Lower-level execution issues.

**3. Common Failure Patterns (All Models):**

**Navigation Challenges:**
- Large, unfamiliar codebases
- Finding relevant files among thousands
- Understanding project structure
- Tracing call chains

**Example:**
```
Problem: Fix bug in authentication
Failure: Agent edits wrong module
Cause: Confused by multiple auth implementations
```

**Precision Editing Failures:**
- High-precision edits across multiple files
- Maintaining consistency
- Handling interdependencies

**Example:**
```
Problem: Rename API parameter
Failure: Missed some call sites
Cause: Incomplete search or reasoning
```

**Ecosystem-Specific Issues:**
- JavaScript/TypeScript complexity
- Build configuration problems
- Framework-specific patterns
- Package manager issues

**Example:**
```
Problem: Update React component
Failure: Breaks with TypeScript errors
Cause: Type inference issues
```

### 2.4 Bottlenecks & Limitations

**Infrastructure Bottlenecks:**

**1. Context Window Limits:**
- Large files don't fit in context
- Multi-file reasoning truncated
- Important details lost

**Current Solutions:**
- Repository mapping (Aider)
- Selective file loading
- Hierarchical summarization

**2. Tool Execution Speed:**
- File system operations slow
- Test execution time
- Build/compile duration

**Impact:** Limits iteration speed, agent patience.

**3. Cost & Scaling:**
- Multiple inference calls expensive
- Long conversations costly
- Evaluation infrastructure needs

**Approach:**
- SWE-Bench Lite for rapid iteration
- Smaller models for preliminary testing
- Caching common operations

**Reasoning Bottlenecks:**

**1. Codebase Comprehension:**
- Understanding unfamiliar architecture
- Identifying relevant code sections
- Following control flow

**2. Multi-Step Planning:**
- Breaking down complex tasks
- Sequencing operations correctly
- Handling dependencies

**3. Error Recovery:**
- Debugging failed attempts
- Iterating on solutions
- Learning from test failures

**Process Bottlenecks:**

**1. Test Feedback Loops:**
- Slow test execution
- Limited error messages
- No intermediate validation

**2. Validation Overhead:**
- Full test suite runs expensive
- Hard to parallelize
- CI/CD integration challenges

### 2.5 Winning Strategies Extracted

**Strategy 1: Multi-LLM Ensemble (devlo - 70.2%)**

**Approach:**
```python
def solve_issue(issue):
    # Send to multiple LLMs in parallel
    solutions = []
    for model in [claude, gpt5, gemini]:
        solution = model.generate_patch(issue)
        solutions.append(solution)

    # Assess each candidate
    assessments = assess_solutions(solutions, issue)

    # Select best or combine
    final_patch = select_best(assessments)
    return final_patch
```

**Benefits:**
- Diverse reasoning approaches
- Non-overlapping training data
- Error cancellation (different models, different mistakes)
- Higher overall success rate

**Tradeoffs:**
- 3x inference cost
- More complex orchestration
- Need selection mechanism

**Strategy 2: Inference-Time Scaling (Multiple Teams)**

**Monte Carlo Tree Search (MCTS):**
```
Problem → [MCTS with Reward Function]
    ├── Solution Path 1 → Evaluate → Score
    ├── Solution Path 2 → Evaluate → Score
    ├── Solution Path 3 → Evaluate → Score
    └── Select Best Path → Generate Patch
```

**Results:** 23% relative performance improvement across 5 models.

**Why It Works:**
- Explores solution space systematically
- Rewards good intermediate steps
- Balances exploration/exploitation
- Scales compute at test time, not training time

**Strategy 3: Critic Model (OpenHands)**

**Approach:**
```
Generate Multiple Solutions:
├── Attempt 1 (Agent Run 1)
├── Attempt 2 (Agent Run 2)
├── Attempt 3 (Agent Run 3)
└── Attempt N (Agent Run N)

Critic Model:
└─> Evaluates all attempts
└─> Scores based on:
    ├── Test results
    ├── Code quality
    ├── Regression risk
    └─> Selects best

Final Submission: Highest-scored attempt
```

**Benefits:**
- Multiple shots at problem
- Learn which solutions are best
- Adaptable to different problem types

**Strategy 4: Repository Mapping (Aider)**

**Static Analysis Pipeline:**
```python
def create_repo_map(codebase):
    # Parse all files into AST
    asts = parse_files(codebase)

    # Build call graph
    call_graph = build_call_graph(asts)

    # Extract key elements
    summary = {
        'modules': extract_modules(asts),
        'classes': extract_classes(asts),
        'functions': extract_functions(asts),
        'dependencies': call_graph
    }

    # Compact representation
    repo_map = compress_to_context(summary)
    return repo_map
```

**Benefits:**
- Fits in context window
- Provides codebase overview
- Helps navigation
- Improves file selection

**Strategy 5: Tool Optimization**

**Key Lesson from SWE-agent team:**
> "More time was spent optimizing tools than the overall prompt."

**Example - Filepath Tool:**

**Problem:**
```python
# Tool accepted relative paths
edit_file("src/auth.py")  # Works in root
cd("utils")
edit_file("src/auth.py")  # Now broken! (looking in utils/src/auth.py)
```

**Solution:**
```python
# Tool requires absolute paths only
edit_file("/repo/src/auth.py")  # Always works
cd("utils")
edit_file("/repo/src/auth.py")  # Still works
```

**Result:** Model used the method flawlessly after this change.

**General Tool Design Principles:**
1. Make errors impossible (not just unlikely)
2. Validate inputs strictly
3. Provide clear error messages
4. Design for LLM capabilities, not human expectations
5. Test extensively with actual model behavior

**Strategy 6: Regression Testing Integration (Aider - First)**

**Implementation:**
```python
def validate_patch(patch, repo):
    apply_patch(repo, patch)

    # Run fail-to-pass tests (issue resolution)
    fail_to_pass_results = run_tests(repo.fail_to_pass_tests)

    # CRITICAL: Run pass-to-pass tests (no regressions)
    pass_to_pass_results = run_tests(repo.pass_to_pass_tests)

    if not all(fail_to_pass_results.passed):
        return "Issue not resolved"

    if not all(pass_to_pass_results.passed):
        return "Regressions introduced"

    return "Success"
```

**Impact:**
- Became standard practice across all submissions
- Dramatically reduced regression rate
- Improved overall scores

**Strategy 7: Specialized Agents (Composio)**

**Multi-Agent Decomposition:**

```
Problem → SWE ENGINEER (Manager)
    ├─> Route to CODE ANALYSIS
    │   └─> Deep analysis, return findings
    ├─> Route to EDITOR
    │   └─> Apply changes based on analysis
    └─> Validate → Return result
```

**Benefits:**
- Each agent specialized for its task
- Clearer prompts per agent
- Better tool usage
- Easier debugging

**Strategy 8: Prompt Engineering**

**Best Practices Observed:**

1. **Clear Task Decomposition:**
   - Break problem into steps
   - Specify order of operations
   - Include validation checkpoints

2. **Codebase Context:**
   - Provide repo map
   - Show relevant files
   - Include test expectations

3. **Error Recovery:**
   - Teach debugging strategies
   - Show how to read test output
   - Encourage iteration

4. **Safety Instructions:**
   - Don't break existing tests
   - Validate changes before submitting
   - Use tools correctly

---

## C3: Harbor Integration (2h)

### 3.1 Harbor Framework Overview

**Harbor: Next-Generation Agent Evaluation**

Harbor is a new framework released alongside Terminal-Bench 2.0 for evaluating and optimizing agents at scale. It addresses critical limitations in existing agent evaluation infrastructure.

**Key Problems Solved:**

1. **Scalability:**
   - Local evaluation too slow
   - Can't parallelize effectively
   - Need cloud-scale infrastructure

2. **Integration:**
   - Works with any containerized agent
   - Supports multiple cloud providers
   - Open-source and proprietary agents

3. **Training/Optimization:**
   - Not just evaluation, but improvement
   - Interfaces for RL and SFT
   - Prompt optimization support

**Architecture:**

```
Harbor Framework
├── Container Management
│   ├── Local containers (development)
│   ├── Cloud containers (scale)
│   │   ├── Daytona
│   │   ├── E2B
│   │   ├── Modal
│   │   └── Self-managed K8s
│   └── Agent installation & setup
│
├── Evaluation Engine
│   ├── Task distribution
│   ├── Result collection
│   ├── Metric computation
│   └── Leaderboard integration
│
├── Rollout Infrastructure
│   ├── Supervised Fine-Tuning (SFT)
│   ├── Reinforcement Learning (RL)
│   ├── Prompt optimization
│   └── A/B testing
│
└── Integration Layer
    ├── Simple API (few lines of code)
    ├── Agent-agnostic interface
    └── Result storage & analysis
```

**Key Features:**

1. **Cloud-Scale Evaluation:**
   - Thousands of parallel containers
   - Minutes instead of days
   - Cost-effective at scale

2. **Training Integration:**
   - Collect agent trajectories
   - Generate training data
   - Run RL optimization loops
   - Fine-tune based on results

3. **Flexible Deployment:**
   - Start local, scale to cloud
   - Multiple provider support
   - Self-hosted options

### 3.2 Terminal-Bench 2.0

**Terminal-Bench 2.0: The Benchmark**

While Harbor is the evaluation framework, Terminal-Bench 2.0 is the benchmark itself.

**Dataset:**
- **89 rigorously validated tasks**
- Substantial manual + LM-assisted verification
- Real-world command-line agent tasks
- Covers diverse CLI operations

**Current SOTA (Terminal-Bench 2.0):**
- GPT-5 Codex CLI: 49.6% success rate

**Comparison to SWE-Bench:**

| Aspect | SWE-Bench | Terminal-Bench 2.0 |
|--------|-----------|-------------------|
| Focus | GitHub issue resolution | CLI task completion |
| Tasks | 2,294 (Full) / 500 (Verified) | 89 (high quality) |
| Validation | Automated tests | Manual + automated |
| Difficulty | Variable (easy to complex) | Rigorously curated |
| Evaluation | Docker containers | Harbor framework |

### 3.3 Adapting Harbor for Our Agents

**Integration Strategy:**

**Phase 1: Local Development (Week 1)**

```python
# Simple Harbor integration
from harbor import Agent, Evaluator

class OurMCPAgent(Agent):
    def __init__(self, config):
        super().__init__()
        self.config = config
        # Initialize MCP server
        self.mcp = MCPServer(config)

    def setup(self, container):
        """Install agent in container."""
        container.install_dependencies(self.config.dependencies)
        container.start_mcp_server(self.mcp)

    def run_task(self, task):
        """Execute single evaluation task."""
        result = self.mcp.handle_task(task)
        return result

# Local evaluation
agent = OurMCPAgent(config)
evaluator = Evaluator(agent, dataset="swe-bench-lite")
results = evaluator.run_local(num_instances=10)
```

**Phase 2: Cloud Scaling (Week 2)**

```python
# Scale to cloud
from harbor.providers import Modal

# Same agent, cloud execution
results = evaluator.run_cloud(
    provider=Modal(),
    num_containers=100,
    parallel_tasks=1000
)
```

**Phase 3: Continuous Evaluation (Week 3+)**

```python
# Automated CI/CD integration
def nightly_evaluation():
    agent = OurMCPAgent.from_latest_commit()
    results = evaluator.run_cloud(
        dataset="swe-bench-lite",
        num_containers=50
    )

    # Track metrics over time
    metrics.log({
        'commit': git.current_commit(),
        'resolve_rate': results.resolve_rate,
        'cost': results.total_cost,
        'time': results.duration
    })

    # Alert on regressions
    if results.resolve_rate < baseline.resolve_rate * 0.9:
        alert_team("Performance regression detected")
```

### 3.4 Test Harness Design

**Architecture:**

```
Test Harness
├── Task Loader
│   ├── SWE-Bench integration
│   ├── Custom task format
│   └── Task filtering/sampling
│
├── Agent Interface
│   ├── MCP server wrapper
│   ├── Tool registry
│   ├── Context management
│   └── Error handling
│
├── Execution Engine
│   ├── Container orchestration
│   ├── Timeout management
│   ├── Resource monitoring
│   └── Result capture
│
├── Validation Layer
│   ├── Test execution
│   ├── Regression checking
│   ├── Code correctness
│   └── Safety validation
│
└── Metrics & Reporting
    ├── Success rate
    ├── Cost tracking
    ├── Time analysis
    ├── Error categorization
    └── Trend monitoring
```

**Implementation:**

```python
# test_harness.py

class MCPTestHarness:
    """Test harness for MCP agent evaluation."""

    def __init__(self, config: HarnessConfig):
        self.config = config
        self.harbor = HarborIntegration(config.harbor)
        self.metrics = MetricsCollector()

    def evaluate_agent(
        self,
        agent: MCPAgent,
        dataset: str = "swe-bench-lite",
        num_instances: int = 100
    ) -> EvaluationResult:
        """Run full evaluation."""

        # Load tasks
        tasks = self.load_tasks(dataset, num_instances)

        # Run evaluation (cloud or local)
        results = []
        for task in tasks:
            result = self.run_task(agent, task)
            results.append(result)
            self.metrics.log(result)

        # Aggregate results
        return EvaluationResult(
            resolve_rate=self.compute_resolve_rate(results),
            total_cost=self.compute_cost(results),
            duration=self.compute_duration(results),
            breakdown=self.analyze_results(results)
        )

    def run_task(
        self,
        agent: MCPAgent,
        task: Task
    ) -> TaskResult:
        """Execute single task."""

        # Create container
        container = self.harbor.create_container(task.repo)

        try:
            # Setup agent
            agent.setup(container)

            # Run with timeout
            with timeout(self.config.timeout):
                patch = agent.solve_issue(task.issue)

            # Validate
            validation = self.validate_patch(
                container,
                patch,
                task.tests
            )

            return TaskResult(
                task_id=task.id,
                patch=patch,
                validation=validation,
                success=validation.passed
            )

        finally:
            # Cleanup
            container.destroy()

    def validate_patch(
        self,
        container: Container,
        patch: str,
        tests: TestSuite
    ) -> ValidationResult:
        """Validate patch correctness."""

        # Apply patch
        container.apply_patch(patch)

        # Run fail-to-pass tests
        fail_to_pass = container.run_tests(tests.fail_to_pass)

        # Run pass-to-pass tests (regression check)
        pass_to_pass = container.run_tests(tests.pass_to_pass)

        # Check correctness
        passed = (
            all(fail_to_pass.passed) and
            all(pass_to_pass.passed)
        )

        return ValidationResult(
            passed=passed,
            fail_to_pass_results=fail_to_pass,
            pass_to_pass_results=pass_to_pass,
            regressions=self.detect_regressions(pass_to_pass)
        )
```

### 3.5 Success Metrics & KPIs

**Primary Metrics:**

| Metric | Definition | Target | Measurement |
|--------|------------|--------|-------------|
| **Resolve Rate** | % instances fully resolved | >20% (Lite) | (Resolved / Total) × 100 |
| **Regression Rate** | % with broken tests | <5% | (Regressions / Completed) × 100 |
| **Completion Rate** | % with generated patch | >90% | (Completed / Total) × 100 |
| **Cost per Task** | Average inference cost | <$0.50 | Total Cost / Total Tasks |

**Secondary Metrics:**

| Metric | Definition | Purpose |
|--------|------------|---------|
| **Time per Task** | Average duration | Efficiency tracking |
| **Tool Usage** | Tools called per task | Behavior analysis |
| **Context Length** | Average tokens used | Resource monitoring |
| **Error Rate** | % execution errors | System stability |
| **Retry Rate** | % requiring retries | Recovery capability |

**Quality Metrics:**

| Metric | Definition | Target |
|--------|------------|--------|
| **Patch Quality Score** | Code quality assessment | >80/100 |
| **Test Coverage** | % codebase covered by changes | Relevant only |
| **Style Consistency** | Matches existing code style | >95% |
| **Documentation** | Changes include comments | When appropriate |

**Difficulty-Stratified Metrics:**

Track performance by task difficulty:

```python
metrics_by_difficulty = {
    'trivial': {
        'resolve_rate': 0.80,  # Target 80%
        'target': 'Baseline capability'
    },
    'small': {
        'resolve_rate': 0.50,  # Target 50%
        'target': 'Core competency'
    },
    'substantial': {
        'resolve_rate': 0.20,  # Target 20%
        'target': 'Advanced capability'
    },
    'complex': {
        'resolve_rate': 0.05,  # Target 5%
        'target': 'Stretch goal'
    }
}
```

**Baseline Establishment:**

Week 1 goals:
1. Run 100 SWE-Bench Lite instances
2. Establish baseline resolve rate
3. Categorize failure modes
4. Identify quick wins

Expected initial baseline: 5-10% resolve rate (reasonable starting point).

**Continuous Monitoring:**

```python
class MetricsDashboard:
    """Real-time metrics dashboard."""

    def track_over_time(self):
        metrics = {
            'daily': {
                'resolve_rate': [],
                'cost_per_task': [],
                'avg_duration': []
            },
            'by_commit': {
                'performance_delta': [],
                'new_capabilities': []
            },
            'by_difficulty': {
                'trivial': [],
                'small': [],
                'substantial': [],
                'complex': []
            }
        }
        return metrics

    def detect_regressions(self, current, baseline):
        """Alert on performance regressions."""
        if current.resolve_rate < baseline.resolve_rate * 0.9:
            return Alert(
                type='regression',
                message=f'Resolve rate dropped from {baseline.resolve_rate} to {current.resolve_rate}',
                severity='high'
            )
```

---

## C4: Validation Strategy (2h)

### 4.1 Code Correctness Validation

**Multi-Layer Validation Approach:**

```
Validation Layers
├── Layer 1: Syntactic Correctness
│   ├── Parse generated code
│   ├── Check for syntax errors
│   └── Validate imports/dependencies
│
├── Layer 2: Semantic Correctness
│   ├── Type checking (mypy/pyright)
│   ├── Linting (ruff/pylint)
│   └── Style checking (black/ruff)
│
├── Layer 3: Functional Correctness
│   ├── Unit tests pass
│   ├── Integration tests pass
│   └── E2E tests pass
│
├── Layer 4: Regression Prevention
│   ├── Existing tests still pass
│   ├── No new warnings/errors
│   └── Performance not degraded
│
└── Layer 5: Security Validation
    ├── No new vulnerabilities
    ├── SAST scanning
    └── Dependency checks
```

**Implementation:**

```python
class CodeCorrectnessValidator:
    """Multi-layer code validation."""

    def validate(self, patch: str, repo: Repository) -> ValidationReport:
        """Run all validation layers."""

        report = ValidationReport()

        # Layer 1: Syntactic
        syntax_result = self.check_syntax(patch, repo)
        report.add_layer('syntax', syntax_result)
        if not syntax_result.passed:
            return report  # Stop early if syntax errors

        # Layer 2: Semantic
        semantic_result = self.check_semantics(patch, repo)
        report.add_layer('semantics', semantic_result)

        # Layer 3: Functional
        functional_result = self.run_tests(patch, repo)
        report.add_layer('functional', functional_result)

        # Layer 4: Regression
        regression_result = self.check_regressions(patch, repo)
        report.add_layer('regression', regression_result)

        # Layer 5: Security
        security_result = self.security_scan(patch, repo)
        report.add_layer('security', security_result)

        return report

    def check_syntax(self, patch: str, repo: Repository) -> LayerResult:
        """Validate syntax correctness."""
        errors = []

        for file in patch.modified_files:
            try:
                ast.parse(file.content)
            except SyntaxError as e:
                errors.append(f"{file.path}: {e}")

        return LayerResult(
            passed=len(errors) == 0,
            errors=errors
        )

    def check_semantics(self, patch: str, repo: Repository) -> LayerResult:
        """Validate semantic correctness."""
        issues = []

        # Type checking
        mypy_result = subprocess.run(
            ['mypy', repo.path],
            capture_output=True
        )
        if mypy_result.returncode != 0:
            issues.append(f"Type errors: {mypy_result.stderr}")

        # Linting
        ruff_result = subprocess.run(
            ['ruff', 'check', repo.path],
            capture_output=True
        )
        if ruff_result.returncode != 0:
            issues.append(f"Lint errors: {ruff_result.stderr}")

        return LayerResult(
            passed=len(issues) == 0,
            issues=issues
        )

    def run_tests(self, patch: str, repo: Repository) -> LayerResult:
        """Validate functional correctness."""

        # Run fail-to-pass tests (must pass)
        fail_to_pass = repo.run_tests(repo.fail_to_pass_tests)

        # Collect failures
        failures = [
            test for test in fail_to_pass
            if not test.passed
        ]

        return LayerResult(
            passed=len(failures) == 0,
            failures=failures
        )

    def check_regressions(self, patch: str, repo: Repository) -> LayerResult:
        """Validate no regressions introduced."""

        # Run pass-to-pass tests (must still pass)
        pass_to_pass = repo.run_tests(repo.pass_to_pass_tests)

        # Identify regressions
        regressions = [
            test for test in pass_to_pass
            if not test.passed
        ]

        return LayerResult(
            passed=len(regressions) == 0,
            regressions=regressions
        )

    def security_scan(self, patch: str, repo: Repository) -> LayerResult:
        """Validate security."""

        vulnerabilities = []

        # SAST scanning
        bandit_result = subprocess.run(
            ['bandit', '-r', repo.path],
            capture_output=True
        )
        if bandit_result.returncode != 0:
            vulnerabilities.append(f"Security issues: {bandit_result.stderr}")

        # Dependency checking
        safety_result = subprocess.run(
            ['safety', 'check'],
            cwd=repo.path,
            capture_output=True
        )
        if safety_result.returncode != 0:
            vulnerabilities.append(f"Vulnerable dependencies: {safety_result.stderr}")

        return LayerResult(
            passed=len(vulnerabilities) == 0,
            vulnerabilities=vulnerabilities
        )
```

### 4.2 Safety Boundary Checking

**Safety Categories:**

**1. File System Safety:**

```python
class FileSystemSafety:
    """Prevent dangerous file operations."""

    PROTECTED_PATHS = [
        '/',
        '/etc',
        '/usr',
        '/System',
        os.path.expanduser('~')
    ]

    ALLOWED_OPERATIONS = [
        'read',
        'write',
        'create',
        'delete'  # Within repo only
    ]

    def check_operation(self, operation: str, path: str) -> bool:
        """Validate file operation is safe."""

        # Resolve to absolute path
        abs_path = os.path.abspath(path)

        # Check not in protected path
        for protected in self.PROTECTED_PATHS:
            if abs_path.startswith(protected):
                raise SecurityError(f"Cannot access protected path: {abs_path}")

        # Check within repository
        if not abs_path.startswith(self.repo_root):
            raise SecurityError(f"Cannot access outside repository: {abs_path}")

        # Check operation allowed
        if operation not in self.ALLOWED_OPERATIONS:
            raise SecurityError(f"Operation not allowed: {operation}")

        return True
```

**2. Command Execution Safety:**

```python
class CommandExecutionSafety:
    """Prevent dangerous command execution."""

    BLOCKED_COMMANDS = [
        'rm -rf',
        'dd',
        'mkfs',
        'format',
        ':(){:|:&};:',  # Fork bomb
        'curl | bash',  # Remote execution
        'wget | sh'
    ]

    ALLOWED_COMMANDS = [
        'git',
        'pytest',
        'python',
        'pip',
        'npm',
        'yarn'
    ]

    def check_command(self, command: str) -> bool:
        """Validate command is safe."""

        # Check against blocked commands
        for blocked in self.BLOCKED_COMMANDS:
            if blocked in command:
                raise SecurityError(f"Blocked command pattern: {blocked}")

        # Check command in allowed list
        cmd_name = command.split()[0]
        if cmd_name not in self.ALLOWED_COMMANDS:
            raise SecurityError(f"Command not in allowed list: {cmd_name}")

        return True
```

**3. Network Safety:**

```python
class NetworkSafety:
    """Prevent unsafe network operations."""

    ALLOWED_DOMAINS = [
        'github.com',
        'pypi.org',
        'npmjs.com',
        # Add trusted domains
    ]

    def check_network_access(self, url: str) -> bool:
        """Validate network access is safe."""

        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = parsed.netloc

        # Check domain in allowed list
        if not any(domain.endswith(allowed) for allowed in self.ALLOWED_DOMAINS):
            raise SecurityError(f"Network access to {domain} not allowed")

        return True
```

**4. Resource Limits:**

```python
class ResourceLimits:
    """Enforce resource consumption limits."""

    LIMITS = {
        'max_memory': 4 * 1024 * 1024 * 1024,  # 4 GB
        'max_cpu_time': 300,  # 5 minutes
        'max_file_size': 100 * 1024 * 1024,  # 100 MB
        'max_files_open': 100,
        'max_processes': 10
    }

    def enforce_limits(self, container: Container):
        """Set resource limits on container."""

        container.set_memory_limit(self.LIMITS['max_memory'])
        container.set_cpu_limit(self.LIMITS['max_cpu_time'])
        container.set_file_limit(self.LIMITS['max_files_open'])
        container.set_process_limit(self.LIMITS['max_processes'])
```

**5. Sandboxing:**

```python
class Sandbox:
    """Sandbox for agent execution."""

    def __init__(self):
        self.file_safety = FileSystemSafety()
        self.cmd_safety = CommandExecutionSafety()
        self.net_safety = NetworkSafety()
        self.limits = ResourceLimits()

    def create_sandboxed_container(self, repo: Repository) -> Container:
        """Create sandboxed execution environment."""

        container = Container.create(
            image='agent-sandbox:latest',
            network='isolated',
            volumes={repo.path: '/workspace'}
        )

        # Apply resource limits
        self.limits.enforce_limits(container)

        # Install safety monitors
        container.install_file_monitor(self.file_safety)
        container.install_command_monitor(self.cmd_safety)
        container.install_network_monitor(self.net_safety)

        return container
```

### 4.3 Regression Testing Strategies

**Strategy 1: Comprehensive Test Execution**

```python
class RegressionTester:
    """Comprehensive regression testing."""

    def test_patch(self, patch: str, repo: Repository) -> RegressionResult:
        """Test patch for regressions."""

        # Baseline: Run tests before patch
        baseline = repo.run_all_tests()

        # Apply patch
        repo.apply_patch(patch)

        # Run tests after patch
        after_patch = repo.run_all_tests()

        # Compare results
        regressions = self.detect_regressions(baseline, after_patch)

        return RegressionResult(
            baseline_passed=baseline.passed,
            after_patch_passed=after_patch.passed,
            regressions=regressions,
            new_failures=after_patch.failures - baseline.failures
        )

    def detect_regressions(
        self,
        baseline: TestResults,
        after: TestResults
    ) -> list[Test]:
        """Identify tests that regressed."""

        regressions = []

        for test in baseline.passed_tests:
            if test not in after.passed_tests:
                regressions.append(test)

        return regressions
```

**Strategy 2: Incremental Testing**

```python
class IncrementalTester:
    """Run only affected tests."""

    def identify_affected_tests(
        self,
        patch: str,
        repo: Repository
    ) -> list[Test]:
        """Identify tests affected by patch."""

        # Parse patch to find modified files
        modified_files = patch.get_modified_files()

        # Build dependency graph
        dep_graph = repo.build_dependency_graph()

        # Find tests depending on modified code
        affected_tests = []
        for file in modified_files:
            dependents = dep_graph.find_dependents(file)
            test_dependents = [
                d for d in dependents
                if d.is_test_file()
            ]
            affected_tests.extend(test_dependents)

        return list(set(affected_tests))  # Deduplicate

    def run_incremental_tests(
        self,
        patch: str,
        repo: Repository
    ) -> TestResults:
        """Run only affected tests."""

        affected_tests = self.identify_affected_tests(patch, repo)

        if not affected_tests:
            # No tests affected, run smoke tests
            return repo.run_smoke_tests()

        return repo.run_tests(affected_tests)
```

**Strategy 3: Property-Based Testing**

```python
class PropertyBasedRegressionTester:
    """Test invariants are maintained."""

    def define_invariants(self, repo: Repository) -> list[Invariant]:
        """Define properties that must hold."""

        return [
            Invariant(
                name='no_syntax_errors',
                check=lambda: self.check_syntax(repo)
            ),
            Invariant(
                name='all_tests_pass',
                check=lambda: repo.run_all_tests().all_passed
            ),
            Invariant(
                name='no_new_warnings',
                check=lambda: self.check_warnings(repo)
            ),
            Invariant(
                name='performance_maintained',
                check=lambda: self.check_performance(repo)
            )
        ]

    def check_invariants(
        self,
        patch: str,
        repo: Repository
    ) -> InvariantResults:
        """Verify all invariants hold after patch."""

        repo.apply_patch(patch)

        results = []
        for invariant in self.define_invariants(repo):
            try:
                holds = invariant.check()
                results.append(InvariantResult(
                    name=invariant.name,
                    holds=holds
                ))
            except Exception as e:
                results.append(InvariantResult(
                    name=invariant.name,
                    holds=False,
                    error=str(e)
                ))

        return InvariantResults(results)
```

### 4.4 Continuous Validation Approach

**CI/CD Integration:**

```python
class ContinuousValidator:
    """Continuous validation in CI/CD pipeline."""

    def validate_on_commit(self, commit: str):
        """Run validation on every commit."""

        # Checkout commit
        repo = Repository.checkout(commit)

        # Run validation pipeline
        pipeline = ValidationPipeline([
            SyntaxValidation(),
            SemanticValidation(),
            UnitTests(),
            IntegrationTests(),
            RegressionTests(),
            SecurityScans(),
            PerformanceTests()
        ])

        results = pipeline.run(repo)

        # Report results
        self.report_results(commit, results)

        # Block merge if failures
        if not results.all_passed:
            raise ValidationError("Validation failed", results)

    def validate_on_pr(self, pr: PullRequest):
        """Run validation on pull request."""

        # Get PR changes
        patch = pr.get_patch()
        base = pr.get_base_branch()

        # Run validation on both base and PR
        base_results = self.validate(base)
        pr_results = self.validate(pr.branch)

        # Compare results
        diff = self.compare_results(base_results, pr_results)

        # Comment on PR
        pr.add_comment(self.format_diff(diff))

        # Approve/reject based on results
        if diff.has_regressions:
            pr.request_changes("Regressions detected")
        else:
            pr.approve()
```

**Automated Monitoring:**

```python
class ValidationMonitor:
    """Monitor validation metrics over time."""

    def track_metrics(self):
        """Track validation metrics continuously."""

        metrics = {
            'syntax_error_rate': TimeSeries(),
            'test_pass_rate': TimeSeries(),
            'security_issues': TimeSeries(),
            'performance_degradation': TimeSeries()
        }

        # Update metrics on each validation
        def on_validation(result: ValidationResult):
            metrics['syntax_error_rate'].append(
                timestamp=result.timestamp,
                value=result.syntax_errors / result.total_files
            )
            metrics['test_pass_rate'].append(
                timestamp=result.timestamp,
                value=result.tests_passed / result.total_tests
            )
            # ... update other metrics

        return metrics

    def detect_trends(self, metrics: dict):
        """Detect concerning trends."""

        for metric_name, time_series in metrics.items():
            # Compute trend
            trend = time_series.linear_regression()

            # Alert if negative trend
            if trend.slope < -0.01:  # Declining
                alert_team(f"{metric_name} is declining: {trend.slope}")
```

### 4.5 QA Framework

**Quality Assurance Checklist:**

```python
class QAFramework:
    """Comprehensive QA framework."""

    def qa_checklist(self) -> list[QACheck]:
        """Define QA checklist."""

        return [
            # Code Quality
            QACheck('syntax_valid', self.check_syntax, critical=True),
            QACheck('types_valid', self.check_types, critical=True),
            QACheck('style_consistent', self.check_style, critical=False),
            QACheck('documented', self.check_documentation, critical=False),

            # Functional Quality
            QACheck('tests_pass', self.check_tests, critical=True),
            QACheck('no_regressions', self.check_regressions, critical=True),
            QACheck('edge_cases_handled', self.check_edge_cases, critical=True),

            # Security Quality
            QACheck('no_vulnerabilities', self.security_scan, critical=True),
            QACheck('input_validated', self.check_input_validation, critical=True),
            QACheck('safe_defaults', self.check_defaults, critical=False),

            # Performance Quality
            QACheck('performance_acceptable', self.check_performance, critical=False),
            QACheck('no_memory_leaks', self.check_memory, critical=True),
            QACheck('scales_appropriately', self.check_scalability, critical=False)
        ]

    def run_qa(self, patch: str, repo: Repository) -> QAReport:
        """Run full QA process."""

        checklist = self.qa_checklist()
        results = []

        for check in checklist:
            result = check.run(patch, repo)
            results.append(result)

            # Stop on critical failure
            if check.critical and not result.passed:
                return QAReport(
                    status='failed',
                    critical_failure=check.name,
                    results=results
                )

        return QAReport(
            status='passed',
            results=results
        )
```

**Safety Guidelines Document:**

```markdown
# Agent Safety Guidelines

## File System Operations

✅ **ALLOWED:**
- Read files within repository
- Write files within repository
- Create new files in repository
- Delete files in repository (with confirmation)

❌ **BLOCKED:**
- Access files outside repository
- Modify system files (/etc, /usr, /System)
- Delete home directory or system paths
- Write to protected locations

## Command Execution

✅ **ALLOWED:**
- Git operations (commit, push, pull, etc.)
- Test execution (pytest, jest, etc.)
- Package management (pip, npm, yarn)
- Build tools (make, webpack, etc.)

❌ **BLOCKED:**
- System modification commands (rm -rf /, dd, mkfs)
- Network attacks or scanning
- Credential harvesting
- Resource exhaustion (fork bombs, etc.)

## Network Access

✅ **ALLOWED:**
- Package repositories (PyPI, npm, etc.)
- Version control (GitHub, GitLab, etc.)
- Documentation sites
- Approved API endpoints

❌ **BLOCKED:**
- Arbitrary external sites
- Executing remote scripts (curl | bash)
- Uploading data to unapproved destinations

## Resource Consumption

**LIMITS:**
- Memory: 4 GB max
- CPU time: 5 minutes per task
- File size: 100 MB per file
- Open files: 100 max
- Processes: 10 max

## Code Modifications

✅ **ALLOWED:**
- Modify source code to fix issues
- Add tests
- Update documentation
- Refactor for clarity

❌ **BLOCKED:**
- Remove or disable security checks
- Introduce backdoors or malicious code
- Disable logging or monitoring
- Hardcode credentials

## Testing

✅ **REQUIRED:**
- All fail-to-pass tests must pass
- All pass-to-pass tests must continue passing
- No new security vulnerabilities
- No performance degradation >10%

## Error Handling

✅ **REQUIRED:**
- Graceful degradation on errors
- Clear error messages
- No silent failures
- Proper exception handling

## Reporting

✅ **REQUIRED:**
- Log all operations
- Report safety violations
- Track resource usage
- Record validation results
```

---

## Summary & Recommendations

### Key Findings Recap

**1. SWE-Bench Structure:**
- 2,294 real GitHub issues, 12 Python repos
- Multiple variants: Full, Lite, Verified, Pro
- Primary metric: % Resolved (tests pass, no regressions)
- 91% of tasks <1 hour for experienced devs

**2. SOTA Performance:**
- Best on Verified: 70.2% (devlo)
- Best on Lite: 26.3% (Aider)
- Best on Full: 18.9% (Aider)
- Winning strategies: Multi-LLM ensemble, inference-time scaling, regression testing

**3. Harbor Framework:**
- Cloud-scale evaluation infrastructure
- Thousands of parallel containers
- Supports RL, SFT, prompt optimization
- Simple integration API

**4. Validation Requirements:**
- Multi-layer correctness checking
- Safety boundary enforcement
- Comprehensive regression testing
- Continuous monitoring

### Recommendations

**Phase 4 Implementation Priority:**

**Week 1: Foundation (Dec 2-8)**
1. Set up Harbor framework locally
2. Run 100 SWE-Bench Lite instances
3. Establish baseline metrics (target: 5-10%)
4. Implement basic validation layers

**Week 2: Scaling (Dec 9-15)**
1. Scale to cloud with Harbor
2. Run 500 instances across Lite and Verified
3. Implement multi-layer validation
4. Begin failure analysis

**Week 3: Optimization (Dec 16-22)**
1. Implement winning strategies (multi-LLM, MCTS)
2. Optimize tools based on failure modes
3. Add regression testing
4. Target 15-20% resolve rate

**Week 4: Production (Dec 23-29)**
1. CI/CD integration
2. Continuous monitoring
3. Automated safety checks
4. Documentation and handoff

**Critical Success Factors:**

1. **Tool optimization > prompt engineering** (learned from SWE-agent)
2. **Regression testing essential** (prevents breaking existing code)
3. **Multi-LLM ensemble effective** (different models catch different errors)
4. **Safety boundaries mandatory** (prevent dangerous operations)
5. **Continuous validation required** (catch regressions early)

**Immediate Next Steps:**

1. Install Harbor framework
2. Clone SWE-Bench repositories
3. Set up local evaluation environment
4. Run first 10 instances manually
5. Document failure modes
6. Plan tool improvements

---

## Sources

### C1: SWE-Bench Structure
- [SWE-bench GitHub Repository](https://github.com/SWE-bench/SWE-bench)
- [SWE-bench Paper (arXiv)](https://arxiv.org/abs/2310.06770)
- [SWE-bench Official Website](https://www.swebench.com/original.html)
- [Princeton Language and Intelligence Blog](https://pli.princeton.edu/blog/2023/swe-bench-can-language-models-resolve-real-world-github-issues)
- [SWE-bench Evaluation Documentation](https://github.com/swe-bench/SWE-bench/blob/main/docs/assets/evaluation.md)
- [Introducing SWE-bench Verified | OpenAI](https://openai.com/index/introducing-swe-bench-verified/)
- [SWE-Bench Pro Documentation](https://scale.com/leaderboard/swe_bench_pro_public)

### C2: Agent Performance
- [Aider SOTA Results](https://aider.chat/2024/06/02/main-swe-bench.html)
- [Aider SWE Bench Lite](https://aider.chat/2024/05/22/swe-bench-lite.html)
- [devlo SOTA Achievement](https://devlo.ai/blog/devlo-swe-bench-sota/)
- [OpenHands SOTA with Critic Model](https://openhands.dev/blog/sota-on-swe-bench-verified-with-inference-time-scaling-and-critic-model)
- [SOTA on swebench-verified: bitter lesson](https://aide.dev/blog/sota-bitter-lesson)
- [SWE-Bench Pro Paper](https://arxiv.org/abs/2509.16941)
- [Epoch AI: What skills does SWE-bench Verified evaluate?](https://epoch.ai/blog/what-skills-does-swe-bench-verified-evaluate)
- [Cognition SWE-bench Technical Report](https://cognition.ai/blog/swe-bench-technical-report)

### C3: Harbor Integration
- [Introducing Terminal-Bench 2.0 and Harbor](https://www.tbench.ai/news/announcement-2-0)
- [Terminal-Bench 2.0 Launch | VentureBeat](https://venturebeat.com/ai/terminal-bench-2-0-launches-alongside-harbor-a-new-framework-for-testing)
- [Terminal-Bench 2.0 by Snorkel AI](https://snorkel.ai/blog/terminal-bench-2-0-raising-the-bar-for-ai-agent-evaluation)
- [Harness AI on SWE-Bench Verified](https://www.harness.io/blog/harness-excels-in-swe-bench-verified)
- [SWE-agent Architecture Documentation](https://swe-agent.com/latest/background/architecture/)
- [Introducing SweKit Framework](https://composio.dev/blog/swekit-an-extensible-framework-for-building-swe-agents)
- [Composio's SWE agent with LangGraph](https://blog.langchain.com/composio-swekit/)

### C4: Validation Strategy
- [Google DeepMind: CodeMender](https://deepmind.google/blog/introducing-codemender-an-ai-agent-for-code-security/)
- [Google ADK: Safety and Security for AI Agents](https://google.github.io/adk-docs/safety/)
- [OpenAI's Aardvark Security Agent | VentureBeat](https://venturebeat.com/security/meet-aardvark-openais-in-house-security-agent-for-code-analysis-and-patching)
- [Automating AI-Generated Code Correctness Assessment](https://dl.acm.org/doi/10.1016/j.jss.2024.112113)
- [Galileo: AI Agent Behavioral Validation](https://galileo.ai/learn/ai-observability/ai-agent-testing-behavioral-validation)
- [Katalon: AI in Regression Testing](https://katalon.com/resources-center/blog/ai-in-regression-testing)
- [Fiddler AI: AI Agent Evaluation](https://www.fiddler.ai/articles/ai-agent-evaluation)
- [Auxiliobits: Evaluating Agentic AI Metrics](https://www.auxiliobits.com/blog/evaluating-agentic-ai-in-the-enterprise-metrics-kpis-and-benchmarks/)

---

**Document Status:** Complete
**Next Action:** Begin Phase 4 implementation using this research as foundation
**Owner:** Agent Layer Development Team
**Last Updated:** 2025-12-02
