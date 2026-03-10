"""Chain module - orchestrates publish_me and t2me commands."""

from __future__ import annotations

import json
import random
import shutil
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

from .schema import (
    SCHEMA_VERSION,
    create_error,
    ErrorCode,
    ErrorStage,
    normalize_notify_error,
    normalize_publish_error,
)
from .film_parser import check_film_date


def generate_correlation_id() -> str:
    """Generate a unique correlation ID.

    Returns:
        Correlation ID in format: p2me_YYYYMMDD_HHMMSS_XXXXXX
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = "".join(random.choices("abcdef0123456789", k=6))
    return f"p2me_{timestamp}_{suffix}"


def get_timestamp() -> str:
    """Get current ISO 8601 timestamp.

    Returns:
        Timestamp string
    """
    return datetime.now(timezone.utc).isoformat()


def find_command(name: str) -> str | None:
    """Find a command in PATH.

    Args:
        name: Command name to find

    Returns:
        Full path to command or None if not found
    """
    return shutil.which(name)


def get_publish_command() -> str:
    """Get the publish command to use.

    Returns:
        Command name (publish_me, p-me, or publish-me)
    """
    for cmd in ["publish_me", "p-me", "publish-me"]:
        if find_command(cmd):
            return cmd
    return "publish_me"


def get_t2me_command() -> str:
    """Get the t2me command to use.

    Returns:
        Command name (t2me or t2me_v2)
    """
    if find_command("t2me"):
        return "t2me"
    if find_command("t2me_v2"):
        return "t2me_v2"
    return "t2me"


def run_publish(
    source: str,
    simplenote: bool = False,
    vps: bool = False,
    mode: str = "standard",
    timeout: int = 30,
    max_retries: int = 3,
    dry_run: bool = False,
    verbose: bool = False,
    json_output: bool = True,
) -> dict[str, Any]:
    """Run publish_me command.

    Args:
        source: Source file path
        simplenote: Publish to Simplenote
        vps: Publish to VPS
        mode: Preprocessing mode
        timeout: Request timeout
        max_retries: Max retry attempts
        dry_run: Dry run mode
        verbose: Verbose output
        json_output: Get JSON output

    Returns:
        Result dictionary with ok, url, errors, etc.
    """
    cmd = [get_publish_command()]
    cmd.append(source)

    if simplenote:
        cmd.append("-sn")
    if vps:
        cmd.append("-vps")

    cmd.extend(["-m", mode])
    cmd.extend(["-t", str(timeout)])
    cmd.extend(["-r", str(max_retries)])

    if dry_run:
        cmd.append("-n")
    if json_output:
        cmd.append("-j")
    if verbose:
        cmd.append("-v")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 10,
        )

        if json_output and result.stdout.strip():
            try:
                return json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                pass

        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "url": None,
            "errors": [result.stderr] if result.stderr else [],
        }

    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": {"code": "TIMEOUT_ERROR", "message": "Publish command timed out"},
            "errors": ["Publish command timed out"],
        }
    except FileNotFoundError:
        return {
            "ok": False,
            "error": {"code": "DEPENDENCY_MISSING", "message": f"Publish command not found: {cmd[0]}"},
            "errors": [f"Publish command not found: {cmd[0]}"],
        }
    except Exception as e:
        return {
            "ok": False,
            "error": {"code": "UNKNOWN_ERROR", "message": str(e)},
            "errors": [str(e)],
        }


def run_t2me(
    message: str,
    caption: str | None = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """Run t2me command to send Telegram notification.

    Args:
        message: Message to send
        caption: Optional caption
        dry_run: Dry run mode
        verbose: Verbose output

    Returns:
        Result dictionary with ok, message_id, errors, etc.
    """
    cmd = [get_t2me_command(), "send", "--markdown"]
    cmd.append(message)

    if caption:
        cmd.extend(["--caption", caption])
    if dry_run:
        cmd.append("--dry-run")
    if verbose:
        cmd.append("-v")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.stdout.strip():
            try:
                data = json.loads(result.stdout.strip())
                return {
                    "ok": data.get("status") == "ok" or result.returncode == 0,
                    "dry_run": dry_run,
                    "message_id": data.get("result", {}).get("message_id"),
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "errors": [],
                }
            except json.JSONDecodeError:
                pass

        return {
            "ok": result.returncode == 0,
            "dry_run": dry_run,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "message_id": None,
            "errors": [result.stderr] if result.returncode != 0 and result.stderr else [],
        }

    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "errors": ["t2me command timed out"],
        }
    except FileNotFoundError:
        return {
            "ok": False,
            "errors": [f"t2me command not found: {cmd[0]}"],
        }
    except Exception as e:
        return {
            "ok": False,
            "errors": [str(e)],
        }


def format_telegram_message(
    publish_result: dict[str, Any],
    source: str,
    caption: str | None = None,
    film_info: dict[str, Any] | None = None,
) -> str:
    """Format message for Telegram notification.

    Args:
        publish_result: Result from publish step
        source: Source file name
        caption: Optional custom caption
        film_info: Optional film date verification info

    Returns:
        Formatted message string
    """
    lines = []

    # Film info first (if provided)
    if film_info:
        title = film_info.get("film_title", "Film")
        if film_info.get("ok"):
            if film_info.get("is_showing_today"):
                lines.append(f"🎬 *{title}* — СЕГОДНЯ!")
            else:
                days = film_info.get("days_until")
                next_date = film_info.get("next_showing", "")
                if days and days > 0:
                    if days == 1:
                        lines.append(f"🎬 *{title}* — завтра ({next_date})")
                    else:
                        lines.append(f"🎬 *{title}* — через {days} дней ({next_date})")
                else:
                    lines.append(f"🎬 *{title}* — {next_date}")

            # Add film URL
            lines.append(f"🎫 {film_info.get('url', '')}")
        else:
            lines.append(f"⚠️ Не удалось проверить дату: {film_info.get('error', 'ошибка')}")
        lines.append("")

    if caption:
        lines.append(f"📝 {caption}")
        lines.append("")

    url = publish_result.get("url", "")
    if url:
        lines.append(f"🔗 {url}")
    else:
        lines.append(f"📄 Published: {source}")

    return "\n".join(lines)


def get_provider_name(simplenote: bool, vps: bool) -> str | None:
    """Determine provider name from flags.

    Args:
        simplenote: Simplenote flag
        vps: VPS flag

    Returns:
        Provider name or None for auto
    """
    if simplenote and vps:
        return "auto"  # Both = auto
    if simplenote:
        return "simplenote"
    if vps:
        return "vps"
    return None  # Auto


def run_chain(
    source: str,
    simplenote: bool = False,
    vps: bool = False,
    mode: str = "standard",
    no_notify: bool = False,
    caption: str | None = None,
    timeout: int = 30,
    max_retries: int = 3,
    dry_run: bool = False,
    json_output: bool = False,
    verbose: bool = False,
    quiet: bool = False,
    correlation_id: str | None = None,
    film_url: str | None = None,
) -> dict[str, Any]:
    """Run the full p2me chain: publish → notify.

    Args:
        source: Source file path or '-' for stdin
        simplenote: Publish to Simplenote
        vps: Publish to VPS
        mode: Preprocessing mode
        no_notify: Skip Telegram notification
        caption: Custom caption for notification
        timeout: Request timeout
        max_retries: Max retry attempts
        dry_run: Dry run mode
        json_output: JSON output mode
        verbose: Verbose mode
        quiet: Quiet mode
        correlation_id: Optional correlation ID (generated if not provided)
        film_url: Optional film page URL to check showing date

    Returns:
        Result dictionary with standardized structure
    """
    # Initialize timing
    start_time = time.time()
    started_at = get_timestamp()

    # Generate or use correlation ID
    if correlation_id is None:
        correlation_id = generate_correlation_id()

    # Initialize result with standardized structure
    result: dict[str, Any] = {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "correlation_id": correlation_id,
        "timestamp": started_at,
        "dry_run": dry_run,
        "input": {
            "source": source,
            "provider": get_provider_name(simplenote, vps),
            "mode": mode,
            "caption": caption,
            "dry_run": dry_run,
            "no_notify": no_notify,
            "timeout": timeout,
            "max_retries": max_retries,
            "film_url": film_url,
        },
        "film": None,
        "publish": None,
        "notify": None,
        "errors": [],
        "warnings": [],
        "timing": {
            "started_at": started_at,
        },
    }

    # Check film date if URL provided
    film_info = None
    if film_url:
        film_start = time.time()
        film_info = check_film_date(film_url, timeout=timeout)
        result["film"] = film_info
        result["timing"]["film_check_ms"] = round((time.time() - film_start) * 1000, 2)

        # Add warning if film is NOT showing today
        if film_info.get("ok") and not film_info.get("is_showing_today"):
            days = film_info.get("days_until")
            if days and days > 0:
                result["warnings"].append({
                    "code": "FILM_NOT_TODAY",
                    "message": f"Film showing in {days} days ({film_info.get('next_showing')}), not today",
                })

    publish_start = time.time()

    # Step 1: Run publish
    publish_result = run_publish(
        source=source,
        simplenote=simplenote,
        vps=vps,
        mode=mode,
        timeout=timeout,
        max_retries=max_retries,
        dry_run=dry_run,
        verbose=verbose,
        json_output=True,
    )
    result["publish"] = publish_result
    result["timing"]["publish_ms"] = round((time.time() - publish_start) * 1000, 2)

    # Check if publish succeeded
    if not publish_result.get("ok", False):
        result["ok"] = False
        error = normalize_publish_error(publish_result)
        if error:
            result["errors"].append(error)
        # Complete timing
        result["timing"]["completed_at"] = get_timestamp()
        result["timing"]["total_ms"] = round((time.time() - start_time) * 1000, 2)
        result["duration_ms"] = result["timing"]["total_ms"]
        return result

    notify_start = time.time()

    # Step 2: Run t2me notification
    if not no_notify:
        message = format_telegram_message(publish_result, source, caption, film_info)
        notify_result = run_t2me(
            message=message,
            caption=caption,
            dry_run=dry_run,
            verbose=verbose,
        )
        result["notify"] = notify_result

        # Notification failure = warning, not error (graceful degradation)
        if not notify_result.get("ok", False):
            error = normalize_notify_error(notify_result)
            if error:
                result["warnings"].append({
                    "code": "NOTIFY_FAILED",
                    "message": error.get("message", "Notification failed but publish succeeded"),
                })

    result["timing"]["notify_ms"] = round((time.time() - notify_start) * 1000, 2)

    # Complete timing
    result["timing"]["completed_at"] = get_timestamp()
    result["timing"]["total_ms"] = round((time.time() - start_time) * 1000, 2)
    result["duration_ms"] = result["timing"]["total_ms"]

    return result
