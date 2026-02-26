"""Observability module for pt-me.

Provides logging, correlation IDs, and structured output.
"""

import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any


def generate_correlation_id() -> str:
    """Generate unique correlation ID for request tracing."""
    return f"pt-{uuid.uuid4().hex[:8]}"


class StructuredLogger:
    """Logger with structured output support."""

    def __init__(
        self,
        name: str,
        correlation_id: str | None = None,
        verbose: bool = False,
        json_output: bool = False,
    ):
        self.correlation_id = correlation_id or generate_correlation_id()
        self.verbose = verbose
        self.json_output = json_output

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)

        # Clear existing handlers
        self.logger.handlers.clear()

        # Console handler
        handler = logging.StreamHandler(sys.stderr if verbose else sys.stdout)
        handler.setLevel(logging.DEBUG if verbose else logging.INFO)

        if verbose:
            formatter = logging.Formatter(
                f"%(asctime)s [{self.correlation_id}] %(levelname)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        else:
            formatter = logging.Formatter("%(message)s")

        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log debug message."""
        if self.verbose:
            self.logger.debug(msg, extra=kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log info message."""
        self.logger.info(msg, extra=kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.logger.warning(msg, extra=kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        """Log error message."""
        self.logger.error(msg, extra=kwargs)

    def log_stage(
        self, stage: str, status: str, details: dict | None = None
    ) -> None:
        """Log pipeline stage with structured data.

        Args:
            stage: Stage name (input, publish, notify)
            status: Status (start, complete, error, skip)
            details: Additional details
        """
        if self.json_output:
            # JSON structured log for machine parsing - goes to stderr
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "correlation_id": self.correlation_id,
                "stage": stage,
                "status": status,
                "details": details or {},
            }
            # Log structured events to stderr to keep stdout clean for final JSON
            print(f"JSON:{log_entry}", file=sys.stderr, flush=True)
        else:
            # Human-readable log
            emoji = {
                "start": "→",
                "complete": "✓",
                "error": "✗",
                "skip": "⊘",
            }.get(status, "•")

            msg = f"{emoji} {stage}: {status}"
            if details:
                for key, value in details.items():
                    msg += f"\n    {key}: {value}"

            if status == "error":
                self.error(msg)
            elif status == "skip":
                self.warning(msg)
            else:
                self.info(msg)


def get_env_config() -> dict[str, str]:
    """Get configuration from environment variables."""
    return {
        key: value
        for key, value in os.environ.items()
        if key.startswith(("PT_ME_", "PUBLISH_ME_", "T2ME_"))
    }
