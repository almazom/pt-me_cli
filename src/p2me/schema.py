"""Schema definitions for p2me CLI output."""

from __future__ import annotations

from typing import Any

# Version for schema compatibility
SCHEMA_VERSION = "1.1.0"

# Standard error codes
class ErrorCode:
    """Standardized error codes for p2me."""
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_READ_ERROR = "FILE_READ_ERROR"
    EMPTY_CONTENT = "EMPTY_CONTENT"
    INVALID_INPUT = "INVALID_INPUT"
    PUBLISH_FAILED = "PUBLISH_FAILED"
    NOTIFY_FAILED = "NOTIFY_FAILED"
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class ErrorStage:
    """Stage where error occurred."""
    INPUT = "input"
    PUBLISH = "publish"
    NOTIFY = "notify"
    UNKNOWN = "unknown"


def create_error(
    code: str,
    message: str,
    stage: str = ErrorStage.UNKNOWN,
    recoverable: bool = False,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a standardized error object.

    Args:
        code: Error code from ErrorCode class
        message: Human-readable error message
        stage: Stage where error occurred
        recoverable: Whether operation could be retried
        details: Additional error details

    Returns:
        Standardized error dictionary
    """
    error: dict[str, Any] = {
        "code": code,
        "message": message,
        "stage": stage,
        "recoverable": recoverable,
    }
    if details:
        error["details"] = details
    return error


def normalize_publish_error(publish_result: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize publish step error to standard format.

    Args:
        publish_result: Raw publish result

    Returns:
        Standardized error or None if no error
    """
    if publish_result.get("ok", False):
        return None

    # Check for existing error structure
    error = publish_result.get("error", {})

    if isinstance(error, dict):
        code = error.get("code", "")
        message = error.get("message", str(error))

        # Map to standard codes
        code_mapping = {
            "FILE_ERROR": ErrorCode.FILE_NOT_FOUND,
            "VALIDATION_ERROR": ErrorCode.INVALID_INPUT,
            "NETWORK_ERROR": ErrorCode.NETWORK_ERROR,
            "TIMEOUT_ERROR": ErrorCode.TIMEOUT_ERROR,
        }
        std_code = code_mapping.get(code, ErrorCode.PUBLISH_FAILED)

        return create_error(
            code=std_code,
            message=message,
            stage=ErrorStage.PUBLISH,
            recoverable=std_code in [ErrorCode.NETWORK_ERROR, ErrorCode.TIMEOUT_ERROR],
        )

    # Check for errors array
    errors = publish_result.get("errors", [])
    if errors:
        message = (
            errors[0]
            if isinstance(errors[0], str)
            else errors[0].get("message", "Publish failed")
        )
        return create_error(
            code=ErrorCode.PUBLISH_FAILED,
            message=message,
            stage=ErrorStage.PUBLISH,
        )

    # Check stderr
    stderr = publish_result.get("stderr", "")
    if stderr:
        return create_error(
            code=ErrorCode.PUBLISH_FAILED,
            message=stderr,
            stage=ErrorStage.PUBLISH,
        )

    # Generic error
    return create_error(
        code=ErrorCode.PUBLISH_FAILED,
        message="Publish failed with unknown error",
        stage=ErrorStage.PUBLISH,
    )


def normalize_notify_error(notify_result: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize notify step error to standard format.

    Args:
        notify_result: Raw notify result

    Returns:
        Standardized error or None if no error
    """
    if notify_result is None:
        return None

    if notify_result.get("ok", False):
        return None

    errors = notify_result.get("errors", [])
    if errors:
        message = (
            errors[0]
            if isinstance(errors[0], str)
            else errors[0].get("message", "Notification failed")
        )
        return create_error(
            code=ErrorCode.NOTIFY_FAILED,
            message=message,
            stage=ErrorStage.NOTIFY,
            recoverable=True,
        )

    stderr = notify_result.get("stderr", "")
    if stderr:
        return create_error(
            code=ErrorCode.NOTIFY_FAILED,
            message=stderr,
            stage=ErrorStage.NOTIFY,
            recoverable=True,
        )

    return create_error(
        code=ErrorCode.NOTIFY_FAILED,
        message="Notification failed",
        stage=ErrorStage.NOTIFY,
        recoverable=True,
    )


# JSON Schema for p2me output
OUTPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/almazomkz/p2me/schema/output.json",
    "title": "p2me Output Schema",
    "description": "Schema for p2me CLI JSON output",
    "type": "object",
    "required": ["ok", "schema_version", "correlation_id", "timestamp"],
    "properties": {
        "ok": {
            "type": "boolean",
            "description": "Overall operation success",
        },
        "schema_version": {
            "type": "string",
            "description": "Schema version for compatibility checking",
            "pattern": "^\\d+\\.\\d+\\.\\d+$",
        },
        "correlation_id": {
            "type": "string",
            "description": "Unique identifier for this operation",
            "pattern": "^p2me_\\d{8}_\\d{6}_[a-f0-9]{6}$",
        },
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of operation start",
        },
        "duration_ms": {
            "type": "number",
            "description": "Total operation duration in milliseconds",
        },
        "input": {
            "type": "object",
            "description": "Echo of input parameters",
            "properties": {
                "source": {"type": "string"},
                "provider": {"type": ["string", "null"]},
                "mode": {"type": "string"},
                "caption": {"type": ["string", "null"]},
                "dry_run": {"type": "boolean"},
                "no_notify": {"type": "boolean"},
                "validate": {"type": "boolean"},
                "timeout": {"type": "integer"},
                "max_retries": {"type": "integer"},
                "film_url": {"type": ["string", "null"]},
            },
        },
        "validation": {
            "type": ["object", "null"],
            "description": "Validation-only result",
            "properties": {
                "ok": {"type": "boolean"},
                "source_type": {"type": "string"},
                "size_bytes": {"type": "integer"},
                "film_url_checked": {"type": "boolean"},
            },
        },
        "publish": {
            "type": ["object", "null"],
            "description": "Publish step result",
            "properties": {
                "ok": {"type": "boolean"},
                "url": {"type": ["string", "null"]},
                "provider": {"type": "string"},
            },
        },
        "notify": {
            "type": ["object", "null"],
            "description": "Notify step result",
            "properties": {
                "ok": {"type": "boolean"},
                "message_id": {"type": ["integer", "null"]},
            },
        },
        "errors": {
            "type": "array",
            "description": "List of errors (empty if ok=true)",
            "items": {
                "type": "object",
                "required": ["code", "message", "stage"],
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "stage": {
                        "type": "string",
                        "enum": ["input", "publish", "notify", "unknown"],
                    },
                    "recoverable": {"type": "boolean"},
                    "details": {"type": "object"},
                },
            },
        },
        "warnings": {
            "type": "array",
            "description": "List of warnings",
            "items": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                },
            },
        },
        "timing": {
            "type": "object",
            "description": "Timing breakdown",
            "properties": {
                "started_at": {"type": "string", "format": "date-time"},
                "completed_at": {"type": "string", "format": "date-time"},
                "publish_ms": {"type": "number"},
                "notify_ms": {"type": "number"},
            },
        },
    },
}


CAPABILITIES: dict[str, Any] = {
    "name": "p2me",
    "version": "1.1.0",
    "schema_version": SCHEMA_VERSION,
        "capabilities": [
            "publish",
            "notify",
            "dry_run",
            "json_output",
        "health_check",
        "validate",
        "schema",
    ],
    "providers": [
        {"name": "simplenote", "flag": "-sn"},
        {"name": "vps", "flag": "-vps"},
    ],
    "modes": ["none", "minimal", "standard", "aggressive"],
    "exit_codes": {
        "0": "success",
        "1": "validation_or_execution_error",
        "2": "invalid_argument",
        "3": "unknown_error",
    },
    "error_codes": {
        "FILE_NOT_FOUND": "Input file does not exist",
        "FILE_READ_ERROR": "Cannot read input file",
        "EMPTY_CONTENT": "Input content is empty",
        "INVALID_INPUT": "Input validation failed",
        "PUBLISH_FAILED": "Publishing to provider failed",
        "NOTIFY_FAILED": "Telegram notification failed",
        "NETWORK_ERROR": "Network connectivity issue",
        "TIMEOUT_ERROR": "Operation timed out",
        "DEPENDENCY_MISSING": "Required dependency not found",
        "UNKNOWN_ERROR": "Unexpected error",
    },
}
