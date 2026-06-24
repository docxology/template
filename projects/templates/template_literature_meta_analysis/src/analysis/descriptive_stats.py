"""Deterministic descriptive statistics for literature meta-analysis corpora."""

from __future__ import annotations

import json
import logging
import statistics
from collections import Counter
from pathlib import Path
from typing import Optional

import numpy as np

from literature.models import Paper

logger = logging.getLogger(__name__)

_DEFAULT_BUCKETS = [0, 1, 10, 50, 100, 500]


def _percentage(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return (numerator / denominator) * 100.0


def _resolve_buckets(buckets: Optional[list[int]]) -> list[int]:
    if buckets is None:
        return list(_DEFAULT_BUCKETS)

    if not buckets:
        raise ValueError("buckets must contain at least one edge")

    resolved = list(buckets)
    for index in range(1, len(resolved)):
        if resolved[index] <= resolved[index - 1]:
            raise ValueError("buckets must be strictly increasing")
    return resolved


def _bucket_labels(bucket_edges: list[int]) -> list[str]:
    labels: list[str] = []
    for index, start in enumerate(bucket_edges):
        if index == len(bucket_edges) - 1:
            labels.append(f"{start}+")
            continue

        stop = bucket_edges[index + 1] - 1
        if start == stop:
            labels.append(str(start))
        else:
            labels.append(f"{start}-{stop}")
    return labels


def descriptive_stats(papers: list[Paper], top_venues: int = 10) -> dict:
    """Compute descriptive bibliometric statistics for a corpus.

    Args:
        papers: Corpus papers to summarize.
        top_venues: Maximum number of venue counts to return.

    Returns:
        Dictionary containing corpus size, year/venue distributions, author
        productivity summaries, citation summaries, and metadata coverage rates.
    """
    total = len(papers)

    years = [paper.year for paper in papers if paper.year is not None]
    year_counts_raw = Counter(years)
    counts_by_year = {year: year_counts_raw[year] for year in sorted(year_counts_raw)}

    venue_counts_raw = Counter(paper.venue for paper in papers if paper.venue is not None)
    sorted_venues = sorted(
        venue_counts_raw.items(),
        key=lambda item: (-item[1], item[0]),
    )
    venue_limit = max(top_venues, 0)
    counts_by_venue = {venue: count for venue, count in sorted_venues[:venue_limit]}

    author_counts: Counter[str] = Counter()
    for paper in papers:
        seen_names: set[str] = set()
        for author in paper.authors:
            if author.name not in seen_names:
                author_counts[author.name] += 1
                seen_names.add(author.name)

    author_publication_counts = sorted(author_counts.values())
    citation_counts = [paper.citation_count for paper in papers]
    open_access_flags = [paper.is_open_access for paper in papers if paper.is_open_access is not None]

    return {
        "total": total,
        "year_min": min(years) if years else None,
        "year_max": max(years) if years else None,
        "counts_by_year": counts_by_year,
        "counts_by_venue": counts_by_venue,
        "unique_authors": len(author_counts),
        "papers_per_author_mean": (
            float(statistics.mean(author_publication_counts)) if author_publication_counts else 0.0
        ),
        "papers_per_author_median": (
            float(statistics.median(author_publication_counts)) if author_publication_counts else 0.0
        ),
        "citation_count_mean": (float(statistics.mean(citation_counts)) if citation_counts else 0.0),
        "citation_count_median": (float(statistics.median(citation_counts)) if citation_counts else 0.0),
        "citation_count_max": max(citation_counts) if citation_counts else 0,
        "citation_count_total": sum(citation_counts),
        "pct_open_access": _percentage(
            sum(1 for is_open_access in open_access_flags if is_open_access),
            len(open_access_flags),
        ),
        "pct_with_abstract": _percentage(
            sum(1 for paper in papers if paper.abstract.strip()),
            total,
        ),
        "pct_with_doi": _percentage(sum(1 for paper in papers if paper.doi), total),
    }


def citation_distribution(
    papers: list[Paper],
    *,
    buckets: Optional[list[int]] = None,
) -> dict:
    """Summarize citation-count dispersion with a histogram and Gini coefficient.

    Buckets are defined by inclusive lower bounds. For edges ``[0, 1, 10]``, the
    resulting labels are ``"0"``, ``"1-9"``, and ``"10+"``. A paper with count
    ``x`` is placed into the first bucket whose next edge is greater than ``x``;
    counts greater than or equal to the final edge go into the final ``"+"`` bucket.

    Args:
        papers: Corpus papers whose ``citation_count`` values will be summarized.
        buckets: Optional strictly increasing bucket edges. When omitted, the
            default edges ``[0, 1, 10, 50, 100, 500]`` are used.

    Returns:
        Dictionary containing the citation histogram, Gini coefficient, paper
        count, and total citations.
    """
    bucket_edges = _resolve_buckets(buckets)
    labels = _bucket_labels(bucket_edges)
    histogram = {label: 0 for label in labels}
    citation_counts = [paper.citation_count for paper in papers]

    for citation_count in citation_counts:
        bucket_index = len(bucket_edges) - 1
        for index in range(len(bucket_edges) - 1):
            if citation_count < bucket_edges[index + 1]:
                bucket_index = index
                break
        histogram[labels[bucket_index]] += 1

    values = np.array(citation_counts, dtype=float)
    if len(values) == 0:
        gini = 0.0
    else:
        mean = float(values.mean())
        if mean == 0.0:
            gini = 0.0
        else:
            pairwise_differences = np.abs(values[:, None] - values[None, :])
            gini = float(pairwise_differences.sum() / (2 * (len(values) ** 2) * mean))

    return {
        "histogram": histogram,
        "gini": gini,
        "n": len(citation_counts),
        "total_citations": sum(citation_counts),
    }


def author_productivity(papers: list[Paper], top_k: int = 20) -> list[tuple[str, int]]:
    """Rank authors by the number of papers they appear on.

    Args:
        papers: Corpus papers to inspect.
        top_k: Maximum number of ranked authors to return.

    Returns:
        List of ``(author_name, paper_count)`` tuples sorted by count descending
        and author name ascending.
    """
    counts: Counter[str] = Counter()
    for paper in papers:
        seen_names: set[str] = set()
        for author in paper.authors:
            if author.name not in seen_names:
                counts[author.name] += 1
                seen_names.add(author.name)

    sorted_counts = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return sorted_counts[: max(top_k, 0)]


def build_meta_report(papers: list[Paper], *, extras: Optional[dict] = None) -> dict:
    """Build a JSON-serializable meta-analysis report artifact.

    Core sections are populated first, then ``extras`` is shallow-merged on top
    without mutating the caller's dictionary. As a result, ``extras`` can
    override the default ``generated`` provenance block when explicitly provided.

    Args:
        papers: Corpus papers to summarize.
        extras: Optional top-level keys to merge into the report.

    Returns:
        Deterministic report dictionary ready for JSON serialization.
    """
    report = {
        "generated": {
            "total_papers": len(papers),
            "schema_version": "1.0",
            "generator": "descriptive_stats.build_meta_report",
        },
        "descriptive_stats": descriptive_stats(papers),
        "citation_distribution": citation_distribution(papers),
        "author_productivity": [[name, count] for name, count in author_productivity(papers)],
    }

    if extras is not None:
        report.update(dict(extras))

    return report


def save_meta_report(report: dict, path: Path) -> Path:
    """Persist a meta-analysis report as pretty JSON.

    Args:
        report: Report dictionary to serialize.
        path: Destination JSON path.

    Returns:
        The written path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    logger.info("Saved meta-analysis report to %s", path)
    return path
