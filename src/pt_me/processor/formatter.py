"""Message formatter for pt-me.

Formats Telegram messages from published content.
"""

from pathlib import Path

from ..core.contracts import MessageContext, MessageFormatter


class MessageFormatter:
    """Base message formatter."""

    def format(self, context: MessageContext) -> str:
        """Format message from context.

        Args:
            context: Message context with all required data

        Returns:
            Formatted message string
        """
        raise NotImplementedError


class TemplateFormatter(MessageFormatter):
    """Template-based message formatter."""

    def __init__(
        self,
        template_name: str = "standard",
        template_dir: str | None = None,
    ):
        """Initialize formatter.

        Args:
            template_name: Name of template to use
            template_dir: Directory containing templates
        """
        self.template_name = template_name
        self.template_dir = Path(template_dir) if template_dir else None
        self._templates: dict[str, str] = {}

    def _load_template(self, name: str) -> str:
        """Load template from file or use built-in.

        Args:
            name: Template name

        Returns:
            Template string
        """
        if name in self._templates:
            return self._templates[name]

        # Try to load from file
        if self.template_dir:
            template_path = self.template_dir / f"{name}.tpl"
            if template_path.exists():
                self._templates[name] = template_path.read_text()
                return self._templates[name]

        # Use built-in templates
        template = self._get_builtin_template(name)
        self._templates[name] = template
        return template

    def _get_builtin_template(self, name: str) -> str:
        """Get built-in template.

        Args:
            name: Template name

        Returns:
            Template string
        """
        # Only emoji from approved list: ○ ● ◐ ◑ ◒ ◓ ⬆︎ ↗︎ ➡︎ ↘︎ ⬇︎ ↙︎ ⬅︎ ↖︎ ① ② ③ ④ ⑤
        templates = {
            "standard": """{caption}

◐ Кратко:

{summary_points}

➡︎ {url}

#published #pt-me""",
            "minimal": """{caption}
➡︎ {url}""",
            "detailed": """{caption}

○ Источник: {source_name}
○ Тип: {source_type}
○ Провайдер: {provider}

◐ Кратко:

{summary_points}

➡︎ {url}

#published #pt-me""",
        }

        return templates.get(name, templates["standard"])

    def format(self, context: MessageContext) -> str:
        """Format message from context.

        Args:
            context: Message context

        Returns:
            Formatted message
        """
        template = self._load_template(self.template_name)

        # Build summary points with approved emoji only
        # Approved: ○ ● ◐ ◑ ◒ ◓ ⬆︎ ↗︎ ➡︎ ↘︎ ⬇︎ ↙︎ ⬅︎ ↖︎ ① ② ③ ④ ⑤ ❶ ❷ ❸ ❹ ❺ ⓵ ⓶ ⓷ ⓸ ⓹
        if context.summary_points:
            # Use circled numbers: ① ② ③ ④ ⑤ (from approved list)
            circled_numbers = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]
            points_text = "\n".join(
                f"{circled_numbers[i] if i < len(circled_numbers) else f'{i + 1}.'} {point}"
                for i, point in enumerate(context.summary_points)
            )
        else:
            points_text = "○ См. ссылку"

        # Build caption - strip any leading emoji to avoid double emoji
        caption = context.caption or context.summary_title or "Опубликовано"
        caption = self._strip_leading_emoji(caption)

        # Format message
        message = template.format(
            caption=caption,
            summary_points=points_text,
            url=context.published_url,
            source_name=context.source_name,
            source_type=context.source_type,
            provider=context.provider,
        )

        # Clean up extra whitespace
        message = "\n".join(
            line.rstrip() for line in message.split("\n")
        )

        return message

    def _strip_leading_emoji(self, text: str) -> str:
        """Strip leading emoji from text to avoid double emoji.

        Args:
            text: Input text

        Returns:
            Text with leading emoji removed
        """
        import re
        # Strip all leading emoji characters (any Unicode emoji)
        # This prevents double emoji like "🧪 ✅ Title"
        emoji_pattern = re.compile(
            r'^[\U0001F000-\U0001FFFF\u2600-\u26FF\u2700-\u27BF\uFE00-\uFE0F]+',
            flags=re.UNICODE
        )
        # Keep stripping emoji until no more at start
        while True:
            match = emoji_pattern.match(text)
            if match:
                text = text[match.end():].lstrip()
            else:
                break
        return text if text else "Опубликовано"
