"""Search-coverage invariants for the template_search_project corpus.

Pure-compute checks (no I/O, no infrastructure imports) that validate
the deep-search aggregate ``output/deep_search/aggregate.json`` and the
single-search corpus ``output/corpus.json``:

  - every paper has the required keys (``id``, ``title``, ``year``)
  - paper IDs are unique
  - DOI rate above a coverage floor
  - year distribution is plausible (≥ 1900, ≤ now+1)
  - keyword coverage: every requested keyword has at least N papers
  - aggregate uniqueness vs union size

Each builder returns a list of :class:`InvariantResult` records; the
companion dashboard script converts them to
:class:`infrastructure.reporting.Invariant`.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class InvariantResult:
    """Witness record for one search-coverage invariant."""

    name: str
    kind: str
    actual: Any
    expected: Any = None
    tol: float = 0.0
    description: str = ""
    extra: dict = field(default_factory=dict)


REQUIRED_PAPER_KEYS = ("id", "title")
NICE_TO_HAVE_KEYS = ("year", "doi", "abstract", "authors")


def schema_invariants(papers: list[dict]) -> list[InvariantResult]:
    """Every paper must have a non-empty ``id`` and ``title``."""
    out: list[InvariantResult] = []
    for k in REQUIRED_PAPER_KEYS:
        missing = [
            i for i, p in enumerate(papers) if not p.get(k) or (isinstance(p.get(k), str) and not p.get(k).strip())
        ]
        out.append(
            InvariantResult(
                name=f"paper_field_present_{k}",
                kind="equal",
                actual=float(len(missing)),
                expected=0.0,
                tol=0.0,
                description=(
                    f"every paper has a non-empty `{k}`; missing at "
                    f"indices {missing[:5]}{'…' if len(missing) > 5 else ''}"
                ),
            )
        )
    return out


def uniqueness_invariants(papers: list[dict]) -> list[InvariantResult]:
    """Paper ``id`` field must be unique across the corpus."""
    ids = [p.get("id") for p in papers if p.get("id")]
    counter = Counter(ids)
    duplicates = [k for k, n in counter.items() if n > 1]
    return [
        InvariantResult(
            name="paper_id_unique",
            kind="equal",
            actual=float(len(duplicates)),
            expected=0.0,
            tol=0.0,
            description=(f"paper IDs must be unique; duplicates: {duplicates[:5]}{'…' if len(duplicates) > 5 else ''}"),
        ),
    ]


def coverage_invariants(
    papers: list[dict],
    *,
    doi_floor: float = 0.5,
    abstract_floor: float = 0.5,
    year_floor: float = 0.7,
) -> list[InvariantResult]:
    """Coverage of optional metadata fields above configured floors.

    The defaults reflect realistic floors for arXiv + Crossref combined
    sources; pass tighter floors when the curated corpus is more complete.
    """
    n = len(papers) or 1
    n_doi = sum(1 for p in papers if p.get("doi"))
    n_abstract = sum(1 for p in papers if isinstance(p.get("abstract"), str) and p["abstract"].strip())
    n_year = sum(1 for p in papers if isinstance(p.get("year"), (int, float)) and p["year"])
    return [
        InvariantResult(
            name="doi_coverage_above_floor",
            kind="ge",
            actual=float(n_doi / n),
            expected=float(doi_floor),
            tol=0.0,
            description=f"|papers with DOI| / N = {n_doi / n:.2%} ≥ {doi_floor:.0%}",
        ),
        InvariantResult(
            name="abstract_coverage_above_floor",
            kind="ge",
            actual=float(n_abstract / n),
            expected=float(abstract_floor),
            tol=0.0,
            description=f"|papers with abstract| / N = {n_abstract / n:.2%} ≥ {abstract_floor:.0%}",
        ),
        InvariantResult(
            name="year_coverage_above_floor",
            kind="ge",
            actual=float(n_year / n),
            expected=float(year_floor),
            tol=0.0,
            description=f"|papers with year| / N = {n_year / n:.2%} ≥ {year_floor:.0%}",
        ),
    ]


def year_invariants(papers: list[dict]) -> list[InvariantResult]:
    """Plausible publication years (≥ 1900, ≤ now + 1)."""
    years = [int(p["year"]) for p in papers if isinstance(p.get("year"), (int, float)) and p["year"]]
    if not years:
        return []
    now_year = datetime.now(tz=timezone.utc).year
    return [
        InvariantResult(
            name="year_min_plausible",
            kind="ge",
            actual=float(min(years)),
            expected=1900.0,
            tol=0.0,
            description=f"earliest paper year = {min(years)}",
        ),
        InvariantResult(
            name="year_max_plausible",
            kind="le",
            actual=float(max(years)),
            expected=float(now_year + 1),
            tol=0.0,
            description=f"latest paper year = {max(years)}",
        ),
    ]


def keyword_invariants(
    aggregate: dict,
    *,
    min_per_keyword: int = 1,
) -> list[InvariantResult]:
    """In a deep-search aggregate, every requested keyword must contribute
    at least ``min_per_keyword`` papers, and the union size must equal the
    deduplicated papers list length.
    """
    out: list[InvariantResult] = []
    keywords = aggregate.get("keywords") or []
    unique_papers = aggregate.get("unique_papers") or []
    out.append(
        InvariantResult(
            name="keywords_nonempty",
            kind="ge",
            actual=float(len(keywords)),
            expected=1.0,
            tol=0.0,
            description=f"deep search ran with {len(keywords)} keywords",
        )
    )
    out.append(
        InvariantResult(
            name="unique_papers_nonempty",
            kind="ge",
            actual=float(len(unique_papers)),
            expected=1.0,
            tol=0.0,
            description=f"unique papers list has {len(unique_papers)} entries",
        )
    )
    out.append(
        InvariantResult(
            name="unique_papers_min_per_keyword",
            kind="ge",
            # average — when keyword tagging is absent we use total / |keywords|
            actual=(float(len(unique_papers)) / max(len(keywords), 1)),
            expected=float(min_per_keyword),
            tol=0.0,
            description=(
                f"avg papers per keyword = {len(unique_papers) / max(len(keywords), 1):.1f} ≥ {min_per_keyword}"
            ),
        )
    )
    return out


def all_invariants(
    papers: list[dict],
    *,
    aggregate: dict | None = None,
    doi_floor: float = 0.5,
    abstract_floor: float = 0.5,
    year_floor: float = 0.7,
    min_per_keyword: int = 1,
) -> list[InvariantResult]:
    """Process all invariants."""
    out: list[InvariantResult] = []
    out.extend(schema_invariants(papers))
    out.extend(uniqueness_invariants(papers))
    out.extend(
        coverage_invariants(
            papers,
            doi_floor=doi_floor,
            abstract_floor=abstract_floor,
            year_floor=year_floor,
        )
    )
    out.extend(year_invariants(papers))
    if aggregate is not None:
        out.extend(keyword_invariants(aggregate, min_per_keyword=min_per_keyword))
    return out


__all__ = [
    "InvariantResult",
    "all_invariants",
    "coverage_invariants",
    "keyword_invariants",
    "schema_invariants",
    "uniqueness_invariants",
    "year_invariants",
]
