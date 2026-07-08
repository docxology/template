"""Word cloud visualization."""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from visualization.style import VIZ_CONFIG

logger = logging.getLogger(__name__)


def plot_word_cloud(
    word_weights: dict[str, float],
    output_path: Path,
    *,
    max_words: int = 100,
    title: str | None = None,
) -> Path:
    """Process plot word cloud."""
    from wordcloud import WordCloud

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
