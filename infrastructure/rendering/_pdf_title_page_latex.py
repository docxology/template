"""LaTeX text-escaping helpers for the config-driven title page."""

from __future__ import annotations

import re

__all__ = [
    "_latex_href_url",
    "_latex_paragraphs",
    "_latex_text",
]

_LATEX_ESCAPE_REPLACEMENTS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def _latex_text(value: object) -> str:
    """Escape a short text value for LaTeX text mode."""
    text = str(value)
    return "".join(_LATEX_ESCAPE_REPLACEMENTS.get(ch, ch) for ch in text)


def _latex_href_url(url: str) -> str:
    """Escape a URL for hyperref ``\\href`` first argument (not text mode)."""
    minimal = {"\\": r"\\", "%": r"\%", "#": r"\#", "&": r"\&"}
    return "".join(minimal.get(ch, ch) for ch in url)


def _latex_paragraphs(value: object) -> str:
    """Escape a prose block for LaTeX and preserve paragraph breaks."""
    raw = str(value).strip()
    if not raw:
        return ""
    paragraphs = [line.strip() for line in re.split(r"\n\s*\n", raw) if line.strip()]
    return r"\par ".join(_latex_text(paragraph) for paragraph in paragraphs)
