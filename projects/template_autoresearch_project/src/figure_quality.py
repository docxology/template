"""Figure-quality checks for generated AutoResearch visual artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .artifact_content import is_substantive_artifact


FIGURE_QUALITY_SCHEMA = "template-autoresearch-figure-quality-report-v1"


def figure_quality_report_payload(
    project_root: Path,
    registry: dict[str, dict[str, object]],
    *,
    generated_at: str,
    require_all_registered: bool = False,
) -> dict[str, object]:
    """Return local checks for registry/source/image consistency."""
    figures_dir = project_root / "output" / "figures"
    rows: list[dict[str, object]] = []
    registered_filenames = {str(record.get("filename", "")) for record in registry.values() if record.get("filename")}
    for label, record in sorted(registry.items()):
        filename = str(record.get("filename", ""))
        figure_path = figures_dir / filename
        if not figure_path.exists() and not require_all_registered:
            continue
        metadata = _mapping(record.get("metadata"))
        image_metrics = _image_metrics(figure_path)
        source = str(metadata.get("source", ""))
        rows.append(
            {
                "label": label,
                "filename": filename,
                "exists": figure_path.exists(),
                "size_bytes": figure_path.stat().st_size if figure_path.exists() else 0,
                "width_px": image_metrics["width_px"],
                "height_px": image_metrics["height_px"],
                "pixel_variance": image_metrics["pixel_variance"],
                "nonblank": image_metrics["pixel_variance"] > 0.0,
                "alt_text": str(metadata.get("alt_text", "")),
                "has_alt_text": bool(str(metadata.get("alt_text", "")).strip()),
                "source": source,
                "source_exists": _source_exists(project_root, source),
                "source_nontrivial": bool(source) and is_substantive_artifact(project_root / source),
                "claim_boundary": str(metadata.get("claim_boundary", "")),
            }
        )
    unregistered_pngs = sorted(
        path.name for path in figures_dir.glob("*.png") if path.is_file() and path.name not in registered_filenames
    )
    valid = (
        bool(rows)
        and not unregistered_pngs
        and all(
            bool(row["exists"])
            and bool(row["source_exists"])
            and bool(row["source_nontrivial"])
            and bool(row["has_alt_text"])
            and bool(row["nonblank"])
            and _has_positive_dimensions(row)
            for row in rows
        )
    )
    return {
        "schema": FIGURE_QUALITY_SCHEMA,
        "generated_at": generated_at,
        "figure_count": len(rows),
        "valid": valid,
        "require_all_registered": require_all_registered,
        "unregistered_pngs": unregistered_pngs,
        "figures": rows,
        "claim_boundary": (
            "Figure-quality checks validate local files, registry bindings, nonblank pixels, "
            "and substantive (non-empty, parseable) source data artifacts."
        ),
    }


def write_figure_quality_report(
    path: Path,
    project_root: Path,
    registry: dict[str, dict[str, object]],
    *,
    generated_at: str,
    require_all_registered: bool = False,
) -> Path:
    """Write the local figure-quality report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            figure_quality_report_payload(
                project_root,
                registry,
                generated_at=generated_at,
                require_all_registered=require_all_registered,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _image_metrics(path: Path) -> dict[str, int | float]:
    if not path.exists():
        return {"width_px": 0, "height_px": 0, "pixel_variance": 0.0}
    from matplotlib import image as mpimg

    pixels = np.asarray(mpimg.imread(path), dtype=float)
    if pixels.ndim == 3:
        grayscale = pixels[..., :3].mean(axis=2)
    else:
        grayscale = pixels
    return {
        "width_px": int(pixels.shape[1]),
        "height_px": int(pixels.shape[0]),
        "pixel_variance": round(float(np.var(grayscale)), 8),
    }


def _source_exists(project_root: Path, source: str) -> bool:
    if not source:
        return False
    return (project_root / source).exists()


def _has_positive_dimensions(row: dict[str, object]) -> bool:
    width = row.get("width_px")
    height = row.get("height_px")
    return isinstance(width, int) and isinstance(height, int) and width > 0 and height > 0


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
