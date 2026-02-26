"""CLI interface for pt-me."""

import argparse
import json
import sys

from . import __version__
from .core.contracts import MessageContext, PipelineResult
from .core.observability import StructuredLogger, generate_correlation_id
from .input.resolver import InputResolver
from .input.validator import InputValidator
from .notifier import T2MENotifier
from .processor.formatter import TemplateFormatter
from .processor.publisher import PMPublisher
from .processor.summarizer import SimpleSummarizer


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for pt-me CLI."""
    parser = argparse.ArgumentParser(
        prog="pt-me",
        description="Publish + Telegram Notify — комбинированный инструмент",
        epilog="""
Примеры:
  pt-me article.md              # Опубликовать + уведомить
  pt-me article.md -sn          # Simplenote
  pt-me article.md -vps         # VPS
  pt-me article.md --no-notify  # Без уведомления
  cat file.md | pt-me -         # Из stdin
  pt-me article.md -j           # JSON вывод
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Positional
    parser.add_argument(
        "source",
        nargs="?",
        default="-",
        help="Source file path, URL, or '-' for stdin (default: '-')",
    )

    # Provider options (from p-me)
    provider_group = parser.add_argument_group("Provider options")
    provider_group.add_argument(
        "-sn",
        "--simplenote",
        action="store_true",
        help="Publish to Simplenote",
    )
    provider_group.add_argument(
        "-vps",
        "--vps",
        action="store_true",
        help="Publish to VPS",
    )
    provider_group.add_argument(
        "-m",
        "--mode",
        choices=["none", "minimal", "standard", "aggressive"],
        default="standard",
        help="Preprocessing mode (default: standard)",
    )

    # Telegram options (from t2me)
    telegram_group = parser.add_argument_group("Telegram options")
    telegram_group.add_argument(
        "--no-notify",
        action="store_true",
        help="Skip Telegram notification",
    )
    telegram_group.add_argument(
        "--caption",
        type=str,
        default=None,
        help="Custom caption for Telegram message",
    )
    telegram_group.add_argument(
        "--summary",
        action="store_true",
        help="Enable AI summarization",
    )
    telegram_group.add_argument(
        "--template",
        choices=["standard", "minimal", "detailed"],
        default="standard",
        help="Message template (default: standard)",
    )

    # Common options
    common_group = parser.add_argument_group("Common options")
    common_group.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)",
    )
    common_group.add_argument(
        "-r",
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retry attempts (default: 3)",
    )
    common_group.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Dry run (no actual publish/notify)",
    )
    common_group.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    common_group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    common_group.add_argument(
        "--quiet",
        action="store_true",
        help="Quiet mode (errors only)",
    )

    # Info options
    info_group = parser.add_argument_group("Info options")
    info_group.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    info_group.add_argument(
        "--health-check",
        action="store_true",
        help="Check system health and exit",
    )

    return parser


def run_health_check(logger: StructuredLogger) -> int:
    """Run health check on dependencies.

    Args:
        logger: Logger instance

    Returns:
        Exit code (0=ok, 1=error)
    """
    logger.info("Running health check...")

    publisher = PMPublisher()
    notifier = T2MENotifier()

    pub_ok = publisher.health_check()
    not_ok = notifier.health_check()

    logger.info(f"  p-me: {'✓' if pub_ok else '✗'}")
    logger.info(f"  t2me: {'✓' if not_ok else '✗'}")

    if pub_ok and not_ok:
        logger.info("Health check: OK")
        return 0
    else:
        logger.error("Health check: FAILED")
        return 1


def run_pipeline(
    source: str,
    provider: str | None = None,
    mode: str = "standard",
    timeout: int = 30,
    max_retries: int = 3,
    no_notify: bool = False,
    caption: str | None = None,
    enable_summary: bool = False,
    template_name: str = "standard",
    dry_run: bool = False,
    json_output: bool = False,
    verbose: bool = False,
    quiet: bool = False,
) -> int:
    """Run the pt-me pipeline.

    Args:
        source: Input source (file, URL, or '-')
        provider: Provider to use (None for auto)
        mode: Preprocessing mode
        timeout: Request timeout
        max_retries: Maximum retries
        no_notify: Skip notification
        caption: Custom caption
        enable_summary: Enable summarization
        template_name: Template name
        dry_run: Dry run mode
        json_output: JSON output mode
        verbose: Verbose mode
        quiet: Quiet mode

    Returns:
        Exit code (0=success, 1=validation, 2=network, 3=unknown)
    """
    # Initialize
    correlation_id = generate_correlation_id()
    logger = StructuredLogger(
        "pt-me",
        correlation_id=correlation_id,
        verbose=verbose and not quiet,
        json_output=json_output,
    )

    try:
        # Resolve input
        logger.log_stage("input", "start", {"source": source})
        resolver = InputResolver(source)
        resolved = resolver.resolve()

        if resolved.error:
            logger.log_stage("input", "error", {"error": resolved.error})
            if json_output:
                print(json.dumps({"ok": False, "error": resolved.error}))
            return 1

        # Create loader
        loader = resolver.create_loader()
        input_type = resolver.get_input_type()

        # Validate input
        validator = InputValidator(loader, resolved.source_type)
        is_valid, errors = validator.validate()

        if not is_valid:
            logger.log_stage("input", "error", {"errors": errors})
            if json_output:
                print(json.dumps({"ok": False, "errors": errors}))
            return 1

        # Load content
        content = loader.load()
        input_type["size_bytes"] = len(content)

        logger.log_stage(
            "input",
            "complete",
            {
                "type": input_type["type"],
                "size": f"{len(content)} bytes",
                "source": loader.get_name(),
            },
        )

        # Initialize result
        result = PipelineResult(
            ok=True,
            correlation_id=correlation_id,
            input_type=input_type,
        )

        # Publish
        logger.log_stage("publish", "start", {"provider": provider or "auto"})
        publisher = PMPublisher(
            provider=provider,
            mode=mode,
            timeout=timeout,
            max_retries=max_retries,
            dry_run=dry_run,
            verbose=verbose,
        )

        # For stdin, we need to pass content differently
        source_name = loader.get_name()
        publish_result = publisher.publish(content, input_type["type"], source_name)
        result.publish = publish_result

        if not publish_result.get("ok", False):
            logger.log_stage(
                "publish", "error", {"errors": publish_result.get("errors", [])}
            )
            result.ok = False
            result.errors.extend(publish_result.get("errors", []))
            result.warnings.extend(publish_result.get("warnings", []))
        else:
            logger.log_stage(
                "publish",
                "complete",
                {
                    "url": publish_result.get("url", ""),
                    "provider": publish_result.get("provider", ""),
                },
            )

        # Notify (if enabled and publish succeeded)
        if not no_notify and publish_result.get("ok", False):
            logger.log_stage("notify", "start")

            # Generate summary if enabled
            summary_points = None
            summary_title = None

            if enable_summary and input_type["type"] == "text":
                summarizer = SimpleSummarizer()
                text_content = content.decode("utf-8", errors="ignore")
                summary_result = summarizer.summarize(text_content)
                if summary_result.get("ok"):
                    summary_points = summary_result.get("points", [])
                    summary_title = summary_result.get("title", "")

            # Format message
            formatter = TemplateFormatter(template_name=template_name)
            context = MessageContext(
                published_url=publish_result.get("url", ""),
                provider=publish_result.get("provider", ""),
                source_name=loader.get_name(),
                source_type=input_type["type"],
                caption=caption,
                summary_points=summary_points,
                summary_title=summary_title,
            )
            message = formatter.format(context)

            # Send notification
            notifier = T2MENotifier(
                dry_run=dry_run,
                verbose=verbose,
                markdown=True,
            )
            send_result = notifier.send(message)
            result.notify = send_result

            if not send_result.get("ok", False):
                logger.log_stage(
                    "notify", "error", {"errors": send_result.get("errors", [])}
                )
                result.errors.extend(send_result.get("errors", []))
                # Don't fail entire pipeline if notification fails (graceful degradation)
                result.warnings.append("Notification failed but publish succeeded")
            else:
                logger.log_stage(
                    "notify",
                    "complete",
                    {
                        "message_id": send_result.get("message_id", 0),
                        "target": send_result.get("target", ""),
                    },
                )
        elif no_notify:
            logger.log_stage("notify", "skip", {"reason": "--no-notify"})
        elif not publish_result.get("ok", False):
            logger.log_stage("notify", "skip", {"reason": "publish failed"})

        # Output result
        if json_output:
            print(json.dumps(result.to_dict(), indent=2))
        elif result.ok:
            if publish_result.get("ok"):
                logger.info(f"✓ Published: {publish_result.get('url', '')}")
            if result.notify and result.notify.get("ok"):
                logger.info(f"✓ Notified: message_id={result.notify.get('message_id')}")
        else:
            for error in result.errors:
                logger.error(f"✗ {error}")

        return 0 if result.ok else (2 if result.errors else 3)

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        if json_output:
            print(json.dumps({"ok": False, "error": str(e)}))
        return 3


def main() -> int:
    """Main entry point for pt-me CLI.

    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args()

    # Determine provider
    provider = None
    if args.simplenote and args.vps:
        provider = "both"  # Will use auto
    elif args.simplenote:
        provider = "simplenote"
    elif args.vps:
        provider = "vps"

    # Health check
    if args.health_check:
        logger = StructuredLogger("pt-me", verbose=not args.quiet)
        return run_health_check(logger)

    # Run pipeline
    return run_pipeline(
        source=args.source,
        provider=provider,
        mode=args.mode,
        timeout=args.timeout,
        max_retries=args.max_retries,
        no_notify=args.no_notify,
        caption=args.caption,
        enable_summary=args.summary,
        template_name=args.template,
        dry_run=args.dry_run,
        json_output=args.json,
        verbose=args.verbose,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    sys.exit(main())
