"""Render the registered-report exemplar figures (thin orchestrator).

All plotting and computation are imported from ``src/registered_report``; this
script only handles argument parsing and file I/O. Figures are written to
``manuscript/figures/`` so the committed manuscript can embed them directly, and
a machine-readable copy of the executed analysis is written to ``output/data/``.
Run headless from the repository root:

    MPLBACKEND=Agg uv run python \
        projects/templates/template_registered_report/scripts/generate_figures.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, cast

os.environ.setdefault("MPLBACKEND", "Agg")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from registered_report import freeze_registration, run_registered_analysis  # noqa: E402
from registered_report.figures import render_all_figures  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registration", type=Path, default=PROJECT_ROOT / "data" / "example_registration.json")
    parser.add_argument("--figures-dir", type=Path, default=PROJECT_ROOT / "manuscript" / "figures")
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "output" / "data")
    args = parser.parse_args()

    registration = cast("dict[str, Any]", json.loads(args.registration.read_text(encoding="utf-8")))
    frozen = freeze_registration(registration)
    summary = run_registered_analysis(frozen)

    figures = render_all_figures(frozen, summary, args.figures_dir)

    # manuscript/figures/ is the git-tracked canonical location; the Beamer
    # slide renderer resolves ../figures/ against output/, so mirror a
    # disposable copy to output/figures/ (sibling convention).
    import shutil

    output_figures = PROJECT_ROOT / "output" / "figures"
    output_figures.mkdir(parents=True, exist_ok=True)
    for figure_path in figures.values():
        shutil.copy2(figure_path, output_figures / figure_path.name)
        print((output_figures / figure_path.name).as_posix())

    args.data_dir.mkdir(parents=True, exist_ok=True)
    analysis_path = args.data_dir / "demo_analysis.json"
    analysis_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for path in figures.values():
        print(path.as_posix())
    print(analysis_path.as_posix())
    print(json.dumps({"p_value": summary["p_value"], "significant": summary["significant"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
