"""LaTeX text-escaping helpers for the config-driven title page."""

from __future__ import annotations

import re

__all__ = [
    "_latex_graphic_alt_text",
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

# LaTeX's tagging layer purifies the value of ``includegraphics[alt={...}]``
# before storing it in the PDF structure tree.  Text-mode display commands such
# as ``\textasciitilde`` survive that purification as their command names rather
# than the intended characters.  Generate category-code-12 character tokens
# instead: they cannot terminate the option value, start a comment, or become a
# control sequence, and the resulting PDF ``/Alt`` string retains the exact
# source character.  ``\csname`` keeps this usable while ExplSyntax is off.
_GRAPHIC_ALT_LITERAL_CODEPOINTS = frozenset(r"\&%$#_{}~^")


def _latex_graphic_alt_text(value: object) -> str:
    """Serialize plain text for LaTeX ``includegraphics`` alt metadata.

    This is intentionally distinct from :func:`_latex_text`: visual title-page
    prose needs printable LaTeX commands, while a graphic alternative must
    survive LaTeX's PDF-string purification as literal Unicode text.  Internal
    whitespace is normalized because PDF alternative text is a single logical
    phrase rather than a typeset paragraph.
    """
    text = " ".join(str(value).split())
    return "".join(
        rf"\csname char_generate:nn\endcsname{{{ord(char)}}}{{12}}" if char in _GRAPHIC_ALT_LITERAL_CODEPOINTS else char
        for char in text
    )


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
