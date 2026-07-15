"""Data models for literature search.

Inspired by the agent-native abstractions of Paperclip
(`https://paperclip.gxl.ai`): every backend produces a normalised
:class:`Paper` record so downstream consumers (citation export, manuscript
synthesis, agent loops) can treat results uniformly regardless of source.

The schema is intentionally a superset of what BibTeX requires so that the
:func:`infrastructure.reference.citation.paper_to_bibentry` converter has
everything it needs without going back to the network.
"""

from __future__ import annotations


import json
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping


@dataclass(frozen=False)
class Paper:
    """A normalised literature-search result.

    Required: ``id``, ``title``. Everything else is optional but populated
    when the backend exposes it.

    Attributes:
        id: Source-prefixed identifier, e.g. ``"arxiv:2501.12948"``,
            ``"doi:10.1126/science.1213847"``. Must be unique within a result
            set; use :func:`merge_papers` to deduplicate by DOI / arXiv id
            across backends.
        title: Paper title.
        authors: Ordered list of author display strings ("First Last" or
            "Last, First"). Citation export normalises both forms.
        abstract: Abstract / summary text, when available.
        year: Four-digit publication year.
        doi: Digital Object Identifier.
        url: Canonical landing-page URL.
        venue: Journal name (article) or conference name (inproceedings) or
            book title (incollection). The converter routes it to the
            appropriate BibTeX field based on ``venue_type``.
        venue_type: One of ``"journal"``, ``"conference"``, ``"book"``,
            ``"preprint"``, ``"online"``, ``"thesis"``, ``"report"``.
        volume / issue / pages: Bibliographic locators.
        publisher / edition / isbn: Publisher metadata.
        keywords: Free-form keyword list.
        source: Backend that produced this record (e.g. ``"crossref"``,
            ``"arxiv"``, ``"local"``, ``"paperclip"``).
        score: Backend-reported relevance score in ``[0, 1]``. Used by the
            aggregator to merge / rank results from heterogeneous backends.
        raw: Optional dict of backend-specific extra metadata. Kept for
            debugging; not part of the canonical hash.
    """

    id: str
    title: str
    authors: list[str] = field(default_factory=list)
    abstract: str | None = None
    year: int | None = None
    doi: str | None = None
    url: str | None = None
    venue: str | None = None
    venue_type: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    publisher: str | None = None
    edition: str | None = None
    isbn: str | None = None
    keywords: list[str] = field(default_factory=list)
    source: str | None = None
    score: float = 0.0
    pdf_url: str | None = None
    fulltext: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not str(self.id).strip():
            raise ValueError("Paper.id must be a non-empty string")
        if not self.title or not str(self.title).strip():
            raise ValueError("Paper.title must be a non-empty string")
        # Normalise list types (callers sometimes pass tuples).
        self.authors = list(self.authors or [])
        self.keywords = list(self.keywords or [])
        if self.year is not None:
            try:
                self.year = int(self.year)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Paper.year must be an integer, got {self.year!r}") from exc

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Paper":
        """Construct a :class:`Paper` from a plain dict.

        Unknown keys are dropped silently so older cache files / hand-written
        records remain compatible across schema additions.
        """
        allowed = {f for f in cls.__dataclass_fields__}
        kwargs = {k: v for k, v in data.items() if k in allowed}
        return cls(**kwargs)


@dataclass
class SearchQuery:
    """A literature search request.

    Attributes:
        text: Free-text query (BM25 / vector / both, depending on backend).
        max_results: Cap on results returned by each backend.
        year_min / year_max: Inclusive year filters; ``None`` disables.
        sources: Optional list of backend names to consult; empty/``None``
            means "all configured backends".
        fields: Optional list of field hints (``"title"``, ``"abstract"``,
            ``"author"``) — backends that support targeted search use them.
    """

    text: str
    max_results: int = 10
    year_min: int | None = None
    year_max: int | None = None
    sources: list[str] = field(default_factory=list)
    fields: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.text or not self.text.strip():
            raise ValueError("SearchQuery.text must be a non-empty string")
        if self.max_results <= 0:
            raise ValueError("SearchQuery.max_results must be positive")
        if self.year_min is not None and self.year_max is not None and self.year_min > self.year_max:
            raise ValueError("year_min cannot exceed year_max")

    def matches_year(self, year: int | None) -> bool:
        """Return True iff *year* satisfies the filter (None always passes)."""
        if year is None:
            return True
        if self.year_min is not None and year < self.year_min:
            return False
        if self.year_max is not None and year > self.year_max:
            return False
        return True


@dataclass
class SearchResult:
    """The aggregate response to a :class:`SearchQuery`.

    Attributes:
        query: The original query (echoed for traceability).
        papers: Deduplicated, score-sorted result list.
        per_source_counts: Map of backend name → number of papers contributed
            *before* deduplication. Useful for debugging coverage.
        errors: Map of backend name → error message for any backends that
            failed. Aggregator does not raise on per-backend failures so a
            single offline source does not break the whole search.
    """

    query: SearchQuery
    papers: list[Paper] = field(default_factory=list)
    per_source_counts: dict[str, int] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.papers)

    def __iter__(self) -> Iterable[Paper]:
        return iter(self.papers)

    def to_dict(self) -> dict[str, Any]:
        """Serialize this object to a plain dict for JSON output."""
        return {
            "query": asdict(self.query),
            "papers": [p.to_dict() for p in self.papers],
            "per_source_counts": dict(self.per_source_counts),
            "errors": dict(self.errors),
        }

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize this object to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, sort_keys=False)


def _canonical_paper_key(paper: Paper) -> str:
    """Build a deduplication key for *paper*.

    Preference order: DOI → arXiv id → normalised (title, year) tuple.
    """
    if paper.doi:
        return f"doi:{paper.doi.lower().strip()}"
    if paper.id and paper.id.lower().startswith("arxiv:"):
        return paper.id.lower().strip()
    title = "".join(ch.lower() for ch in (paper.title or "") if ch.isalnum())
    year = paper.year or "?"
    return f"title:{title}:{year}"


def merge_papers(papers: Iterable[Paper]) -> list[Paper]:
    """Deduplicate *papers* by canonical key, keeping the highest-scored copy.

    When duplicates are merged, fields missing on the winner are filled from
    the loser ("union of evidence"). Authors / keywords are merged in order.
    """
    by_key: dict[str, Paper] = {}
    for paper in papers:
        key = _canonical_paper_key(paper)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = paper
            continue
        winner, loser = (existing, paper) if existing.score >= paper.score else (paper, existing)
        # Fill missing scalar fields from loser onto winner.
        for fname in (
            "abstract",
            "year",
            "doi",
            "url",
            "venue",
            "venue_type",
            "volume",
            "issue",
            "pages",
            "publisher",
            "edition",
            "isbn",
        ):
            if getattr(winner, fname) in (None, "") and getattr(loser, fname) not in (None, ""):
                setattr(winner, fname, getattr(loser, fname))
        # Merge list fields preserving order, no duplicates.
        for fname in ("authors", "keywords"):
            seen: set[str] = set()
            merged: list[str] = []
            for value in list(getattr(winner, fname)) + list(getattr(loser, fname)):
                if value and value not in seen:
                    seen.add(value)
                    merged.append(value)
            setattr(winner, fname, merged)
        by_key[key] = winner
    return list(by_key.values())
