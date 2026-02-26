"""Input source resolver for pt-me.

Determines input type (file, URL, stdin) and creates appropriate loader.
"""

import os
import re
from dataclasses import dataclass
from enum import Enum, auto

from ..core.contracts import InputSource, InputType


class SourceType(Enum):
    """Type of input source."""

    FILE = auto()
    URL = auto()
    STDIN = auto()
    UNKNOWN = auto()


# URL pattern (simplified but covers most cases)
URL_PATTERN = re.compile(
    r"^https?://"
    r"(?:(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})"
    r"(?:/[^\s]*)?$"
)

# Supported file extensions
TEXT_EXTENSIONS = {".md", ".txt", ".text", ".rst"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".flac"}


@dataclass
class ResolvedInput:
    """Result of input resolution."""

    source_type: SourceType
    source: str  # File path, URL, or '-' for stdin
    exists: bool = True
    error: str | None = None


class InputResolver:
    """Resolves input source and creates appropriate loader."""

    def __init__(self, source: str):
        """Initialize resolver with source string.

        Args:
            source: File path, URL, or '-' for stdin
        """
        self.source = source

    def resolve(self) -> ResolvedInput:
        """Resolve input source type.

        Returns:
            ResolvedInput with source type and validation info
        """
        # Check for stdin
        if self.source == "-":
            return ResolvedInput(source_type=SourceType.STDIN, source="-")

        # Check for URL
        if URL_PATTERN.match(self.source):
            return ResolvedInput(source_type=SourceType.URL, source=self.source)

        # Check for file
        if os.path.isfile(self.source):
            return ResolvedInput(
                source_type=SourceType.FILE, source=self.source, exists=True
            )

        # Unknown source
        return ResolvedInput(
            source_type=SourceType.UNKNOWN,
            source=self.source,
            exists=False,
            error=f"Source not found: {self.source}",
        )

    def get_mime_type(self) -> str:
        """Guess MIME type from source."""
        if self.source == "-":
            return "text/markdown"

        if URL_PATTERN.match(self.source):
            return "text/markdown"  # Default for URLs

        ext = os.path.splitext(self.source)[1].lower()

        if ext in TEXT_EXTENSIONS:
            return "text/markdown" if ext == ".md" else "text/plain"
        elif ext in IMAGE_EXTENSIONS:
            return f"image/{ext.lstrip('.')}"
        elif ext in AUDIO_EXTENSIONS:
            return f"audio/{ext.lstrip('.')}"

        return "application/octet-stream"

    def get_input_type(self) -> InputType:
        """Get input type information."""
        mime_type = self.get_mime_type()

        if mime_type.startswith("text/"):
            type_name = "text"
        elif mime_type.startswith("image/"):
            type_name = "image"
        elif mime_type.startswith("audio/"):
            type_name = "audio"
        elif URL_PATTERN.match(self.source):
            type_name = "url"
        else:
            type_name = "unknown"

        return InputType(type=type_name, mime_type=mime_type, size_bytes=0)

    def create_loader(self) -> InputSource:
        """Create appropriate loader for resolved source.

        Returns:
            InputSource implementation

        Raises:
            ValueError: If source cannot be resolved
        """
        resolved = self.resolve()

        if resolved.source_type == SourceType.STDIN:
            from .loader import StdinLoader

            return StdinLoader()
        elif resolved.source_type == SourceType.FILE:
            from .loader import FileLoader

            return FileLoader(resolved.source)
        elif resolved.source_type == SourceType.URL:
            from .loader import URLLoader

            return URLLoader(resolved.source)
        else:
            raise ValueError(resolved.error or "Unknown source type")
