"""Figure writers for template_sia."""

from __future__ import annotations

from pathlib import Path

from .sia_loop_diagram import write_sia_loop_topology
from .sia_metrics import write_sia_metric_progression


def write_all_figures(project_root: Path) -> list[Path]:
    """Generate all registry figures."""
    project_root = project_root.resolve()
    return [
        write_sia_metric_progression(project_root),
        write_sia_loop_topology(project_root),
    ]


__all__ = ["write_all_figures"]
