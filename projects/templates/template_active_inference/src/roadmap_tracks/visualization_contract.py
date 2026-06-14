"""Style and auxiliary-output contracts for deterministic figures."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from visualizations.figure_io import image_render_metrics
from visualizations.figure_registry import load_figure_registry
from visualizations.figure_style import load_figure_style

MIN_TYPOGRAPHY_POINTS: dict[str, float] = {
    "title": 12.0,
    "subtitle": 10.5,
    "header": 10.0,
    "axis_label": 10.0,
    "tick": 9.0,
    "legend": 9.0,
    "annotation": 8.5,
    "source_note": 8.5,
    "table_cell": 8.0,
    "matrix_label": 7.0,
    "matrix_label_dense": 6.0,
}

KNOWN_AUXILIARY_VISUALIZATIONS: dict[str, dict[str, str]] = {
    "graphical_abstract.png": {
        "classification": "auxiliary_publication_asset",
        "producer": "manual_or_external_publication_export",
        "reason": "non-registry graphical abstract kept outside numbered manuscript figures",
    },
    "si_belief_trajectory.gif": {
        "classification": "deterministic_animation_track",
        "producer": "scripts/render_animation.py",
        "reason": "optional animation artifact validated by animation_frame_deltas",
    },
    "si_tmaze_model_matrices.png": {
        "classification": "auxiliary_model_inspection",
        "producer": "manual_or_external_publication_export",
        "reason": "model-matrix inspection image kept outside numbered manuscript figures",
    },
    "transmission_integrity_strip.png": {
        "classification": "auxiliary_transmission_check",
        "producer": "manual_or_external_publication_export",
        "reason": "release/transmission inspection strip kept outside numbered manuscript figures",
    },
    "transmission_pairing.png": {
        "classification": "auxiliary_transmission_check",
        "producer": "manual_or_external_publication_export",
        "reason": "release/transmission pairing image kept outside numbered manuscript figures",
    },
}

STYLE_LITERAL_RE = re.compile(
    r"(?P<name>fontsize|title_size|label_fontsize)\s*=\s*(?P<value>[0-9]+(?:\.[0-9]+)?)"
    r"|set_fontsize\(\s*(?P<call_value>[0-9]+(?:\.[0-9]+)?)"
)


def _visualization_source_files(root: Path) -> list[Path]:
    return sorted((root / "src" / "visualizations").glob("*.py"))


def build_style_contract(project_root: Path) -> dict[str, Any]:
    """Build a live typography-token and source-literal contract."""
    root = project_root.resolve()
    style = load_figure_style(root)
    rows = []
    for role, minimum in MIN_TYPOGRAPHY_POINTS.items():
        points = float(style.text_size(role))
        rows.append(
            {
                "role": role,
                "points": points,
                "minimum_points": float(minimum),
                "ok": points >= float(minimum),
            }
        )
    literal_issues: list[dict[str, Any]] = []
    for path in _visualization_source_files(root):
        rel = str(path.relative_to(root))
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if "style.text_size(" in line:
                continue
            match = STYLE_LITERAL_RE.search(line)
            if not match:
                continue
            value = match.group("value") or match.group("call_value")
            literal_issues.append(
                {
                    "path": rel,
                    "line": line_no,
                    "value": float(value),
                    "snippet": line.strip(),
                }
            )
    return {
        "schema": "template_active_inference.visualization_style_contract.v1",
        "rows": rows,
        "token_count": len(rows),
        "all_token_minima_ok": bool(rows) and all(row["ok"] for row in rows),
        "literal_issues": literal_issues,
        "literal_issue_count": len(literal_issues),
        "source_file_count": len(_visualization_source_files(root)),
        "ok": bool(rows) and all(row["ok"] for row in rows) and not literal_issues,
    }


def build_auxiliary_visualization_inventory(project_root: Path) -> dict[str, Any]:
    """Inventory visual files intentionally outside the numbered figure registry."""
    root = project_root.resolve()
    figure_dir = root / "output" / "figures"
    registry_filenames = {spec.filename for spec in load_figure_registry(root).values()}
    visual_paths = sorted(
        path
        for suffix in ("*.png", "*.gif")
        for path in figure_dir.glob(suffix)
        if not path.name.startswith(".") and path.name not in registry_filenames
    )
    rows: list[dict[str, Any]] = []
    for path in visual_paths:
        rel = f"output/figures/{path.name}"
        classification = KNOWN_AUXILIARY_VISUALIZATIONS.get(path.name, {})
        metrics = image_render_metrics(path)
        rendered = (
            metrics["exists"]
            and int(metrics["width_px"]) > 0
            and int(metrics["height_px"]) > 0
            and int(metrics["size_bytes"]) > 0
            and metrics["nonblank"]
        )
        rows.append(
            {
                "path": rel,
                "filename": path.name,
                "classified": bool(classification),
                "classification": classification.get("classification", "unclassified"),
                "producer": classification.get("producer", ""),
                "reason": classification.get("reason", ""),
                "rendered": rendered,
                **metrics,
            }
        )
    return {
        "schema": "template_active_inference.auxiliary_visualization_inventory.v1",
        "rows": rows,
        "auxiliary_visualization_count": len(rows),
        "known_auxiliary_filenames": sorted(KNOWN_AUXILIARY_VISUALIZATIONS),
        "all_auxiliary_outputs_classified": all(row["classified"] for row in rows),
        "all_auxiliary_outputs_rendered": all(row["rendered"] for row in rows),
    }


__all__ = [
    "KNOWN_AUXILIARY_VISUALIZATIONS",
    "MIN_TYPOGRAPHY_POINTS",
    "build_auxiliary_visualization_inventory",
    "build_style_contract",
]
