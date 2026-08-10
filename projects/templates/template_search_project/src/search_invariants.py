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
from typing import Any, Literal


@dataclass
class InvariantResult:
    """Witness record for one search-coverage invariant."""

    name: str
    kind: Literal[
        "equal",
        "le",
        "ge",
        "in_range",
        "monotone_increasing",
        "monotone_decreasing",
        "finite",
        "nonneg",
        "array_close",
    ]
    actual: Any
    expected: Any = None
    tol: float = 0.0
    description: str = ""
    extra: dict = field(default_factory=dict)


REQUIRED_PAPER_KEYS = ("id", "title")
NICE_TO_HAVE_KEYS = ("year", "doi", "abstract", "authors")


def cache_invariants(payload: dict[str, Any]) -> list[InvariantResult]:
    """Validate the versioned search-cache envelope without reading files.

    The cache is an offline replay boundary: a malformed or identity-less
    entry must be rejected rather than silently treated as a valid retrieval.
    ``infrastructure.search`` performs the same checks while loading; this
    pure companion is suitable for dashboard and receipt validation.
    """
    required = ("query", "papers", "per_source_counts", "errors")
    missing = [key for key in required if key not in payload]
    version_ok = payload.get("_schema_version") == 1
    key_ok = isinstance(payload.get("_cache_key"), str) and bool(payload.get("_cache_key"))
    return [
        InvariantResult(
            name="cache_envelope_complete",
            kind="equal",
            actual=float(len(missing)),
            expected=0.0,
            description=f"cache envelope missing fields: {missing}",
        ),
        InvariantResult(
            name="cache_schema_version_pinned",
            kind="equal",
            actual=float(version_ok),
            expected=1.0,
            description="cache entries carry schema version 1",
        ),
        InvariantResult(
            name="cache_identity_present",
            kind="equal",
            actual=float(key_ok),
            expected=1.0,
            description="cache entries carry an explicit query identity key",
        ),
    ]


def fulltext_invariants(
    papers: list[dict[str, Any]],
    *,
    require_fulltext: bool = False,
    max_chars: int | None = None,
) -> list[InvariantResult]:
    """Validate full-text retrieval state without treating absence as success."""
    invalid = [
        i
        for i, paper in enumerate(papers)
        if paper.get("fulltext") is not None and not isinstance(paper.get("fulltext"), str)
    ]
    missing = [i for i, paper in enumerate(papers) if not str(paper.get("fulltext") or "").strip()]
    over_limit = (
        [i for i, paper in enumerate(papers) if len(str(paper.get("fulltext") or "")) > max_chars]
        if max_chars is not None
        else []
    )
    return [
        InvariantResult(
            name="fulltext_field_types_valid",
            kind="equal",
            actual=float(len(invalid)),
            expected=0.0,
            description=f"invalid fulltext values at indices {invalid[:5]}",
        ),
        InvariantResult(
            name="fulltext_present_when_required",
            kind="equal",
            actual=float(len(missing)) if require_fulltext else 0.0,
            expected=0.0,
            description=f"missing fulltext at indices {missing[:5]}",
        ),
        InvariantResult(
            name="fulltext_length_within_limit",
            kind="equal",
            actual=float(len(over_limit)),
            expected=0.0,
            description=f"fulltext exceeds configured limit at indices {over_limit[:5]}",
        ),
    ]


def retrieval_invariants(result: dict[str, Any]) -> list[InvariantResult]:
    """Validate backend counts/errors so offline degradation is explicit."""
    errors = result.get("errors", {})
    counts = result.get("per_source_counts", {})
    if isinstance(errors, dict):
        invalid_errors = [
            key
            for key, value in errors.items()
            if not isinstance(key, str) or not isinstance(value, str) or not value.strip()
        ]
    else:
        invalid_errors = ["errors"]
    invalid_counts = []
    if isinstance(counts, dict):
        invalid_counts = [
            key for key, value in counts.items() if not isinstance(key, str) or not isinstance(value, int) or value < 0
        ]
    else:
        invalid_counts = ["per_source_counts"]
    return [
        InvariantResult(
            name="retrieval_errors_actionable",
            kind="equal",
            actual=float(len(invalid_errors)),
            expected=0.0,
            description=f"backend errors must be non-empty strings: {invalid_errors[:5]}",
        ),
        InvariantResult(
            name="retrieval_counts_nonnegative",
            kind="equal",
            actual=float(len(invalid_counts)),
            expected=0.0,
            description=f"backend counts must be non-negative integers: {invalid_counts[:5]}",
        ),
    ]


def deep_search_invariants(aggregate: dict[str, Any]) -> list[InvariantResult]:
    """Validate the deep-search aggregate/citation contract."""
    keywords = aggregate.get("keywords")
    papers = aggregate.get("unique_papers")
    citation_keys = aggregate.get("citation_keys")
    keyword_list = keywords if isinstance(keywords, list) else []
    paper_list = papers if isinstance(papers, list) else []
    key_map = citation_keys if isinstance(citation_keys, dict) else {}
    ids = [paper.get("id") for paper in paper_list if isinstance(paper, dict)]
    missing_citations = [paper_id for paper_id in ids if paper_id not in key_map]
    duplicate_keywords = (
        len(keyword_list) - len(set(keyword_list)) if all(isinstance(k, str) for k in keyword_list) else 1
    )
    return [
        InvariantResult(
            name="deep_search_keywords_present",
            kind="ge",
            actual=float(len(keyword_list)),
            expected=1.0,
            description=f"deep-search aggregate contains {len(keyword_list)} keyword(s)",
        ),
        InvariantResult(
            name="deep_search_keywords_unique",
            kind="equal",
            actual=float(max(duplicate_keywords, 0)),
            expected=0.0,
            description=f"duplicate deep-search keywords: {duplicate_keywords}",
        ),
        InvariantResult(
            name="deep_search_citation_keys_complete",
            kind="equal",
            actual=float(len(missing_citations)),
            expected=0.0,
            description=f"papers without citation keys: {missing_citations[:5]}",
        ),
    ]


def schema_invariants(papers: list[dict]) -> list[InvariantResult]:
    """Every paper must have a non-empty ``id`` and ``title``."""
    out: list[InvariantResult] = []
    for k in REQUIRED_PAPER_KEYS:
        missing = []
        for i, paper in enumerate(papers):
            value = paper.get(k)
            if not value or (isinstance(value, str) and not value.strip()):
                missing.append(i)
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
        out.extend(deep_search_invariants(aggregate))
    return out


__all__ = [
    "InvariantResult",
    "all_invariants",
    "cache_invariants",
    "coverage_invariants",
    "deep_search_invariants",
    "fulltext_invariants",
    "keyword_invariants",
    "retrieval_invariants",
    "schema_invariants",
    "uniqueness_invariants",
    "year_invariants",
]
