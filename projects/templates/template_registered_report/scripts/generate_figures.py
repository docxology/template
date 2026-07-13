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
sys.path.insert(0, str(PROJECT_ROOT.parents[2]))

from infrastructure.documentation.generated_figure_registry import publish_generated_figures  # noqa: E402
from registered_report import freeze_registration, run_registered_analysis  # noqa: E402
from registered_report.figures import (  # noqa: E402
    FIGURE_REGISTRY_SCHEMA,
    REGISTERED_REPORT_FIGURE_SPECS,
    render_all_figures,
)


def publish_output_figures(figures: dict[str, Path], output_figures: Path) -> list[Path]:
    """Mirror a complete real render and write its provenance registry."""
    return publish_generated_figures(
        output_figures,
        REGISTERED_REPORT_FIGURE_SPECS,
        figures.values(),
        schema_version=FIGURE_REGISTRY_SCHEMA,
    )


def generate_assets(
    registration_path: Path,
    figures_dir: Path,
    output_figures_dir: Path,
    data_dir: Path,
) -> tuple[list[Path], dict[str, Any]]:
    """Execute the registered analysis and emit figures, registry, and data."""
    registration = cast(
        "dict[str, Any]",
        json.loads(registration_path.read_text(encoding="utf-8")),
    )
    frozen = freeze_registration(registration)
    summary = run_registered_analysis(frozen)
    figures = render_all_figures(frozen, summary, figures_dir)
    published = publish_output_figures(figures, output_figures_dir)

    data_dir.mkdir(parents=True, exist_ok=True)
    analysis_path = data_dir / "demo_analysis.json"
    analysis_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return [*figures.values(), *published, analysis_path], summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registration", type=Path, default=PROJECT_ROOT / "data" / "example_registration.json")
    parser.add_argument("--figures-dir", type=Path, default=PROJECT_ROOT / "manuscript" / "figures")
    parser.add_argument("--output-figures-dir", type=Path, default=PROJECT_ROOT / "output" / "figures")
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "output" / "data")
    args = parser.parse_args()

    written, summary = generate_assets(
        args.registration,
        args.figures_dir,
        args.output_figures_dir,
        args.data_dir,
    )
    for path in written:
        print(path.as_posix())
    print(json.dumps({"p_value": summary["p_value"], "significant": summary["significant"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
