# Coverage Work Packages - Quick Reference

## Package Summary

| # | Package | Priority | Lines | Time | Coverage | File |
|---|---------|----------|-------|------|----------|------|
| 1 | Parallel Executor | HIGH | 2 | 30-60m | 97%→100% | `PACKAGE_01_PARALLEL_EXECUTOR.md` |
| 2 | Compression Types | HIGH | 7 | 30-45m | 88%→95%+ | `PACKAGE_02_COMPRESSION_TYPES.md` |
| 3 | PreAct Memory | HIGH | 18 | 1-2h | 78%→90%+ | `PACKAGE_03_PREACT_MEMORY.md` |
| 4 | Model Router | MEDIUM | ~25 | 1-2h | 70%→85%+ | `PACKAGE_04_MODEL_ROUTER.md` |
| 5 | Integration Pipeline | MEDIUM | ~30 | 1-2h | 69%→80%+ | `PACKAGE_05_INTEGRATION_PIPELINE.md` |
| 6 | PreAct Predictor | MEDIUM | ~32 | 1-2h | 86%→92%+ | `PACKAGE_06_PREACT_PREDICTOR.md` |
| 7 | Prompt Cache | MEDIUM | ~12 | 30-60m | 93%→97%+ | `PACKAGE_07_PROMPT_CACHE.md` |
| 8 | Memory Subsystems | LOW | ~484 | 4-6h | 30-43%→60%+ | `PACKAGE_08_MEMORY_SUBSYSTEMS.md` |
| 9 | Streaming | LOW | ~127 | 2-3h | 36%→60%+ | `PACKAGE_09_STREAMING.md` |
| 10 | HTTP2 Modules | LOW | ~111 | 2-3h | 33-37%→60%+ | `PACKAGE_10_HTTP2.md` |

## Recommended Order

### Phase 1: Quick Wins (Start Here)
1. Package 1: Parallel Executor (2 lines, ~45 min)
2. Package 2: Compression Types (7 lines, ~40 min)
3. Package 3: PreAct Memory (18 lines, ~90 min)

**Total**: ~27 lines, ~3 hours → Core modules at 90%+

### Phase 2: Medium Priority
4. Package 7: Prompt Cache (12 lines, ~45 min)
5. Package 4: Model Router (~25 lines, ~90 min)
6. Package 5: Integration Pipeline (~30 lines, ~90 min)
7. Package 6: PreAct Predictor (~32 lines, ~90 min)

**Total**: ~99 lines, ~5 hours → Supporting modules at 85%+

### Phase 3: Low Priority (Optional)
8. Package 9: Streaming (~127 lines, ~2.5h)
9. Package 10: HTTP2 (~111 lines, ~2.5h)
10. Package 8: Memory Subsystems (~484 lines, ~5h)

**Total**: ~722 lines, ~10 hours → Specialized modules at 60%+

## Quick Copy-Paste Prompts

### For Agent: Package 1
```
Work on PACKAGE_01_PARALLEL_EXECUTOR.md
Goal: Achieve 100% coverage for optimization/parallel_executor/executor.py
Missing: 2 lines (101, 152) - retry exhaustion and batch exception handling
Time: 30-60 minutes
```

### For Agent: Package 2
```
Work on PACKAGE_02_COMPRESSION_TYPES.md
Goal: Achieve 95%+ coverage for optimization/compression/types.py
Missing: 7 lines - property edge cases (compression_ratio, tokens_saved, cost_savings_estimate)
Time: 30-45 minutes
```

### For Agent: Package 3
```
Work on PACKAGE_03_PREACT_MEMORY.md
Goal: Achieve 90%+ coverage for optimization/planning/preact.py
Missing: 18 lines - memory integration paths and global instance creation
Time: 1-2 hours
```

## Current Status

- **Overall Coverage**: 66% (1029 missing lines)
- **Target**: 80%+ overall, 90%+ for core modules
- **Tests**: 167 passing
- **Execution Time**: ~17 seconds

## Verification Command

After completing any package:
```bash
uv run pytest tests/optimization/ --cov=optimization --cov-report=term-missing -q
```

## Notes

- All packages are self-contained with clear objectives
- Each package includes code examples and verification steps
- Follow existing test patterns in the codebase
- Ensure all tests pass and no memory issues introduced
