"""Render :class:`BibEntry` / :class:`BibDatabase` records to BibTeX text.

The output format reproduces, byte-for-byte, the conventions used in
``projects/templates/template_code_project/manuscript/references.bib``:

* ``@type{citation_key,`` opens the entry on its own line.
* Each field uses **two-space indentation**: ``  field={value},``.
* Every field except the **last** has a trailing comma.
* The closing ``}`` sits flush-left on its own line.
* Values are wrapped in braces (``{...}``); LaTeX special characters are
  escaped (``&`` → ``\\&`` etc.) but unicode is preserved.
* Author lists use ``" and "`` as the separator.
* Page ranges use the BibTeX-canonical en-dash form ``--``.
* A blank line separates entries; the file ends with a single newline.

A leading ``@comment{...}`` preamble is emitted before any entries when the
caller provides one.
"""

from io import StringIO
from pathlib import Path
from typing import Iterable

from infrastructure.reference.citation.escape import escape_latex
from infrastructure.reference.citation.models import BibDatabase, BibEntry

_INDENT = "  "

# Fields whose values are numeric / symbolic and should *not* be LaTeX-escaped.
# (Matches the convention in the exemplar references.bib.)
_VERBATIM_FIELDS: frozenset[str] = frozenset(
    {"year", "volume", "number", "month", "edition", "isbn", "issn", "doi", "url"}
)

# Author-like fields are split on " and " for normalisation but otherwise
# escaped like normal text.
_AUTHOR_FIELDS: frozenset[str] = frozenset({"author", "editor"})

# Page ranges are normalised to use the BibTeX em-dash form ``--``.
_PAGE_FIELDS: frozenset[str] = frozenset({"pages"})


def _normalise_pages(value: str) -> str:
    """Normalise ``"123-456"`` / ``"123–456"`` / ``"123—456"`` to ``"123--456"``."""
    if not value:
        return value
    out = value.replace("–", "--").replace("—", "--")
    # Collapse single ASCII hyphens *between digits* to ``--`` while leaving
    # other hyphens (e.g. inside DOIs) untouched. We require digits on both
    # sides so single-page entries (e.g. "S5") stay intact.
    result_chars: list[str] = []
    i = 0
    while i < len(out):
        ch = out[i]
        if (
            ch == "-"
            and (i == 0 or out[i - 1].isdigit())
            and (i + 1 < len(out) and out[i + 1].isdigit())
            and not (i + 1 < len(out) and out[i + 1] == "-")
            and not (i > 0 and out[i - 1] == "-")
        ):
            result_chars.append("--")
        else:
            result_chars.append(ch)
        i += 1
    return "".join(result_chars)


def _escape_author_part(part: str) -> str:
    """Escape LaTeX specials in an author part while preserving balanced
    braces.

    BibTeX uses braces inside author fields *structurally* — a name
    wrapped in ``{...}`` is treated as a single literal token (the
    canonical form for corporate authors such as ``{Cambridge University
    Press}``). LaTeX-escaping ``{`` / ``}`` to ``\\{`` / ``\\}`` would
    destroy that signal, so this helper escapes everything `escape_latex`
    does *except* balanced top-level brace pairs.
    """
    if part.startswith("{") and part.endswith("}") and len(part) >= 2:
        # Preserve corporate-name braces; escape only the inner text.
        inner = part[1:-1]
        return "{" + escape_latex(inner) + "}"
    return escape_latex(part)


def _format_value(field_name: str, raw_value: str) -> str:
    """Apply field-specific normalisation + LaTeX escaping."""
    if raw_value is None:
        return ""
    if field_name in _PAGE_FIELDS:
        return _normalise_pages(raw_value)
    if field_name in _VERBATIM_FIELDS:
        # DOIs and URLs already have valid BibTeX syntax — no escaping.
        return raw_value
    if field_name in _AUTHOR_FIELDS:
        # Normalise spacing around " and " separators and preserve any
        # corporate-author braces in each part.
        parts = [p.strip() for p in raw_value.split(" and ") if p.strip()]
        return " and ".join(_escape_author_part(p) for p in parts)
    return escape_latex(raw_value)


def render_entry(entry: BibEntry) -> str:
    """Render a single :class:`BibEntry` to a BibTeX string."""
    if not entry.fields:
        # Still legal — emit ``@type{key,\n}``.
        return f"@{entry.entry_type}{{{entry.citation_key}\n}}\n"

    buf = StringIO()
    if entry.comment:
        buf.write(f"@comment{{{entry.comment}}}\n")

    buf.write(f"@{entry.entry_type}{{{entry.citation_key},\n")
    items = list(entry.fields.items())
    last_index = len(items) - 1
    for i, (name, raw_value) in enumerate(items):
        formatted = _format_value(name, raw_value)
        suffix = "," if i < last_index else ""
        buf.write(f"{_INDENT}{name}={{{formatted}}}{suffix}\n")
    buf.write("}\n")
    return buf.getvalue()


def render_database(database: BibDatabase) -> str:
    """Render an entire :class:`BibDatabase` to a BibTeX string.

    Entries are separated by a single blank line. A trailing newline is
    emitted so the file ends with ``\\n``.
    """
    buf = StringIO()
    if database.preamble:
        buf.write(f"@comment{{\n{database.preamble.rstrip()}\n}}\n\n")
    for i, entry in enumerate(database.entries):
        buf.write(render_entry(entry))
        if i < len(database.entries) - 1:
            buf.write("\n")
    return buf.getvalue()


def write_bibfile(path: Path | str, database: BibDatabase, *, encoding: str = "utf-8") -> Path:
    """Render *database* and write it to *path*.

    Returns the resolved :class:`~pathlib.Path` of the written file. Parent
    directories are created if missing. Existing files are overwritten.
    """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_database(database), encoding=encoding)
    return output_path


def render_entries(entries: Iterable[BibEntry]) -> str:
    """Convenience: render an iterable of entries (no preamble)."""
    db = BibDatabase(entries=list(entries))
    return render_database(db)
