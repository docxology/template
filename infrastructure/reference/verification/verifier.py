"""Classify each cited reference into a :class:`VerificationStatus`.

Given a parsed ``.bib`` database and a :class:`ReferenceResolver`, decide for
every entry whether the cited work exists and whether the cited metadata
matches the indexed record. The classification rules are deterministic:

* future-dated citation (year after the as-of year) -> ``ANACHRONISM``
* offline + not cached -> ``UNCHECKED`` (never silently OK)
* identifier present but index returns nothing -> ``FABRICATED``
* no identifier and title search inconclusive -> ``UNVERIFIABLE``
* resolved but title/year/author disagree -> ``MISMATCH``
* resolved and consistent -> ``OK``

The temporal-integrity layer (anachronism detection) is distilled from the
Academic Research Skills temporal-integrity audit (CC-BY-NC-4.0); this is an
original Apache-2.0 implementation.
"""

from __future__ import annotations

import re
from pathlib import Path

from infrastructure.core.text_slug import extract_surname
from infrastructure.reference.citation.bibtex_parser import parse_bibfile
from infrastructure.reference.citation.models import BibDatabase, BibEntry
from infrastructure.reference.verification.models import (
    ReferenceVerdict,
    VerificationReport,
    VerificationStatus,
)
from infrastructure.reference.verification.resolver import ReferenceResolver, title_similarity

__all__ = [
    "extract_arxiv_id",
    "parse_bib_year",
    "verify_bibfile",
    "verify_database",
    "verify_entry",
]

# arXiv ids: legacy (e.g. ``math.GT/0309136``) and modern (``2501.12948``).
_ARXIV_ID_RE = re.compile(r"(\d{4}\.\d{4,5}(v\d+)?|[a-z\-]+(\.[A-Z]{2})?/\d{7})", re.IGNORECASE)
# DOIs minted by arXiv encode the arXiv id: 10.48550/arXiv.2501.12948
_ARXIV_DOI_RE = re.compile(r"10\.48550/arxiv\.(?P<id>\S+)", re.IGNORECASE)


def parse_bib_year(value: str | None) -> int | None:
    """Extract a four-digit year from a BibTeX ``year`` field, if present."""
    if not value:
        return None
    match = re.search(r"\d{4}", value)
    return int(match.group(0)) if match else None


def extract_arxiv_id(entry: BibEntry) -> str | None:
    """Recover an arXiv identifier from ``eprint`` / ``doi`` / ``url`` fields."""
    archiveprefix = (entry.get("archiveprefix") or entry.get("archivePrefix") or "").lower()
    eprint = entry.get("eprint")
    if eprint and ("arxiv" in archiveprefix or not archiveprefix):
        cleaned = eprint.strip()
        if _ARXIV_ID_RE.fullmatch(cleaned) or "arxiv" in archiveprefix:
            return cleaned
    doi = entry.get("doi")
    if doi:
        doi_match = _ARXIV_DOI_RE.search(doi)
        if doi_match:
            return doi_match.group("id")
    url = entry.get("url") or ""
    if "arxiv.org/abs/" in url:
        tail = url.split("arxiv.org/abs/", 1)[1].strip().strip("/")
        if tail:
            return tail
    return None


def _is_arxiv_only_doi(doi: str | None) -> bool:
    return bool(doi and _ARXIV_DOI_RE.search(doi))


def verify_entry(
    entry: BibEntry,
    resolver: ReferenceResolver,
    *,
    as_of_year: int | None = None,
) -> ReferenceVerdict:
    """Verify a single ``.bib`` entry and return its verdict."""
    doi = entry.get("doi")
    arxiv_id = extract_arxiv_id(entry)
    title = entry.get("title")
    bib_year = parse_bib_year(entry.get("year"))

    # An arXiv-minted DOI is best resolved through the arXiv API, not Crossref.
    resolve_doi = None if _is_arxiv_only_doi(doi) else doi

    # Temporal integrity: a citation dated after the manuscript cannot be real.
    if as_of_year is not None and bib_year is not None and bib_year > as_of_year:
        return ReferenceVerdict(
            citation_key=entry.citation_key,
            status=VerificationStatus.ANACHRONISM,
            detail=f"cited year {bib_year} is after as-of year {as_of_year}",
            doi=doi,
            arxiv_id=arxiv_id,
            issues=[f"future-dated citation ({bib_year} > {as_of_year})"],
        )

    has_identifier = bool(resolve_doi or arxiv_id)
    resolution = resolver.resolve(doi=resolve_doi, arxiv_id=arxiv_id, title=title)

    if not resolution.checked:
        return ReferenceVerdict(
            citation_key=entry.citation_key,
            status=VerificationStatus.UNCHECKED,
            detail="offline and not cached — run with --live to resolve",
            doi=doi,
            arxiv_id=arxiv_id,
        )

    if resolution.paper is None:
        if has_identifier:
            ident = f"doi:{doi}" if resolve_doi else f"arxiv:{arxiv_id}"
            return ReferenceVerdict(
                citation_key=entry.citation_key,
                status=VerificationStatus.FABRICATED,
                detail=f"{ident} did not resolve in any index",
                doi=doi,
                arxiv_id=arxiv_id,
                issues=["identifier resolves to no record"],
            )
        return ReferenceVerdict(
            citation_key=entry.citation_key,
            status=VerificationStatus.UNVERIFIABLE,
            detail="no DOI/arXiv id and title search inconclusive",
            doi=doi,
            arxiv_id=arxiv_id,
        )

    paper = resolution.paper
    sim = title_similarity(title, paper.title)
    cited_surname = _first_author_surname(entry)
    indexed_surname = extract_surname(paper.authors[0]) if paper.authors else None
    year_agrees = bib_year is not None and paper.year is not None and abs(bib_year - paper.year) <= 1
    author_agrees = bool(cited_surname and indexed_surname and cited_surname.lower() == indexed_surname.lower())

    # Title-only resolution (no DOI/arXiv id): a fuzzy title match above the
    # similarity floor is NOT enough to certify a reference — near-miss titles
    # (e.g. same template, different domain) routinely clear ~0.82. Require an
    # exact normalized title OR a corroborating year/author before trusting it;
    # otherwise it is unverifiable, not ok.
    if not has_identifier and sim < 1.0 and not (year_agrees or author_agrees):
        return ReferenceVerdict(
            citation_key=entry.citation_key,
            status=VerificationStatus.UNVERIFIABLE,
            detail=f"title-only match too weak to certify (similarity {sim:.2f}, no corroborating year/author)",
            doi=doi,
            arxiv_id=arxiv_id,
            resolved_via=resolution.via,
            title_similarity=sim,
        )

    issues: list[str] = []
    if title and paper.title and sim < resolver.title_match_floor:
        issues.append(f"title mismatch (similarity {sim:.2f}): cited {title!r} vs indexed {paper.title!r}")

    if bib_year is not None and paper.year is not None and abs(bib_year - paper.year) > 1:
        issues.append(f"year mismatch: cited {bib_year} vs indexed {paper.year}")

    if cited_surname and indexed_surname and cited_surname.lower() != indexed_surname.lower():
        issues.append(f"first-author mismatch: cited {cited_surname!r} vs indexed {indexed_surname!r}")

    # Anachronism can also surface from the resolved (canonical) year.
    if as_of_year is not None and paper.year is not None and paper.year > as_of_year:
        return ReferenceVerdict(
            citation_key=entry.citation_key,
            status=VerificationStatus.ANACHRONISM,
            detail=f"indexed year {paper.year} is after as-of year {as_of_year}",
            doi=doi,
            arxiv_id=arxiv_id,
            resolved_via=resolution.via,
            title_similarity=sim,
            issues=[f"future-dated record ({paper.year} > {as_of_year})"],
        )

    status = VerificationStatus.MISMATCH if issues else VerificationStatus.OK
    detail = "; ".join(issues) if issues else f"resolved via {resolution.via}"
    return ReferenceVerdict(
        citation_key=entry.citation_key,
        status=status,
        detail=detail,
        doi=doi,
        arxiv_id=arxiv_id,
        resolved_via=resolution.via,
        title_similarity=sim,
        issues=issues,
    )


def verify_database(
    db: BibDatabase,
    resolver: ReferenceResolver,
    *,
    as_of_year: int | None = None,
) -> VerificationReport:
    """Verify every entry in *db* and aggregate the verdicts."""
    verdicts = [verify_entry(entry, resolver, as_of_year=as_of_year) for entry in db]
    return VerificationReport(verdicts=verdicts, network_used=resolver.allow_network)


def verify_bibfile(
    path: Path | str,
    resolver: ReferenceResolver,
    *,
    as_of_year: int | None = None,
) -> VerificationReport:
    """Parse a ``.bib`` file and verify every entry it declares."""
    db = parse_bibfile(path)
    return verify_database(db, resolver, as_of_year=as_of_year)


def _first_author_surname(entry: BibEntry) -> str | None:
    """Return the surname of the first author in a BibTeX ``author`` field."""
    author = entry.get("author")
    if not author:
        return None
    first = re.split(r"\band\b", author, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    return extract_surname(first) if first else None
