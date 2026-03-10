"""Film page parser for kinoteatr.ru - extracts showing dates."""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from datetime import date, datetime
from typing import Any
from urllib.parse import urlsplit


def validate_film_url(url: str | None) -> str | None:
    """Validate that the film URL stays within the supported trust boundary.

    Args:
        url: Candidate film page URL

    Returns:
        Error message if invalid, otherwise None
    """
    if not url:
        return None

    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        return "Film URL must use http or https"

    if parsed.username or parsed.password:
        return "Film URL must not include credentials"

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return "Film URL must include a hostname"

    if hostname == "kinoteatr.ru" or hostname.endswith(".kinoteatr.ru"):
        return None

    return "Film URL must point to kinoteatr.ru"


def fetch_page(url: str, timeout: int = 10) -> str | None:
    """Fetch HTML page content.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        HTML content or None on error
    """
    if validate_film_url(url):
        return None

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="ignore")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return None


def extract_dates(html: str) -> list[str]:
    """Extract available dates from kinoteatr.ru page.

    Args:
        html: HTML content

    Returns:
        List of date strings in YYYY-MM-DD format
    """
    dates = []

    # Method 1: data-dates attribute
    # <input data-dates="2026-02-28" ...>
    pattern = r'data-dates="([^"]+)"'
    matches = re.findall(pattern, html)
    for match in matches:
        if match and match not in dates:
            dates.append(match)

    # Method 2: date class in schedule
    # <a href="..." class="date"> 28 февраля </a>
    # Also look for multiple dates
    if not dates:
        # Try to find all date mentions
        month_map = {
            "января": "01", "февраля": "02", "марта": "03", "апреля": "04",
            "мая": "05", "июня": "06", "июля": "07", "августа": "08",
            "сентября": "09", "октября": "10", "ноября": "11", "декабря": "12",
        }
        date_pattern = r'class="date"[^>]*>\s*(\d{1,2})\s+([а-яё]+)\s*</a>'
        for match in re.finditer(date_pattern, html, re.IGNORECASE):
            day = match.group(1).zfill(2)
            month_ru = match.group(2).lower()
            month = month_map.get(month_ru, "01")
            year = str(date.today().year)
            date_str = f"{year}-{month}-{day}"
            if date_str not in dates:
                dates.append(date_str)

    return dates


def parse_film_page(url: str, timeout: int = 10) -> dict[str, Any]:
    """Parse kinoteatr.ru film page for showing dates.

    Args:
        url: Full URL to film page
        timeout: Request timeout

    Returns:
        Dict with:
            - ok: bool
            - url: str
            - dates: list of available dates (YYYY-MM-DD)
            - is_showing_today: bool
            - next_showing: str | None (next available date)
            - film_title: str | None
            - error: str | None
    """
    result: dict[str, Any] = {
        "ok": True,
        "url": url,
        "dates": [],
        "is_showing_today": False,
        "next_showing": None,
        "film_title": None,
        "days_until": None,
        "error": None,
    }

    # Fetch page
    html = fetch_page(url, timeout)
    if not html:
        result["ok"] = False
        result["error"] = "Failed to fetch page"
        return result

    # Extract title
    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    if title_match:
        result["film_title"] = title_match.group(1).strip()

    # Extract dates
    dates = extract_dates(html)
    result["dates"] = dates

    if not dates:
        result["ok"] = False
        result["error"] = "No showing dates found"
        return result

    # Check if showing today
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    result["is_showing_today"] = today_str in dates

    # Find next showing date
    future_dates = [d for d in dates if d >= today_str]
    if future_dates:
        result["next_showing"] = future_dates[0]

        # Calculate days until
        try:
            next_date = datetime.strptime(future_dates[0], "%Y-%m-%d").date()
            result["days_until"] = (next_date - today).days
        except ValueError:
            pass

    return result


def format_film_status(film_info: dict[str, Any]) -> str:
    """Format film showing status for message.

    Args:
        film_info: Result from parse_film_page

    Returns:
        Human-readable status string
    """
    if not film_info.get("ok"):
        return f"⚠️ Could not verify film dates: {film_info.get('error', 'unknown')}"

    if film_info.get("is_showing_today"):
        return "🎬 Showing TODAY"
    elif film_info.get("days_until") is not None:
        days = film_info["days_until"]
        if days == 1:
            return f"🎬 Showing TOMORROW ({film_info['next_showing']})"
        elif days > 1:
            return f"🎬 Showing in {days} days ({film_info['next_showing']})"
        else:
            return f"🎬 Showing date: {film_info.get('next_showing', 'unknown')}"
    else:
        return f"🎬 Available dates: {', '.join(film_info.get('dates', []))}"


def check_film_date(url: str | None, timeout: int = 10) -> dict[str, Any]:
    """Check film date and return structured result.

    This is the main entry point for film date verification.

    Args:
        url: Film page URL (kinoteatr.ru)
        timeout: Request timeout

    Returns:
        Structured result with film info and status
    """
    if not url:
        return {
            "ok": False,
            "error": "No URL provided",
            "is_showing_today": None,
        }

    validation_error = validate_film_url(url)
    if validation_error:
        return {
            "ok": False,
            "url": url,
            "error": validation_error,
            "is_showing_today": None,
        }

    # Parse the page
    film_info = parse_film_page(url, timeout)

    return {
        "ok": film_info.get("ok", False),
        "url": url,
        "film_title": film_info.get("film_title"),
        "dates": film_info.get("dates", []),
        "is_showing_today": film_info.get("is_showing_today", False),
        "next_showing": film_info.get("next_showing"),
        "days_until": film_info.get("days_until"),
        "status_text": format_film_status(film_info),
        "error": film_info.get("error"),
    }
