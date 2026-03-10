# Testability Engineer Report — 2026-03-10T16:08:36+03:00

## Blocker or LGTM
[BLOCKER [HIGH]: the change introduces side-effecting behavior behind `--validate` and lands with a broken test file, so the new CLI cannot be trusted under automation -> fix the contract and restore executable tests before merge]

## Findings
- High: `--validate` is advertised as validation-only, but `main()` still routes through the full publish and notify chain; a verification run with `PYTHONPATH=src python -m p2me <tmp> --validate -n -j` produced both `publish` and `notify` sections, so tests are missing the most important safety assertion for this flag — `src/p2me/cli.py#L140`, `src/p2me/cli.py#L321`, `src/p2me/schema.py#L277`, `src/p2me/chain.py#L413-L449`
- High: `tests/test_p2me_cli.py` hardcodes `/home/pets/TOOLS/p2me_cli`, which fails immediately in this checkout and leaves the change with 3 failing tests (`PYTHONPATH=src python -m pytest tests/test_p2me_cli.py`) — `tests/test_p2me_cli.py#L19-L20`, `tests/test_p2me_cli.py#L31-L32`, `tests/test_p2me_cli.py#L44-L45`
- High: there is no dedicated test coverage for `--film-url` trust-boundary validation, `--validate` safety, or `--quiet` error semantics even though those flags are part of the public contract and docs — `src/p2me/cli.py#L111-L115`, `src/p2me/cli.py#L140-L160`, `src/p2me/cli.py#L338-L348`, `tests/test_p2me_cli.py#L10-L186`

## Confidence
95%

## Recommended Action
Add contract tests for `--validate`, `--quiet`, and `--film-url`, replace hardcoded paths with repo-relative fixtures, and do not publish new docs/test claims until those cases run green in CI.

## Story Points Estimate
5
