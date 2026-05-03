"""Citation submodule — BibTeX read/write/convert.

Public API:

* :class:`BibEntry`, :class:`BibDatabase` — data models that preserve
  field order for byte-stable round trips.
* :func:`render_entry`, :func:`render_database`, :func:`write_bibfile` —
  serialise to the same format as
  ``projects/template_code_project/manuscript/references.bib``.
* :func:`parse_bibtex`, :func:`parse_bibfile`, :class:`BibParseError` —
  forgiving parser sufficient for round-tripping our own output and the
  exemplar file.
* :func:`paper_to_bibentry`, :func:`generate_citation_key` — bridge from
  :class:`infrastructure.search.literature.Paper` to BibTeX records.
* :func:`escape_latex`, :func:`unescape_latex` — LaTeX-special-character
  helpers.
"""

from __future__ import annotations

from infrastructure.reference.citation.bibtex_parser import (
    BibParseError,
    parse_bibfile,
    parse_bibtex,
)
from infrastructure.reference.citation.bibtex_writer import (
    render_database,
    render_entries,
    render_entry,
    write_bibfile,
)
from infrastructure.reference.citation.converter import (
    generate_citation_key,
    paper_to_bibentry,
)
from infrastructure.reference.citation.escape import escape_latex, unescape_latex
from infrastructure.reference.citation.models import (
    CANONICAL_ENTRY_TYPES,
    BibDatabase,
    BibEntry,
)

__all__ = [
    # Models
    "BibEntry",
    "BibDatabase",
    "CANONICAL_ENTRY_TYPES",
    # Writer
    "render_entry",
    "render_database",
    "render_entries",
    "write_bibfile",
    # Parser
    "parse_bibtex",
    "parse_bibfile",
    "BibParseError",
    # Converter
    "paper_to_bibentry",
    "generate_citation_key",
    # Escape helpers
    "escape_latex",
    "unescape_latex",
]
