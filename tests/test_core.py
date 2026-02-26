"""Tests for core module."""

import json

import pytest

from pt_me.core.contracts import MessageContext, PipelineResult
from pt_me.core.observability import (
    StructuredLogger,
    generate_correlation_id,
    get_env_config,
)


class TestCorrelationID:
    """Tests for correlation ID generation."""

    def test_generate_correlation_id(self) -> None:
        """Test correlation ID generation."""
        corr_id = generate_correlation_id()

        assert isinstance(corr_id, str)
        assert len(corr_id) > 0
        assert corr_id.startswith("pt-")

    def test_correlation_id_uniqueness(self) -> None:
        """Test that correlation IDs are unique."""
        ids = [generate_correlation_id() for _ in range(100)]

        # All IDs should be unique
        assert len(ids) == len(set(ids))


class TestStructuredLogger:
    """Tests for StructuredLogger class."""

    def test_init(self) -> None:
        """Test logger initialization."""
        logger = StructuredLogger("test")

        assert logger.correlation_id.startswith("pt-")
        assert logger.verbose is False
        assert logger.json_output is False

    def test_init_with_options(self) -> None:
        """Test logger initialization with options."""
        logger = StructuredLogger(
            "test",
            correlation_id="pt-custom",
            verbose=True,
            json_output=True,
        )

        assert logger.correlation_id == "pt-custom"
        assert logger.verbose is True
        assert logger.json_output is True

    def test_log_stage_human_readable(self, capsys: pytest.CaptureFixture) -> None:
        """Test logging stage in human-readable mode."""
        logger = StructuredLogger("test", verbose=True)

        logger.log_stage("input", "start", {"source": "test.md"})

        captured = capsys.readouterr()
        output = captured.err  # Verbose logs to stderr

        assert "input" in output
        assert "start" in output

    def test_log_stage_complete(self, capsys: pytest.CaptureFixture) -> None:
        """Test logging complete stage."""
        logger = StructuredLogger("test", verbose=True)

        logger.log_stage("publish", "complete", {"url": "https://example.com"})

        captured = capsys.readouterr()
        output = captured.err

        assert "✓" in output or "complete" in output

    def test_log_stage_error(self, capsys: pytest.CaptureFixture) -> None:
        """Test logging error stage."""
        logger = StructuredLogger("test", verbose=True)

        logger.log_stage("notify", "error", {"error": "Failed"})

        captured = capsys.readouterr()
        output = captured.err

        assert "✗" in output or "error" in output

    def test_log_stage_skip(self, capsys: pytest.CaptureFixture) -> None:
        """Test logging skip stage."""
        logger = StructuredLogger("test", verbose=True)

        logger.log_stage("notify", "skip", {"reason": "disabled"})

        captured = capsys.readouterr()
        output = captured.err

        assert "⊘" in output or "skip" in output

    def test_log_stage_json(self, capsys: pytest.CaptureFixture) -> None:
        """Test logging stage in JSON mode."""
        logger = StructuredLogger("test", json_output=True)

        logger.log_stage("input", "start", {"source": "test.md"})

        captured = capsys.readouterr()
        # JSON logs go to stderr to keep stdout clean for final output
        output = captured.err + captured.out

        # JSON logs should contain structured data
        assert "JSON:" in output or "input" in output


class TestPipelineResult:
    """Tests for PipelineResult class."""

    def test_to_dict(self) -> None:
        """Test converting result to dictionary."""
        from pt_me.core.contracts import InputType

        result = PipelineResult(
            ok=True,
            correlation_id="pt-test123",
            input_type=InputType(type="text", mime_type="text/markdown", size_bytes=100),
        )

        result_dict = result.to_dict()

        assert result_dict["ok"] is True
        assert result_dict["correlation_id"] == "pt-test123"
        assert result_dict["pipeline"] == "pt-me"
        assert "stages" in result_dict

    def test_to_dict_with_publish(self) -> None:
        """Test converting result with publish data."""
        from pt_me.core.contracts import InputType, PublishResult

        result = PipelineResult(
            ok=True,
            correlation_id="pt-test123",
            input_type=InputType(type="text", mime_type="text/markdown", size_bytes=100),
            publish=PublishResult(
                ok=True,
                url="https://example.com",
                provider="simplenote",
                metadata={},
                errors=[],
                warnings=[],
                attempts=1,
            ),
        )

        result_dict = result.to_dict()

        assert result_dict["stages"]["publish"]["ok"] is True
        assert result_dict["stages"]["publish"]["url"] == "https://example.com"

    def test_to_dict_with_errors(self) -> None:
        """Test converting result with errors."""
        from pt_me.core.contracts import InputType

        result = PipelineResult(
            ok=False,
            correlation_id="pt-test123",
            input_type=InputType(type="text", mime_type="text/markdown", size_bytes=100),
            errors=["Error 1", "Error 2"],
        )

        result_dict = result.to_dict()

        assert result_dict["ok"] is False
        assert len(result_dict["errors"]) == 2

    def test_to_dict_json_serializable(self) -> None:
        """Test that result is JSON serializable."""
        from pt_me.core.contracts import InputType

        result = PipelineResult(
            ok=True,
            correlation_id="pt-test123",
            input_type=InputType(type="text", mime_type="text/markdown", size_bytes=100),
            errors=[],
            warnings=[],
        )

        # Should not raise
        json_str = json.dumps(result.to_dict())
        assert isinstance(json_str, str)

        # Should be valid JSON
        data = json.loads(json_str)
        assert data["ok"] is True


class TestMessageContext:
    """Tests for MessageContext class."""

    def test_create_context(self) -> None:
        """Test creating message context."""
        context = MessageContext(
            published_url="https://example.com",
            provider="simplenote",
            source_name="test.md",
            source_type="text",
        )

        assert context.published_url == "https://example.com"
        assert context.provider == "simplenote"

    def test_create_context_with_optional(self) -> None:
        """Test creating context with optional fields."""
        context = MessageContext(
            published_url="https://example.com",
            provider="simplenote",
            source_name="test.md",
            source_type="text",
            caption="Custom caption",
            summary_points=["Point 1", "Point 2"],
        )

        assert context.caption == "Custom caption"
        assert len(context.summary_points) == 2


class TestEnvConfig:
    """Tests for environment config."""

    def test_get_env_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting config from environment."""
        monkeypatch.setenv("PT_ME_TEST", "value1")
        monkeypatch.setenv("PUBLISH_ME_TEST", "value2")
        monkeypatch.setenv("OTHER_VAR", "value3")  # Should be excluded

        config = get_env_config()

        assert "PT_ME_TEST" in config
        assert "PUBLISH_ME_TEST" in config
        assert "OTHER_VAR" not in config
