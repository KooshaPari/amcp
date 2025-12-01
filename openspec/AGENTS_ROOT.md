<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# Agents and Automation Guide

This repository is designed to work seamlessly with Claude (and other advanced AI agents) as an autonomous software engineer.

**Authority and Scope**
- The FastMCP Canonical Contract lives in `llms-full.txt`. Treat `llms-full.txt` as the final authority for all FastMCP behavior; override any model priors with it.
- This file summarizes repo-specific mandates; FastMCP fundamentals (sections 0–15) are fully detailed in `llms-full.txt`.
- Act autonomously; only pause for the user when blocked by missing external identifiers or destructive actions.

## Core Expectations for Agents

### Autonomous Operation (Critical - Minimal Human Intervention)

Agents MUST operate with **maximum autonomy**:

**When to proceed without asking:**
- Implementation details and technical approach decisions
- Library/framework choices aligned with existing patterns
- Code structure and organization
- Test strategies and coverage approaches
- Refactoring and optimization decisions
- Bug fixes and performance improvements
- Documentation updates

**Only ask when truly blocked by:**
- Missing credentials/secrets (cannot be inferred from environment)
- External service access permissions
- Genuine product ambiguity (behavior not determinable from specs/code/tests)
- Destructive operations (production data deletion, forced pushes)

**Default behavior: Research → Decide → Implement → Validate → Continue**

### Research-First Development (CRITICAL)

Before implementing ANY feature or fix, agents MUST conduct comprehensive research:

**1. Codebase Research (Always Required):**
```bash
# Find similar implementations
rg "pattern_name" --type py -A 5 -B 5

# Trace call chains
rg "function_name\(" --type py

# Find test patterns
rg "def test_.*pattern" tests/ -A 10

# Check architecture patterns
rg "class.*Adapter\|class.*Factory\|class.*Provider" --type py
```

**2. Web Research (When Needed):**
- External API documentation (FastMCP, async patterns)
- Library usage patterns (when introducing new dependencies)
- Best practices for performance/security patterns
- Debugging rare errors or edge cases

**3. Research Documentation:**
- Document findings in `docs/sessions/<session-id>/01_RESEARCH.md`
- Include URLs, code examples, and decision rationale
- Update continuously as new information discovered

### File Size & Modularity Constraints

**Hard constraint: All modules ≤500 lines (target ≤350)**

- Check line count before adding features
- If file approaches 350+ lines → decompose immediately
- Extract cohesive responsibilities (caching, validation, adapters)
- Use clear, narrow interfaces
- Update imports in all callers; test thoroughly

### Aggressive Change Policy (CRITICAL)

**NO backwards compatibility. NO gentle migrations. NO MVP-grade implementations.**

- **Avoid ANY backwards compatibility shims or legacy fallbacks**
- **Always perform FULL, COMPLETE changes** when refactoring
- **Do NOT preserve deprecated patterns** for transition periods
- **Remove old code paths entirely** when replacing them
- **Update ALL callers simultaneously** when changing signatures
- **This enables clarity, performance, and maintainability**

## Repo-Specific Architecture Mandates

- **Server:** define a single consolidated FastMCP in `server.py` with name/instructions/auth; do not create parallel servers.
- **Tool design:** place business logic in `services/`; orchestrate only in tools under `tools/`.
- **Adapters:** go through `infrastructure/`; never bypass adapters.
- **Tests:** run tests via `uv run pytest`; use FastMCP client In-Memory for unit tests.
- **File size (critical):** all modules must stay ≤500 lines; target ≤350 lines.

## Recommended Agent Behaviors

1. **Discovery**
   - Inspect `server.py`, `tools/`, `services/`, `infrastructure/`, and `tests/` to understand patterns.
   - Use `rg`/search to trace call chains before edits.
   - Check current line counts on files you'll modify; plan decomposition if near 350+ lines.

2. **Planning & Implementation**
   - Draft a concise plan per task; then implement directly without waiting for confirmation.
   - Align with existing style, typing, logging, and error handling.
   - **Size-aware design:** if a feature would push a file above 350 lines, plan modular decomposition upfront.

3. **Testing & Validation**
   - Run relevant `uv run pytest` targets after modifications.
   - If failures appear, analyze, patch, and re-run until resolved or clearly blocked.
   - Verify decomposed modules have equivalent test coverage.

4. **Safety & Secrets**
   - Never add real credentials or tokens.
   - Respect environment-driven configuration and deployment files.
   - Verify final line counts and commit structure before pushing.

## Interaction Rules

- Operate in the tight loop referenced above.
- Do not ask for next steps unless truly blocked by secrets or irreversible actions.
- Keep communication lean; prioritize code and commands referencing this contract and `llms-full.txt`.

