"""Word cloud visualization."""

from __future__ import annotations

import importlib.util
import logging
import math
from pathlib import Path

from matplotlib import colormaps
from matplotlib.transforms import Bbox

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from template_literature_meta_analysis.visualization.style import VIZ_CONFIG

logger = logging.getLogger(__name__)

GOLDEN_ANGLE_STEP = 0.35
MAX_PLACEMENT_STEPS = 2400


def plot_word_cloud(
    word_weights: dict[str, float],
    output_path: Path,
    *,
    max_words: int = 100,
    title: str | None = None,
) -> Path:
    """Process plot word cloud.

    The packed layout comes from the ``wordcloud`` extension when it is
    installed. CPython 3.15 has no distribution of that extension yet, so a
    deterministic spiral packer renders the same figure from the same weights
    instead of leaving the manuscript's reference unresolved.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 8), dpi=VIZ_CONFIG["dpi"])
    if not word_weights:
        ax.text(
            0.5,
            0.5,
            "No word data available",
            ha="center",
            va="center",
            fontsize=VIZ_CONFIG["font_size"],
        )
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    if _wordcloud_available():
        from wordcloud import WordCloud

        wc = WordCloud(
            width=1200,
            height=800,
            max_words=max_words,
            background_color="white",
            colormap="cividis",
            prefer_horizontal=0.7,
            min_font_size=16,
            random_state=42,
        ).generate_from_frequencies(word_weights)
        ax.imshow(wc, interpolation="bilinear")
    else:
        _pack_terms(ax, fig, word_weights, max_words=max_words)
    ax.set_axis_off()
    ax.set_title(
        title or "Literature Corpus — Term Cloud",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
        pad=12,
    )
    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)
    logger.info("Word cloud saved: %s (%d terms)", output_path, len(word_weights))
    return output_path


def _wordcloud_available() -> bool:
    """Return whether the packed-layout extension can be imported."""
    return importlib.util.find_spec("wordcloud") is not None


def _pack_terms(ax, fig, word_weights: dict[str, float], *, max_words: int) -> None:
    """Place terms on a deterministic golden-angle spiral without overlaps.

    Larger weights get larger type; the first term that fits at a candidate
    centre keeps it, so identical inputs render identical bytes.
    """
    items = sorted(word_weights.items(), key=lambda item: (-item[1], item[0]))[:max_words]
    heaviest = items[0][1] or 1.0
    colormap = colormaps["cividis"]
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    placed: list[Bbox] = []
    for index, (term, weight) in enumerate(items):
        size = 16.0 + 38.0 * math.sqrt(max(weight, 0.0) / heaviest)
        for step in range(MAX_PLACEMENT_STEPS):
            radius = 0.004 * step
            x = 0.5 + radius * math.cos(step * GOLDEN_ANGLE_STEP) * 1.4
            y = 0.5 + radius * math.sin(step * GOLDEN_ANGLE_STEP)
            if not (0.03 <= x <= 0.97 and 0.03 <= y <= 0.97):
                if radius > 0.8:
                    break
                continue
            drawn = ax.text(
                x,
                y,
                term,
                fontsize=size,
                ha="center",
                va="center",
                color=colormap(index / max(len(items) - 1, 1)),
                transform=ax.transAxes,
            )
            bounds = drawn.get_window_extent(renderer).transformed(ax.transAxes.inverted())
            if not any(bounds.overlaps(other) for other in placed):
                placed.append(bounds)
                break
            drawn.remove()
    logger.info("Word cloud packed %d of %d terms with the spiral fallback", len(placed), len(items))
