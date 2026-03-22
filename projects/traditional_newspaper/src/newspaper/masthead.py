"""Deterministic masthead figure generation (matplotlib, headless)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def render_masthead_png(
    path: Path,
    *,
    seed: int = 42,
    dpi: int = 200,
    title: str = "TEMPLATE GAZETTE",
    tagline: str = "All the news that fits the pipeline",
) -> Path:
    """Write a wide masthead PNG suitable for full-width inclusion above columns.

    Args:
        path: Output file path (parent directories are created).
        seed: RNG seed for any decorative jitter (currently unused; reserved).
        dpi: Rasterization resolution.
        title: Main banner text.
        tagline: Subtitle under the rule.

    Returns:
        ``path`` after writing.
    """
    rng = np.random.default_rng(seed)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig_w, fig_h = 11.0, 1.35
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    y_top = 0.62 + 0.008 * (rng.random() - 0.5)
    y_bot = 0.58 + 0.006 * (rng.random() - 0.5)
    ax.axhline(y_top, color="black", linewidth=2.2)
    ax.axhline(y_bot, color="black", linewidth=0.8)
    ax.text(
        0.5,
        0.78,
        title,
        ha="center",
        va="center",
        fontsize=26,
        fontfamily="serif",
        fontweight="bold",
    )
    ax.text(
        0.5,
        0.42,
        tagline,
        ha="center",
        va="center",
        fontsize=10,
        fontfamily="serif",
        style="italic",
    )
    fig.savefig(path, bbox_inches="tight", pad_inches=0.08, facecolor="white")
    plt.close(fig)
    return path
