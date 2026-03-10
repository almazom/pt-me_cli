# P2_001: Align `--quiet` Contract And Published Test Results

## Quick Info

| Field | Value |
|-------|-------|
| Title | Align `--quiet` contract and regenerate published test results |
| Priority | P2 - Medium priority |
| Story Points | 2 |
| Complexity | Small |
| Expert | Maintainer |
| Source Report | [maintainer_report_at20260310_160836.md](../reports/maintainer_report_at20260310_160836.md) |
| Status | Backlog |
| Estimated Time | 1-2 hours |

## Goal

Make help text, `TEST_PLAN.md`, and runtime behavior agree on what quiet mode does, then republish test docs from real runs in this repo.

## Full Context

### Current Problem

`--quiet` is described as "errors only", but non-JSON quiet mode suppresses all output in `main()`. The published test plan also claims a clean test state that does not match current local runs.

## Success Criteria

### Must Have

- [ ] Quiet-mode behavior and wording are consistent
- [ ] A regression test covers quiet-mode error output semantics
- [ ] `TEST_PLAN.md` reflects actual results from this repository

### Should Have

- [ ] `HOW_TO_TEST.md` and `TEST_PLAN.md` use the same command forms
- [ ] Stale claims are removed

## Implementation Guide

1. Decide the contract: either print errors in quiet mode or document total silence.
2. Update the implementation or the wording to match that decision.
3. Add a test for the chosen behavior.
4. Re-run the documented commands and refresh `TEST_PLAN.md`.

## Files to Touch

| File | Action |
|------|--------|
| `src/p2me/cli.py` | Modify |
| `tests/test_p2me_cli.py` | Modify |
| `HOW_TO_TEST.md` | Modify |
| `TEST_PLAN.md` | Modify |

## Testing Strategy

- CLI error run with `--quiet`
- Focused pytest run for p2me tests
- Optional full pytest run after docs refresh

## Risks

| Risk | Mitigation |
|------|------------|
| Quiet-mode expectations already differ across users | Pick one contract and document it explicitly |

## Git Info

- Branch: `chore/P2_001-quiet-mode-docs`
- Commit message: `chore(P2_001): align quiet mode docs and tests`

## Pre-Completion Checklist

- [ ] Contract decision made
- [ ] Code/docs aligned
- [ ] Test plan regenerated
