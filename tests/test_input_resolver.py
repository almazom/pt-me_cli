"""Tests for input resolver module."""

from pathlib import Path

from pt_me.input.resolver import (
    InputResolver,
    ResolvedInput,
    SourceType,
)


class TestInputResolver:
    """Tests for InputResolver class."""

    def test_resolve_file(self, tmp_path: Path) -> None:
        """Test resolving a file source."""
        # Create temp file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        resolver = InputResolver(str(test_file))
        result = resolver.resolve()

        assert result.source_type == SourceType.FILE
        assert result.exists is True
        assert result.error is None

    def test_resolve_url(self) -> None:
        """Test resolving a URL source."""
        url = "https://example.com/article.md"
        resolver = InputResolver(url)
        result = resolver.resolve()

        assert result.source_type == SourceType.URL
        assert result.exists is True
        assert result.source == url

    def test_resolve_stdin(self) -> None:
        """Test resolving stdin source."""
        resolver = InputResolver("-")
        result = resolver.resolve()

        assert result.source_type == SourceType.STDIN
        assert result.source == "-"
        assert result.exists is True

    def test_resolve_unknown(self) -> None:
        """Test resolving unknown source."""
        resolver = InputResolver("/nonexistent/file.md")
        result = resolver.resolve()

        assert result.source_type == SourceType.UNKNOWN
        assert result.exists is False
        assert result.error is not None

    def test_get_mime_type_text(self, tmp_path: Path) -> None:
        """Test MIME type detection for text files."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        resolver = InputResolver(str(test_file))
        mime_type = resolver.get_mime_type()

        assert mime_type == "text/markdown"

    def test_get_mime_type_url(self) -> None:
        """Test MIME type detection for URLs."""
        url = "https://example.com/article.md"
        resolver = InputResolver(url)
        mime_type = resolver.get_mime_type()

        assert mime_type == "text/markdown"

    def test_get_input_type(self, tmp_path: Path) -> None:
        """Test input type detection."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        resolver = InputResolver(str(test_file))
        input_type = resolver.get_input_type()

        assert input_type["type"] == "text"
        assert input_type["mime_type"] == "text/markdown"

    def test_create_loader_file(self, tmp_path: Path) -> None:
        """Test creating file loader."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        resolver = InputResolver(str(test_file))
        loader = resolver.create_loader()

        content = loader.load()
        assert content == b"# Test"

    def test_url_patterns(self) -> None:
        """Test URL pattern matching."""
        valid_urls = [
            "https://example.com",
            "http://example.com/article.md",
            "https://sub.example.com/path/to/file.md",
        ]

        for url in valid_urls:
            resolver = InputResolver(url)
            result = resolver.resolve()
            assert result.source_type == SourceType.URL, f"Failed for {url}"

        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "/local/file.md",
        ]

        for url in invalid_urls:
            resolver = InputResolver(url)
            result = resolver.resolve()
            assert result.source_type != SourceType.URL, f"Failed for {url}"


class TestResolvedInput:
    """Tests for ResolvedInput dataclass."""

    def test_resolved_input_defaults(self) -> None:
        """Test ResolvedInput default values."""
        result = ResolvedInput(source_type=SourceType.FILE, source="test.md")

        assert result.exists is True
        assert result.error is None

    def test_resolved_input_with_error(self) -> None:
        """Test ResolvedInput with error."""
        result = ResolvedInput(
            source_type=SourceType.UNKNOWN,
            source="test.md",
            exists=False,
            error="File not found",
        )

        assert result.exists is False
        assert result.error == "File not found"
