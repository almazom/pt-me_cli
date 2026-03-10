"""CLI interface for p2me - chains publish_me and t2me."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from . import __version__
from .chain import (
    find_command,
    generate_correlation_id,
    get_publish_command,
    get_t2me_command,
    get_timestamp,
    run_chain,
)
from .film_parser import validate_film_url
from .schema import (
    CAPABILITIES,
    OUTPUT_SCHEMA,
    SCHEMA_VERSION,
    ErrorCode,
    ErrorStage,
    create_error,
)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for p2me CLI."""
    parser = argparse.ArgumentParser(
        prog="p2me",
        description="Publish to Me - Chain publish_me and t2me in one command",
        epilog="""
Examples:
  p2me article.md              # Publish + notify
  p2me article.md -vps         # Publish to VPS only + notify
  p2me article.md -sn          # Publish to Simplenote only + notify
  p2me article.md --no-notify  # Publish without Telegram notification
  p2me article.md -n           # Dry run (no actual actions)
  cat file.md | p2me -         # Read from stdin
  p2me article.md -j           # JSON output

AI Agent Commands:
  p2me --schema                # Get JSON output schema
  p2me --capabilities          # Get capabilities and features
  p2me --health-check          # Verify dependencies
  p2me file.md --validate      # Validate without publishing

Exit codes:
  0 = success
  1 = validation/execution error
  2 = invalid argument
  3 = unknown error
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Info flags (standalone)
    info_group = parser.add_argument_group("Info flags (standalone)")
    info_group.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    info_group.add_argument(
        "--schema",
        action="store_true",
        help="Output JSON schema for -j output format",
    )
    info_group.add_argument(
        "--capabilities",
        action="store_true",
        help="Output tool capabilities as JSON",
    )
    info_group.add_argument(
        "--health-check",
        action="store_true",
        help="Check if dependencies are available",
    )

    # Positional argument
    parser.add_argument(
        "source",
        nargs="?",
        default="-",
        help="Source file path or '-' for stdin (default: '-')",
    )

    # Publish options
    publish_group = parser.add_argument_group("Publish options (→ publish_me)")
    publish_group.add_argument(
        "-sn",
        "--simplenote",
        action="store_true",
        help="Publish to Simplenote only",
    )
    publish_group.add_argument(
        "-vps",
        "--vps",
        action="store_true",
        help="Publish to VPS only",
    )
    publish_group.add_argument(
        "-m",
        "--mode",
        choices=["none", "minimal", "standard", "aggressive"],
        default="standard",
        help="Preprocessing mode (default: standard)",
    )

    # Telegram options
    telegram_group = parser.add_argument_group("Telegram options (→ t2me)")
    telegram_group.add_argument(
        "--no-notify",
        action="store_true",
        help="Skip Telegram notification",
    )
    telegram_group.add_argument(
        "--caption",
        type=str,
        default=None,
        help="Custom caption for Telegram message",
    )
    telegram_group.add_argument(
        "--film-url",
        type=str,
        default=None,
        help="Film page URL on kinoteatr.ru to verify showing date",
    )

    # Common options
    common_group = parser.add_argument_group("Common options")
    common_group.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)",
    )
    common_group.add_argument(
        "-r",
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retry attempts (default: 3)",
    )
    common_group.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Dry run (no actual publish/notify)",
    )
    common_group.add_argument(
        "--validate",
        action="store_true",
        help="Validate input and optional film URL without publishing",
    )
    common_group.add_argument(
        "-j",
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON",
    )
    common_group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    common_group.add_argument(
        "--quiet",
        action="store_true",
        help="Quiet mode (errors only)",
    )
    common_group.add_argument(
        "--correlation-id",
        type=str,
        default=None,
        help="Custom correlation ID for tracking",
    )

    return parser


def run_health_check(json_output: bool = False) -> int:
    """Run health check on dependencies.

    Args:
        json_output: Output as JSON

    Returns:
        Exit code (0=ok, 1=error)
    """
    health: dict = {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "health": {
            "publish_me": {"available": False, "path": None},
            "t2me": {"available": False, "path": None},
        },
    }

    # Check publish_me
    publish_cmd = get_publish_command()
    publish_path = find_command(publish_cmd)
    if publish_path:
        health["health"]["publish_me"] = {"available": True, "path": publish_path}
    else:
        health["ok"] = False

    # Check t2me
    t2me_cmd = get_t2me_command()
    t2me_path = find_command(t2me_cmd)
    if t2me_path:
        health["health"]["t2me"] = {"available": True, "path": t2me_path}
    else:
        health["ok"] = False

    if json_output:
        print(json.dumps(health, indent=2))
    else:
        print("Health check:")
        print(f"  publish_me ({publish_cmd}): {'✓' if publish_path else '✗'}")
        print(f"  t2me ({t2me_cmd}): {'✓' if t2me_path else '✗'}")
        print(f"Overall: {'OK' if health['ok'] else 'FAILED'}")

    return 0 if health["ok"] else 1


def output_schema() -> int:
    """Output JSON schema.

    Returns:
        Exit code (always 0)
    """
    print(json.dumps(OUTPUT_SCHEMA, indent=2))
    return 0


def output_capabilities() -> int:
    """Output capabilities.

    Returns:
        Exit code (always 0)
    """
    print(json.dumps(CAPABILITIES, indent=2))
    return 0


def _read_stdin_bytes() -> bytes:
    """Read stdin content as bytes."""
    stream = getattr(sys.stdin, "buffer", sys.stdin)
    content = stream.read()
    if isinstance(content, bytes):
        return content
    return content.encode("utf-8")


def _input_error(code: str, message: str) -> dict[str, Any]:
    """Create a standardized input-stage error."""
    return create_error(
        code=code,
        message=message,
        stage=ErrorStage.INPUT,
    )


def _validation_payload(source_type: str, size_bytes: int) -> dict[str, Any]:
    """Create a validation result payload."""
    return {
        "ok": True,
        "source_type": source_type,
        "size_bytes": size_bytes,
    }


def _decode_validation_content(
    content: bytes,
    *,
    stdin: bool = False,
    source: str | None = None,
) -> dict[str, Any] | None:
    """Validate UTF-8 content and return an input error if decoding fails."""
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        if stdin:
            return _input_error(
                ErrorCode.FILE_READ_ERROR,
                "Cannot decode stdin as UTF-8",
            )
        return _input_error(
            ErrorCode.FILE_READ_ERROR,
            f"Cannot decode file as UTF-8: {source}",
        )
    return None


def validate_source_input(
    source: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Validate source input without triggering publish side effects."""
    if source == "-":
        content = _read_stdin_bytes()
        if not content:
            return None, _input_error(
                ErrorCode.EMPTY_CONTENT,
                "No input provided via stdin",
            )

        decode_error = _decode_validation_content(content, stdin=True)
        if decode_error:
            return None, decode_error

        return _validation_payload("stdin", len(content)), None

    path = Path(source).expanduser()
    if not path.exists():
        return None, _input_error(ErrorCode.FILE_NOT_FOUND, f"File not found: {source}")
    if not path.is_file():
        return None, _input_error(
            ErrorCode.INVALID_INPUT,
            f"Path is not a file: {source}",
        )

    try:
        content = path.read_bytes()
    except OSError as exc:
        return None, _input_error(
            ErrorCode.FILE_READ_ERROR,
            f"Cannot read file: {exc}",
        )

    if not content:
        return None, _input_error(ErrorCode.EMPTY_CONTENT, "Content is empty")

    decode_error = _decode_validation_content(content, source=source)
    if decode_error:
        return None, decode_error

    return _validation_payload("file", len(content)), None


def run_validation(
    source: str,
    mode: str = "standard",
    no_notify: bool = False,
    caption: str | None = None,
    timeout: int = 30,
    max_retries: int = 3,
    dry_run: bool = False,
    correlation_id: str | None = None,
    film_url: str | None = None,
) -> dict[str, Any]:
    """Run validation-only flow without publish or notify side effects."""
    start_time = time.time()
    started_at = get_timestamp()
    correlation_id = correlation_id or generate_correlation_id()

    result: dict[str, Any] = {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "correlation_id": correlation_id,
        "timestamp": started_at,
        "dry_run": dry_run,
        "input": {
            "source": source,
            "provider": None,
            "mode": mode,
            "caption": caption,
            "dry_run": dry_run,
            "no_notify": no_notify,
            "validate": True,
            "timeout": timeout,
            "max_retries": max_retries,
            "film_url": film_url,
        },
        "validation": None,
        "film": None,
        "publish": None,
        "notify": None,
        "errors": [],
        "warnings": [],
        "timing": {
            "started_at": started_at,
        },
    }

    validation, error = validate_source_input(source)
    if error:
        result["ok"] = False
        result["errors"].append(error)
    else:
        result["validation"] = validation

    if film_url:
        film_url_error = validate_film_url(film_url)
        if film_url_error:
            result["ok"] = False
            result["errors"].append(
                create_error(
                    code=ErrorCode.INVALID_INPUT,
                    message=film_url_error,
                    stage=ErrorStage.INPUT,
                )
            )
        elif result["validation"] is None:
            result["validation"] = {
                "ok": True,
                "source_type": "unknown",
                "size_bytes": 0,
            }

        if result["validation"] is not None:
            result["validation"]["film_url_checked"] = True
    elif result["validation"] is not None:
        result["validation"]["film_url_checked"] = False

    if result["validation"] is not None:
        result["validation"]["ok"] = result["ok"]

    result["timing"]["completed_at"] = get_timestamp()
    result["timing"]["total_ms"] = round((time.time() - start_time) * 1000, 2)
    result["duration_ms"] = result["timing"]["total_ms"]

    return result


def format_human_output(result: dict) -> str:
    """Format result for human-readable output.

    Args:
        result: Chain result

    Returns:
        Human-readable string
    """
    lines = []
    validation = result.get("validation")

    if validation and result.get("ok"):
        lines.append("✓ Input is valid")
        source_type = validation.get("source_type")
        if source_type:
            lines.append(f"  Source type: {source_type}")
        size_bytes = validation.get("size_bytes")
        if size_bytes is not None:
            lines.append(f"  Size: {size_bytes} bytes")
        if result.get("input", {}).get("film_url"):
            lines.append("  Film URL: valid")
        if result.get("correlation_id"):
            lines.append(f"  ID: {result['correlation_id']}")
        return "\n".join(lines)

    if result.get("ok"):
        # Film info
        film = result.get("film")
        if film and film.get("ok"):
            title = film.get("film_title", "Film")
            if film.get("is_showing_today"):
                lines.append(f"🎬 {title} — СЕГОДНЯ!")
            else:
                days = film.get("days_until")
                next_date = film.get("next_showing", "")
                if days and days > 0:
                    if days == 1:
                        lines.append(f"🎬 {title} — завтра ({next_date})")
                    else:
                        lines.append(f"🎬 {title} — через {days} дней ({next_date})")
                else:
                    lines.append(f"🎬 {title} — {next_date}")

        if result.get("publish", {}).get("url"):
            url = result["publish"]["url"]
            lines.append(f"✓ Published: {url}")
        elif result.get("dry_run"):
            lines.append("✓ Published: (dry-run)")

        notify = result.get("notify")
        if (notify and notify.get("ok")) or (
            result.get("dry_run") and not result.get("input", {}).get("no_notify")
        ):
            lines.append("✓ Notified via Telegram")

        if result.get("dry_run"):
            lines.append("  (dry-run mode - no actual changes)")

        # Show warnings
        for warning in result.get("warnings", []):
            if isinstance(warning, dict):
                warning_message = warning.get("message", warning.get("code", "Warning"))
                lines.append(f"⚠️  {warning_message}")
            else:
                lines.append(f"⚠️  {warning}")

        # Show correlation ID for tracking
        if result.get("correlation_id"):
            lines.append(f"  ID: {result['correlation_id']}")
    else:
        for error in result.get("errors", []):
            if isinstance(error, dict):
                error_code = error.get("code", "ERROR")
                error_message = error.get("message", "Unknown error")
                lines.append(f"✗ [{error_code}] {error_message}")
            else:
                lines.append(f"✗ {error}")

    return "\n".join(lines)


def main() -> int:
    """Main entry point for p2me CLI.

    Returns:
        Exit code (0=success, 1=validation, 2=invalid arg, 3=unknown)
    """
    parser = create_parser()
    args = parser.parse_args()

    # Handle standalone info flags
    if args.schema:
        return output_schema()

    if args.capabilities:
        return output_capabilities()

    if args.health_check:
        return run_health_check(json_output=args.json_output)

    if args.validate:
        result = run_validation(
            source=args.source,
            mode=args.mode,
            no_notify=args.no_notify,
            caption=args.caption,
            timeout=args.timeout,
            max_retries=args.max_retries,
            dry_run=args.dry_run,
            correlation_id=args.correlation_id,
            film_url=args.film_url,
        )
    else:
        result = run_chain(
            source=args.source,
            simplenote=args.simplenote,
            vps=args.vps,
            mode=args.mode,
            no_notify=args.no_notify,
            caption=args.caption,
            timeout=args.timeout,
            max_retries=args.max_retries,
            dry_run=args.dry_run,
            json_output=args.json_output,
            verbose=args.verbose,
            quiet=args.quiet,
            correlation_id=args.correlation_id,
            film_url=args.film_url,
        )

    # Output result
    if args.json_output:
        print(json.dumps(result, indent=2))
    elif not args.quiet or not result.get("ok"):
        print(format_human_output(result))

    # Return appropriate exit code
    if result.get("ok"):
        return 0
    elif result.get("errors"):
        return 1
    else:
        return 3


if __name__ == "__main__":
    sys.exit(main())
