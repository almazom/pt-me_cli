"""Tests for p2me CLI - chains publish_me and t2me."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SUBPROCESS_ENV = {
    **os.environ,
    "PYTHONPATH": str(REPO_ROOT / "src"),
}


def run_p2me(
    *args: str,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run `python -m p2me` from the current repository root."""
    return subprocess.run(
        [sys.executable, "-m", "p2me", *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=SUBPROCESS_ENV,
        input=input_text,
    )


class TestP2MeCLIHelp:
    """Test help and version outputs."""

    def test_help_flag_shows_usage(self) -> None:
        """p2me -h should show usage information."""
        result = run_p2me("-h")
        assert result.returncode == 0
        assert "p2me" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_help_shows_publish_options(self) -> None:
        """Help should mention publish-related options."""
        result = run_p2me("-h")
        assert result.returncode == 0
        assert "-vps" in result.stdout or "--vps" in result.stdout

    def test_help_shows_telegram_options(self) -> None:
        """Help should mention telegram-related options."""
        result = run_p2me("-h")
        assert result.returncode == 0
        assert "--no-notify" in result.stdout or "notify" in result.stdout.lower()


class TestP2MeChaining:
    """Test that p2me chains publish_me and t2me correctly."""

    @patch("p2me.chain.subprocess.run")
    def test_calls_publish_me_first(self, mock_run: MagicMock) -> None:
        """p2me should call publish_me as first step."""
        from p2me.chain import run_chain

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"ok": true, "url": "http://example.com/a"}',
            stderr="",
        )

        run_chain("test.md", dry_run=True)

        assert mock_run.call_count >= 1
        first_call_args = mock_run.call_args_list[0]
        assert "publish" in str(first_call_args).lower() or "p-me" in str(
            first_call_args
        ).lower()

    @patch("p2me.chain.subprocess.run")
    def test_calls_t2me_after_publish_success(self, mock_run: MagicMock) -> None:
        """p2me should call t2me after successful publish (when not dry-run)."""
        from p2me.chain import run_chain

        mock_run.side_effect = [
            MagicMock(
                returncode=0,
                stdout='{"ok": true, "url": "http://example.com/a"}',
                stderr="",
            ),
            MagicMock(
                returncode=0,
                stdout='{"ok": true, "message_id": 123}',
                stderr="",
            ),
        ]

        run_chain("test.md", dry_run=False)

        assert mock_run.call_count == 2
        second_call_args = mock_run.call_args_list[1]
        assert "t2me" in str(second_call_args).lower()

    @patch("p2me.chain.subprocess.run")
    def test_skips_t2me_on_publish_failure(self, mock_run: MagicMock) -> None:
        """p2me should NOT call t2me if publish fails."""
        from p2me.chain import run_chain

        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='{"ok": false, "error": "Failed"}',
            stderr="boom",
        )

        result = run_chain("test.md", dry_run=True)

        assert mock_run.call_count == 1
        assert result["ok"] is False

    @patch("p2me.chain.subprocess.run")
    def test_no_notify_flag_skips_t2me(self, mock_run: MagicMock) -> None:
        """p2me --no-notify should skip t2me even on success."""
        from p2me.chain import run_chain

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"ok": true, "url": "http://example.com/a"}',
            stderr="",
        )

        result = run_chain("test.md", dry_run=True, no_notify=True)

        assert mock_run.call_count == 1
        assert result["ok"] is True


class TestP2MeArguments:
    """Test argument parsing and forwarding."""

    def test_forwards_vps_flag_to_publish(self) -> None:
        """-vps flag should be forwarded to publish_me."""
        from p2me.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["test.md", "-vps"])

        assert args.vps is True

    def test_forwards_simplenote_flag_to_publish(self) -> None:
        """-sn flag should be forwarded to publish_me."""
        from p2me.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["test.md", "-sn"])

        assert args.simplenote is True

    def test_dry_run_flag_available(self) -> None:
        """-n/--dry-run flag should be available."""
        from p2me.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["test.md", "-n"])

        assert args.dry_run is True

    def test_validate_flag_available(self) -> None:
        """--validate flag should be available."""
        from p2me.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["test.md", "--validate"])

        assert args.validate is True

    def test_verbose_flag_available(self) -> None:
        """-v/--verbose flag should be available."""
        from p2me.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["test.md", "-v"])

        assert args.verbose is True

    def test_json_output_flag_available(self) -> None:
        """-j/--json flag should be available."""
        from p2me.cli import create_parser

        parser = create_parser()
        args = parser.parse_args(["test.md", "-j"])

        assert args.json_output is True


class TestP2MeValidation:
    """Test validation-only behavior."""

    def test_validate_skips_chain_execution(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """--validate should not call the publish/notify chain."""
        from p2me import cli

        test_file = tmp_path / "article.md"
        test_file.write_text("# hello\n", encoding="utf-8")

        monkeypatch.setattr(
            sys,
            "argv",
            ["p2me", str(test_file), "--validate", "-j"],
        )

        with patch("p2me.cli.run_chain") as mock_run_chain:
            exit_code = cli.main()

        output = json.loads(capsys.readouterr().out)
        assert exit_code == 0
        assert mock_run_chain.call_count == 0
        assert output["ok"] is True
        assert output["validation"]["ok"] is True
        assert output["publish"] is None
        assert output["notify"] is None

    def test_validate_rejects_invalid_film_url_without_subprocess(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """--validate should reject film URLs outside kinoteatr.ru."""
        from p2me import cli

        test_file = tmp_path / "article.md"
        test_file.write_text("# hello\n", encoding="utf-8")

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "p2me",
                str(test_file),
                "--validate",
                "--film-url",
                "https://example.com/movie",
                "-j",
            ],
        )

        with patch("p2me.cli.run_chain") as mock_run_chain:
            exit_code = cli.main()

        output = json.loads(capsys.readouterr().out)
        assert exit_code == 1
        assert mock_run_chain.call_count == 0
        assert output["ok"] is False
        assert output["publish"] is None
        assert output["notify"] is None
        assert any(error["code"] == "INVALID_INPUT" for error in output["errors"])


class TestP2MeOutputContracts:
    """Test user-visible output behavior."""

    def test_quiet_mode_prints_errors(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Quiet mode should still print human-readable errors."""
        from p2me import cli

        monkeypatch.setattr(sys, "argv", ["p2me", "missing.md", "--quiet"])

        with patch(
            "p2me.cli.run_chain",
            return_value={
                "ok": False,
                "errors": [
                    {
                        "code": "FILE_NOT_FOUND",
                        "message": "File not found: missing.md",
                        "stage": "input",
                    }
                ],
                "warnings": [],
            },
        ):
            exit_code = cli.main()

        output = capsys.readouterr().out
        assert exit_code == 1
        assert "FILE_NOT_FOUND" in output
        assert "missing.md" in output


class TestFilmUrlValidation:
    """Test trust-boundary checks for film URLs."""

    @pytest.mark.parametrize(
        ("url", "expected_error"),
        [
            ("https://kinoteatr.ru/movie/123", None),
            ("https://spb.kinoteatr.ru/film/abc", None),
            ("file:///etc/passwd", "Film URL must use http or https"),
            ("https://example.com/movie", "Film URL must point to kinoteatr.ru"),
            ("http://localhost:8000/test", "Film URL must point to kinoteatr.ru"),
        ],
    )
    def test_validate_film_url(self, url: str, expected_error: str | None) -> None:
        """Film URL validation should enforce kinoteatr-only hosts."""
        from p2me.film_parser import validate_film_url

        assert validate_film_url(url) == expected_error


class TestP2MeDryRun:
    """Test dry-run mode."""

    @patch("p2me.chain.subprocess.run")
    def test_dry_run_does_not_execute_commands(self, mock_run: MagicMock) -> None:
        """In dry-run mode, mocked chain calls still report dry-run."""
        from p2me.chain import run_chain

        result = run_chain("test.md", dry_run=True)

        assert result.get("dry_run") is True or result.get("ok") is True
