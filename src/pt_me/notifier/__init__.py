"""Notifier module for pt-me.

Wraps t2me CLI tool for sending Telegram notifications.
"""

import json
import subprocess
from typing import Optional

from ..core.contracts import Notifier, SendResult


class T2MENotifier:
    """Notifier using t2me CLI tool."""

    def __init__(
        self,
        config_dir: str | None = None,
        dry_run: bool = False,
        verbose: bool = False,
        markdown: bool = True,
    ):
        """Initialize notifier.

        Args:
            config_dir: Config directory for t2me
            dry_run: Dry run mode
            verbose: Verbose output
            markdown: Enable Markdown parsing
        """
        self.config_dir = config_dir
        self.dry_run = dry_run
        self.verbose = verbose
        self.markdown = markdown

    def _build_command(self, message: str, file: bytes | None = None) -> list[str]:
        """Build t2me command.

        Args:
            message: Message text
            file: Optional file content to attach

        Returns:
            Command list for subprocess
        """
        # Global flags come before subcommand
        cmd = ["t2me"]

        if self.config_dir:
            cmd.extend(["--config-dir", self.config_dir])

        if self.verbose:
            cmd.append("--verbose")

        # Add subcommand
        cmd.append("send")

        if self.dry_run:
            cmd.append("--dry-run")

        if self.markdown:
            cmd.append("-m")

        # Add file if provided
        if file:
            # Write file to temp location
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
                f.write(file)
                temp_path = f.name

            cmd.extend(["--file", temp_path])
            cmd.extend(["--caption", message])
        else:
            # Add message
            cmd.append(message)

        return cmd

    def send(self, message: str, file: bytes | None = None) -> SendResult:
        """Send message via t2me.

        Args:
            message: Message text
            file: Optional file content to attach

        Returns:
            SendResult with success status
        """
        cmd = self._build_command(message, file)

        try:
            # Run t2me command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            output = result.stdout.strip()

            # Parse JSON output
            if output.startswith("{"):
                try:
                    data = json.loads(output)
                    if data.get("status") == "ok":
                        send_data = data.get("result", {})
                        return SendResult(
                            ok=True,
                            message_id=send_data.get("message_id", 0),
                            target=send_data.get("target", ""),
                            errors=[],
                        )
                    else:
                        return SendResult(
                            ok=False,
                            message_id=0,
                            target="",
                            errors=[data.get("error", "Unknown error")],
                        )
                except json.JSONDecodeError:
                    pass

            # Parse human-readable output
            if result.returncode == 0:
                # Extract message ID if available
                message_id = 0
                target = ""

                for line in output.split("\n"):
                    if "message_id" in line:
                        try:
                            message_id = int(line.split(":")[1].strip())
                        except (ValueError, IndexError):
                            pass
                    if "target" in line:
                        try:
                            target = line.split(":")[1].strip().strip('"')
                        except (ValueError, IndexError):
                            pass

                return SendResult(
                    ok=True,
                    message_id=message_id,
                    target=target,
                    errors=[],
                )
            else:
                return SendResult(
                    ok=False,
                    message_id=0,
                    target="",
                    errors=[result.stderr.strip() or "Unknown error"],
                )

        except subprocess.TimeoutExpired:
            return SendResult(
                ok=False,
                message_id=0,
                target="",
                errors=["Timeout after 60s"],
            )
        except FileNotFoundError:
            return SendResult(
                ok=False,
                message_id=0,
                target="",
                errors=["t2me command not found"],
            )
        except Exception as e:
            return SendResult(
                ok=False,
                message_id=0,
                target="",
                errors=[str(e)],
            )

    def health_check(self) -> bool:
        """Check if t2me is available and authorized."""
        try:
            result = subprocess.run(
                ["t2me", "status"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                if output.startswith("{"):
                    try:
                        data = json.loads(output)
                        return data.get("result", {}).get("valid", False)
                    except json.JSONDecodeError:
                        pass
                return "valid" in output.lower()

            return False

        except Exception:
            return False
