# Simplicity Advocate Report — 2026-03-10T16:08:36+03:00

## Blocker or LGTM
[BLOCKER [HIGH]: the change adds unsupported public surface (`--validate`, broad `--film-url`, machine-specific test instructions) that can be deleted or narrowed instead of carried as debt -> remove promises that the code does not yet implement]

## Findings
- High: `--validate` increases CLI surface area, docs, schema capabilities, and user expectations, but the code never implements a validation-only branch; the simplest safe fix is to delete the flag and capability until it exists for real — `src/p2me/cli.py#L140`, `src/p2me/schema.py#L271-L279`, `src/p2me/cli.py#L321-L335`, `src/p2me/chain.py#L413-L449`
- High: `--film-url` adds a whole remote-fetch subsystem to the command without guardrails, even though the help text frames it as a narrow kinoteatr helper; if host validation is not added now, the feature should be removed from the public interface — `src/p2me/cli.py#L111-L115`, `src/p2me/chain.py#L395-L399`, `src/p2me/film_parser.py#L12-L31`
- High: the new tests and test doc hardcode one local filesystem path, which is complexity without value; use repo-relative discovery instead of teaching the suite about one workstation layout — `tests/test_p2me_cli.py#L19-L20`, `tests/test_p2me_cli.py#L31-L32`, `tests/test_p2me_cli.py#L44-L45`, `HOW_TO_TEST.md#L39-L40`

## Confidence
92%

## Recommended Action
Prefer deletion over partial implementation: drop unsupported flags/capabilities now or reduce them to the minimal safe surface, then re-add features only once they have tests and clear contracts.

## Story Points Estimate
5
