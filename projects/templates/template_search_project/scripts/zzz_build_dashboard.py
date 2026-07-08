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
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

THIS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
# PROJECT_ROOT is projects/templates/<name>/; repo root is three levels above it.
REPO_ROOT = PROJECT_ROOT.parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(REPO_ROOT))

from src.dashboard import (  # noqa: E402
    build_dashboard,
    compute_payload,
    filter_papers,
    load_papers,
)

OUTPUT = PROJECT_ROOT / "output"
WEB_DIR = OUTPUT / "web"
DATA_DIR = OUTPUT / "data"
REP_DIR = OUTPUT / "reports"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--corpus",
        type=Path,
        default=OUTPUT / "corpus.json",
        help="path to single-search corpus (default: output/corpus.json)",
    )
    p.add_argument(
        "--aggregate",
        type=Path,
        default=OUTPUT / "deep_search" / "aggregate.json",
        help="optional deep-search aggregate (default: output/deep_search/aggregate.json)",
    )
    p.add_argument("--year-min", type=int, default=None)
    p.add_argument("--year-max", type=int, default=None)
    p.add_argument("--doi-floor", type=float, default=0.5)
    p.add_argument("--abstract-floor", type=float, default=0.5)
    p.add_argument("--year-floor", type=float, default=0.7)
    p.add_argument("--min-per-keyword", type=int, default=1)
    p.add_argument("--html-out", type=Path, default=WEB_DIR / "dashboard.html")
    p.add_argument("--json-out", type=Path, default=DATA_DIR / "dashboard_payload.json")
    p.add_argument("--invariants-out", type=Path, default=REP_DIR / "dashboard_invariants.txt")
    p.add_argument("--summary-out", type=Path, default=REP_DIR / "dashboard_summary.txt")
    args = p.parse_args(argv)
    if not args.corpus.exists():
        p.error(f"corpus not found: {args.corpus} — run scripts/run_search_pipeline.py first")
    if args.year_min is not None and args.year_max is not None and args.year_min > args.year_max:
        p.error("--year-min must be ≤ --year-max")
    return args


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    args = _parse_args(argv)
    papers, aggregate = load_papers(args)
    filtered = filter_papers(papers, args)
    payload = compute_payload(filtered, aggregate)
    d = build_dashboard(args, payload, filtered, aggregate, repo_root=REPO_ROOT)
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
