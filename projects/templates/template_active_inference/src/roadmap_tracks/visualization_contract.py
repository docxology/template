"""Style and auxiliary-output contracts for deterministic figures."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from visualizations.figure_io import image_render_metrics
from visualizations.figure_registry import load_figure_registry
from visualizations.figure_style import load_figure_style

from .image_content_hash import image_content_sha256

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
        "producer": "infrastructure.publishing.transmission_barcode_strip.write_transmission_barcode_strip",
        "reason": "infrastructure-generated integrity strip for transmission bookends",
    },
    "transmission_pairing.png": {
        "classification": "auxiliary_transmission_check",
        "producer": "infrastructure.publishing.transmission_figure.write_transmission_diagram",
        "reason": "infrastructure-generated release-pairing diagram for transmission bookends",
    },
}

_COMPRESSION_DEPENDENT_AUXILIARY_FIELDS = frozenset({"size_bytes"})

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
        content_sha256 = image_content_sha256(path)
        rendered = (
            metrics["exists"]
            and int(metrics["width_px"]) > 0
            and int(metrics["height_px"]) > 0
            and int(metrics["size_bytes"]) > 0
            and metrics["nonblank"]
            and bool(content_sha256)
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
                "content_sha256": content_sha256,
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


def auxiliary_visualization_rows_match(saved_rows: object, live_rows: object) -> bool:
    """Compare auxiliary evidence without treating PNG compression size as content.

    ``size_bytes`` remains useful diagnostic evidence in the saved report, but
    Pillow and zlib versions can encode identical decoded pixels to different
    byte lengths. Every other field remains fail-closed, including the decoded
    content hash, dimensions, mode, nonblank status, classification, and
    producer attribution.
    """
    if not isinstance(saved_rows, list) or not isinstance(live_rows, list):
        return False
    if not all(isinstance(row, dict) for row in [*saved_rows, *live_rows]):
        return False
    saved_evidence = [
        {key: value for key, value in row.items() if key not in _COMPRESSION_DEPENDENT_AUXILIARY_FIELDS}
        for row in saved_rows
    ]
    live_evidence = [
        {key: value for key, value in row.items() if key not in _COMPRESSION_DEPENDENT_AUXILIARY_FIELDS}
        for row in live_rows
    ]
    return saved_evidence == live_evidence


__all__ = [
    "KNOWN_AUXILIARY_VISUALIZATIONS",
    "MIN_TYPOGRAPHY_POINTS",
    "auxiliary_visualization_rows_match",
    "build_auxiliary_visualization_inventory",
    "build_style_contract",
]
