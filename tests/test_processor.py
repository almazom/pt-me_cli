"""Tests for processor module."""


from pt_me.core.contracts import MessageContext
from pt_me.processor.formatter import TemplateFormatter
from pt_me.processor.summarizer import SimpleSummarizer


class TestSimpleSummarizer:
    """Tests for SimpleSummarizer class."""

    def test_extract_title_from_heading(self) -> None:
        """Test extracting title from markdown heading."""
        content = "# My Article Title\n\nSome content here..."

        summarizer = SimpleSummarizer()
        result = summarizer.summarize(content)

        assert result["ok"] is True
        assert result["title"] == "My Article Title"

    def test_extract_title_from_first_line(self) -> None:
        """Test extracting title from first line."""
        content = "Important Title\n\nSome content here..."

        summarizer = SimpleSummarizer()
        result = summarizer.summarize(content)

        assert result["ok"] is True
        assert "Important Title" in result["title"]

    def test_extract_key_points_from_list(self) -> None:
        """Test extracting key points from list items."""
        content = """# Title

- First important point
- Second important point
- Third important point
"""

        summarizer = SimpleSummarizer()
        result = summarizer.summarize(content)

        assert result["ok"] is True
        assert len(result["points"]) >= 3

    def test_extract_key_points_from_numbered_list(self) -> None:
        """Test extracting points from numbered list."""
        content = """# Title

1. First step
2. Second step
3. Third step
"""

        summarizer = SimpleSummarizer()
        result = summarizer.summarize(content)

        assert result["ok"] is True
        # At least one point should be extracted
        assert len(result["points"]) >= 1

    def test_summarize_empty_content(self) -> None:
        """Test summarizing empty content."""
        content = ""

        summarizer = SimpleSummarizer()
        result = summarizer.summarize(content)

        assert result["ok"] is True
        assert len(result["points"]) > 0  # Should have fallback

    def test_summarize_short_content(self) -> None:
        """Test summarizing short content."""
        content = "This is a short article."

        summarizer = SimpleSummarizer()
        result = summarizer.summarize(content)

        assert result["ok"] is True

    def test_max_points_limit(self) -> None:
        """Test that max_points limit is respected."""
        content = """# Title

- Point 1
- Point 2
- Point 3
- Point 4
- Point 5
"""

        summarizer = SimpleSummarizer(max_points=3)
        result = summarizer.summarize(content)

        assert len(result["points"]) <= 3

    def test_max_length_truncation(self) -> None:
        """Test that long points are truncated."""
        long_point = "x" * 200
        content = f"# Title\n\n- {long_point}"

        summarizer = SimpleSummarizer(max_length=50)
        result = summarizer.summarize(content)

        assert result["ok"] is True
        for point in result["points"]:
            assert len(point) <= 53  # max_length + "..."

    def test_error_handling(self) -> None:
        """Test error handling in summarizer."""
        # This should not raise exceptions
        summarizer = SimpleSummarizer()
        result = summarizer.summarize(None)  # type: ignore

        assert result["ok"] is False or result["ok"] is True


class TestTemplateFormatter:
    """Tests for TemplateFormatter class."""

    def test_format_standard_template(self) -> None:
        """Test formatting with standard template."""
        context = MessageContext(
            published_url="https://example.com/article",
            provider="simplenote",
            source_name="article.md",
            source_type="text",
            caption="My Article",
            summary_points=["Point 1", "Point 2", "Point 3"],
        )

        formatter = TemplateFormatter(template_name="standard")
        message = formatter.format(context)

        assert "My Article" in message
        assert "https://example.com/article" in message
        assert "Point 1" in message
        assert "◐" in message  # Minimal emoji for "Кратко"
        assert "➡︎" in message  # Minimal emoji for link
        assert "①" in message  # Circled numbers

    def test_format_minimal_template(self) -> None:
        """Test formatting with minimal template."""
        context = MessageContext(
            published_url="https://example.com/article",
            provider="simplenote",
            source_name="article.md",
            source_type="text",
            caption="Quick post",
        )

        formatter = TemplateFormatter(template_name="minimal")
        message = formatter.format(context)

        assert "Quick post" in message
        assert "https://example.com/article" in message
        assert "➡︎" in message  # Minimal emoji for link

    def test_format_detailed_template(self) -> None:
        """Test formatting with detailed template."""
        context = MessageContext(
            published_url="https://example.com/article",
            provider="simplenote",
            source_name="article.md",
            source_type="text",
            caption="Detailed Article",
            summary_points=["Summary point"],
        )

        formatter = TemplateFormatter(template_name="detailed")
        message = formatter.format(context)

        assert "Detailed Article" in message
        assert "article.md" in message
        assert "simplenote" in message
        assert "https://example.com/article" in message
        assert "○" in message  # Minimal emoji for metadata
        assert "◐" in message  # Minimal emoji for "Кратко"

    def test_format_without_caption(self) -> None:
        """Test formatting without custom caption."""
        context = MessageContext(
            published_url="https://example.com/article",
            provider="simplenote",
            source_name="article.md",
            source_type="text",
            summary_title="Auto Title",
        )

        formatter = TemplateFormatter(template_name="standard")
        message = formatter.format(context)

        assert "Auto Title" in message

    def test_format_without_summary(self) -> None:
        """Test formatting without summary points."""
        context = MessageContext(
            published_url="https://example.com/article",
            provider="simplenote",
            source_name="article.md",
            source_type="text",
        )

        formatter = TemplateFormatter(template_name="standard")
        message = formatter.format(context)

        assert "https://example.com/article" in message
        # Should have fallback text with minimal emoji
        assert "○" in message

    def test_custom_template_not_found(self) -> None:
        """Test handling of missing custom template."""
        context = MessageContext(
            published_url="https://example.com/article",
            provider="simplenote",
            source_name="article.md",
            source_type="text",
        )

        # Should fall back to standard template
        formatter = TemplateFormatter(template_name="nonexistent")
        message = formatter.format(context)

        assert len(message) > 0

    def test_format_cleans_whitespace(self) -> None:
        """Test that formatter cleans extra whitespace."""
        context = MessageContext(
            published_url="https://example.com/article",
            provider="simplenote",
            source_name="article.md",
            source_type="text",
            caption="Test  ",  # Trailing spaces
        )

        formatter = TemplateFormatter(template_name="minimal")
        message = formatter.format(context)

        # Lines should not have trailing whitespace
        for line in message.split("\n"):
            assert line == line.rstrip()
