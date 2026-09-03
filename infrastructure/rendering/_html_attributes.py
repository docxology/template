"""Exact HTML-attribute matching and source-preserving removal helpers."""

from __future__ import annotations

import re


def html_attribute_assignment_pattern(name: str) -> re.Pattern[str]:
    """Return an exact HTML attribute assignment pattern for ``name``.

    HTML attributes in renderer output are separated by whitespace. A regex
    word boundary is insufficient because ``-`` is not a word character, so
    ``\balt`` also matches ``data-fig-alt`` and ``\bsrc`` matches ``data-src``.
    """

    return re.compile(
        rf"(?<!\S){re.escape(name)}\s*=\s*(?:\"(?P<double>[^\"]*)\"|'(?P<single>[^']*)'|(?P<bare>[^\s>]+))",
        flags=re.IGNORECASE | re.DOTALL,
    )


def remove_html_attribute_assignment(attributes: str, name: str) -> str:
    """Remove exact ``name`` assignments without blank indentation residue.

    Pandoc may format a long tag with one attribute per line. When an
    assignment owns its complete physical line, this removes the line and its
    newline. Otherwise only the assignment is removed, preserving unrelated
    attributes and their authored values.
    """

    pattern = html_attribute_assignment_pattern(name)
    while (match := pattern.search(attributes)) is not None:
        line_start = attributes.rfind("\n", 0, match.start()) + 1
        newline = attributes.find("\n", match.end())
        line_end = len(attributes) if newline < 0 else newline
        prefix = attributes[line_start : match.start()]
        suffix = attributes[match.end() : line_end]
        if not prefix.strip() and not suffix.strip():
            remove_end = line_end if newline < 0 else line_end + 1
            attributes = attributes[:line_start] + attributes[remove_end:]
        else:
            attributes = attributes[: match.start()] + attributes[match.end() :]
    return attributes


def remove_unquoted_whitespace_only_lines(fragment: str) -> str:
    """Remove blank lines and trailing indentation outside quoted values."""

    quote: str | None = None
    retained: list[str] = []
    for line in fragment.splitlines(keepends=True):
        if quote is None and not line.strip():
            continue
        for character in line:
            if quote is None and character in {'"', "'"}:
                quote = character
            elif character == quote:
                quote = None
        if quote is None:
            newline = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
            body = line[: -len(newline)] if newline else line
            line = body.rstrip(" \t") + newline
        retained.append(line)
    return "".join(retained)


__all__ = [
    "html_attribute_assignment_pattern",
    "remove_html_attribute_assignment",
    "remove_unquoted_whitespace_only_lines",
]
