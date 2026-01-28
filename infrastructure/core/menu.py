"""Interactive menu utilities (pure helpers).

This module exists to keep menu parsing logic testable and reusable across
CLI entry points. It intentionally avoids any business logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class MenuOption:
    """Single menu option descriptor."""

    key: str
    label: str


def parse_choice_sequence(raw: str) -> list[str]:
    """Parse a user-entered menu choice sequence.

    Supported forms:
    - Concatenated digits: "345" -> ["3", "4", "5"]
    - Comma-separated digits: "3,4,5" -> ["3", "4", "5"]
    - Whitespace is ignored: " 3, 4 ,5 " -> ["3", "4", "5"]

    Args:
        raw: Raw user input.

    Returns:
        List of choice tokens (as strings).

    Raises:
        ValueError: If input cannot be parsed into a non-empty choice list.
    """

    cleaned = "".join(ch for ch in raw.strip() if not ch.isspace())
    if not cleaned:
        raise ValueError("Empty choice")

    if cleaned.isdigit() and len(cleaned) > 1:
        return list(cleaned)

    parts = [p for p in cleaned.split(",") if p]
    if not parts:
        raise ValueError("No valid choices found")

    if any(not p.isdigit() for p in parts):
        raise ValueError(f"Invalid choice token(s): {parts}")

    return parts


def format_menu(title: str, options: Sequence[MenuOption], current_project: str) -> str:
    """Return a plain-text menu representation.

    This is deliberately presentation-only (no ANSI / styling), so bash or
    richer UIs can style it as needed.
    """

    lines: list[str] = []
    lines.append(title)
    lines.append("")
    lines.append(f"Project: {current_project}")
    lines.append("")
    for opt in options:
        lines.append(f"  {opt.key}. {opt.label}")
    return "\n".join(lines)
