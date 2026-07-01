from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Wedge

from figures._common import FIGURE_DPI, PNG_METADATA, STAGE_COLORS, SVG_METADATA, _normalize_svg_whitespace
from formalisms import formalism_count
from integrity import build_integrity_dimensions
from security_assay import build_security_assay

try:
    from .config import load_gold_refinement_config
    from .evidence import build_evidence_registry
    from .refinery import run_refinery
except ImportError:
    from config import load_gold_refinement_config  # type: ignore[no-redef]
    from evidence import build_evidence_registry  # type: ignore[no-redef]
    from refinery import run_refinery  # type: ignore[no-redef]


COVER_PNG = "cover_visualization.png"
COVER_REPORT = "cover_visualization.json"


def _project_root(project_root: Path | None) -> Path:
    return project_root or Path(__file__).resolve().parent.parent


def _cover_background(width: int = 1200, height: int = 1600) -> np.ndarray:
    y_values = np.linspace(0.0, 1.0, height)
    x_values = np.linspace(0.0, 1.0, width)
    y, x = np.meshgrid(y_values, x_values, indexing="ij")
    base = np.zeros((height, width, 3), dtype=float)
    base[:] = np.array([0.025, 0.021, 0.014])
    furnace = np.exp(-(((x - 0.52) ** 2) / 0.055 + ((y - 0.50) ** 2) / 0.075))
    crown = np.exp(-(((x - 0.50) ** 2) / 0.19 + ((y - 0.92) ** 2) / 0.012))
    assay = np.exp(-(((x - 0.22) ** 2) / 0.03 + ((y - 0.72) ** 2) / 0.04))
    base += furnace[..., None] * np.array([0.76, 0.45, 0.09])
    base += crown[..., None] * np.array([0.30, 0.18, 0.04])
    base += assay[..., None] * np.array([0.00, 0.20, 0.18])
    texture = 0.018 * np.sin(85 * x + 31 * y) + 0.012 * np.sin(41 * x - 77 * y)
    base += texture[..., None]
    return np.clip(base, 0.0, 1.0)


def _polar(center: tuple[float, float], radius: float, degrees: float) -> tuple[float, float]:
    angle = math.radians(degrees)
    return center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)


def _add_text(
    ax: plt.Axes,
    x: float,
    y: float,
    value: str,
    *,
    size: float,
    color: str = "#f8fafc",
    weight: str = "normal",
    ha: str = "center",
    va: str = "center",
    alpha: float = 1.0,
) -> None:
    ax.text(
        x,
        y,
        value,
        color=color,
        fontsize=size,
        fontweight=weight,
        ha=ha,
        va=va,
        alpha=alpha,
        family="DejaVu Sans",
    )


def _draw_stage_arc(ax: plt.Axes, center: tuple[float, float], stage_names: list[str]) -> None:
    start = 204.0
    span = 312.0 / len(stage_names)
    for index, _name in enumerate(stage_names):
        theta1 = start + index * span
        theta2 = theta1 + span - 5.0
        color = STAGE_COLORS[index % len(STAGE_COLORS)]
        ax.add_patch(
            Wedge(
                center,
                0.365,
                theta1,
                theta2,
                width=0.038,
                facecolor=color,
                edgecolor="#fef3c7",
                lw=0.8,
                alpha=0.96,
            )
        )


def _draw_security_arc(ax: plt.Axes, center: tuple[float, float], count: int) -> None:
    for index in range(count):
        angle = 198 + index * (168 / max(count - 1, 1))
        x, y = _polar(center, 0.435, angle)
        ax.add_patch(Circle((x, y), 0.018, facecolor="#22d3ee", edgecolor="#cffafe", lw=0.7, alpha=0.92))
        ax.add_patch(Circle((x, y), 0.009, facecolor="#fbbf24", edgecolor="none", alpha=0.95))


def _draw_faceted_gold(ax: plt.Axes, center: tuple[float, float]) -> None:
    cx, cy = center
    facets = [
        ([(cx, cy + 0.120), (cx - 0.110, cy + 0.030), (cx, cy + 0.005)], "#fde68a"),
        ([(cx, cy + 0.120), (cx + 0.110, cy + 0.030), (cx, cy + 0.005)], "#f59e0b"),
        ([(cx - 0.110, cy + 0.030), (cx - 0.070, cy - 0.105), (cx, cy + 0.005)], "#b45309"),
        ([(cx + 0.110, cy + 0.030), (cx + 0.070, cy - 0.105), (cx, cy + 0.005)], "#d97706"),
        ([(cx - 0.070, cy - 0.105), (cx + 0.070, cy - 0.105), (cx, cy + 0.005)], "#fbbf24"),
    ]
    ax.add_patch(Circle(center, 0.190, facecolor="#facc15", edgecolor="none", alpha=0.11))
    ax.add_patch(Circle(center, 0.150, facecolor="#f59e0b", edgecolor="none", alpha=0.10))
    for points, color in facets:
        ax.add_patch(Polygon(points, closed=True, facecolor=color, edgecolor="#fffbeb", lw=0.7, alpha=0.96))
    ax.add_patch(
        Polygon(
            [
                (cx, cy + 0.120),
                (cx + 0.110, cy + 0.030),
                (cx + 0.070, cy - 0.105),
                (cx - 0.070, cy - 0.105),
                (cx - 0.110, cy + 0.030),
            ],
            closed=True,
            fill=False,
            edgecolor="#fff7ed",
            lw=1.0,
            alpha=0.86,
        )
    )


def _draw_assay_cards(ax: plt.Axes, records: tuple[Any, ...]) -> None:
    labels = ["ZERO TRUST", "SSDF", "SLSA", "ATT&CK", "SECURE DESIGN"]
    for index, record in enumerate(records):
        y = 0.705 - index * 0.049
        ax.add_patch(
            FancyBboxPatch(
                (0.700, y),
                0.238,
                0.031,
                boxstyle="round,pad=0.005,rounding_size=0.008",
                facecolor="#042f2e",
                edgecolor="#67e8f9",
                linewidth=0.55,
                alpha=0.86,
            )
        )
        _add_text(ax, 0.715, y + 0.016, f"S{index + 1}", size=6.4, color="#fde68a", weight="bold", ha="left")
        _add_text(
            ax,
            0.760,
            y + 0.016,
            labels[index] if index < len(labels) else str(record.standard).upper()[:14],
            size=5.9,
            color="#d1fae5",
            ha="left",
        )


def _draw_metric_cards(ax: plt.Axes, metrics: list[tuple[str, str]]) -> None:
    for index, (value, label) in enumerate(metrics):
        x = 0.095 + index * 0.205
        ax.add_patch(
            FancyBboxPatch(
                (x, 0.115),
                0.165,
                0.085,
                boxstyle="round,pad=0.008,rounding_size=0.016",
                facecolor="#111827",
                edgecolor="#f59e0b",
                linewidth=0.8,
                alpha=0.80,
            )
        )
        _add_text(ax, x + 0.0825, 0.165, value, size=20, color="#fde68a", weight="bold")
        _add_text(ax, x + 0.0825, 0.132, label.upper(), size=5.9, color="#e5e7eb", weight="bold")


def _save_cover_figure(fig: plt.Figure, out_path: Path) -> Path:
    svg_path = out_path.with_suffix(".svg")
    fig.savefig(out_path, dpi=FIGURE_DPI, metadata=PNG_METADATA, facecolor=fig.get_facecolor())
    fig.savefig(svg_path, format="svg", metadata=SVG_METADATA, facecolor=fig.get_facecolor())
    _normalize_svg_whitespace(svg_path)
    plt.close(fig)
    return out_path


def generate_cover_visualization(
    output_dir: Path | None = None,
    *,
    project_root: Path | None = None,
) -> Path:
    root = _project_root(project_root)
    output = output_dir or root / "output" / "figures"
    output.mkdir(parents=True, exist_ok=True)
    cfg = load_gold_refinement_config(root)
    refinery = run_refinery()
    security_records = build_security_assay(cfg)
    integrity_count = len(build_integrity_dimensions(cfg))
    evidence = build_evidence_registry(cfg, root)
    stage_names = [stage.name for stage in refinery.stages]

    fig = plt.figure(figsize=(8, 10.6666667), facecolor="#080704")
    ax = fig.add_axes((0, 0, 1, 1))
    ax.imshow(_cover_background(), extent=(0, 1, 0, 1), origin="lower")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    center = (0.50, 0.515)
    ax.add_patch(Circle(center, 0.465, facecolor="none", edgecolor="#fef3c7", lw=0.7, alpha=0.22))
    ax.add_patch(Circle(center, 0.400, facecolor="none", edgecolor="#67e8f9", lw=0.6, alpha=0.26))
    _draw_stage_arc(ax, center, stage_names)
    _draw_security_arc(ax, center, len(security_records))
    _draw_faceted_gold(ax, center)
    _draw_assay_cards(ax, security_records)

    _add_text(ax, 0.500, 0.903, "REFINEMENT OF GOLD", size=29, color="#fff7ed", weight="bold")
    _add_text(ax, 0.500, 0.869, "manuscript purity under adversarial assay", size=10.5, color="#fef3c7")
    _add_text(
        ax,
        0.500,
        0.823,
        "ORE  |  SMELTING  |  ASSAYING  |  CUPELLATION  |  CERTIFICATION",
        size=7.4,
        color="#d1d5db",
        weight="bold",
    )
    _add_text(ax, 0.500, 0.515, "9N", size=34, color="#fff7ed", weight="bold")
    _add_text(ax, 0.500, 0.475, "SOURCE-OWNED", size=8.4, color="#111827", weight="bold")
    _add_text(ax, 0.500, 0.456, "CERTIFICATION", size=8.4, color="#111827", weight="bold")
    _add_text(ax, 0.195, 0.708, "LOCAL GATES", size=8.0, color="#a7f3d0", weight="bold")
    _add_text(ax, 0.205, 0.684, "claims / figures / render / citations", size=6.4, color="#d1fae5")
    _add_text(ax, 0.810, 0.750, "ADVERSARIAL ASSAY", size=8.0, color="#cffafe", weight="bold")
    _add_text(
        ax,
        0.500,
        0.245,
        "No scan claim without artifacts. No compliance claim without scope.",
        size=9.0,
        color="#fef3c7",
        weight="bold",
    )

    metrics = [
        (str(formalism_count()), "formalisms"),
        (str(integrity_count), "integrity gates"),
        (str(len(security_records)), "assay rows"),
        (f"{evidence.supported_claims}/{evidence.total_claims}", "claims supported"),
    ]
    _draw_metric_cards(ax, metrics)

    out_path = output / COVER_PNG
    return _save_cover_figure(fig, out_path)


def cover_visualization_manifest(image_path: Path) -> dict[str, Any]:
    image = np.asarray(mpimg.imread(image_path))
    rgb = image[..., :3] if image.ndim == 3 else np.stack([image, image, image], axis=-1)
    rgb_float = rgb.astype(float)
    if rgb_float.max(initial=0.0) > 1.0:
        rgb_float = rgb_float / 255.0
    height, width = rgb_float.shape[:2]
    nonwhite = np.max(np.abs(rgb_float - 1.0), axis=2) > 0.02
    return {
        "schema": "template-gold-refinement-cover-v1",
        "png_path": "output/figures/cover_visualization.png",
        "svg_path": "output/figures/cover_visualization.svg",
        "generated_by": "src/cover_visualization.py::generate_cover_visualization",
        "width_px": int(width),
        "height_px": int(height),
        "nonwhite_fraction": round(float(np.mean(nonwhite)), 6),
        "color_variance": round(float(np.var(rgb_float)), 8),
        "png_bytes": int(image_path.stat().st_size),
        "svg_bytes": int(image_path.with_suffix(".svg").stat().st_size),
    }


def write_cover_visualization(
    project_root: Path | None = None,
    *,
    output_dir: Path | None = None,
    report_dir: Path | None = None,
) -> Path:
    root = _project_root(project_root)
    image_path = generate_cover_visualization(output_dir=output_dir, project_root=root)
    reports = report_dir or root / "output" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    report_path = reports / COVER_REPORT
    report_path.write_text(json.dumps(cover_visualization_manifest(image_path), indent=2), encoding="utf-8")
    return image_path


__all__ = [
    "COVER_PNG",
    "COVER_REPORT",
    "cover_visualization_manifest",
    "generate_cover_visualization",
    "write_cover_visualization",
]
