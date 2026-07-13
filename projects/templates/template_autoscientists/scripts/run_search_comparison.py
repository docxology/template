#!/usr/bin/env python3
"""Thin orchestrator: coordinated search vs single-thread baseline.

Runs the coordinated AutoScientists loop and the single-thread baseline on the
same deterministic objective under a *matched* experiment budget, then renders
their champion trajectories plus a machine-readable summary. Because coordinated
teams partition the same sequential budget (rather than adding parallel compute),
this is an honest robustness/efficiency comparison, not a speedup claim — the
summary reports both the reported metric and the noise-free clean metric. All
computation lives in ``src``; this script only orchestrates, plots, and writes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_ROOT.parents[2]
for path in (PROJECT_ROOT, PROJECT_ROOT / "src", REPO_ROOT):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from src.comparison import build_comparison_payload, build_objective, run_comparison  # noqa: E402
from src.figures import write_comparison_figure, write_figure_registry  # noqa: E402


def main() -> int:
    """CLI entry point."""
    objective = build_objective()
    coordinated, baseline = run_comparison(objective)

    figures_dir = PROJECT_ROOT / "output" / "figures"
    data_dir = PROJECT_ROOT / "output" / "data"
    figures_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    figure_path = figures_dir / "search_comparison.png"
    data_path = data_dir / "search_comparison.json"
    write_comparison_figure(coordinated, baseline, figure_path)
    registry_path = write_figure_registry(figures_dir)
    data_path.write_text(
        json.dumps(build_comparison_payload(objective, coordinated, baseline), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(figure_path)
    print(registry_path)
    print(data_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
