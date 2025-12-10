# Code Cleanup Checklist

## Unrelated Code Found in SmartCP

### Go Code (✅ KEEP - Project CLI)
**Status**: Legitimate SmartCP CLI code - **KEEP ALL**

- [x] `smartcp/cmd/smartcpcli/main.go` → **KEEP** (CLI entrypoint)
- [x] `smartcp/internal/cmd/*.go` (7 files) → **KEEP** (CLI commands)
- [x] `smartcp/internal/config/config.go` → **KEEP** (CLI config)
- [x] `smartcp/internal/services/*.go` (2 files) → **KEEP** (CLI services)
- [x] `smartcp/go.mod` → **KEEP** (Go module)
- [x] `smartcp/go.sum` → **KEEP** (Go dependencies)
- [x] `smartcp/Makefile` → **KEEP** (CLI build tooling)

**Action Items**:
- [ ] Document Go CLI in README
- [ ] Exclude Go files from Python coverage
- [ ] Add Go build artifacts to `.gitignore`

### Docker Configs (Review if needed)
- [ ] `smartcp/docker-compose.yml` - Keep if for SmartCP local dev
- [ ] `smartcp/docker-compose.local.example.yml` - Keep if needed
- [ ] Add `.dockerignore` if missing

### Tunnel Config (Remove)
- [ ] `smartcp/tunnel_config.json` - Remove (unrelated)

### Legacy Code (Review)
- [ ] `smartcp/main.py` - Determine if deprecated
  - If deprecated: Remove and update imports
  - If active: Add to coverage plan

### Bifrost Client (Keep - Part of SmartCP)
- [x] `smartcp/bifrost_client.py` - **KEEP** (delegation layer)
  - Add to coverage plan (Phase 6)

## Action Items

1. **Before Coverage**: Complete Phase 0 cleanup
2. **Decision Needed**: Is `main.py` deprecated?
3. **Decision Needed**: Are Docker configs for SmartCP or bifrost-extensions?
