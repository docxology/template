#!/usr/bin/env python3
"""Generate manuscript assets: figures for the autopoiesis paper."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT.parents[2]))

from infrastructure.documentation.generated_figure_registry import write_generated_figure_registry
from src.manuscript_figures import (
    FIGURE_REGISTRY_SCHEMA,
    MANUSCRIPT_FIGURE_SPECS,
    fig_coverage_by_module,
    generate_manuscript_figures,
)
from src.project_paths import project_output_dirs


def generate_assets(
    project_root: Path = PROJECT_ROOT,
    *,
    figures_dir: Path | None = None,
    coverage_path: Path | None = None,
) -> list[Path]:
    """Generate every referenced figure and its fail-closed registry."""
    root = Path(project_root)
    dirs = project_output_dirs(root)
    destination = figures_dir or dirs["figures"]
    destination.mkdir(parents=True, exist_ok=True)
    coverage = coverage_path or dirs["data"] / "coverage_full.json"
    if not coverage.is_file():
        raise FileNotFoundError(f"required per-module coverage input not found: {coverage}")

    written: list[Path] = generate_manuscript_figures(root, destination)
    written.append(fig_coverage_by_module(coverage, destination))
    registry = write_generated_figure_registry(
        destination / "figure_registry.json",
        MANUSCRIPT_FIGURE_SPECS,
        written,
        schema_version=FIGURE_REGISTRY_SCHEMA,
    )
    written.append(registry)
    return written


def main() -> None:
    """CLI entry point."""
    print("Generating manuscript figures...")
    written = generate_assets()
    for path in written:
        print(path)
    print(f"Done. Figures in {written[-1].parent}")


if __name__ == "__main__":
    main()
