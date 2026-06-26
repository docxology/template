"""Descriptive statistics visualizations: citation distribution, top venues, author productivity."""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from visualization.style import VIZ_CONFIG, apply_visual_style

logger = logging.getLogger(__name__)

_FIG_SIZE = (12, 7)


def plot_citation_distribution(
    citation_dist: dict,
    output_path: Path,
) -> Path:
    """Plot citation count distribution as a bar chart with Gini annotation.

    Args:
        citation_dist: The ``citation_distribution`` dict from
            ``descriptive_stats.json`` — must contain ``histogram``, ``gini``,
            ``n``, and ``total_citations``.
        output_path: Destination PNG path.

    Returns:
        The output path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    apply_visual_style()

    histogram = citation_dist.get("histogram", {})
    gini = citation_dist.get("gini", 0.0)
    n = citation_dist.get("n", 0)
    total = citation_dist.get("total_citations", 0)

    fig, ax = plt.subplots(figsize=_FIG_SIZE, dpi=VIZ_CONFIG["dpi"])

    if not histogram:
        ax.text(
            0.5,
            0.5,
            "No citation data available",
            ha="center",
            va="center",
            fontsize=VIZ_CONFIG["font_size"],
        )
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    labels = list(histogram.keys())
    counts = list(histogram.values())
    colors = VIZ_CONFIG["palette"] * (len(labels) // len(VIZ_CONFIG["palette"]) + 1)

    bars = ax.bar(labels, counts, color=colors[: len(labels)], edgecolor="white", linewidth=0.5)

    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(counts) * 0.02,
                str(count),
                ha="center",
                va="bottom",
                fontsize=VIZ_CONFIG["font_size"] - 3,
                fontweight="bold",
            )

    ax.set_xlabel("Citation Count Bucket", fontsize=VIZ_CONFIG["font_size"])
    ax.set_ylabel("Number of Papers", fontsize=VIZ_CONFIG["font_size"])
    ax.set_title(
        f"Citation Distribution (Gini = {gini:.3f}, N = {n:,}, Total = {total:,})",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
        pad=12,
    )
    ax.tick_params(axis="x", labelsize=VIZ_CONFIG["font_size"] - 2)
    ax.tick_params(axis="y", labelsize=VIZ_CONFIG["tick_size"])
    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)
    logger.info("Citation distribution saved: %s", output_path)
    return output_path


def plot_top_venues(
    stats: dict,
    output_path: Path,
    top_n: int = 15,
) -> Path:
    """Plot top publication venues as a horizontal bar chart.

    Args:
        stats: The ``descriptive_stats`` dict from ``descriptive_stats.json`` —
            must contain ``counts_by_venue``.
        output_path: Destination PNG path.
        top_n: Maximum number of venues to display.

    Returns:
        The output path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    apply_visual_style()

    venues = stats.get("counts_by_venue", {})
    fig, ax = plt.subplots(figsize=_FIG_SIZE, dpi=VIZ_CONFIG["dpi"])

    if not venues:
        ax.text(
            0.5,
            0.5,
            "No venue data available",
            ha="center",
            va="center",
            fontsize=VIZ_CONFIG["font_size"],
        )
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    sorted_venues = sorted(venues.items(), key=lambda x: -x[1])[:top_n]
    labels = [v[0][:40] for v in sorted_venues]  # Truncate long venue names
    counts = [v[1] for v in sorted_venues]

    y_pos = np.arange(len(labels))
    colors = VIZ_CONFIG["palette"] * (len(labels) // len(VIZ_CONFIG["palette"]) + 1)

    ax.barh(y_pos, counts, color=colors[: len(labels)], edgecolor="white", linewidth=0.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=VIZ_CONFIG["font_size"] - 3)
    ax.invert_yaxis()
    ax.set_xlabel("Number of Papers", fontsize=VIZ_CONFIG["font_size"])
    ax.set_title(
        f"Top {len(labels)} Publication Venues",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
        pad=12,
    )
    ax.tick_params(axis="x", labelsize=VIZ_CONFIG["tick_size"])
    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)
    logger.info("Top venues chart saved: %s", output_path)
    return output_path


def plot_author_productivity(
    author_data: list,
    output_path: Path,
    top_n: int = 20,
) -> Path:
    """Plot top authors by publication count as a horizontal bar chart.

    Args:
        author_data: List of ``[name, count]`` pairs from
            ``descriptive_stats.json``.
        output_path: Destination PNG path.
        top_n: Maximum number of authors to display.

    Returns:
        The output path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    apply_visual_style()

    fig, ax = plt.subplots(figsize=_FIG_SIZE, dpi=VIZ_CONFIG["dpi"])

    if not author_data:
        ax.text(
            0.5,
            0.5,
            "No author data available",
            ha="center",
            va="center",
            fontsize=VIZ_CONFIG["font_size"],
        )
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    top_authors = author_data[:top_n]
    labels = [a[0][:30] for a in top_authors]  # Truncate long author names
    counts = [a[1] for a in top_authors]

    y_pos = np.arange(len(labels))
    colors = VIZ_CONFIG["palette"] * (len(labels) // len(VIZ_CONFIG["palette"]) + 1)

    ax.barh(y_pos, counts, color=colors[: len(labels)], edgecolor="white", linewidth=0.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=VIZ_CONFIG["font_size"] - 3)
    ax.invert_yaxis()
    ax.set_xlabel("Number of Papers", fontsize=VIZ_CONFIG["font_size"])
    ax.set_title(
        f"Top {len(labels)} Authors by Publication Count",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
        pad=12,
    )
    ax.tick_params(axis="x", labelsize=VIZ_CONFIG["tick_size"])
    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)
    logger.info("Author productivity chart saved: %s", output_path)
    return output_path


def plot_similarity_heatmap(
    similar_pairs: list,
    output_path: Path,
) -> Path:
    """Plot top similar document pairs as a ranked bar chart.

    Args:
        similar_pairs: List of ``{"paper_a", "paper_b", "similarity"}`` dicts
            from ``embedding_analysis.json``.
        output_path: Destination PNG path.

    Returns:
        The output path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    apply_visual_style()

    fig, ax = plt.subplots(figsize=_FIG_SIZE, dpi=VIZ_CONFIG["dpi"])

    if not similar_pairs:
        ax.text(
            0.5,
            0.5,
            "No similarity data available",
            ha="center",
            va="center",
            fontsize=VIZ_CONFIG["font_size"],
        )
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    # Take top 15 pairs
    pairs = similar_pairs[:15]
    labels = [f"{p['paper_a'][:15]}… — {p['paper_b'][:15]}…" for p in pairs]
    scores = [p["similarity"] for p in pairs]

    y_pos = np.arange(len(labels))
    colors = VIZ_CONFIG["palette"] * (len(labels) // len(VIZ_CONFIG["palette"]) + 1)

    ax.barh(y_pos, scores, color=colors[: len(labels)], edgecolor="white", linewidth=0.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=VIZ_CONFIG["font_size"] - 4)
    ax.invert_yaxis()
    ax.set_xlabel("Cosine Similarity", fontsize=VIZ_CONFIG["font_size"])
    ax.set_title(
        f"Top {len(labels)} Most Similar Document Pairs",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
        pad=12,
    )
    ax.set_xlim(0, 1.0)
    ax.tick_params(axis="x", labelsize=VIZ_CONFIG["tick_size"])
    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)
    logger.info("Similarity heatmap saved: %s", output_path)
    return output_path


def plot_entity_bar_chart(
    entities: dict,
    output_path: Path,
    top_n: int = 20,
) -> Path:
    """Plot top named entities as a horizontal bar chart.

    Args:
        entities: Dict mapping entity name to count from ``entities.json``.
        output_path: Destination PNG path.
        top_n: Maximum number of entities to display.

    Returns:
        The output path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    apply_visual_style()

    fig, ax = plt.subplots(figsize=_FIG_SIZE, dpi=VIZ_CONFIG["dpi"])

    if not entities:
        ax.text(
            0.5,
            0.5,
            "No entity data available",
            ha="center",
            va="center",
            fontsize=VIZ_CONFIG["font_size"],
        )
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    sorted_entities = sorted(entities.items(), key=lambda x: -x[1])[:top_n]
    labels = [e[0][:30] for e in sorted_entities]
    counts = [e[1] for e in sorted_entities]

    y_pos = np.arange(len(labels))
    colors = VIZ_CONFIG["palette"] * (len(labels) // len(VIZ_CONFIG["palette"]) + 1)

    ax.barh(y_pos, counts, color=colors[: len(labels)], edgecolor="white", linewidth=0.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=VIZ_CONFIG["font_size"] - 3)
    ax.invert_yaxis()
    ax.set_xlabel("Frequency", fontsize=VIZ_CONFIG["font_size"])
    ax.set_title(
        f"Top {len(labels)} Named Entities in Abstracts",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
        pad=12,
    )
    ax.tick_params(axis="x", labelsize=VIZ_CONFIG["tick_size"])
    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)
    logger.info("Entity bar chart saved: %s", output_path)
    return output_path
