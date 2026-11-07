"""Literal and comment boundaries in Pandoc-generated slide TeX."""

from __future__ import annotations

import re


_VERBATIM_ENVIRONMENT_RE = re.compile(
    r"\\begin\{(?P<environment>verbatim\*?|Verbatim|lstlisting|minted)\}.*?"
    r"\\end\{(?P=environment)\}",
    flags=re.DOTALL,
)
_INLINE_VERB_RE = re.compile(r"\\verb\*?(?P<delimiter>[^\w\s]).*?(?P=delimiter)", flags=re.DOTALL)


def commented_at(text: str, position: int) -> bool:
    """Return whether one TeX token follows an unescaped percent on its line."""

    line_start = text.rfind("\n", 0, position) + 1
    for index in range(line_start, position):
        if text[index] != "%":
            continue
        backslashes = 0
        cursor = index - 1
        while cursor >= line_start and text[cursor] == "\\":
            backslashes += 1
            cursor -= 1
        if backslashes % 2 == 0:
            return True
    return False


def literal_spans(text: str) -> tuple[tuple[int, int], ...]:
    """Return verbatim spans whose literal examples must remain byte-identical."""

    spans = [
        *(match.span() for match in _VERBATIM_ENVIRONMENT_RE.finditer(text)),
        *(match.span() for match in _INLINE_VERB_RE.finditer(text)),
    ]
    return tuple(sorted(spans))


def in_literal_span(position: int, spans: tuple[tuple[int, int], ...]) -> bool:
    """Check whether a source position lies inside a literal span."""

    return any(start <= position < end for start, end in spans)
