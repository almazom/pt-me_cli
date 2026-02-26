"""Publisher wrapper for pt-me.

Wraps p-me CLI tool for publishing content.
"""

import json
import subprocess

from ..core.contracts import PublishResult


class PMPublisher:
    """Publisher using p-me CLI tool."""

    def __init__(
        self,
        provider: str | None = None,
        mode: str = "standard",
        timeout: int = 30,
        max_retries: int = 3,
        dry_run: bool = False,
        verbose: bool = False,
    ):
        """Initialize publisher.

        Args:
            provider: Provider to use (simplenote, vps, or None for auto)
            mode: Preprocessing mode
            timeout: Request timeout
            max_retries: Maximum retry attempts
            dry_run: Dry run mode
            verbose: Verbose output
        """
        self.provider = provider
        self.mode = mode
        self.timeout = timeout
        self.max_retries = max_retries
        self.dry_run = dry_run
        self.verbose = verbose

    def _build_command(self, content: bytes, source_name: str) -> list[str]:
        """Build p-me command.

        Args:
            content: Content to publish
            source_name: Source file name or '-' for stdin

        Returns:
            Command list for subprocess
        """
        cmd = ["p-me"]

        # Add provider flags
        if self.provider == "simplenote":
            cmd.append("-sn")
        elif self.provider == "vps":
            cmd.append("-vps")
        # else: auto mode (no flags)

        # Add options
        cmd.extend(["-m", self.mode])
        cmd.extend(["-t", str(self.timeout)])
        cmd.extend(["-r", str(self.max_retries)])

        if self.dry_run:
            cmd.append("-n")

        if self.verbose:
            cmd.append("-v")

        # For stdin, pass '-' as source
        # p-me will read from its stdin
        cmd.append(source_name if source_name != "stdin" else "-")

        return cmd

    def publish(
        self, content: bytes, source_type: str, source_name: str
    ) -> PublishResult:
        """Publish content using p-me.

        Args:
            content: Content bytes to publish
            source_type: Type of content (text, image, etc.)
            source_name: Source identifier (file path, URL, or '-')

        Returns:
            PublishResult with success status and metadata
        """
        cmd = self._build_command(content, source_name)

        try:
            # For stdin source, pass content via stdin to p-me
            # subprocess with text=True expects string input
            input_data = content.decode("utf-8") if source_name == "stdin" else None

            # Run p-me command
            # For stdin, we need to use shell to pipe content
            if input_data:
                # Use shell to pipe content
                import shlex
                cmd_str = " ".join(shlex.quote(arg) for arg in cmd)
                result = subprocess.run(
                    cmd_str,
                    capture_output=True,
                    text=True,
                    input=input_data,
                    timeout=self.timeout * 2,
                    shell=True,
                )
            else:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout * 2,
                )

            # Parse output
            output = result.stdout.strip()
            errors = []

            # Check for JSON output (if -j was added internally)
            if output.startswith("{"):
                try:
                    data = json.loads(output)
                    return PublishResult(
                        ok=data.get("ok", False),
                        url=data.get("url", ""),
                        provider=data.get("provider", ""),
                        metadata=data.get("metadata", {}),
                        errors=data.get("errors", []),
                        warnings=data.get("warnings", []),
                        attempts=data.get("diagnostics", {}).get("total_attempts", 0),
                    )
                except json.JSONDecodeError:
                    pass

            # Parse human-readable output
            if result.returncode == 0:
                # Extract URL from output
                url = ""
                provider = self.provider or "auto"

                for line in output.split("\n"):
                    if "URL:" in line:
                        url = line.split("URL:")[1].strip()
                    if "simplenote" in line.lower():
                        provider = "simplenote"
                    if "vps" in line.lower():
                        provider = "vps"

                return PublishResult(
                    ok=True,
                    url=url,
                    provider=provider,
                    metadata={},
                    errors=[],
                    warnings=["dry-run: no content was published"] if self.dry_run else [],
                    attempts=1,
                )
            else:
                errors.append(result.stderr.strip() or "Unknown error")

            return PublishResult(
                ok=False,
                url="",
                provider="",
                metadata={},
                errors=errors,
                warnings=[],
                attempts=0,
            )

        except subprocess.TimeoutExpired:
            return PublishResult(
                ok=False,
                url="",
                provider="",
                metadata={},
                errors=[f"Timeout after {self.timeout * 2}s"],
                warnings=[],
                attempts=0,
            )
        except FileNotFoundError:
            return PublishResult(
                ok=False,
                url="",
                provider="",
                metadata={},
                errors=["p-me command not found"],
                warnings=[],
                attempts=0,
            )
        except Exception as e:
            return PublishResult(
                ok=False,
                url="",
                provider="",
                metadata={},
                errors=[str(e)],
                warnings=[],
                attempts=0,
            )

    def health_check(self) -> bool:
        """Check if p-me is available."""
        try:
            result = subprocess.run(
                ["p-me", "--health-check"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False
