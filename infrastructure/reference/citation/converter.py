"""Convert literature-search :class:`Paper` records to :class:`BibEntry`.

This module is the bridge between :mod:`infrastructure.search.literature`
(discovery) and :mod:`infrastructure.reference.citation` (export). It is
deliberately one-way: literature search returns enough metadata to build a
canonical BibTeX record, and we map it into the same field shape used by
``projects/template_code_project/manuscript/references.bib``.

Citation-key generation follows the convention observed in the exemplar:
``{first_author_lastname_lowercase}{year}{first_significant_title_word}``,
e.g. ``nocedal2006numerical``. Stop-words ("a"/"an"/"the"/"of"/"on"/...) are
skipped so titles like *On Convex Optimization* still produce ``…convex``
rather than ``…on``.
"""

from __future__ import annotations

import re
import unicodedata
from collections import OrderedDict
from typing import TYPE_CHECKING

from infrastructure.reference.citation.models import BibEntry

if TYPE_CHECKING:
    from infrastructure.search.literature.models import Paper

# Words skipped when picking the title-word component of the citation key.
_TITLE_STOP_WORDS: frozenset[str] = frozenset(
    {
        "a", "an", "the",
        "and", "or", "but", "nor",
        "of", "on", "in", "at", "to", "from", "for", "with", "by",
        "is", "are", "was", "were", "be", "been", "being",
        "as", "into", "via",
    }
)

# Map literature-source / venue type → BibTeX entry type.
_SOURCE_TO_ENTRY_TYPE: dict[str, str] = {
    "arxiv": "article",
    "biorxiv": "article",
    "medrxiv": "article",
    "pubmed": "article",
    "pmc": "article",
    "openalex": "article",
    "crossref": "article",
    "paperclip": "article",
    "book": "book",
    "inbook": "incollection",
    "chapter": "incollection",
    "conference": "inproceedings",
    "proceedings": "inproceedings",
    "thesis": "phdthesis",
    "report": "techreport",
    "preprint": "article",
    "software": "software",
    "dataset": "dataset",
    "online": "online",
}


def _slugify_token(text: str) -> str:
    """ASCII-fold *text* and strip non-alphanumerics. Lowercased."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", ascii_text.lower())


def _surname(author: str) -> str:
    """Extract the surname from a free-form author string.

    Handles both ``"Lastname, Firstname"`` and ``"Firstname Lastname"`` forms.
    """
    if not author:
        return ""
    if "," in author:
        # "Cauchy, Augustin-Louis" → "Cauchy"
        return author.split(",", 1)[0].strip()
    parts = [p for p in re.split(r"\s+", author.strip()) if p]
    return parts[-1] if parts else ""


def _title_key_word(title: str) -> str:
    """Pick the first non-stop-word from *title* for the citation key."""
    if not title:
        return ""
    for raw in re.split(r"\s+", title.strip()):
        slug = _slugify_token(raw)
        if slug and slug not in _TITLE_STOP_WORDS:
            return slug
    return ""


def generate_citation_key(
    *,
    authors: list[str],
    year: int | str | None,
    title: str,
    fallback: str = "anon",
) -> str:
    """Build a citation key in the project's house style.

    Format: ``<author_surname_slug><year><title_first_word>``.
    Falls back to *fallback* + ``year`` + title-word when there are no
    authors. Returns ``"anon"`` only as an absolute last resort.
    """
    surname = _slugify_token(_surname(authors[0])) if authors else ""
    year_str = str(year) if year is not None else ""
    title_word = _title_key_word(title)
    head = surname or fallback
    pieces = [piece for piece in (head, year_str, title_word) if piece]
    key = "".join(pieces) or fallback
    return key


def paper_to_bibentry(
    paper: "Paper",
    *,
    citation_key: str | None = None,
    entry_type: str | None = None,
) -> BibEntry:
    """Convert a :class:`Paper` record into a :class:`BibEntry`.

    The resulting fields preserve the ordering used by the exemplar
    ``references.bib`` (title, author, journal/booktitle, year, volume,
    number, pages, publisher, edition, isbn, doi, url, abstract, keywords).
    Empty / ``None`` values are skipped so the rendered output stays clean.
    """
    if entry_type is None:
        source_key = (paper.source or "").lower()
        venue_key = (paper.venue_type or "").lower()
        entry_type = (
            _SOURCE_TO_ENTRY_TYPE.get(venue_key)
            or _SOURCE_TO_ENTRY_TYPE.get(source_key)
            or "article"
        )

    if citation_key is None:
        citation_key = generate_citation_key(
            authors=list(paper.authors),
            year=paper.year,
            title=paper.title,
        )

    fields: "OrderedDict[str, str]" = OrderedDict()

    if paper.title:
        fields["title"] = paper.title
    if paper.authors:
        fields["author"] = " and ".join(a.strip() for a in paper.authors if a.strip())
    elif paper.publisher or paper.venue:
        # Crossref / arXiv occasionally return entries without an explicit
        # ``author`` (book chapters indexed at the chapter level, anthology
        # entries, etc.). natbib's authoryear style falls back to the
        # citation-key prefix when ``author`` and ``editor`` are both
        # missing, which renders as the unhelpful "[ano, 2004a]". Inject a
        # double-braced corporate author drawn from the publisher (or the
        # venue if no publisher is given) so the citation reads e.g.
        # "[Cambridge University Press, 2004]" instead. Double braces tell
        # BibTeX to treat the value as a single literal token rather than
        # ``Firstname Lastname``-splitting it.
        corporate = (paper.publisher or paper.venue or "Anonymous").strip()
        fields["author"] = f"{{{corporate}}}"
    if entry_type in {"inproceedings", "incollection"} and paper.venue:
        fields["booktitle"] = paper.venue
    elif entry_type in {"book", "phdthesis", "mastersthesis", "techreport", "misc"}:
        # Books/theses/reports keep venue out of BibTeX; series belongs in
        # publisher / series, both of which are handled below.
        pass
    elif paper.venue:
        fields["journal"] = paper.venue
    if paper.year is not None:
        fields["year"] = str(paper.year)
    if paper.volume:
        fields["volume"] = str(paper.volume)
    if paper.issue:
        fields["number"] = str(paper.issue)
    if paper.pages:
        fields["pages"] = str(paper.pages)
    if paper.publisher:
        fields["publisher"] = paper.publisher
    if paper.edition:
        fields["edition"] = paper.edition
    if paper.isbn:
        fields["isbn"] = paper.isbn
    if paper.doi:
        fields["doi"] = paper.doi
    if paper.url and not paper.doi:
        # If a DOI is present, the URL is redundant — match the exemplar style.
        fields["url"] = paper.url
    if paper.abstract:
        fields["abstract"] = paper.abstract
    if paper.keywords:
        fields["keywords"] = ", ".join(paper.keywords)

    return BibEntry(entry_type=entry_type, citation_key=citation_key, fields=fields)
