# Coverage Work Packages

Individual work packages for improving test coverage in the `optimization` module.

## Quick Start

Each package is a self-contained prompt that can be handed to an agent. Packages are prioritized:

### HIGH PRIORITY (Start Here)
1. **PACKAGE_01_PARALLEL_EXECUTOR.md** - 2 lines, 30-60 min → 100% coverage
2. **PACKAGE_02_COMPRESSION_TYPES.md** - 7 lines, 30-45 min → 95%+ coverage  
3. **PACKAGE_03_PREACT_MEMORY.md** - 18 lines, 1-2 hours → 90%+ coverage

### MEDIUM PRIORITY (After Quick Wins)
4. **PACKAGE_04_MODEL_ROUTER.md** - ~25 lines, 1-2 hours → 85%+ coverage
5. **PACKAGE_05_INTEGRATION_PIPELINE.md** - ~30 lines, 1-2 hours → 80%+ coverage
6. **PACKAGE_06_PREACT_PREDICTOR.md** - ~32 lines, 1-2 hours → 92%+ coverage
7. **PACKAGE_07_PROMPT_CACHE.md** - ~12 lines, 30-60 min → 97%+ coverage

### LOW PRIORITY (Optional)
8. **PACKAGE_08_MEMORY_SUBSYSTEMS.md** - Large, 4-6 hours → 60%+ coverage
9. **PACKAGE_09_STREAMING.md** - Large, 2-3 hours → 60%+ coverage
10. **PACKAGE_10_HTTP2.md** - Large, 2-3 hours → 60%+ coverage

## Usage

1. **Select a package** based on priority
2. **Read the package file** for detailed instructions
3. **Execute the tasks** following the provided patterns
4. **Verify coverage** using the provided commands
5. **Mark complete** in `COVERAGE_WORK_PACKAGES.md`

## Current Status

- Overall Coverage: **66%** (1029 missing lines)
- Target: **80%+** overall, **90%+** for core modules

## Package Format

Each package includes:
- **Objective**: Clear goal
- **Missing Lines**: Specific lines to cover
- **Tasks**: Step-by-step instructions
- **Verification**: How to check success
- **Reference**: Relevant files and code

## Agent Instructions

When working on a package:
1. Read the package file completely
2. Review referenced code files
3. Follow existing test patterns
4. Run verification commands
5. Ensure all tests pass
6. Update completion status
