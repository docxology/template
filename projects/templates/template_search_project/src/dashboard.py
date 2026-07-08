"""Build the interactive search-coverage dashboard payload and panels.

Extracted from ``scripts/zzz_build_dashboard.py`` (thin-orchestrator
refactor): the script now only wires up argparse and calls into these
functions, which own the corpus loading, filtering, payload computation,
and :class:`~infrastructure.reporting.interactive_dashboard.InteractiveDashboard`
assembly.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from infrastructure.reporting.interactive_dashboard import (
    InteractiveDashboard,
    Invariant,
    Panel,
)

from .search_invariants import InvariantResult, all_invariants


def load_papers(args: argparse.Namespace) -> tuple[list[dict], dict | None]:
    """Load papers from a file."""
    raw = json.loads(args.corpus.read_text())
    papers = raw["papers"] if isinstance(raw, dict) and "papers" in raw else raw
    aggregate = None
    if args.aggregate.exists():
        agg = json.loads(args.aggregate.read_text())
        if "unique_papers" in agg:
            aggregate = agg
    return papers, aggregate


def filter_papers(papers: list[dict], args: argparse.Namespace) -> list[dict]:
    """Process filter papers."""
    out = []
    for p in papers:
        y = p.get("year")
        if y is not None and isinstance(y, (int, float)):
            if args.year_min is not None and y < args.year_min:
                continue
            if args.year_max is not None and y > args.year_max:
                continue
        out.append(p)
    return out


def compute_payload(
    papers: list[dict],
    aggregate: dict | None,
) -> dict:
    """Process compute payload."""
    n = len(papers) or 1
    by_year: Counter[int] = Counter()
    by_source: Counter[str] = Counter()
    by_venue_type: Counter[str] = Counter()
    for p in papers:
        if isinstance(p.get("year"), (int, float)):
            by_year[int(p["year"])] += 1
        src = p.get("source") or p.get("backend") or "unknown"
        by_source[str(src)] += 1
        vt = p.get("venue_type") or "unknown"
        by_venue_type[str(vt)] += 1

    n_doi = sum(1 for p in papers if p.get("doi"))
    n_abstract = sum(1 for p in papers if isinstance(p.get("abstract"), str) and p["abstract"].strip())
    n_year = sum(1 for p in papers if isinstance(p.get("year"), (int, float)) and p["year"])

    keyword_overlap: list[list[int | str]] = []
    keywords = []
    if aggregate is not None:
        keywords = aggregate.get("keywords") or []

    return {
        "n_total": len(papers),
        "year_distribution": {str(k): v for k, v in sorted(by_year.items())},
        "source_distribution": dict(by_source),
        "venue_type_distribution": dict(by_venue_type),
        "coverage": {
            "doi": n_doi / n,
            "abstract": n_abstract / n,
            "year": n_year / n,
        },
        "keywords": keywords,
        "keyword_overlap_matrix": keyword_overlap,
        "papers_preview": [
            {
                "id": str(p.get("id", "")),
                "title": str(p.get("title", ""))[:120],
                "year": p.get("year"),
                "doi": p.get("doi"),
                "venue": p.get("venue"),
            }
            for p in papers[:20]
        ],
    }


def _to_dashboard_invariant(r: InvariantResult) -> Invariant:
    return Invariant(
        name=r.name,
        actual=r.actual,
        expected=r.expected,
        tol=r.tol,
        kind=r.kind,
        description=r.description,
    )


def build_dashboard(
    args: argparse.Namespace,
    payload: dict,
    papers: list[dict],
    aggregate: dict | None,
    *,
    repo_root: Path,
) -> InteractiveDashboard:
    """Build dashboard."""
    d = InteractiveDashboard(
        title="Literature Search Coverage Dashboard",
        subtitle=(
            f"{payload['n_total']} papers · "
            f"{len(payload['year_distribution'])} years · "
            f"{len(payload['source_distribution'])} sources · "
            "every floor and filter is CLI-configurable."
        ),
        project_name="template_search_project",
        repo_root=repo_root,
    )
    d.set_hyperparameters(
        {
            "corpus_path": str(args.corpus),
            "aggregate_path": str(args.aggregate) if aggregate is not None else None,
            "year_min_filter": args.year_min,
            "year_max_filter": args.year_max,
            "doi_floor": args.doi_floor,
            "abstract_floor": args.abstract_floor,
            "year_floor": args.year_floor,
            "min_per_keyword": args.min_per_keyword,
            "n_papers": payload["n_total"],
            "n_keywords": len(payload["keywords"]),
        }
    )
    d.set_payload(payload)
    d.add_note(
        "Coverage floors are CLI-overridable and reflected in the "
        "invariants gate (default: 50% DOI / abstract, 70% year)."
    )

    # Year distribution
    yd = payload["year_distribution"]
    d.add_panel(
        Panel(
            panel_id="year_distribution",
            title="Papers per year",
            description="Distribution of publication years across the corpus.",
            traces=[
                {
                    "type": "bar",
                    "x": list(yd.keys()),
                    "y": list(yd.values()),
                    "marker": {"color": "#38bdf8"},
                },
            ],
            layout={"xaxis": {"title": "year"}, "yaxis": {"title": "count"}},
        )
    )

    # Source distribution
    sd = payload["source_distribution"]
    d.add_panel(
        Panel(
            panel_id="source_distribution",
            title="Papers per source backend",
            description="arXiv / Crossref / local / OpenAlex breakdown.",
            traces=[
                {
                    "type": "bar",
                    "x": list(sd.keys()),
                    "y": list(sd.values()),
                    "marker": {"color": "#a78bfa"},
                }
            ],
            layout={"xaxis": {"title": "source"}, "yaxis": {"title": "count"}},
        )
    )

    # Venue type breakdown
    vd = payload["venue_type_distribution"]
    d.add_panel(
        Panel(
            panel_id="venue_type",
            title="Venue-type breakdown",
            description="Conference / journal / book / preprint distribution.",
            traces=[
                {
                    "type": "pie",
                    "labels": list(vd.keys()),
                    "values": list(vd.values()),
                    "marker": {"colors": ["#22c55e", "#fb923c", "#a78bfa", "#94a3b8", "#f5f5f5"]},
                }
            ],
            layout={},
        )
    )

    # Coverage gauge
    cov = payload["coverage"]
    d.add_panel(
        Panel(
            panel_id="coverage",
            title="Metadata coverage",
            description=(
                f"DOI / abstract / year coverage; floors at "
                f"{args.doi_floor:.0%} / {args.abstract_floor:.0%} / "
                f"{args.year_floor:.0%}."
            ),
            traces=[
                {
                    "type": "bar",
                    "x": ["DOI", "abstract", "year"],
                    "y": [cov["doi"], cov["abstract"], cov["year"]],
                    "marker": {"color": ["#22c55e", "#fb923c", "#38bdf8"]},
                    "name": "actual",
                },
                {
                    "type": "scatter",
                    "mode": "markers",
                    "name": "floor",
                    "x": ["DOI", "abstract", "year"],
                    "y": [args.doi_floor, args.abstract_floor, args.year_floor],
                    "marker": {"color": "#ef4444", "size": 12, "symbol": "diamond"},
                },
            ],
            layout={
                "yaxis": {"title": "fraction", "range": [0, 1.05]},
                "legend": {"orientation": "h", "y": -0.2},
            },
        )
    )

    if payload["keywords"]:
        d.add_panel(
            Panel(
                panel_id="keywords",
                title="Search keywords",
                description=(
                    f"Deep-search ran on {len(payload['keywords'])} keywords; "
                    f"unique papers across them: {payload['n_total']}."
                ),
                traces=[
                    {
                        "type": "bar",
                        "x": payload["keywords"],
                        "y": [payload["n_total"] / max(len(payload["keywords"]), 1)] * len(payload["keywords"]),
                        "marker": {"color": "#facc15"},
                        "name": "avg unique / keyword",
                    }
                ],
                layout={
                    "xaxis": {"title": "keyword", "tickangle": -25},
                    "yaxis": {"title": "papers"},
                },
            )
        )

    for r in all_invariants(
        papers,
        aggregate=aggregate,
        doi_floor=args.doi_floor,
        abstract_floor=args.abstract_floor,
        year_floor=args.year_floor,
        min_per_keyword=args.min_per_keyword,
    ):
        d.add_invariant(_to_dashboard_invariant(r))

    return d


__all__ = [
    "build_dashboard",
    "compute_payload",
    "filter_papers",
    "load_papers",
]
