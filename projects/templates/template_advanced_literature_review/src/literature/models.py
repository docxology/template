"""Data models for literature corpus.

Provides Paper, Author, and Citation dataclasses used throughout
the literature meta-analysis pipeline for representing
bibliographic records, authorship, and citation relationships.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

_DOI_RESOLVER_PREFIX = re.compile(r"^(?:https?://)?(?:dx\.)?doi\.org/", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_PREPRINT_HINTS = (
    "arxiv",
    "biorxiv",
    "medrxiv",
    "chemrxiv",
    "ssrn",
    "preprint",
    "working paper",
    "hal",
    "europepmc",
    "europe pmc",
)


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    text = _WHITESPACE_RE.sub(" ", value).strip().lower()
    return _NON_ALNUM_RE.sub(" ", text).strip()


def _normalize_author_signature(authors: list[Author]) -> str:
    normalized: list[str] = []
    for author in authors[:3]:
        name = _normalize_text(author.name)
        if name:
            normalized.append(name)
    return " | ".join(normalized)


def normalize_doi(doi: str) -> str:
    """Return a canonical, comparable form of a DOI.

    DOIs are case-insensitive by ISO 26324, but academic search engines disagree
    on case and on whether they prepend a ``https://doi.org/`` resolver prefix.
    Without normalization the SAME paper returned by two engines as
    ``10.1038/Nature12345`` and ``https://doi.org/10.1038/nature12345`` produces
    two distinct ``canonical_id`` values and silently escapes cross-engine
    de-duplication. Lower-casing + prefix/whitespace stripping collapses these to
    one key. (Applied only to the comparison key; the raw ``doi`` field is left
    as the source engine returned it for display/citation fidelity.)
    """
    cleaned = _DOI_RESOLVER_PREFIX.sub("", doi.strip())
    return cleaned.lower()


@dataclass
class Author:
    """Represents a paper author.

    Attributes:
        name: Full name (e.g., "Karl Friston")
        affiliation: Institution name, if known
        orcid: ORCID identifier, if known
    """

    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None


@dataclass
class Citation:
    """A directional citation link between two papers.

    Attributes:
        source_id: Canonical ID of the citing paper
        target_id: Canonical ID of the cited paper
        context: Optional citation context text
    """

    source_id: str
    target_id: str
    context: Optional[str] = None


@dataclass
class Paper:
    """Represents a single research paper.

    The canonical_id property returns the best available identifier
    with priority: doi > pmid > arxiv_id > s2_id > openalex_id > title hash.

    Attributes:
        title: Paper title
        abstract: Paper abstract text
        authors: List of Author objects
        year: Publication year
        doi: Digital Object Identifier
        pmid: PubMed identifier (e.g., "12345678")
        arxiv_id: arXiv identifier (e.g., "2301.12345")
        s2_id: Semantic Scholar paper ID
        openalex_id: OpenAlex work ID
        venue: Publication venue/journal
        citation_count: Number of citations
        references: List of canonical IDs this paper cites
        publication_date: Full publication date if available
        pdf_url: Direct URL to a PDF of the full text, if available
        is_open_access: Whether the paper is open access
        full_text_source: Provenance of the full text (e.g., "arxiv",
            "publisher", "repository")
    """

    title: str
    abstract: str = ""
    authors: list[Author] = field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    arxiv_id: Optional[str] = None
    s2_id: Optional[str] = None
    openalex_id: Optional[str] = None
    venue: Optional[str] = None
    citation_count: int = 0
    references: list[str] = field(default_factory=list)
    publication_date: Optional[date] = None
    pdf_url: Optional[str] = None
    is_open_access: Optional[bool] = None
    full_text_source: Optional[str] = None
    keywords: list[str] = field(default_factory=list)

    @property
    def referenced_works(self) -> list[str]:
        """Alias for :attr:`references` — matches the OpenAlex/S2 field name.

        Some engines (OpenAlex, Semantic Scholar) expose the reference list
        under ``referenced_works`` rather than ``references``. The pipeline
        runner (:func:`analysis.pipeline_runner._count_paper_references`)
        already checks both names; this alias makes the Paper model
        self-documenting.
        """
        return self.references

    @property
    def canonical_id(self) -> str:
        """Return best available identifier with priority: doi > pmid > arxiv_id > s2_id > openalex_id > title hash.

        The DOI is normalized (case-folded, resolver-prefix/whitespace stripped) so the
        same paper returned by different engines under case/format-variant DOIs merges.
        """
        if self.doi:
            return f"doi:{normalize_doi(self.doi)}"
        if self.pmid:
            return f"pmid:{self.pmid}"
        if self.arxiv_id:
            return f"arxiv:{self.arxiv_id}"
        if self.s2_id:
            return f"s2:{self.s2_id}"
        if self.openalex_id:
            return f"openalex:{self.openalex_id}"
        # Stable digest, NOT the builtin hash(): str hashing is salted by
        # PYTHONHASHSEED (random per process), which would give the same
        # ID-less paper a different canonical_id every run — breaking both
        # de-duplication and byte-stable corpora on live records that lack
        # all four identifiers. A content hash is process-independent.
        # usedforsecurity=False: this is a content fingerprint for record identity,
        # not a security primitive — collision-resistance is not required.
        digest = hashlib.sha1(self.title.lower().strip().encode("utf-8"), usedforsecurity=False).hexdigest()
        return f"title:{digest[:16]}"

    @property
    def normalized_title(self) -> str:
        """Process normalized title."""
        return _normalize_text(self.title)

    @property
    def author_signature(self) -> str:
        """Process author signature."""
        return _normalize_author_signature(self.authors)

    @property
    def publication_signature(self) -> str:
        """Process publication signature."""
        parts = [self.normalized_title, self.author_signature]
        return "|".join(part for part in parts if part)

    @property
    def is_preprint(self) -> bool:
        """Check whether preprint."""
        if self.arxiv_id and not self.doi:
            return True
        haystacks = [self.full_text_source, self.venue, self.pdf_url]
        for haystack in haystacks:
            if not haystack:
                continue
            normalized = haystack.lower()
            if any(hint in normalized for hint in _PREPRINT_HINTS):
                return True
        return False

    @property
    def metadata_completeness(self) -> int:
        """Count of non-None metadata fields for merge priority.

        Returns:
            Number of populated optional fields.
        """
        count = 0
        if self.abstract:
            count += 1
        if self.authors:
            count += 1
        if self.year is not None:
            count += 1
        if self.doi:
            count += 1
        if self.pmid:
            count += 1
        if self.arxiv_id:
            count += 1
        if self.s2_id:
            count += 1
        if self.openalex_id:
            count += 1
        if self.venue:
            count += 1
        if self.citation_count > 0:
            count += 1
        if self.references:
            count += 1
        if self.publication_date:
            count += 1
        if self.pdf_url:
            count += 1
        if self.is_open_access is not None:
            count += 1
        if self.keywords:
            count += 1
        return count

    def to_dict(self) -> dict:
        """Serialize paper to dictionary for JSONL storage.

        Returns:
            Dictionary representation suitable for JSON serialization.
        """
        return {
            "title": self.title,
            "abstract": self.abstract,
            "authors": [{"name": a.name, "affiliation": a.affiliation, "orcid": a.orcid} for a in self.authors],
            "year": self.year,
            "doi": self.doi,
            "pmid": self.pmid,
            "arxiv_id": self.arxiv_id,
            "s2_id": self.s2_id,
            "openalex_id": self.openalex_id,
            "venue": self.venue,
            "citation_count": self.citation_count,
            "references": self.references,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "pdf_url": self.pdf_url,
            "is_open_access": self.is_open_access,
            "full_text_source": self.full_text_source,
            "keywords": self.keywords,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Paper:
        """Deserialize paper from dictionary.

        Args:
            data: Dictionary with paper fields.

        Returns:
            Paper instance reconstructed from the dictionary.
        """
        authors = [Author(**a) for a in data.get("authors", [])]
        pub_date = None
        if data.get("publication_date"):
            pub_date = date.fromisoformat(data["publication_date"])
        return cls(
            title=data["title"],
            abstract=data.get("abstract", ""),
            authors=authors,
            year=data.get("year"),
            doi=data.get("doi"),
            pmid=data.get("pmid"),
            arxiv_id=data.get("arxiv_id"),
            s2_id=data.get("s2_id"),
            openalex_id=data.get("openalex_id"),
            venue=data.get("venue"),
            citation_count=data.get("citation_count", 0),
            references=data.get("references", []),
            publication_date=pub_date,
            pdf_url=data.get("pdf_url"),
            is_open_access=data.get("is_open_access"),
            full_text_source=data.get("full_text_source"),
            keywords=data.get("keywords", []),
        )
