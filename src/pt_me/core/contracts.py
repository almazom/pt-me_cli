"""Core contracts for pt-me pipeline.

Defines Protocol interfaces for loose coupling between modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol, TypedDict


class InputType(TypedDict):
    """Input source type information."""

    type: Literal["text", "image", "audio", "url", "unknown"]
    mime_type: str
    size_bytes: int


class InputSource(Protocol):
    """Contract for input source resolution and loading."""

    def load(self) -> bytes:
        """Load content from source."""
        ...

    def get_type(self) -> InputType:
        """Get input type information."""
        ...

    def get_name(self) -> str:
        """Get human-readable source name."""
        ...

    def validate(self) -> list[str]:
        """Validate input and return list of errors."""
        ...


class PublishResult(TypedDict, total=False):
    """Result from publisher module."""

    ok: bool
    url: str
    provider: str
    metadata: dict
    errors: list[str]
    warnings: list[str]
    attempts: int


class Publisher(Protocol):
    """Contract for publishing content (p-me wrapper)."""

    def publish(
        self, content: bytes, source_type: str, source_name: str
    ) -> PublishResult:
        """Publish content and return result."""
        ...

    def health_check(self) -> bool:
        """Check if publisher is available."""
        ...


class SummarizerResult(TypedDict):
    """Result from summarizer module."""

    ok: bool
    points: list[str]
    title: str
    errors: list[str]


class Summarizer(Protocol):
    """Contract for AI summarization."""

    def summarize(self, content: str) -> SummarizerResult:
        """Generate summary from content."""
        ...


@dataclass
class MessageContext:
    """Context for message formatting."""

    published_url: str
    provider: str
    source_name: str
    source_type: str
    caption: str | None = None
    summary_points: list[str] | None = None
    summary_title: str | None = None


class MessageFormatter(Protocol):
    """Contract for message formatting."""

    def format(self, context: MessageContext) -> str:
        """Format message from context."""
        ...


class SendResult(TypedDict, total=False):
    """Result from notifier module."""

    ok: bool
    message_id: int
    target: str
    errors: list[str]


class Notifier(Protocol):
    """Contract for sending notifications (t2me wrapper)."""

    def send(self, message: str, file: bytes | None = None) -> SendResult:
        """Send message and return result."""
        ...

    def health_check(self) -> bool:
        """Check if notifier is available."""
        ...


@dataclass
class PipelineResult:
    """Final result from pt-me pipeline."""

    ok: bool
    correlation_id: str
    input_type: InputType
    publish: PublishResult | None = None
    notify: SendResult | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "ok": self.ok,
            "pipeline": "pt-me",
            "version": "1.0.0",
            "correlation_id": self.correlation_id,
            "stages": {
                "input": {
                    "type": self.input_type.get("type"),
                    "mime_type": self.input_type.get("mime_type"),
                    "size_bytes": self.input_type.get("size_bytes"),
                },
                "publish": self.publish or {"skipped": True},
                "notify": self.notify or {"skipped": True},
            },
            "errors": self.errors,
            "warnings": self.warnings,
        }


class Config(Protocol):
    """Contract for configuration."""

    def get(self, key: str, default: str | None = None) -> str | None:
        """Get configuration value."""
        ...

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value."""
        ...

    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value."""
        ...
