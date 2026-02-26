"""Tests for input loader module."""

import io
import sys
from pathlib import Path

import pytest

from pt_me.input.loader import FileLoader, StdinLoader, URLLoader


class TestFileLoader:
    """Tests for FileLoader class."""

    def test_load_file(self, tmp_path: Path) -> None:
        """Test loading content from file."""
        test_file = tmp_path / "test.md"
        test_content = "# Test Content\n\nHello World"
        test_file.write_text(test_content)

        loader = FileLoader(str(test_file))
        content = loader.load()

        assert content == test_content.encode("utf-8")

    def test_load_binary_file(self, tmp_path: Path) -> None:
        """Test loading binary file."""
        test_file = tmp_path / "test.bin"
        test_content = b"\x00\x01\x02\x03"
        test_file.write_bytes(test_content)

        loader = FileLoader(str(test_file))
        content = loader.load()

        assert content == test_content

    def test_get_type(self, tmp_path: Path) -> None:
        """Test getting file type."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        loader = FileLoader(str(test_file))
        input_type = loader.get_type()

        assert input_type["type"] == "text"
        assert input_type["mime_type"] == "text/markdown"
        assert input_type["size_bytes"] > 0

    def test_get_name(self, tmp_path: Path) -> None:
        """Test getting file name."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        loader = FileLoader(str(test_file))
        name = loader.get_name()

        assert name == str(test_file)

    def test_validate_empty_file(self, tmp_path: Path) -> None:
        """Test validation of empty file."""
        test_file = tmp_path / "empty.md"
        test_file.write_text("")

        loader = FileLoader(str(test_file))
        errors = loader.validate()

        assert len(errors) > 0
        assert "empty" in errors[0].lower()

    def test_validate_nonexistent_file(self, tmp_path: Path) -> None:
        """Test validation of nonexistent file."""
        loader = FileLoader(str(tmp_path / "nonexistent.md"))
        errors = loader.validate()

        assert len(errors) > 0


class TestStdinLoader:
    """Tests for StdinLoader class."""

    @pytest.mark.skip(reason="Incompatible with pytest stdin capture - covered by E2E tests")
    def test_load_stdin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading from stdin."""
        test_content = b"# Test from stdin"
        monkeypatch.setattr(sys.stdin, "buffer", io.BytesIO(test_content))

        loader = StdinLoader()
        content = loader.load()

        assert content == test_content

    @pytest.mark.skip(reason="Incompatible with pytest stdin capture - covered by E2E tests")
    def test_get_type_stdin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting stdin type."""
        test_content = b"# Test"
        monkeypatch.setattr(sys.stdin, "buffer", io.BytesIO(test_content))

        loader = StdinLoader()
        input_type = loader.get_type()

        assert input_type["type"] == "text"
        assert input_type["mime_type"] == "text/markdown"

    def test_get_name_stdin(self) -> None:
        """Test getting stdin name."""
        loader = StdinLoader()
        name = loader.get_name()

        assert name == "stdin"

    @pytest.mark.skip(reason="Incompatible with pytest stdin capture - covered by E2E tests")
    def test_validate_empty_stdin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test validation of empty stdin."""
        monkeypatch.setattr(sys.stdin, "buffer", io.BytesIO(b""))

        loader = StdinLoader()
        errors = loader.validate()

        assert len(errors) > 0
        assert "no input" in errors[0].lower()


class TestURLLoader:
    """Tests for URLLoader class."""

    def test_init(self) -> None:
        """Test URLLoader initialization."""
        url = "https://example.com/article.md"
        loader = URLLoader(url, timeout=10)

        assert loader.url == url
        assert loader.timeout == 10

    def test_get_name(self) -> None:
        """Test getting URL name."""
        url = "https://example.com/article.md"
        loader = URLLoader(url)
        name = loader.get_name()

        assert name == url

    @pytest.mark.skip(reason="Requires network access")
    def test_load_url(self) -> None:
        """Test loading from URL (requires network)."""
        url = "https://example.com/article.md"
        loader = URLLoader(url)

        # This would make a real HTTP request
        # content = loader.load()
        # assert len(content) > 0

    @pytest.mark.skip(reason="Requires network access")
    def test_validate_invalid_url(self) -> None:
        """Test validation of invalid URL (requires network)."""
        loader = URLLoader("https://nonexistent.example.com/")
        errors = loader.validate()

        assert len(errors) > 0
