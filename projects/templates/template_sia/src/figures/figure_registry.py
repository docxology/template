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
from typing import Any

from ..generation_records import generation_metrics, load_run_summary
from ..loop_config import load_sia_settings


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
    alt_text: str | None = None


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
        alt_text=(
            "Three labeled boxes form a directed cycle from Meta to Target to Feedback "
            "and back to Meta, depicting the harness control flow."
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
            "Generation-over-generation metric delta (Δaccuracy) for the SIA fixture replay; "
            "the flat trace confirms threshold robustness and prevents a fabricated improvement claim."
        ),
    ),
)


def figure_path(project_root: Path, spec: FigureSpec) -> Path:
    """Return output path for a registered figure."""
    return project_root / "output" / "figures" / spec.filename


def build_metric_figure_alt_texts(metrics: list[dict[str, Any]]) -> dict[str, str]:
    """Describe the metric figures from the exact rows used by their writers."""
    if not metrics:
        return {
            "fig:sia-metric-progression": (
                "An empty metric-progression chart contains no generation points, so no trend is inferred."
            ),
            "fig:sia-generation-heatmap": (
                "A placeholder panel states that no metric data are available for the generation heatmap."
            ),
            "fig:sia-improvement-delta": (
                "A placeholder panel states that at least two generations are required to calculate a metric delta."
            ),
        }

    metric_name = str(metrics[0].get("metric_name") or "metric")
    progression_values = [float(row["metric_value"]) for row in metrics if row.get("metric_value") is not None]
    heatmap_values = [float(row["metric_value"]) if row.get("metric_value") is not None else 0.0 for row in metrics]
    sample_counts = [int(row["n_samples"]) if row.get("n_samples") else 0 for row in metrics]

    if progression_values:
        progression = (
            f"A line chart plots {len(progression_values)} {metric_name} value(s), changing from "
            f"{_format_metric(progression_values[0])} to {_format_metric(progression_values[-1])}; "
            f"the observed range is {_format_metric(min(progression_values))} to "
            f"{_format_metric(max(progression_values))}."
        )
    else:
        progression = (
            "An empty metric-progression chart contains no numeric generation values, so no trend is inferred."
        )

    heatmap = (
        f"A two-row heatmap compares {metric_name} and sample count across {len(metrics)} generation(s); "
        f"metric values range from {_format_metric(min(heatmap_values))} to {_format_metric(max(heatmap_values))}, "
        f"and sample counts range from {min(sample_counts)} to {max(sample_counts)}."
    )

    if len(metrics) < 2:
        delta = "A placeholder panel states that at least two generations are required to calculate a metric delta."
    else:
        delta_values = [heatmap_values[index + 1] - heatmap_values[index] for index in range(len(heatmap_values) - 1)]
        positive = sum(value > 0 for value in delta_values)
        negative = sum(value < 0 for value in delta_values)
        zero = sum(value == 0 for value in delta_values)
        delta = (
            f"A signed bar chart shows {len(delta_values)} generation-to-generation {metric_name} change(s): "
            f"{positive} positive, {negative} negative, and {zero} unchanged; "
            f"the cumulative change is {_format_signed_metric(sum(delta_values))}."
        )

    return {
        "fig:sia-metric-progression": progression,
        "fig:sia-generation-heatmap": heatmap,
        "fig:sia-improvement-delta": delta,
    }


def _format_metric(value: float) -> str:
    return f"{value:.1%}" if abs(value) <= 1.0 else f"{value:.2f}"


def _format_signed_metric(value: float) -> str:
    return f"{value:+.1%}" if abs(value) <= 1.0 else f"{value:+.2f}"


def write_figure_registry(project_root: Path) -> Path:
    """Write ``output/figures/figure_registry.json`` from FIGURE_SPECS."""
    project_root = project_root.resolve()
    settings = load_sia_settings(project_root)
    summary = load_run_summary(project_root, run_id=settings.run_id)
    dynamic_alt_text = build_metric_figure_alt_texts(generation_metrics(summary))
    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "figure_registry.json"
    figure_records: list[dict[str, object]] = []
    payload: dict[str, object] = {
        "schema_version": "template-sia-figure-registry-v1",
        "figures": figure_records,
    }
    for spec in FIGURE_SPECS:
        alt_text = dynamic_alt_text.get(spec.figure_id, spec.alt_text)
        if not alt_text or not alt_text.strip():
            raise ValueError(f"Missing figure alt text: {spec.figure_id}")
        figure_records.append(
            {
                "label": spec.figure_id,
                "filename": spec.filename,
                "caption": spec.caption,
                "generated_by": "src.figures",
                "metadata": {"alt_text": alt_text},
            }
        )
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


__all__ = [
    "FIGURE_SPECS",
    "PALETTE",
    "FigureSpec",
    "build_metric_figure_alt_texts",
    "figure_path",
    "write_figure_registry",
]
