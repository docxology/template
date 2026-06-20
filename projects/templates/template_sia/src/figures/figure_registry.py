"""Registry-backed figures for template_sia."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FigureSpec:
    """Minimal figure registry entry."""

    figure_id: str
    filename: str
    caption: str


# NOTE: captions here mirror the canonical captions authored inline in the
# manuscript (`manuscript/02_methodology.md`, `manuscript/03_results.md`), which
# are the single source of truth rendered into the PDF. Keep them in sync.
FIGURE_SPECS: tuple[FigureSpec, ...] = (
    FigureSpec(
        figure_id="fig:sia-metric-progression",
        filename="sia_metric_progression.png",
        caption="SIA metric progression across generations.",
    ),
    FigureSpec(
        figure_id="fig:sia-loop-topology",
        filename="sia_loop_topology.png",
        caption=(
            "Meta → Target → Feedback loop topology for the SIA harness, "
            "generated programmatically by write_sia_loop_topology."
        ),
    ),
)


def figure_path(project_root: Path, spec: FigureSpec) -> Path:
    """Return output path for a registered figure."""
    return project_root / "output" / "figures" / spec.filename


def write_figure_registry(project_root: Path) -> Path:
    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "figure_registry.json"
    payload = {
        "schema_version": "template-sia-figure-registry-v1",
        "figures": [
            {
                "label": spec.figure_id,
                "filename": spec.filename,
                "caption": spec.caption,
                "generated_by": "src.figures",
            }
            for spec in FIGURE_SPECS
        ],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


__all__ = ["FIGURE_SPECS", "FigureSpec", "figure_path", "write_figure_registry"]
