#!/usr/bin/env python3
"""Generate manuscript assets: figures for the autopoiesis paper."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.manuscript_figures import fig_coverage_by_module, generate_manuscript_figures
from src.project_paths import project_output_dirs


def main() -> None:
    dirs = project_output_dirs(PROJECT_ROOT)
    fig_dir = dirs["figures"]
    print("Generating manuscript figures...")
    generate_manuscript_figures(PROJECT_ROOT, fig_dir)
    coverage_full = dirs["data"] / "coverage_full.json"
    if coverage_full.is_file():
        fig_coverage_by_module(coverage_full, fig_dir)
    else:
        print(f"  (skipping fig_coverage_by_module — {coverage_full} not yet generated)")
    print(f"Done. Figures in {fig_dir}")


if __name__ == "__main__":
    main()
