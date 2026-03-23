"""B&W section header strips for interior and supplemental folios."""

from __future__ import annotations

import zlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from newspaper.visualization import configure_matplotlib_bw_style


def _rng_for_stem(stem: str) -> np.random.Generator:
    """Deterministic generator from stem (stable across processes)."""
    seed = zlib.adler32(stem.encode("utf-8")) & 0xFFFFFFFF
    return np.random.default_rng(int(seed))


def render_section_banner_bw(
    path: Path,
    stem: str,
    section_title: str,
    *,
    dpi: int = 150,
    paper_name: str = "Template Gazette",
    width_in: float = 7.0,
    height_in: float = 1.25,
) -> Path:
    """Write a wide, short monochrome banner PNG for a folio.

    Layout: rules, large section title, small publication name, and a row of
    deterministic gray ticks suggesting a measure / edition rhythm.

    Args:
        path: Output path (parent dirs created).
        stem: File stem (e.g. ``03_world``); seeds micro-geometry only.
        section_title: Display title (e.g. ``World``).
        dpi: Raster resolution.
        paper_name: Small caps line under the title.
        width_in: Figure width in inches (matches text block width order).
        height_in: Figure height in inches.

    Returns:
        ``path`` after writing.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    configure_matplotlib_bw_style()
    rng = _rng_for_stem(stem)

    fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=dpi)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.axhline(y=0.92, color="black", linewidth=2.2, xmin=0.02, xmax=0.98)
    ax.axhline(y=0.88, color="black", linewidth=0.6, xmin=0.02, xmax=0.98)

    ax.text(
        0.5,
        0.62,
        section_title.strip(),
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
        color="black",
    )
    ax.text(
        0.5,
        0.38,
        paper_name.upper(),
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=8,
        color="0.35",
    )

    n_ticks = 48
    xs = np.linspace(0.04, 0.96, n_ticks)
    heights = 0.06 + 0.05 * rng.random(n_ticks)
    for x, h in zip(xs, heights, strict=True):
        ax.plot([x, x], [0.06, 0.06 + h], color="0.45", linewidth=0.45, solid_capstyle="butt")

    ax.axhline(y=0.04, color="0.55", linewidth=0.8, xmin=0.02, xmax=0.98)

    fig.tight_layout(pad=0.05)
    fig.savefig(path, format="png", dpi=dpi, facecolor="white", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    return path


def section_banner_filename(stem: str) -> str:
    """Basename for the banner asset: ``section_banner_{stem}.png``."""
    return f"section_banner_{stem}.png"
