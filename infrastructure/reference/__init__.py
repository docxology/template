"""Reference module — bibliographic data interchange.

This package contains tools for working with bibliographic references:

* :mod:`infrastructure.reference.citation` — BibTeX read/write/convert
  matching the syntax used by ``projects/template_code_project/manuscript/references.bib``.

The reference module is the export side of the literature workflow; see
:mod:`infrastructure.search.literature` for the discovery side.
"""

from infrastructure.reference.citation import (
    BibDatabase,
    BibEntry,
    BibParseError,
    generate_citation_key,
    paper_to_bibentry,
    parse_bibfile,
    parse_bibtex,
    render_database,
    render_entry,
    write_bibfile,
)

__all__ = [
    "BibEntry",
    "BibDatabase",
    "BibParseError",
    "render_entry",
    "render_database",
    "write_bibfile",
    "parse_bibtex",
    "parse_bibfile",
    "paper_to_bibentry",
    "generate_citation_key",
]
