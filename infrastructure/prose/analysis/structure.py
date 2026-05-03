"""Structural analysis of Markdown prose: heading outline, balance, gaps.

Companion to :mod:`infrastructure.prose.analysis.metrics`. Where metrics
operate on raw text, this module reads the Markdown structure and
returns a structural model — the heading outline, depth, and per-section
word counts. This is what an editor cares about when checking that a
manuscript is well-paced.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from infrastructure.prose.analysis.metrics import tokenize_words

_ATX_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_FENCE_RE = re.compile(r"^```")


@dataclass
class Heading:
    """One heading in a Markdown document."""

    level: int
    title: str
    line: int


@dataclass
class Section:
    """A heading together with the body text up to the next same-or-shallower heading."""

    heading: Heading
    body: str
    word_count: int = 0


@dataclass
class StructureReport:
    """Outline of a Markdown document, with per-section word counts."""

    headings: list[Heading] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)
    total_words: int = 0
    max_depth: int = 0
    has_h1: bool = False
    has_skipped_level: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "total_words": self.total_words,
            "max_depth": self.max_depth,
            "has_h1": self.has_h1,
            "has_skipped_level": self.has_skipped_level,
            "headings": [{"level": h.level, "title": h.title, "line": h.line} for h in self.headings],
            "sections": [
                {
                    "level": s.heading.level,
                    "title": s.heading.title,
                    "line": s.heading.line,
                    "word_count": s.word_count,
                }
                for s in self.sections
            ],
        }


def parse_headings(markdown: str) -> list[Heading]:
    """Extract ATX (#-style) headings from *markdown*, ignoring code fences."""
    headings: list[Heading] = []
    in_fence = False
    for i, line in enumerate(markdown.splitlines(), start=1):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _ATX_RE.match(line)
        if m:
            headings.append(Heading(level=len(m.group(1)), title=m.group(2), line=i))
    return headings


def analyze_structure(markdown: str) -> StructureReport:
    """Build a :class:`StructureReport` for *markdown*."""
    headings = parse_headings(markdown)
    lines = markdown.splitlines()

    sections: list[Section] = []
    for idx, h in enumerate(headings):
        # Body runs from the line *after* the heading until the next heading.
        start = h.line  # 0-based: lines[h.line] is the line *after* the heading
        end = headings[idx + 1].line - 1 if idx + 1 < len(headings) else len(lines)
        body = "\n".join(lines[start:end])
        sections.append(Section(heading=h, body=body, word_count=len(tokenize_words(body))))

    total_words = sum(s.word_count for s in sections)
    max_depth = max((h.level for h in headings), default=0)
    has_h1 = any(h.level == 1 for h in headings)

    has_skipped = False
    last_level = 0
    for h in headings:
        if last_level and h.level > last_level + 1:
            has_skipped = True
            break
        last_level = h.level

    return StructureReport(
        headings=headings,
        sections=sections,
        total_words=total_words,
        max_depth=max_depth,
        has_h1=has_h1,
        has_skipped_level=has_skipped,
    )


def render_outline(report: StructureReport) -> str:
    """Render *report* as a plain-text bulleted outline."""
    lines: list[str] = []
    for h in report.headings:
        indent = "  " * (h.level - 1)
        lines.append(f"{indent}- {h.title}")
    return "\n".join(lines)
