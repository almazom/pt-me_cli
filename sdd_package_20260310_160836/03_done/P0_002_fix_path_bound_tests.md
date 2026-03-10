# P0_002: Fix Path-Bound `p2me` Tests And Docs

## Quick Info

| Field | Value |
|-------|-------|
| Title | Fix path-bound `p2me` tests and docs |
| Priority | P0 - Merge blocker |
| Story Points | 2 |
| Complexity | Small |
| Expert | Testability Engineer |
| Source Report | [testability_engineer_report_at20260310_160836.md](../reports/testability_engineer_report_at20260310_160836.md) |
| Status | Backlog |
| Estimated Time | 1-2 hours |

## Goal

Remove workstation-specific absolute paths from the new test file and manual test instructions so the `p2me` review surface runs in this repository and CI-like environments.

## Full Context

### Current Problem

The new help tests and `HOW_TO_TEST.md` point at `/home/pets/TOOLS/p2me_cli`, but the actual checkout is `/home/pets/TOOLS/pt-me_cli`. The added tests currently fail for that reason alone.

### Evidence

- `PYTHONPATH=src python -m pytest tests/test_p2me_cli.py` failed 3 tests locally
- `PYTHONPATH=src python -m pytest` finished with `3 failed, 111 passed, 9 skipped`

## Success Criteria

### Must Have

- [ ] Tests derive the repo root dynamically
- [ ] No new docs rely on one absolute machine path
- [ ] Full repository pytest run is green

### Should Have

- [ ] Manual test docs use project-relative commands
- [ ] The new tests are stable across working directories

## Implementation Guide

1. Replace hardcoded `cwd` values with a path derived from `Path(__file__).resolve()`.
2. Avoid custom `env` values that discard unrelated environment variables unless required.
3. Update `HOW_TO_TEST.md` to use the actual repo name or relative paths.
4. Re-run the focused and full test suites.

## Files to Touch

| File | Action |
|------|--------|
| `tests/test_p2me_cli.py` | Modify |
| `HOW_TO_TEST.md` | Modify |
| `TEST_PLAN.md` | Modify if it references the bad path |

## Testing Strategy

- Focused test run: `PYTHONPATH=src python -m pytest tests/test_p2me_cli.py`
- Full regression run: `PYTHONPATH=src python -m pytest`

## Risks

| Risk | Mitigation |
|------|------------|
| Dynamic path logic still fails under CI | Use `Path(__file__).resolve().parents[1]` style lookup and keep tests self-contained |

## Git Info

- Branch: `fix/P0_002-p2me-test-paths`
- Commit message: `fix(P0_002): remove machine-local paths from p2me tests`

## Pre-Completion Checklist

- [ ] Focused tests pass
- [ ] Full pytest run passes
- [ ] Docs updated
