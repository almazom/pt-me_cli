# p2me CLI: AI Agent Confidence Improvement Plan

## Target: 95%+ Confidence & Satisfaction for AI Agent Use

**Current State:**
- Confidence: 7/10
- Satisfaction: 6/10
- Test Coverage: 68 tests passing

**Target State:**
- Confidence: 9.5/10
- Satisfaction: 9.5/10
- Test Coverage: 100+ tests

---

## Phase 1: PREDICTABILITY (Target: +2 points)

### 1.1 Normalize Error Schema
**Problem:** Errors appear in multiple places (`errors[]`, `publish.error`, nested objects)

**Solution:**
```
ALL errors go to top-level errors[] with consistent structure:
{
  "ok": false,
  "errors": [
    {
      "code": "FILE_NOT_FOUND",
      "message": "File not found: nonexistent.md",
      "stage": "input",
      "recoverable": false
    }
  ]
}
```

**Files to modify:**
- [ ] `src/p2me/chain.py` - normalize errors from publish/notify
- [ ] `src/p2me/cli.py` - ensure consistent output

**Tests needed:**
- [ ] Test: all errors have code, message, stage
- [ ] Test: error codes are consistent (FILE_ERROR, NETWORK_ERROR, etc.)
- [ ] Test: nested errors are flattened

### 1.2 Add JSON Schema
**Problem:** AI doesn't know output structure

**Solution:**
```bash
p2me --schema          # Output JSON schema
p2me --schema strict   # Output with all fields documented
```

**Files to create/modify:**
- [ ] `src/p2me/schema.py` - define output schema
- [ ] `src/p2me/cli.py` - add --schema flag

**Tests needed:**
- [ ] Test: --schema outputs valid JSON Schema
- [ ] Test: schema matches actual output structure

### 1.3 Strict JSON Mode
**Problem:** Output format may vary

**Solution:**
```bash
p2me file.md --strict  # Guaranteed schema compliance
```

**Tests needed:**
- [ ] Test: --strict always produces valid schema
- [ ] Test: --strict rejects ambiguous inputs

---

## Phase 2: OBSERVABILITY (Target: +1.5 points)

### 2.1 Correlation ID
**Problem:** Can't trace operations across logs

**Solution:**
```json
{
  "ok": true,
  "correlation_id": "p2me_20260226_192640_a1b2c3",
  "timestamp": "2026-02-26T19:26:40.123Z",
  ...
}
```

**Files to modify:**
- [ ] `src/p2me/chain.py` - generate correlation_id
- [ ] `src/p2me/cli.py` - include in output

**Tests needed:**
- [ ] Test: correlation_id is unique per run
- [ ] Test: correlation_id format is consistent
- [ ] Test: can pass --correlation-id to reuse

### 2.2 Echo Input Parameters
**Problem:** AI can't verify what parameters were used

**Solution:**
```json
{
  "ok": true,
  "input": {
    "source": "article.md",
    "provider": "vps",
    "caption": "🚀 New Article",
    "dry_run": false
  },
  ...
}
```

**Files to modify:**
- [ ] `src/p2me/chain.py` - track input params
- [ ] `src/p2me/cli.py` - include in output

**Tests needed:**
- [ ] Test: all flags echoed in output
- [ ] Test: caption appears in input section
- [ ] Test: defaults are shown

### 2.3 Timestamps
**Problem:** No timing information

**Solution:**
```json
{
  "ok": true,
  "timing": {
    "started_at": "2026-02-26T19:26:40.123Z",
    "completed_at": "2026-02-26T19:26:42.456Z",
    "duration_ms": 2333,
    "stages": {
      "publish_ms": 1800,
      "notify_ms": 533
    }
  }
}
```

**Tests needed:**
- [ ] Test: timestamps are ISO 8601
- [ ] Test: duration_ms is accurate
- [ ] Test: stage timings sum correctly

---

## Phase 3: DISCOVERABILITY (Target: +1 point)

### 3.1 Health Check
**Problem:** Can't verify dependencies before running

**Solution:**
```bash
p2me --health-check
```
```json
{
  "ok": true,
  "health": {
    "publish_me": {"available": true, "version": "1.0.0"},
    "t2me": {"available": true, "configured": true},
    "network": {"vps_reachable": true, "telegram_api": true}
  }
}
```

**Files to create/modify:**
- [ ] `src/p2me/health.py` - health check logic
- [ ] `src/p2me/cli.py` - add --health-check flag

**Tests needed:**
- [ ] Test: --health-check exits 0 when healthy
- [ ] Test: --health-check exits 1 when deps missing
- [ ] Test: --health-check -j outputs JSON

### 3.2 Capabilities Query
**Problem:** AI doesn't know what features exist

**Solution:**
```bash
p2me --capabilities
```
```json
{
  "version": "1.0.0",
  "capabilities": ["publish", "notify", "dry_run", "json_output"],
  "providers": ["simplenote", "vps"],
  "modes": ["none", "minimal", "standard", "aggressive"],
  "exit_codes": {
    "0": "success",
    "1": "validation_error",
    "2": "invalid_argument",
    "3": "unknown_error"
  }
}
```

**Tests needed:**
- [ ] Test: --capabilities outputs valid JSON
- [ ] Test: capabilities match actual features

### 3.3 Version Check
**Problem:** Can't verify minimum version

**Solution:**
```bash
p2me --version --json
```
```json
{
  "name": "p2me",
  "version": "1.1.0",
  "dependencies": {
    "publish_me": ">=1.0.0",
    "t2me": ">=2.0.0"
  }
}
```

---

## Phase 4: RELIABILITY (Target: +1 point)

### 4.1 Validate Without Publishing
**Problem:** Can't pre-check input without side effects

**Solution:**
```bash
p2me file.md --validate
```
```json
{
  "ok": true,
  "validation": {
    "input": {"valid": true, "size_bytes": 1234, "type": "markdown"},
    "content": {"valid": true, "warnings": []},
    "would_publish_to": ["simplenote", "vps"]
  }
}
```

**Tests needed:**
- [ ] Test: --validate checks file exists
- [ ] Test: --validate checks content is valid
- [ ] Test: --validate makes no network calls

### 4.2 Graceful Degradation
**Problem:** Partial failures not communicated clearly

**Solution:**
```json
{
  "ok": true,
  "degraded": true,
  "warnings": [
    {"code": "TELEGRAM_RATE_LIMITED", "message": "Notification delayed 60s"}
  ],
  "partial_success": {
    "publish": true,
    "notify": false
  }
}
```

**Tests needed:**
- [ ] Test: degraded mode still returns ok=true
- [ ] Test: warnings array populated

### 4.3 Retry Visibility
**Problem:** Silent retries, AI doesn't know

**Solution:**
```json
{
  "ok": true,
  "retries": {
    "publish": {"attempts": 2, "max": 3},
    "notify": {"attempts": 1, "max": 3}
  }
}
```

---

## Phase 5: PORTABILITY (Target: +0.5 points)

### 5.1 Remove Hardcoded Paths
**Problem:** Wrapper uses hardcoded /home/pets paths

**Solution:**
```bash
# Environment-based configuration
export P2ME_PROJECT_DIR=/opt/p2me
export P2ME_PYTHON_BIN=python3
```

**Files to modify:**
- [ ] `/home/pets/bin/p2me` - use environment variables
- [ ] Add installation script for any system

**Tests needed:**
- [ ] Test: works with custom P2ME_PROJECT_DIR
- [ ] Test: installation script works

### 5.2 Self-Contained Package
**Problem:** Requires external publish_me, t2me

**Solution:**
- [ ] Bundle as pip-installable package
- [ ] Document minimum versions of dependencies
- [ ] Add setup.py / pyproject.toml dependencies

---

## Phase 6: TESTING (Target: +0.5 points)

### 6.1 Expand Test Coverage
- [ ] Add 50+ more edge case tests
- [ ] Add property-based testing (hypothesis)
- [ ] Add mutation testing
- [ ] Add performance benchmarks

### 6.2 AI Agent Integration Tests
- [ ] Test: AI can parse all JSON outputs
- [ ] Test: AI can handle all error codes
- [ ] Test: AI can use --health-check workflow

---

## Implementation Order

| Phase | Priority | Effort | Impact | Order |
|-------|----------|--------|--------|-------|
| 1.1 Normalize Errors | HIGH | 2h | HIGH | 1 |
| 2.1 Correlation ID | HIGH | 1h | HIGH | 2 |
| 3.1 Health Check | HIGH | 2h | HIGH | 3 |
| 2.2 Echo Input Params | MEDIUM | 1h | HIGH | 4 |
| 1.2 JSON Schema | MEDIUM | 2h | MEDIUM | 5 |
| 4.1 Validate Flag | MEDIUM | 2h | MEDIUM | 6 |
| 2.3 Timestamps | LOW | 1h | MEDIUM | 7 |
| 3.2 Capabilities | LOW | 1h | MEDIUM | 8 |
| 5.1 Remove Hardcoded | LOW | 1h | LOW | 9 |

**Total Estimated Effort: ~13 hours**

---

## Success Metrics

After implementation, AI agent should be able to:

```bash
# 1. Check if tool is ready
p2me --health-check -j
# → {"ok": true, "health": {...}}

# 2. Discover capabilities
p2me --capabilities -j
# → {"version": "1.1.0", "capabilities": [...]}

# 3. Validate input
p2me article.md --validate -j
# → {"ok": true, "validation": {...}}

# 4. Execute with full traceability
p2me article.md -vps --caption "Test" -j
# → {
#     "ok": true,
#     "correlation_id": "p2me_20260226_...",
#     "timestamp": "...",
#     "input": {"source": "article.md", ...},
#     "timing": {...},
#     "publish": {...},
#     "notify": {...}
#   }

# 5. Handle errors predictably
p2me bad.md -j
# → {
#     "ok": false,
#     "correlation_id": "...",
#     "errors": [{"code": "FILE_NOT_FOUND", "message": "...", "stage": "input"}]
#   }
```

---

## Confidence Projection

| After Phase | Confidence | Satisfaction |
|-------------|------------|--------------|
| Current | 7/10 | 6/10 |
| Phase 1 (Predictability) | 8/10 | 7/10 |
| Phase 2 (Observability) | 8.5/10 | 8/10 |
| Phase 3 (Discoverability) | 9/10 | 8.5/10 |
| Phase 4 (Reliability) | 9.5/10 | 9/10 |
| Phase 5+6 (Portability+Testing) | 9.5/10 | 9.5/10 |

**Target achieved after all phases complete.**
