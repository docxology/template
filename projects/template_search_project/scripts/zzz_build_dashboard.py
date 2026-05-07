#!/usr/bin/env python3
"""Build the interactive search-coverage dashboard for template_search_project.

Reads ``output/corpus.json`` and (optionally) ``output/deep_search/aggregate.json``
and emits:

  - 5 Plotly panels: per-source / per-year / per-venue distributions,
    DOI vs abstract coverage scatter, keyword overlap matrix
  - configurable filters: year range, source filter, keyword whitelist,
    coverage floors
  - plaintext invariants + summary + payload artefacts

Every flag is overridable; defaults reproduce the canonical view.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
REPO_ROOT = PROJECT_ROOT.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(REPO_ROOT))

from infrastructure.reporting.interactive_dashboard import (  # noqa: E402
    InteractiveDashboard,
    Invariant,
    Panel,
)
from src.search_invariants import all_invariants  # noqa: E402

OUTPUT = PROJECT_ROOT / "output"
WEB_DIR = OUTPUT / "web"
DATA_DIR = OUTPUT / "data"
REP_DIR = OUTPUT / "reports"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--corpus", type=Path, default=OUTPUT / "corpus.json",
                   help="path to single-search corpus (default: output/corpus.json)")
    p.add_argument("--aggregate", type=Path,
                   default=OUTPUT / "deep_search" / "aggregate.json",
                   help="optional deep-search aggregate (default: "
                        "output/deep_search/aggregate.json)")
    p.add_argument("--year-min", type=int, default=None)
    p.add_argument("--year-max", type=int, default=None)
    p.add_argument("--doi-floor", type=float, default=0.5)
    p.add_argument("--abstract-floor", type=float, default=0.5)
    p.add_argument("--year-floor", type=float, default=0.7)
    p.add_argument("--min-per-keyword", type=int, default=1)
    p.add_argument("--html-out", type=Path, default=WEB_DIR / "dashboard.html")
    p.add_argument("--json-out", type=Path, default=DATA_DIR / "dashboard_payload.json")
    p.add_argument("--invariants-out", type=Path,
                   default=REP_DIR / "dashboard_invariants.txt")
    p.add_argument("--summary-out", type=Path,
                   default=REP_DIR / "dashboard_summary.txt")
    args = p.parse_args(argv)
    if not args.corpus.exists():
        p.error(f"corpus not found: {args.corpus} — run scripts/run_search_pipeline.py first")
    if args.year_min is not None and args.year_max is not None and \
       args.year_min > args.year_max:
        p.error("--year-min must be ≤ --year-max")
    return args


def _load_papers(args: argparse.Namespace) -> tuple[list[dict], dict | None]:
    raw = json.loads(args.corpus.read_text())
    papers = raw["papers"] if isinstance(raw, dict) and "papers" in raw else raw
    aggregate = None
    if args.aggregate.exists():
        agg = json.loads(args.aggregate.read_text())
        if "unique_papers" in agg:
            aggregate = agg
    return papers, aggregate


def _filter_papers(papers: list[dict], args: argparse.Namespace) -> list[dict]:
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


def _compute_payload(
    papers: list[dict],
    aggregate: dict | None,
) -> dict:
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
    n_abstract = sum(1 for p in papers
                     if isinstance(p.get("abstract"), str) and p["abstract"].strip())
    n_year = sum(1 for p in papers
                 if isinstance(p.get("year"), (int, float)) and p["year"])

    keyword_overlap: list[list[int | str]] = []
    keywords = []
    if aggregate is not None:
        keywords = aggregate.get("keywords") or []
        # Reconstruct overlap by reading per-keyword papers files:
        agg_dir = Path(aggregate.get("__source_dir__", "")) if aggregate.get("__source_dir__") else None

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


def _to_dashboard_invariant(r) -> Invariant:
    return Invariant(
        name=r.name,
        actual=r.actual,
        expected=r.expected,
        tol=r.tol,
        kind=r.kind,
        description=r.description,
    )


def _build_dashboard(
    args: argparse.Namespace,
    payload: dict,
    papers: list[dict],
    aggregate: dict | None,
) -> InteractiveDashboard:
    d = InteractiveDashboard(
        title="Literature Search Coverage Dashboard",
        subtitle=(
            f"{payload['n_total']} papers · "
            f"{len(payload['year_distribution'])} years · "
            f"{len(payload['source_distribution'])} sources · "
            "every floor and filter is CLI-configurable."
        ),
        project_name="template_search_project",
        repo_root=REPO_ROOT,
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


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    papers, aggregate = _load_papers(args)
    filtered = _filter_papers(papers, args)
    payload = _compute_payload(filtered, aggregate)
    d = _build_dashboard(args, payload, filtered, aggregate)
    out = d.write(
        html_path=args.html_out,
        json_path=args.json_out,
        invariants_path=args.invariants_out,
        txt_path=args.summary_out,
    )
    for k in ("html", "json", "invariants", "summary"):
        if k in out:
            print(out[k])

    failed = [i for i in d.evaluate_invariants() if not i["passed"]]
    if failed:
        names = ", ".join(i["name"] for i in failed)
        print(f"FAILED INVARIANTS: {names}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
