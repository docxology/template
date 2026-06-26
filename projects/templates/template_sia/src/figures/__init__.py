"""Figure writers for template_sia — publication-quality visualizations.

Public API
----------
``write_all_figures(project_root)``
    Generate every registered figure and the ``figure_registry.json`` manifest.
    Returns a list of output ``Path`` objects (PNGs + JSON).

Individual writers (called by ``write_all_figures`` and exposed for direct use):

``write_sia_metric_progression``
    Line plot of accuracy (or primary metric) vs generation, with baseline
    reference line, per-point annotations, and improvement-range shading.

``write_sia_loop_topology``
    Box-and-arrow diagram of the Meta → Target → Feedback three-agent cycle,
    with role subtitles and generation-counter annotation.

``write_sia_generation_heatmap``
    Two-row heatmap: accuracy and (normalised) sample count across generations.
    Useful for comparing runs at a glance.

``write_sia_improvement_delta``
    Signed bar chart of generation-over-generation Δaccuracy with a secondary
    cumulative-gain overlay — communicates the incremental self-improvement signal.

All writers are headless (``MPLBACKEND=Agg``), produce PNG output under
``output/figures/``, and emit deterministic bytes when called with the same
run data (metadata fields pinned to ``None``).
"""

from __future__ import annotations

from pathlib import Path

from .figure_registry import write_figure_registry
from .sia_generation_heatmap import write_sia_generation_heatmap
from .sia_improvement_delta import write_sia_improvement_delta
from .sia_loop_diagram import write_sia_loop_topology
from .sia_metrics import write_sia_metric_progression


def write_all_figures(project_root: Path) -> list[Path]:
    """Generate all registered SIA figures and the figure-registry manifest.

    Calls every individual writer in canonical order, then writes the JSON
    figure registry.  All outputs land under ``<project_root>/output/figures/``.

    Args:
        project_root: Absolute or relative path to the project root directory.

    Returns:
        List of output ``Path`` objects — PNG files first, then the JSON
        registry at the end.
    """
    project_root = project_root.resolve()
    paths: list[Path] = [
        write_sia_metric_progression(project_root),
        write_sia_loop_topology(project_root),
        write_sia_generation_heatmap(project_root),
        write_sia_improvement_delta(project_root),
    ]
    paths.append(write_figure_registry(project_root))
    return paths


__all__ = [
    "write_all_figures",
    "write_figure_registry",
    "write_sia_generation_heatmap",
    "write_sia_improvement_delta",
    "write_sia_loop_topology",
    "write_sia_metric_progression",
]
