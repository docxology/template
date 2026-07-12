#!/usr/bin/env python3
"""Thin orchestrator: per-mechanism ablation of the coordination loop.

Reproduces the paper's "remove one component" study. Starting from the full
coordinated configuration, each mechanism (confirmation, dead-end registry,
effect-size ranking, stagnation reorganization) is switched off in turn and the
resulting final champion metric is compared against the full configuration. All
computation lives in ``src``; this script only orchestrates and writes outputs.
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

from src.ablation import DEFAULT_BUDGET, build_ablation_payload, run_ablations  # noqa: E402
from src.figures import write_ablation_figure, write_efficiency_figure, write_figure_registry  # noqa: E402


def main() -> int:
    """CLI entry point."""
    rows = run_ablations()

    figures_dir = PROJECT_ROOT / "output" / "figures"
    data_dir = PROJECT_ROOT / "output" / "data"
    figures_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    figure_path = figures_dir / "ablation.png"
    efficiency_path = figures_dir / "ablation_efficiency.png"
    data_path = data_dir / "ablation.json"
    write_ablation_figure(rows, figure_path)
    write_efficiency_figure(rows, efficiency_path)
    registry_path = write_figure_registry(figures_dir)
    data_path.write_text(
        json.dumps(build_ablation_payload(rows, budget=DEFAULT_BUDGET), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(figure_path)
    print(efficiency_path)
    print(registry_path)
    print(data_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
