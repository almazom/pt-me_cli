# Minimal Emoji Style for pt-me

## Rules

1. **Never 2 emoji in a row** — Leading emoji in captions are stripped
2. **Only approved emoji** — Strict whitelist from the palette below
3. **Vertical padding** — Empty line between header and bullet list

## Emoji Palette

### Status Indicators
- `○` — Neutral/bullet point
- `●` — Filled/active
- `◐` — Section header (Кратко)
- `◑` — Alternative section
- `◒` — Reserved
- `◓` — Reserved

### Directional Arrows
- `⬆︎` — Up/upload
- `↗︎` — Up-right
- `➡︎` — Right/link/next
- `↘︎` — Down-right
- `⬇︎` — Down/download
- `↙︎` — Down-left
- `⬅︎` — Left/back
- `↖︎` — Up-left

### Numbered Lists
- `① ② ③ ④ ⑤` — Circled numbers (1-10)
- `❶ ❷ ❸ ❹ ❺` — Filled circled numbers
- `⓵ ⓶ ⓷ ⓸ ⓹` — Double-circled numbers

## Template Examples

### Standard Template
```
{caption}

◐ Кратко:

{summary_points}

➡︎ {url}

#published #pt-me
```

### Minimal Template
```
{caption}
➡︎ {url}
```

### Detailed Template
```
{caption}

○ Источник: {source_name}
○ Тип: {source_type}
○ Провайдер: {provider}

◐ Кратко:

{summary_points}

➡︎ {url}

#published #pt-me
```

## Example Output

**Input caption:** `🧪 ✅ E2E Real Test`  
**Output caption:** `E2E Real Test` (emoji stripped)

**Input:**
```markdown
# My Article

Key points:
- First important thing
- Second important thing
- Third important thing
```

**Telegram Message:**
```
My Article

◐ Кратко:

① First important thing
② Second important thing
③ Third important thing

➡︎ https://simp.ly/p/XYZ

#published #pt-me
```

## Rationale

1. **Clean** — No double emoji sequences
2. **Professional** — Suitable for technical/content publishing
3. **Readable** — Vertical padding improves scanability
4. **Universal** — Standard Unicode, no platform-specific emoji
5. **Consistent** — Limited palette ensures predictable output

## Implementation

Located in: `src/pt_me/processor/formatter.py`

```python
# Approved emoji only
circled_numbers = ["①", "②", "③", "④", "⑤", ...]

# Template symbols (from approved list)
"◐"  # Section header
"○"  # Bullet point
"➡︎"  # Link arrow

# Auto-strip leading emoji from captions
caption = self._strip_leading_emoji(caption)
```
