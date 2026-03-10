# P0_001: Make `--validate` Truly Side-Effect Free

## Quick Info

| Field | Value |
|-------|-------|
| Title | Make `--validate` truly side-effect free |
| Priority | P0 - Merge blocker |
| Story Points | 5 |
| Complexity | Medium |
| Expert | API Guardian |
| Source Report | [api_guardian_report_at20260310_160836.md](../reports/api_guardian_report_at20260310_160836.md) |
| Status | Backlog |
| Estimated Time | 0.5-1 day |

## Goal

Make `p2me file --validate` safe to run under automation by ensuring it performs validation only and never publishes content or sends notifications.

## Full Context

### Current Problem

`--validate` is documented in help and capabilities, but `main()` never branches on it. The command always enters `run_chain()`, which still executes publish and notify logic.

### Where It Lives

- `src/p2me/cli.py`
- `src/p2me/schema.py`
- `src/p2me/chain.py`
- `tests/test_p2me_cli.py`

### Why It Matters

- Users and agents will treat `--validate` as a safe preflight.
- The current implementation can still trigger side effects.
- Reviewers unanimously marked this as a blocker.

## Success Criteria

### Must Have

- [ ] `--validate` never invokes publish or notify
- [ ] Output clearly communicates validation-only success/failure
- [ ] Help text and capabilities reflect the final behavior
- [ ] Tests cover both passing and failing validation-only runs

### Should Have

- [ ] Validation path is fast and local
- [ ] JSON output includes enough detail for automation

## Implementation Guide

### Option A: Implement Validation Properly

1. Add a dedicated validation branch in `main()` before `run_chain()`.
2. Reuse or add minimal local input validation logic.
3. Return a validation-only result shape with no `publish` or `notify` side effects.
4. Add tests that assert publish and notify are not called.

### Option B: Remove the Unsupported Surface

1. Delete `--validate` from parser help.
2. Remove `validate` from `CAPABILITIES`.
3. Remove `--validate` examples and docs.
4. Add release note / changelog note if needed.

## Files to Touch

| File | Action |
|------|--------|
| `src/p2me/cli.py` | Modify |
| `src/p2me/schema.py` | Modify |
| `src/p2me/chain.py` | Modify or leave untouched if validation bypasses it |
| `tests/test_p2me_cli.py` | Modify |
| `HOW_TO_TEST.md` | Modify |

## Testing Strategy

- Unit test: `--validate` success path
- Unit test: `--validate` invalid input path
- Mocked test: assert publish/notify are not called
- CLI test: `p2me <tmp> --validate -j`

## Risks

| Risk | Mitigation |
|------|------------|
| Validation logic diverges from runtime publish checks | Reuse existing validation where possible |
| Contract changes break automation | Update help, docs, and schema in the same change |

## Git Info

- Branch: `fix/P0_001-validate-contract`
- Commit message: `fix(P0_001): make validate mode side-effect free`

## Pre-Completion Checklist

- [ ] Behavior implemented or surface removed
- [ ] Tests added and passing
- [ ] Docs updated
- [ ] Self-review complete
