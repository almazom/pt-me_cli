"""Input loaders for pt-me.

Loads content from file, URL, or stdin.
"""

import sys

import requests

from ..core.contracts import InputType
from .resolver import InputResolver


class FileLoader:
    """Load content from file."""

    def __init__(self, file_path: str):
        """Initialize file loader.

        Args:
            file_path: Path to file
        """
        self.file_path = file_path
        self._resolver = InputResolver(file_path)
        self._content: bytes | None = None

    def load(self) -> bytes:
        """Load content from file."""
        if self._content is None:
            with open(self.file_path, "rb") as f:
                self._content = f.read()
        return self._content

    def get_type(self) -> InputType:
        """Get input type information."""
        input_type = self._resolver.get_input_type()
        content = self.load()
        return InputType(
            type=input_type["type"],
            mime_type=input_type["mime_type"],
            size_bytes=len(content),
        )

    def get_name(self) -> str:
        """Get human-readable source name."""
        return self.file_path

    def validate(self) -> list[str]:
        """Validate file and return list of errors."""
        errors = []

        try:
            content = self.load()
            if len(content) == 0:
                errors.append("File is empty")
            elif len(content) > 50 * 1024 * 1024:  # 50MB limit
                errors.append("File too large (max 50MB)")
        except OSError as e:
            errors.append(f"Cannot read file: {e}")

        return errors


class URLLoader:
    """Load content from URL."""

    def __init__(self, url: str, timeout: int = 30):
        """Initialize URL loader.

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
        """
        self.url = url
        self.timeout = timeout
        self._resolver = InputResolver(url)
        self._content: bytes | None = None
        self._content_type: str | None = None

    def load(self) -> bytes:
        """Load content from URL."""
        if self._content is None:
            response = requests.get(self.url, timeout=self.timeout)
            response.raise_for_status()
            self._content = response.content
            self._content_type = response.headers.get("Content-Type", "")
        return self._content

    def get_type(self) -> InputType:
        """Get input type information."""
        content = self.load()

        # Determine type from content type header
        mime_type = "text/markdown"
        if self._content_type:
            if self._content_type.startswith("image/") or self._content_type.startswith("audio/"):
                mime_type = self._content_type
            elif self._content_type.startswith("text/"):
                mime_type = "text/markdown"

        type_name = "url"
        if mime_type.startswith("text/"):
            type_name = "text"
        elif mime_type.startswith("image/"):
            type_name = "image"
        elif mime_type.startswith("audio/"):
            type_name = "audio"

        return InputType(type=type_name, mime_type=mime_type, size_bytes=len(content))

    def get_name(self) -> str:
        """Get human-readable source name."""
        return self.url

    def validate(self) -> list[str]:
        """Validate URL and return list of errors."""
        errors = []

        try:
            content = self.load()
            if len(content) == 0:
                errors.append("URL returned empty content")
            elif len(content) > 50 * 1024 * 1024:  # 50MB limit
                errors.append("Content too large (max 50MB)")
        except requests.RequestException as e:
            errors.append(f"Cannot fetch URL: {e}")

        return errors


class StdinLoader:
    """Load content from stdin."""

    def __init__(self):
        """Initialize stdin loader."""
        self._resolver = InputResolver("-")
        self._content: bytes | None = None

    def load(self) -> bytes:
        """Load content from stdin."""
        if self._content is None:
            self._content = sys.stdin.buffer.read()
        return self._content

    def get_type(self) -> InputType:
        """Get input type information."""
        content = self.load()
        return InputType(type="text", mime_type="text/markdown", size_bytes=len(content))

    def get_name(self) -> str:
        """Get human-readable source name."""
        return "stdin"

    def validate(self) -> list[str]:
        """Validate stdin content and return list of errors."""
        errors = []

        content = self.load()
        if len(content) == 0:
            errors.append("No input provided via stdin")

        return errors
