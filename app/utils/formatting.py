from datetime import date


def current_year() -> int:
    """Jinja global for footer copyright years."""
    return date.today().year


def format_duration(seconds) -> str:
    """Render a duration in seconds as a compact human string.

    3725 -> "1h 02m", 750 -> "12m 30s", 45 -> "45s".
    Accepts int/float/Decimal (DynamoDB numbers); anything unparseable -> "".
    """
    try:
        total = int(seconds)
    except (TypeError, ValueError):
        return ""
    if total < 0:
        total = 0
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"
