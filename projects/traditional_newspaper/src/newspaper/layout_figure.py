"""Tabloid page geometry schematic for documentation figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from newspaper.layout_spec import LAYOUT, NewspaperLayout


def render_layout_schematic_png(
    path: Path,
    *,
    layout: NewspaperLayout | None = None,
    dpi: int = 150,
) -> Path:
    """Write a PNG showing page outline, margin inset, and column grid.

    Drawing uses ``layout`` dimensions in inches as data coordinates: outer
    rectangle is the sheet, dashed inner box is the text block inset by
    ``margin_in``, and three shaded columns include ``column_sep_in`` gutters.

    Args:
        path: Output file path; parent directories are created.
        layout: Layout constants; defaults to :data:`~newspaper.layout_spec.LAYOUT`.
        dpi: Rasterization resolution.

    Returns:
        ``path`` after writing.
    """
    lay = layout or LAYOUT
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    pw, ph = lay.paper_width_in, lay.paper_height_in
    margin = lay.margin_in
    sep = lay.column_sep_in
    ncols = lay.column_count

    inner_w = pw - 2 * margin
    inner_h = ph - 2 * margin
    col_w = (inner_w - (ncols - 1) * sep) / float(ncols)

    fig, ax = plt.subplots(figsize=(5.5, 8.5), dpi=dpi)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.add_patch(Rectangle((0, 0), pw, ph, fill=False, edgecolor="black", linewidth=2.0))
    ax.add_patch(
        Rectangle(
            (margin, margin),
            inner_w,
            inner_h,
            fill=False,
            edgecolor="dimgray",
            linewidth=1.0,
            linestyle=(0, (4, 3)),
        )
    )

    tones = ("#e8e8e8", "#f2f2f2", "#e8e8e8")
    x = margin
    y = margin
    for i in range(ncols):
        face = tones[i % len(tones)]
        ax.add_patch(
            Rectangle(
                (x, y),
                col_w,
                inner_h,
                facecolor=face,
                edgecolor="black",
                linewidth=0.9,
            )
        )
        x += col_w + sep

    ax.set_xlim(-0.15, pw + 0.15)
    ax.set_ylim(-0.15, ph + 0.15)
    ax.invert_yaxis()

    title_y = margin * 0.35
    ax.text(
        pw / 2,
        title_y,
        f"Tabloid {pw:g} x {ph:g} in",
        ha="center",
        va="top",
        fontsize=11,
        fontweight="bold",
    )
    ax.text(
        pw / 2,
        title_y + 0.22,
        f"margin {margin:g} in | {ncols} cols | sep {sep:g} in",
        ha="center",
        va="top",
        fontsize=8,
        color="dimgray",
    )

    fig.savefig(path, bbox_inches="tight", pad_inches=0.12, facecolor="white")
    plt.close(fig)
    return path
