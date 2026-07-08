"""Topic and co-occurrence visualizations."""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from visualization.style import VIZ_CONFIG

logger = logging.getLogger(__name__)


def plot_topic_term_bars(topics: list[dict], output_path: Path) -> Path:
    """Process plot topic term bars."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    n_topics = len(topics)
    if n_topics == 0:
        fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure_size"], dpi=VIZ_CONFIG["dpi"])
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    ncols = min(n_topics, 3)
    nrows = (n_topics + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 4 * nrows), dpi=VIZ_CONFIG["dpi"])
    if n_topics == 1:
        axes = np.array([axes])
    axes = np.atleast_2d(axes)
    palette = VIZ_CONFIG["palette"]

    for idx, topic in enumerate(topics):
        row, col = divmod(idx, ncols)
        ax = axes[row, col]
        words = topic.get("top_words", [])[:10][::-1]
        weights = topic.get("weights", [])[:10][::-1]
        if not words:
            ax.set_axis_off()
            continue
        ax.barh(
            range(len(words)),
            weights,
            color=palette[idx % len(palette)],
            edgecolor="white",
            linewidth=0.3,
        )
        ax.set_yticks(range(len(words)))
        ax.set_yticklabels(words, fontsize=max(VIZ_CONFIG["font_size"] - 2, 16))
        ax.set_title(
            f"Topic {topic.get('topic_id', idx)}",
            fontsize=VIZ_CONFIG["font_size"],
            fontweight="bold",
        )
        ax.grid(axis="x", alpha=VIZ_CONFIG["grid_alpha"])

    for idx in range(n_topics, nrows * ncols):
        row, col = divmod(idx, ncols)
        axes[row, col].set_axis_off()

    fig.suptitle(
        "NMF Topic — Top Terms",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
        y=1.02,
    )
    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_cooccurrence_matrix(
    documents: list[list[str]],
    output_path: Path,
    *,
    n_terms: int = 30,
) -> Path:
    """Process plot cooccurrence matrix."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 10), dpi=VIZ_CONFIG["dpi"])
    if not documents:
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    term_doc_freq: dict[str, int] = {}
    for tokens in documents:
        for token in set(tokens):
            term_doc_freq[token] = term_doc_freq.get(token, 0) + 1

    top_terms = sorted(term_doc_freq.keys(), key=lambda t: -term_doc_freq[t])[:n_terms]
    term_idx = {t: i for i, t in enumerate(top_terms)}
    n = len(top_terms)
    if n < 2:
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    cooc = np.zeros((n, n), dtype=np.float64)
    for tokens in documents:
        present = [t for t in set(tokens) if t in term_idx]
        for i_term in range(len(present)):
            for j_term in range(i_term + 1, len(present)):
                a, b = term_idx[present[i_term]], term_idx[present[j_term]]
                cooc[a, b] += 1
                cooc[b, a] += 1

    np.fill_diagonal(cooc, 0.0)
    max_val = cooc.max()
    if max_val > 0:
        cooc /= max_val

    im = ax.imshow(cooc, cmap="Blues", interpolation="nearest", vmin=0, vmax=1)
    ax.set_xticks(range(n))
    ax.set_xticklabels(
        top_terms,
        rotation=45,
        ha="right",
        fontsize=max(VIZ_CONFIG["font_size"] - 3, 16),
    )
    ax.set_yticks(range(n))
    ax.set_yticklabels(top_terms, fontsize=max(VIZ_CONFIG["font_size"] - 3, 16))
    ax.set_title(
        "Term Co-occurrence Matrix",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
    )
    fig.colorbar(im, ax=ax, label="Normalized Co-occurrence", shrink=0.8)
    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)
    return output_path
