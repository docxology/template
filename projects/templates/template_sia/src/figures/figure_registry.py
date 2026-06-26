"""Registry-backed figures for template_sia.

Every public figure writer is registered here.  The ``FIGURE_SPECS`` tuple is
the single source of truth for figure ids, output filenames, and captions.
Captions mirror the canonical captions in the manuscript (``02_methodology.md``,
``03_results.md``); keep them in sync — the test suite enforces this contract.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


# ── colour palette ─────────────────────────────────────────────────────────────
# Okabe–Ito–aligned, colourblind-safe palette shared by all SIA figure writers.
PALETTE: dict[str, str] = {
    "positive": "#0f766e",  # teal — primary metric line / progress
    "positive_light": "#5eead4",  # light teal — fill / band
    "accent": "#2563eb",  # blue — secondary series
    "accent_light": "#93c5fd",  # pale blue — fills
    "warning": "#a16207",  # amber — caution markers
    "negative": "#7c2d12",  # rust — below-baseline
    "muted": "#64748b",  # slate — baselines / reference
    "rule": "#94a3b8",  # lighter slate — axis spines
    "grid": "#e2e8f0",  # near-white blue — grid lines
    "annotation": "#475569",  # dark slate — annotation text
    "ink": "#0f172a",  # near-black — titles / labels
    "box_face": "#ecfdf5",  # pale mint — diagram node fill
    "box_edge": "#0f172a",  # near-black — diagram node border
    "arrow": "#0f766e",  # teal — diagram arrows
    "row_alt": "#f1f5f9",  # very pale grey-blue — alt row heatmap
}


@dataclass(frozen=True)
class FigureSpec:
    """Minimal figure registry entry."""

    figure_id: str
    filename: str
    caption: str


# NOTE: captions here mirror the canonical captions authored inline in the
# manuscript (``manuscript/02_methodology.md``, ``manuscript/03_results.md``),
# which are the single source of truth rendered into the PDF. Keep them in sync.
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
    FigureSpec(
        figure_id="fig:sia-generation-heatmap",
        filename="sia_generation_heatmap.png",
        caption=("Per-generation metric heatmap showing accuracy and sample count across SIA generations."),
    ),
    FigureSpec(
        figure_id="fig:sia-improvement-delta",
        filename="sia_improvement_delta.png",
        caption=(
            "Generation-over-generation metric delta (Δaccuracy) for the SIA loop, "
            "illustrating the incremental improvement at each self-refinement step."
        ),
    ),
)


def figure_path(project_root: Path, spec: FigureSpec) -> Path:
    """Return output path for a registered figure."""
    return project_root / "output" / "figures" / spec.filename


def write_figure_registry(project_root: Path) -> Path:
    """Write ``output/figures/figure_registry.json`` from FIGURE_SPECS."""
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


__all__ = ["FIGURE_SPECS", "PALETTE", "FigureSpec", "figure_path", "write_figure_registry"]
