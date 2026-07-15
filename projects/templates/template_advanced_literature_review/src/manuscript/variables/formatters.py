"""String formatters for manuscript template variables."""

from __future__ import annotations


def latex_number(n: int) -> str:
    """Process latex number."""
    s = str(n)
    if len(s) <= 3:
        return s
    parts: list[str] = []
    while len(s) > 3:
        parts.append(s[-3:])
        s = s[:-3]
    parts.append(s)
    return ",".join(reversed(parts))


def humanize_list(items: list[str]) -> str:
    """Process humanize list."""
    normalized = [str(i) for i in items]
    if not normalized:
        return ""
    if len(normalized) == 1:
        return normalized[0]
    if len(normalized) == 2:
        return f"{normalized[0]} and {normalized[1]}"
    return ", ".join(normalized[:-1]) + f", and {normalized[-1]}"


def humanize_key(key: str) -> str:
    """Process humanize key."""
    return key.replace("_", " ").title()


def percentage(fraction: float) -> str:
    """Format a fraction as a percentage string."""
    return f"{fraction * 100:.1f}"
