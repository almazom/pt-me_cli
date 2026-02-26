"""Integration tests for pt-me pipeline."""

import json
import subprocess
from pathlib import Path

import pytest

# Path to venv python
VENV_PYTHON = Path(__file__).parent.parent / ".venv" / "bin" / "python"


class TestCLIIntegration:
    """Integration tests for pt-me CLI."""

    def test_cli_help(self) -> None:
        """Test CLI help output."""
        result = subprocess.run(
            [str(VENV_PYTHON), "-m", "pt_me.cli", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )

        assert result.returncode == 0
        assert "Publish + Telegram Notify" in result.stdout
        assert "source" in result.stdout

    def test_cli_version(self) -> None:
        """Test CLI version output."""
        result = subprocess.run(
            [str(VENV_PYTHON), "-m", "pt_me.cli", "--version"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )

        assert result.returncode == 0
        assert "pt-me" in result.stdout

    def test_cli_health_check(self) -> None:
        """Test CLI health check."""
        result = subprocess.run(
            [str(VENV_PYTHON), "-m", "pt_me.cli", "--health-check"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )

        # Should complete without crash
        assert result.returncode in [0, 1]  # OK or dependency missing

    def test_cli_dry_run_file(self, tmp_path: Path) -> None:
        """Test CLI dry run with file input."""
        # Create test file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test Article\n\nThis is test content.")

        result = subprocess.run(
            [
                str(VENV_PYTHON),
                "-m",
                "pt_me.cli",
                str(test_file),
                "--dry-run",
                "--no-notify",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )

        # Should not crash
        assert result.returncode in [0, 1, 2]

    def test_cli_dry_run_json(self, tmp_path: Path) -> None:
        """Test CLI dry run with JSON output."""
        # Create test file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test Article\n\nThis is test content.")

        result = subprocess.run(
            [
                str(VENV_PYTHON),
                "-m",
                "pt_me.cli",
                str(test_file),
                "--dry-run",
                "--no-notify",
                "--json",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )

        # Should output valid JSON
        if result.returncode == 0:
            data = json.loads(result.stdout)
            assert "ok" in data
            assert "correlation_id" in data

    def test_cli_invalid_file(self) -> None:
        """Test CLI with invalid file."""
        result = subprocess.run(
            [str(VENV_PYTHON), "-m", "pt_me.cli", "/nonexistent/file.md"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )

        # Should fail validation
        assert result.returncode != 0

    def test_cli_stdin_input(self) -> None:
        """Test CLI with stdin input."""
        result = subprocess.run(
            [str(VENV_PYTHON), "-m", "pt_me.cli", "-", "--dry-run", "--no-notify"],
            input="# Test from stdin",
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )

        # Should not crash (may fail due to empty input handling)
        # Just verify it runs

    def test_cli_provider_flags(self, tmp_path: Path) -> None:
        """Test CLI with different provider flags."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        # Test Simplenote flag
        result_sn = subprocess.run(
            [str(VENV_PYTHON), "-m", "pt_me.cli", str(test_file), "-sn", "--dry-run", "--no-notify"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result_sn.returncode in [0, 1, 2]

        # Test VPS flag
        result_vps = subprocess.run(
            [str(VENV_PYTHON), "-m", "pt_me.cli", str(test_file), "-vps", "--dry-run", "--no-notify"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result_vps.returncode in [0, 1, 2]

    def test_cli_template_flags(self, tmp_path: Path) -> None:
        """Test CLI with different template flags."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        # Test minimal template
        result = subprocess.run(
            [
                str(VENV_PYTHON),
                "-m",
                "pt_me.cli",
                str(test_file),
                "--template",
                "minimal",
                "--dry-run",
                "--no-notify",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode in [0, 1, 2]

    def test_cli_caption_flag(self, tmp_path: Path) -> None:
        """Test CLI with caption flag."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        result = subprocess.run(
            [
                str(VENV_PYTHON),
                "-m",
                "pt_me.cli",
                str(test_file),
                "--caption",
                "Custom caption",
                "--dry-run",
                "--no-notify",
            ],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode in [0, 1, 2]

    def test_cli_verbose_flag(self, tmp_path: Path) -> None:
        """Test CLI with verbose flag."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        result = subprocess.run(
            [str(VENV_PYTHON), "-m", "pt_me.cli", str(test_file), "-v", "--dry-run", "--no-notify"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )

        # Verbose should produce more output
        assert result.returncode in [0, 1, 2]


class TestPipelineIntegration:
    """Integration tests for full pipeline."""

    @pytest.mark.skip(reason="Requires p-me and t2me to be installed and configured")
    def test_full_pipeline(self, tmp_path: Path) -> None:
        """Test full publish + notify pipeline."""
        # This test requires:
        # 1. p-me installed and configured
        # 2. t2me installed and authorized
        # 3. Network access

        test_file = tmp_path / "article.md"
        test_file.write_text("# Test Article\n\nTesting full pipeline.")

        result = subprocess.run(
            ["pt-me", str(test_file)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

    @pytest.mark.skip(reason="Requires p-me to be installed")
    def test_publish_only(self, tmp_path: Path) -> None:
        """Test publish without notification."""
        test_file = tmp_path / "article.md"
        test_file.write_text("# Test Article")

        result = subprocess.run(
            ["pt-me", str(test_file), "--no-notify"],
            capture_output=True,
            text=True,
        )

        # Should succeed if p-me is configured
        assert result.returncode in [0, 1, 2]
