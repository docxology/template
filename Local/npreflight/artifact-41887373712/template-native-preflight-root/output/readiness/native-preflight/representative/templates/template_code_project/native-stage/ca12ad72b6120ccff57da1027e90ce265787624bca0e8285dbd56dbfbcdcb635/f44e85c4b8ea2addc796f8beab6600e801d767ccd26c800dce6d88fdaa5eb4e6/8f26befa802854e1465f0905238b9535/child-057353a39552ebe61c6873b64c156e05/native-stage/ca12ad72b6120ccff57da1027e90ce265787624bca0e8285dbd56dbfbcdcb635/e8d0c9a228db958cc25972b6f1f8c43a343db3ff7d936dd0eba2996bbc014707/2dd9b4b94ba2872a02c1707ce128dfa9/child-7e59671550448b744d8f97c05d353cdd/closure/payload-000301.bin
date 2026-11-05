"""Shared ASCII slug helpers for citation keys and deposit filenames."""

from __future__ import annotations

import re
import unicodedata

TITLE_STOP_WORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "nor",
        "of",
        "on",
        "in",
        "at",
        "to",
        "from",
        "for",
        "with",
        "by",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "as",
        "into",
        "via",
    }
)


def slugify_token(text: str) -> str:
    """ASCII-fold *text* and strip non-alphanumerics. Lowercased."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", ascii_text.lower())


def extract_surname(author: str) -> str:
    """Extract surname from ``Last, First`` or ``First Last`` author strings."""
    if not author:
        return ""
    if "," in author:
        return author.split(",", 1)[0].strip()
    parts = [part for part in re.split(r"\s+", author.strip()) if part]
    return parts[-1] if parts else ""


def title_key_word(title: str) -> str:
    """Return the first non-stop-word slug from *title*."""
    if not title:
        return ""
    for raw in re.split(r"\s+", title.strip()):
        slug = slugify_token(raw)
        if slug and slug not in TITLE_STOP_WORDS:
            return slug
    return ""


def pascal_case_token(text: str) -> str:
    """Return PascalCase ASCII token derived from *text*."""
    slug = slugify_token(text)
    if not slug:
        return ""
    return slug[0].upper() + slug[1:]
