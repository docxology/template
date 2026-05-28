"""Sheaf coverage heatmap data assembly."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from manuscript.sheaf.report import CoverageConfig, load_coverage_config


@dataclass(frozen=True)
class HeatmapPayload:
    track_ids: list[str]
    y_labels: list[str]
    grid: list[list[float]]
    group_boundaries: list[float]
    cfg: CoverageConfig
    sections: list[dict[str, Any]]


def coverage_heatmap_payload(project_root: Path) -> HeatmapPayload | None:
    root = project_root.resolve()
    matrix_path = root / "output" / "data" / "sheaf_coverage_matrix.json"
    if not matrix_path.is_file():
        return None
    from manuscript.sheaf.coverage import load_coverage_json

    data = load_coverage_json(matrix_path)
    track_ids = list(data.get("tracks") or [])
    sections = list(data.get("sections") or [])
    if not track_ids or not sections:
        return None

    from manuscript.sheaf.report import default_coverage_config_path

    cfg = load_coverage_config(default_coverage_config_path(root), project_root=root)
    color_map = {"black": 0.0, "white": 1.0, "gray": 2.0}
    grid: list[list[float]] = []
    y_labels: list[str] = []
    group_boundaries: list[float] = []
    prev_imrad = None
    for section in sections:
        imrad = section.get("imrad")
        if prev_imrad is not None and imrad != prev_imrad and cfg.heatmap.group_separator:
            group_boundaries.append(len(y_labels) - 0.5)
        prev_imrad = imrad
        depth = int(section.get("depth", 0))
        prefix = cfg.heatmap.indent_prefix * depth
        title = section.get("title", section.get("id", ""))
        if section.get("kind") == "group":
            title = f"{title} —"
        y_labels.append(f"{prefix}{title}")
        cells_by_track = {cell["track"]: cell for cell in section.get("cells") or []}
        grid.append(
            [
                float(color_map.get(cells_by_track.get(track_id, {}).get("color", "white"), 1.0))
                for track_id in track_ids
            ]
        )
    return HeatmapPayload(
        track_ids=track_ids,
        y_labels=y_labels,
        grid=grid,
        group_boundaries=group_boundaries,
        cfg=cfg,
        sections=sections,
    )
