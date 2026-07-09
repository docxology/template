"""Word-boundary-safe pitch-deck cliche lint.

Enforces "non-cliche" as a testable constraint rather than a vibe: any
resolved slide text containing one of these stock phrases fails the deck
content audit the same way an uncovered line fails a coverage gate.

Uses ``\\b`` word-boundary regex per term rather than bare substring search —
a naive ``"class" in text`` style check would false-positive on "classic" or
miss "disruptive" inside a legitimate sentence about disruptive-*looking*
design; word boundaries avoid both directions of that failure.
"""

from __future__ import annotations

import re

DENYLIST: tuple[str, ...] = (
    "synergy",
    "synergies",
    "disrupt",
    "disruptive",
    "disruption",
    "unicorn",
    "10x",
    "game-changing",
    "game changer",
    "rocket ship",
    "north star",
    "move fast and break things",
    "paradigm shift",
    "best-in-class",
    "bleeding edge",
    "revolutionize",
    "revolutionary",
    "world-class",
    "turnkey solution",
    "low-hanging fruit",
)

_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE) for term in DENYLIST
)


def lint_text(text: str) -> list[str]:
    """Return the denylisted terms found in ``text``, in `DENYLIST` order.

    Each match is whole-word: "classic" does not match "best-in-class" absent
    an exact phrase match, and "disruptive-looking" still matches
    "disruptive" because the hyphen is a word boundary.
    """
    return [term for term, pattern in zip(DENYLIST, _PATTERNS) if pattern.search(text)]


def lint_deck_texts(texts: dict[str, str]) -> dict[str, list[str]]:
    """Lint a ``{slide_field_id: text}`` mapping; return only entries with hits."""
    results = {key: lint_text(value) for key, value in texts.items()}
    return {key: hits for key, hits in results.items() if hits}


__all__ = ["DENYLIST", "lint_text", "lint_deck_texts"]
