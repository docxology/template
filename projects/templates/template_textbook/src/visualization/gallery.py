"""Figure gallery — a worked example of every common scientific plot type.

Each function is deterministic (seeded RNG or closed-form data, headless Agg) and
returns the saved PNG path. The companion appendix
``manuscript/appendices/appendix_format_gallery.md`` embeds these so a future
author can see — and copy — a working version of every chart they might need.

This module is intentionally broad rather than deep: replace any function with a
subject-specific figure, or add new ones following the same ``(output_dir) ->
Path`` contract and register them in :data:`GALLERY`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import numpy as np

from textbook import models
from textbook_logging import get_logger

from ._scaffold import BLUE, GRAY, GREEN, ORANGE, PURPLE, SERIES, VERMILLION, new_figure, save_figure

logger = get_logger(__name__)


def _rng() -> np.random.Generator:
    """A fixed-seed generator so every gallery figure is byte-reproducible."""
    return np.random.default_rng(0)


def line_plot(output_dir: Path) -> Path:
    """Multi-series line plot."""
    x = np.linspace(0, 2 * np.pi, 200)
    fig, ax = new_figure()
    for color, k in zip(SERIES, (1, 2, 3)):
        ax.plot(x, np.sin(k * x), color=color, label=f"sin({k}x)")
    ax.set_xlabel("x")
    ax.set_ylabel("amplitude")
    ax.set_title("Line plot — multiple series")
    ax.legend()
    return save_figure(fig, output_dir, "gallery_line")


def scatter_with_fit(output_dir: Path) -> Path:
    """Scatter with an ordinary-least-squares fit line (uses models.linear_fit)."""
    rng = _rng()
    x = np.linspace(0, 10, 40)
    y = 1.5 * x + 2.0 + rng.normal(0, 1.5, x.size)
    fit = models.linear_fit(x, y)
    fig, ax = new_figure()
    ax.scatter(x, y, color=GREEN, s=20, label="observations")
    ax.plot(x, fit.predict(x), color=BLUE, lw=2, label=f"fit (R²={fit.r_squared:.2f})")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Scatter with regression line")
    ax.legend()
    return save_figure(fig, output_dir, "gallery_scatter_fit")


def bar_chart(output_dir: Path) -> Path:
    """Vertical bar chart with value labels."""
    labels = ["A", "B", "C", "D", "E"]
    values = [3, 7, 5, 9, 4]
    fig, ax = new_figure()
    bars = ax.bar(labels, values, color=BLUE)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 0.1, str(value), ha="center")
    ax.set_ylabel("count")
    ax.set_title("Bar chart")
    return save_figure(fig, output_dir, "gallery_bar")


def grouped_bar(output_dir: Path) -> Path:
    """Grouped (clustered) bar chart."""
    labels = ["Q1", "Q2", "Q3", "Q4"]
    group_a = [4, 6, 5, 8]
    group_b = [3, 5, 7, 6]
    x = np.arange(len(labels))
    width = 0.38
    fig, ax = new_figure()
    ax.bar(x - width / 2, group_a, width, color=BLUE, label="series A")
    ax.bar(x + width / 2, group_b, width, color=ORANGE, label="series B")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title("Grouped bar chart")
    ax.legend()
    return save_figure(fig, output_dir, "gallery_grouped_bar")


def horizontal_bar(output_dir: Path) -> Path:
    """Horizontal bar chart (good for long category labels)."""
    labels = ["category one", "category two", "category three", "category four"]
    values = [12, 19, 7, 15]
    fig, ax = new_figure()
    ax.barh(labels, values, color=PURPLE)
    ax.set_xlabel("value")
    ax.set_title("Horizontal bar chart")
    return save_figure(fig, output_dir, "gallery_hbar")


def histogram(output_dir: Path) -> Path:
    """Histogram of a sample with an overlaid mean line."""
    rng = _rng()
    data = rng.normal(50, 12, 600)
    fig, ax = new_figure()
    ax.hist(data, bins=24, color=BLUE, alpha=0.8, edgecolor="white")
    ax.axvline(float(np.mean(data)), color=VERMILLION, lw=2, label="mean")
    ax.set_xlabel("value")
    ax.set_ylabel("frequency")
    ax.set_title("Histogram")
    ax.legend()
    return save_figure(fig, output_dir, "gallery_histogram")


def box_plot(output_dir: Path) -> Path:
    """Box-and-whisker plot across groups."""
    rng = _rng()
    data = [rng.normal(loc, 1.0, 100) for loc in (2, 4, 3, 5)]
    fig, ax = new_figure()
    ax.boxplot(data, tick_labels=["G1", "G2", "G3", "G4"])
    ax.set_ylabel("value")
    ax.set_title("Box plot")
    return save_figure(fig, output_dir, "gallery_box")


def violin_plot(output_dir: Path) -> Path:
    """Violin plot (distribution shape across groups)."""
    rng = _rng()
    data = [rng.normal(loc, scale, 200) for loc, scale in ((2, 0.6), (4, 1.0), (3, 0.4))]
    fig, ax = new_figure()
    ax.violinplot(data, showmeans=True)
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(["G1", "G2", "G3"])
    ax.set_ylabel("value")
    ax.set_title("Violin plot")
    return save_figure(fig, output_dir, "gallery_violin")


def heatmap(output_dir: Path) -> Path:
    """Heatmap (2-D matrix) with a colour bar."""
    x = np.linspace(-3, 3, 60)
    y = np.linspace(-3, 3, 60)
    xx, yy = np.meshgrid(x, y)
    z = np.exp(-(xx**2 + yy**2) / 2)
    fig, ax = new_figure()
    im = ax.imshow(z, extent=(-3, 3, -3, 3), origin="lower", cmap="viridis", aspect="auto")
    fig.colorbar(im, ax=ax, label="density")
    ax.set_title("Heatmap")
    return save_figure(fig, output_dir, "gallery_heatmap")


def contour_plot(output_dir: Path) -> Path:
    """Filled contour plot with labelled levels."""
    x = np.linspace(-3, 3, 100)
    y = np.linspace(-3, 3, 100)
    xx, yy = np.meshgrid(x, y)
    z = np.sin(xx) * np.cos(yy)
    fig, ax = new_figure()
    cs = ax.contourf(xx, yy, z, levels=12, cmap="coolwarm")
    ax.contour(xx, yy, z, levels=12, colors="k", linewidths=0.3)
    fig.colorbar(cs, ax=ax, label="z")
    ax.set_title("Contour plot")
    return save_figure(fig, output_dir, "gallery_contour")


def quiver_field(output_dir: Path) -> Path:
    """Vector field / phase-portrait style quiver plot."""
    x = np.linspace(-2, 2, 16)
    y = np.linspace(-2, 2, 16)
    xx, yy = np.meshgrid(x, y)
    u = -yy
    v = xx
    fig, ax = new_figure()
    ax.quiver(xx, yy, u, v, color=BLUE)
    ax.set_title("Vector field (quiver)")
    ax.set_aspect("equal")
    return save_figure(fig, output_dir, "gallery_quiver")


def step_plot(output_dir: Path) -> Path:
    """Step plot (piecewise-constant signal)."""
    x = np.arange(0, 12)
    y = np.array([0, 1, 1, 3, 2, 2, 4, 4, 3, 5, 5, 6])
    fig, ax = new_figure()
    ax.step(x, y, where="post", color=GREEN, lw=2)
    ax.set_xlabel("step")
    ax.set_ylabel("level")
    ax.set_title("Step plot")
    return save_figure(fig, output_dir, "gallery_step")


def stacked_area(output_dir: Path) -> Path:
    """Stacked area chart (composition over time)."""
    x = np.linspace(0, 10, 50)
    a = 2 + np.sin(x)
    b = 1 + 0.5 * np.cos(x)
    c = 1.5 + 0.3 * x / 10
    fig, ax = new_figure()
    ax.stackplot(x, a, b, c, labels=["A", "B", "C"], colors=(BLUE, ORANGE, GREEN), alpha=0.85)
    ax.set_xlabel("time")
    ax.set_ylabel("amount")
    ax.set_title("Stacked area")
    ax.legend(loc="upper left")
    return save_figure(fig, output_dir, "gallery_stacked_area")


def errorbar_plot(output_dir: Path) -> Path:
    """Mean with error bars."""
    x = np.arange(1, 7)
    y = np.array([2.1, 3.0, 3.6, 4.2, 4.8, 5.1])
    yerr = np.array([0.2, 0.3, 0.25, 0.4, 0.35, 0.3])
    fig, ax = new_figure()
    ax.errorbar(x, y, yerr=yerr, fmt="o-", color=BLUE, ecolor=GRAY, capsize=4)
    ax.set_xlabel("condition")
    ax.set_ylabel("measurement ± SE")
    ax.set_title("Error bars")
    return save_figure(fig, output_dir, "gallery_errorbar")


def log_log_plot(output_dir: Path) -> Path:
    """Log-log plot showing a power law as a straight line."""
    x = np.logspace(0, 3, 50)
    y = 2.0 * x**1.5
    fig, ax = new_figure()
    ax.loglog(x, y, color=VERMILLION, lw=2)
    ax.set_xlabel("x (log)")
    ax.set_ylabel("y (log)")
    ax.set_title("Log-log plot (power law)")
    return save_figure(fig, output_dir, "gallery_loglog")


def pie_chart(output_dir: Path) -> Path:
    """Pie chart with percentage labels."""
    sizes = [40, 25, 20, 15]
    labels = ["Alpha", "Beta", "Gamma", "Delta"]
    fig, ax = new_figure(width=5, height=5)
    ax.pie(
        sizes,
        labels=labels,
        autopct="%1.0f%%",
        colors=(BLUE, ORANGE, GREEN, PURPLE),
        startangle=90,
    )
    ax.set_title("Pie chart")
    return save_figure(fig, output_dir, "gallery_pie")


def annotated_plot(output_dir: Path) -> Path:
    """Line plot with an annotation arrow pointing to a feature."""
    x = np.linspace(0, 10, 200)
    y = np.sin(x) * np.exp(-x / 8)
    fig, ax = new_figure()
    ax.plot(x, y, color=BLUE)
    peak_index = int(np.argmax(y))
    ax.annotate(
        "first peak",
        xy=(x[peak_index], y[peak_index]),
        xytext=(x[peak_index] + 2, y[peak_index] + 0.1),
        arrowprops={"arrowstyle": "->", "color": VERMILLION},
    )
    ax.set_title("Annotated plot")
    return save_figure(fig, output_dir, "gallery_annotated")


def multi_panel(output_dir: Path) -> Path:
    """2x2 multi-panel composite figure."""
    import matplotlib.pyplot as plt

    rng = _rng()
    x = np.linspace(0, 10, 100)
    fig, axes = plt.subplots(2, 2, figsize=(8, 6))
    axes[0, 0].plot(x, np.sin(x), color=BLUE)
    axes[0, 0].set_title("(a) line")
    axes[0, 1].scatter(x, np.cos(x) + rng.normal(0, 0.1, x.size), s=8, color=GREEN)
    axes[0, 1].set_title("(b) scatter")
    axes[1, 0].bar(["p", "q", "r"], [3, 5, 2], color=ORANGE)
    axes[1, 0].set_title("(c) bar")
    axes[1, 1].hist(rng.normal(0, 1, 300), bins=20, color=PURPLE, edgecolor="white")
    axes[1, 1].set_title("(d) histogram")
    for ax in axes.flat:
        ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.5)
    fig.suptitle("Multi-panel composite figure", fontsize=13)
    return save_figure(fig, output_dir, "gallery_multipanel")


# Registry: name -> generator. Add new gallery plots here.
GALLERY: tuple[tuple[str, Callable[[Path], Path]], ...] = (
    ("line", line_plot),
    ("scatter_fit", scatter_with_fit),
    ("bar", bar_chart),
    ("grouped_bar", grouped_bar),
    ("hbar", horizontal_bar),
    ("histogram", histogram),
    ("box", box_plot),
    ("violin", violin_plot),
    ("heatmap", heatmap),
    ("contour", contour_plot),
    ("quiver", quiver_field),
    ("step", step_plot),
    ("stacked_area", stacked_area),
    ("errorbar", errorbar_plot),
    ("loglog", log_log_plot),
    ("pie", pie_chart),
    ("annotated", annotated_plot),
    ("multipanel", multi_panel),
)


def generate_gallery_figures(output_dir: Path) -> list[Path]:
    """Generate every gallery figure into ``output_dir``."""
    paths = [fn(output_dir) for _, fn in GALLERY]
    logger.info("generated %d gallery figures in %s", len(paths), output_dir)
    return paths


__all__ = [
    "GALLERY",
    "annotated_plot",
    "bar_chart",
    "box_plot",
    "contour_plot",
    "errorbar_plot",
    "generate_gallery_figures",
    "grouped_bar",
    "heatmap",
    "histogram",
    "horizontal_bar",
    "line_plot",
    "log_log_plot",
    "multi_panel",
    "pie_chart",
    "quiver_field",
    "scatter_with_fit",
    "stacked_area",
    "step_plot",
    "violin_plot",
]
