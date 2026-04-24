"""Stable, dotted IDs for content-validation diagnostics.

Codes follow ``namespace.SCREAMING_SNAKE_CASE`` so they grep cleanly out
of log files and JSON reports, e.g.::

    jq '.events[] | select(.code=="MARKDOWN.PANDOC_BARE_PIPE")' diagnostics.json
    rg 'MARKDOWN\\.IMG_MISSING' projects/*/output/reports/

Any change to an existing code value is a **breaking change** for
downstream filters and must be called out in release notes. Adding a new
code is non-breaking; consumers MUST treat unknown codes as opaque.

Codes are intentionally orthogonal to ``DiagnosticEvent.category``:
- ``category`` is a coarse user-facing grouping (``MARKDOWN_LINK``).
- ``code`` is a fine, immutable identifier (``MARKDOWN.LINK_BARE_URL``)
  suitable for programmatic suppression / pattern matching.
"""

from __future__ import annotations


class MarkdownCode:
    """Stable IDs for findings emitted by ``markdown_validator``."""

    IMG_MISSING = "MARKDOWN.IMG_MISSING"
    REF_EQUATION_MISSING = "MARKDOWN.REF_EQUATION_MISSING"
    LINK_ANCHOR_MISSING = "MARKDOWN.LINK_ANCHOR_MISSING"
    LINK_BARE_URL = "MARKDOWN.LINK_BARE_URL"
    LINK_BAD_TEXT = "MARKDOWN.LINK_BAD_TEXT"
    MATH_DOLLAR_DISPLAY = "MARKDOWN.MATH_DOLLAR_DISPLAY"
    MATH_BRACKET_DISPLAY = "MARKDOWN.MATH_BRACKET_DISPLAY"
    MATH_LABEL_MISSING = "MARKDOWN.MATH_LABEL_MISSING"
    MATH_LABEL_DUPLICATE = "MARKDOWN.MATH_LABEL_DUPLICATE"
    PANDOC_BARE_PIPE = "MARKDOWN.PANDOC_BARE_PIPE"
    PANDOC_TABLE_ESCAPED_PIPE = "MARKDOWN.PANDOC_TABLE_ESCAPED_PIPE"


class BibtexCode:
    """Stable IDs for citation/bibliography findings."""

    UNDEFINED_KEY = "BIBTEX.UNDEFINED_KEY"


__all__ = ["MarkdownCode", "BibtexCode"]
