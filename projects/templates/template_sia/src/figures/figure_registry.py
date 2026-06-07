"""Registry-backed figures for template_sia."""

from __future__ import annotations

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


__all__ = ["FIGURE_SPECS", "FigureSpec", "figure_path"]
