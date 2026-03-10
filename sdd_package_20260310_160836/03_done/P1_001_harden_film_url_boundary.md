# P1_001: Harden Or Remove `--film-url`

## Quick Info

| Field | Value |
|-------|-------|
| Title | Harden or remove `--film-url` network boundary |
| Priority | P1 - High priority |
| Story Points | 3 |
| Complexity | Medium |
| Expert | Security Auditor |
| Source Report | [security_auditor_report_at20260310_160836.md](../reports/security_auditor_report_at20260310_160836.md) |
| Status | Backlog |
| Estimated Time | 0.5 day |

## Goal

Close the trust-boundary hole around `--film-url` so the CLI cannot be used to fetch arbitrary remote or internal endpoints.

## Full Context

### Current Problem

Help text frames `--film-url` as a kinoteatr helper, but the value is passed directly into `urllib.request.urlopen()` without allowlist checks.

### Why It Matters

- Arbitrary outbound fetches can hit internal network targets
- The public contract is broader than the help text says
- The feature adds security and latency risk at the same time

## Success Criteria

### Must Have

- [ ] Only allowed scheme/host combinations are accepted, or the flag is removed
- [ ] Localhost, private-address, and unsupported schemes are rejected
- [ ] Rejection produces a clear structured error
- [ ] Tests cover both allowed and denied URLs

### Should Have

- [ ] Timeout behavior stays bounded and documented
- [ ] Help text matches the actual accepted inputs

## Implementation Guide

1. Parse the URL before use.
2. Allow only the intended kinoteatr host pattern and HTTPS.
3. Reject local network targets and unsupported schemes.
4. Add tests for valid kinoteatr URLs and blocked inputs.
5. If the safe behavior is unclear, remove the flag until requirements are settled.

## Files to Touch

| File | Action |
|------|--------|
| `src/p2me/cli.py` | Modify help text if needed |
| `src/p2me/chain.py` | Modify validation flow |
| `src/p2me/film_parser.py` | Modify fetch entrypoint |
| `tests/test_p2me_cli.py` | Add coverage |

## Testing Strategy

- Unit tests for URL validation
- Negative tests for `http://localhost`, private IPs, and `file://`
- Positive test for expected kinoteatr URL format

## Risks

| Risk | Mitigation |
|------|------------|
| Overly strict matching blocks legitimate pages | Document the accepted pattern and add representative fixtures |
| Safe allowlist is unclear | Remove the flag until a clear contract exists |

## Git Info

- Branch: `refactor/P1_001-film-url-boundary`
- Commit message: `refactor(P1_001): harden film-url boundary`

## Pre-Completion Checklist

- [ ] Validation or removal implemented
- [ ] Tests added
- [ ] Docs updated
