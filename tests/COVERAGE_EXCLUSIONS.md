# Coverage Exclusions

## Go Code (Excluded from Python Coverage)

The SmartCP project includes Go code for the CLI tool (`smartcpcli`). This code should be **excluded** from Python coverage metrics.

### Go Files (Exclude from Coverage)
- `smartcp/cmd/**/*.go`
- `smartcp/internal/**/*.go`
- `smartcp/go.mod`
- `smartcp/go.sum`

### Coverage Command
```bash
# Exclude Go files from coverage
coverage run --source=smartcp/runtime,smartcp/tools -m pytest smartcp/tests/unit/ -v

# Or explicitly exclude Go files
coverage run --source=smartcp --omit='**/*.go' -m pytest smartcp/tests/unit/ -v
```

### Coverage Report
```bash
# Report only Python files
coverage report --include="smartcp/**/*.py" --omit="**/*.go"
```

## Other Exclusions

### Build Artifacts
- `smartcpcli` (Go binary)
- `*.exe` (Windows binaries)
- `__pycache__/`
- `*.pyc`
- `.venv/`

### Test Files
- Test files themselves are not included in coverage
- Only source code (`smartcp/runtime/`, `smartcp/tools/`) is measured

## Verification

To verify Go files are excluded:
```bash
coverage report --include="smartcp/**/*.py" --show-missing | grep -i "\.go" | wc -l
# Should return 0 (no Go files in report)
```
