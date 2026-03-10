# API Guardian Report — 2026-03-10T16:08:36+03:00

## Blocker or LGTM
[BLOCKER [HIGH]: the public CLI contract is not truthful -> `--validate`, `--quiet`, capabilities, and docs must match actual runtime behavior before this interface can be considered stable]

## Findings
- High: `--validate` is documented in help and exported in `CAPABILITIES`, but the runtime never honors it and still executes the publish/notify chain; this is a direct contract violation for consumers and automation — `src/p2me/cli.py#L29-L33`, `src/p2me/cli.py#L140`, `src/p2me/schema.py#L271-L279`, `src/p2me/cli.py#L321-L335`, `src/p2me/chain.py#L413-L449`
- High: `--film-url` claims a kinoteatr-specific input but accepts any URL and fetches it directly, leaking an implementation detail and widening the public API beyond what the help text promises — `src/p2me/cli.py#L111-L115`, `src/p2me/chain.py#L397`, `src/p2me/film_parser.py#L23-L31`
- High: the docs and tests teach consumers the wrong operational contract: help tests depend on a nonexistent absolute repo path, and the published test plan says `--quiet` is "errors only" even though quiet mode suppresses all non-JSON output — `tests/test_p2me_cli.py#L19-L20`, `tests/test_p2me_cli.py#L31-L32`, `tests/test_p2me_cli.py#L44-L45`, `TEST_PLAN.md#L77-L79`, `src/p2me/cli.py#L338-L348`

## Confidence
94%

## Recommended Action
Freeze the surface until it is internally consistent: implement the promised behavior or remove the claims from help, capabilities, and docs, then add contract tests for every public flag before declaring the CLI stable.

## Story Points Estimate
5
