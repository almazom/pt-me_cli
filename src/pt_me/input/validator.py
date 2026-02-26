"""Input validator for pt-me.

Validates input before processing.
"""


from ..core.contracts import InputSource
from .resolver import SourceType


class InputValidator:
    """Validates input source before processing."""

    def __init__(self, source: InputSource, source_type: SourceType):
        """Initialize validator.

        Args:
            source: Input source to validate
            source_type: Type of input source
        """
        self.source = source
        self.source_type = source_type
        self._errors: list[str] | None = None

    def validate(self) -> tuple[bool, list[str]]:
        """Validate input and return success status and errors.

        Returns:
            Tuple of (is_valid, errors)
        """
        if self._errors is None:
            self._errors = self.source.validate()

        is_valid = len(self._errors) == 0
        return is_valid, self._errors

    def get_errors(self) -> list[str]:
        """Get validation errors."""
        if self._errors is None:
            self.validate()
        return self._errors or []

    def has_errors(self) -> bool:
        """Check if validation has errors."""
        return len(self.get_errors()) > 0
