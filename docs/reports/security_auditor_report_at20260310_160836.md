# Security Auditor Report — 2026-03-10T16:08:36+03:00

## Blocker or LGTM
[BLOCKER [HIGH]: `--validate` is documented as safe validation but still executes publish and notify paths -> implement a side-effect-free validation branch or remove the flag and capability until it exists]

## Findings
- High: `--validate` is exposed as "Validate input without publishing", but `main()` never branches on `args.validate` and always calls `run_chain()`, which then executes `run_publish()` and `run_t2me()` — `src/p2me/cli.py#L140`, `src/p2me/cli.py#L321`, `src/p2me/chain.py#L413`, `src/p2me/chain.py#L444`
- High: `--film-url` crosses a trust boundary without host or scheme validation; user input flows into `urllib.request.urlopen()` even though help text implies a kinoteatr-only URL, creating an SSRF-style fetch primitive — `src/p2me/cli.py#L111`, `src/p2me/chain.py#L397`, `src/p2me/film_parser.py#L23-L31`
- High: the new CLI safety net is already broken because the added tests and manual test instructions hardcode a nonexistent checkout path, so this change can merge without a working regression barrier — `tests/test_p2me_cli.py#L19-L20`, `tests/test_p2me_cli.py#L31-L32`, `tests/test_p2me_cli.py#L44-L45`, `HOW_TO_TEST.md#L39-L40`

## Confidence
94%

## Recommended Action
Treat `--validate` as a merge blocker, restrict `--film-url` to an explicit allowlist or remove it, and repair the path-bound tests before trusting this CLI in automation.

## Story Points Estimate
3
