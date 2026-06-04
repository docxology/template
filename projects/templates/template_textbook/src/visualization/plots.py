"""Figure generators — every figure the manuscript references is produced here.

Two families:

* **Worked-model figures** visualise the tested functions in
  :mod:`textbook.models` (the formalisms readers should trust and reuse).
* **Chapter overview placeholders** — one per chapter, named
  ``<part_id>_<stem>.png`` to match the ``\\includegraphics`` path emitted by
  ``textbook.content.scaffold_chapter``. Replace each with a real subject figure
  as the chapter is written; the filename contract keeps cross-references valid.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from textbook import models
from textbook.config import iter_chapters, load_config
from textbook_logging import get_logger

from ._scaffold import BLUE, GRAY, GREEN, ORANGE, SERIES, new_figure, save_figure

logger = get_logger(__name__)


def plot_logistic_growth(output_dir: Path) -> Path:
    """Logistic growth curve from ``models.logistic_growth``."""
    t = np.linspace(0, 12, 200)
    fig, ax = new_figure()
    for color, r in zip(SERIES, (0.4, 0.7, 1.1)):
        y = models.logistic_growth(t, r=r, carrying_capacity=100.0, initial=5.0)
        ax.plot(t, y, color=color, label=f"r = {r}")
    ax.axhline(100.0, color=GRAY, linestyle="--", linewidth=0.8, label="K = 100")
    ax.set_xlabel("time")
    ax.set_ylabel("quantity N(t)")
    ax.set_title("Logistic growth")
    ax.legend()
    return save_figure(fig, output_dir, "logistic_growth")


def plot_saturating_response(output_dir: Path) -> Path:
    """Hill-style saturating response from ``models.saturating_response``."""
    x = np.linspace(0, 10, 200)
    fig, ax = new_figure()
    for color, n in zip(SERIES, (1.0, 2.0, 4.0)):
        y = models.saturating_response(x, maximum=1.0, half_saturation=3.0, hill=n)
        ax.plot(x, y, color=color, label=f"n = {n}")
    ax.set_xlabel("input x")
    ax.set_ylabel("response y")
    ax.set_title("Saturating (Hill) response")
    ax.legend()
    return save_figure(fig, output_dir, "saturating_response")


def plot_exponential_decay(output_dir: Path) -> Path:
    """Exponential decay with annotated half-life."""
    t = np.linspace(0, 10, 200)
    rate = 0.5
    y = models.exponential_decay(t, initial=100.0, rate=rate)
    fig, ax = new_figure()
    ax.plot(t, y, color=BLUE, label="decay")
    t_half = models.half_life(rate)
    ax.axvline(t_half, color=ORANGE, linestyle="--", linewidth=0.9, label=f"t½ = {t_half:.2f}")
    ax.set_xlabel("time")
    ax.set_ylabel("amount")
    ax.set_title("Exponential decay")
    ax.legend()
    return save_figure(fig, output_dir, "exponential_decay")


def plot_linear_fit(output_dir: Path) -> Path:
    """Scatter with an OLS line from ``models.linear_fit`` (deterministic data)."""
    x = np.linspace(0, 10, 25)
    # Deterministic pseudo-noise (no RNG) so the figure is byte-stable.
    noise = np.sin(x * 1.7) * 1.5
    y = 2.0 * x + 3.0 + noise
    fit = models.linear_fit(x, y)
    fig, ax = new_figure()
    ax.scatter(x, y, color=GREEN, s=18, label="data")
    ax.plot(x, fit.predict(x), color=BLUE, label=f"fit: y={fit.slope:.2f}x+{fit.intercept:.2f}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(f"Linear fit (R² = {fit.r_squared:.3f})")
    ax.legend()
    return save_figure(fig, output_dir, "linear_fit")


def placeholder_overview(title: str, output_dir: Path, filename: str) -> Path:
    """A neutral, titled placeholder figure for a not-yet-illustrated chapter."""
    fig, ax = new_figure(width=6.4, height=3.6)
    ax.axis("off")
    ax.text(
        0.5,
        0.62,
        title,
        ha="center",
        va="center",
        fontsize=15,
        weight="bold",
        wrap=True,
    )
    ax.text(
        0.5,
        0.34,
        "Placeholder overview figure — replace via src/visualization/plots.py",
        ha="center",
        va="center",
        fontsize=9,
        color=GRAY,
    )
    fig.patch.set_edgecolor(BLUE)
    fig.patch.set_linewidth(2)
    return save_figure(fig, output_dir, filename)


def cover_art(output_dir: Path, *, title: str = "The Template Textbook", subtitle: str = "") -> Path:
    """Render a deterministic cover image: nested modular blocks + title.

    The nesting (book -> parts -> chapters -> sections) visually states the
    template's organising idea. Deterministic, so the cover is byte-stable.
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    fig, ax = plt.subplots(figsize=(6.4, 8.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12.5)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # Nested rounded rectangles, largest (book) to smallest (section).
    palette = [BLUE, GREEN, ORANGE, "#8E44AD"]
    for i, color in enumerate(palette):
        inset = i * 0.9
        box = FancyBboxPatch(
            (1.0 + inset, 2.2 + inset),
            8.0 - 2 * inset,
            6.5 - 2 * inset,
            boxstyle="round,pad=0.1,rounding_size=0.25",
            linewidth=2.2,
            edgecolor=color,
            facecolor="none",
        )
        ax.add_patch(box)
    labels = ["Book", "Part", "Chapter", "Section"]
    for i, (label, color) in enumerate(zip(labels, palette)):
        ax.text(1.35 + i * 0.9, 8.35 - i * 0.9, label, color=color, fontsize=10, weight="bold")

    ax.text(5, 11.4, title, ha="center", va="center", fontsize=21, weight="bold")
    if subtitle:
        ax.text(5, 10.5, subtitle, ha="center", va="center", fontsize=10, color=GRAY, wrap=True)
    ax.text(5, 1.1, "A modular, fillable scaffold", ha="center", va="center", fontsize=11, style="italic", color=GRAY)
    return save_figure(fig, output_dir, "template_textbook_cover")


def generate_worked_figures(output_dir: Path) -> list[Path]:
    """Generate the worked-model figures."""
    return [
        plot_logistic_growth(output_dir),
        plot_saturating_response(output_dir),
        plot_exponential_decay(output_dir),
        plot_linear_fit(output_dir),
    ]


def generate_chapter_placeholders(output_dir: Path, config: dict[str, Any] | None = None) -> list[Path]:
    """Generate one ``<part_id>_<stem>.png`` placeholder per chapter in config."""
    cfg = config if config is not None else load_config()
    paths: list[Path] = []
    for chapter in iter_chapters(cfg):
        filename = f"{chapter.part_id}_{chapter.stem}.png"
        paths.append(placeholder_overview(chapter.title, output_dir, filename))
    return paths


def generate_all_figures(output_dir: Path, config: dict[str, Any] | None = None) -> list[Path]:
    """Generate every figure the manuscript references."""
    paths = generate_worked_figures(output_dir)
    paths.extend(generate_chapter_placeholders(output_dir, config))
    logger.info("generated %d figures in %s", len(paths), output_dir)
    return paths


__all__ = [
    "cover_art",
    "generate_all_figures",
    "generate_chapter_placeholders",
    "generate_worked_figures",
    "placeholder_overview",
    "plot_exponential_decay",
    "plot_linear_fit",
    "plot_logistic_growth",
    "plot_saturating_response",
]
