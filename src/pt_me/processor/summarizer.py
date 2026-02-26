"""Summarizer for pt-me.

Generates brief summaries from text content.
"""

import re

from ..core.contracts import SummarizerResult


class SimpleSummarizer:
    """Simple extractive summarizer.

    Uses basic text analysis to extract key points.
    Note: For production, consider integrating with AI API.
    """

    def __init__(self, max_points: int = 3, max_length: int = 100):
        """Initialize summarizer.

        Args:
            max_points: Maximum number of summary points
            max_length: Maximum length per point
        """
        self.max_points = max_points
        self.max_length = max_length

    def _extract_title(self, content: str) -> str:
        """Extract title from content.

        Args:
            content: Text content

        Returns:
            Extracted or generated title
        """
        # Try to find first heading
        lines = content.split("\n")
        for line in lines[:10]:  # Check first 10 lines
            if line.startswith("# "):
                return line[2:].strip()

        # Try to find first non-empty line
        for line in lines[:5]:
            line = line.strip()
            if line:
                # Truncate if too long
                if len(line) > self.max_length:
                    return line[: self.max_length - 3] + "..."
                return line

        return "Untitled"

    def _extract_sentences(self, content: str) -> list[str]:
        """Extract sentences from content.

        Args:
            content: Text content

        Returns:
            List of sentences
        """
        # Remove markdown formatting
        text = re.sub(r"[*_`#]", "", content)

        # Split on sentence boundaries
        sentences = re.split(r"[.!?]\s+", text)

        # Filter and clean
        cleaned = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:  # Reasonable sentence length
                cleaned.append(sentence)

        return cleaned

    def _extract_key_points(self, content: str) -> list[str]:
        """Extract key points from content.

        Args:
            content: Text content

        Returns:
            List of key points
        """
        points = []

        # Look for list items
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith(("- ", "* ", "• ", "1.", "2.", "3.")):
                # Remove list marker
                text = re.sub(r"^[-*•]\s*|\d+\.\s*", "", line)
                if len(text) > 10:
                    points.append(text)

        return points

    def summarize(self, content: str) -> SummarizerResult:
        """Generate summary from content.

        Args:
            content: Text content to summarize

        Returns:
            SummarizerResult with title and key points
        """
        try:
            # Extract title
            title = self._extract_title(content)

            # Extract key points from lists first
            points = self._extract_key_points(content)

            # If not enough list items, extract from sentences
            if len(points) < self.max_points:
                sentences = self._extract_sentences(content)
                for sentence in sentences:
                    if sentence not in points and title not in sentence:
                        points.append(sentence)
                        if len(points) >= self.max_points:
                            break

            # Truncate points if needed
            points = [
                p[: self.max_length] + "..." if len(p) > self.max_length else p
                for p in points[: self.max_points]
            ]

            # If no points extracted, create generic summary
            if not points:
                points = ["Content published", "See link for details"]

            return SummarizerResult(
                ok=True,
                points=points,
                title=title,
                errors=[],
            )

        except Exception as e:
            return SummarizerResult(
                ok=False,
                points=[],
                title="Error",
                errors=[str(e)],
            )
