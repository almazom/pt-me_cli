# How to Test `p2me`

## Quick Checks

```bash
# Help and metadata
PYTHONPATH=src python -m p2me -h
PYTHONPATH=src python -m p2me --version
PYTHONPATH=src python -m p2me --schema
PYTHONPATH=src python -m p2me --capabilities
PYTHONPATH=src python -m p2me --health-check -j
```

## Safe Local Validation

```bash
# Validation-only path: no publish, no notify
tmp="$(mktemp)"
printf '# hello\n' > "$tmp"
PYTHONPATH=src python -m p2me "$tmp" --validate -j
rm -f "$tmp"

# Film URL validation is restricted to kinoteatr.ru
tmp="$(mktemp)"
printf '# hello\n' > "$tmp"
PYTHONPATH=src python -m p2me "$tmp" --validate \
  --film-url https://kinoteatr.ru/movie/123 -j
rm -f "$tmp"

# Invalid film hosts are rejected locally
tmp="$(mktemp)"
printf '# hello\n' > "$tmp"
PYTHONPATH=src python -m p2me "$tmp" --validate \
  --film-url https://example.com/movie -j
rm -f "$tmp"
```

## Error And Quiet-Mode Checks

```bash
# Quiet mode stays silent on success
tmp="$(mktemp)"
printf '# hello\n' > "$tmp"
PYTHONPATH=src python -m p2me "$tmp" -n --no-notify --quiet
rm -f "$tmp"

# Quiet mode still prints errors
PYTHONPATH=src python -m p2me nonexistent.md --quiet
echo "Exit: $?"
```

## Dry-Run Chain Checks

```bash
tmp="$(mktemp)"
printf '# hello\n' > "$tmp"

# Publish + notify flow without side effects
PYTHONPATH=src python -m p2me "$tmp" -n -j
PYTHONPATH=src python -m p2me "$tmp" -n --no-notify

rm -f "$tmp"
```

## Automated Tests

```bash
cd /home/pets/TOOLS/pt-me_cli

# Focused p2me contract tests
PYTHONPATH=src python -m pytest tests/test_p2me_cli.py

# Full repository regression suite
PYTHONPATH=src python -m pytest

# Lint for the changed files
PYTHONPATH=src python -m ruff check src/p2me/cli.py \
  src/p2me/film_parser.py src/p2me/schema.py tests/test_p2me_cli.py
```

## Current Expectations

- `--validate` never populates `publish` or `notify`
- `--film-url` accepts only `kinoteatr.ru` hosts over `http` or `https`
- `--quiet` prints nothing on success and still prints human-readable errors on failure
- `PYTHONPATH=src python -m pytest` is expected to pass, with a small number of existing integration skips

For the latest verified results, see `TEST_PLAN.md`.
