"""Field overview visualizations for the literature meta-analysis.

Provides summary bar charts and pie charts showing the distribution
of publications across the configured subfields.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from visualization.style import VIZ_CONFIG, SUBFIELD_NAMES


def _format_subfield_label(sf: str) -> str:
    """Standardize subfield label using SUBFIELD_NAMES."""
    return SUBFIELD_NAMES.get(sf, sf.replace("_", " ").title())


def plot_field_summary(
    total_papers: int,
    subfield_counts: dict[str, int],
    output_path: Path,
) -> Path:
    """Create a summary bar chart of papers per subfield.

    Bars are colored using the subfield_colors from VIZ_CONFIG.
    The total paper count is displayed in the title.

    Args:
        total_papers: Total number of papers in the corpus.
        subfield_counts: Mapping of subfield name to paper count.
        output_path: File path to save the figure.

    Returns:
        The output_path after saving.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    subfields = list(subfield_counts.keys())
    counts = list(subfield_counts.values())
    colors = [VIZ_CONFIG["subfield_colors"].get(sf, VIZ_CONFIG["palette"][0]) for sf in subfields]

    fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure_size"], dpi=VIZ_CONFIG["dpi"])

    bars = ax.barh(
        [_format_subfield_label(sf) for sf in subfields],
        counts,
        color=colors,
        edgecolor="white",
        linewidth=0.5,
    )

    # Add count + percentage labels on bars
    for bar, count in zip(bars, counts):
        pct = 100 * count / total_papers if total_papers else 0
        ax.text(
            bar.get_width() + max(counts) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{count} ({pct:.1f}%)",
            va="center",
            fontsize=VIZ_CONFIG["font_size"] - 1,
        )

    ax.set_xlabel("Number of Papers", fontsize=VIZ_CONFIG["font_size"])
    ax.set_title(
        f"Literature by Subfield (N={total_papers})",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
    )
    ax.grid(axis="x", alpha=VIZ_CONFIG["grid_alpha"])
    ax.invert_yaxis()

    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)

    return output_path


def plot_subfield_distribution(
    subfield_counts: dict[str, int],
    output_path: Path,
) -> Path:
    """Create a pie chart showing proportional distribution of subfields.

    Subfields with fewer than 2% of papers are grouped into an "Other"
    category to keep the chart readable.

    Args:
        subfield_counts: Mapping of subfield name to paper count.
        output_path: File path to save the figure.

    Returns:
        The output_path after saving.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total = sum(subfield_counts.values())
    if total == 0:
        # Generate an empty figure if no data
        fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure_size"], dpi=VIZ_CONFIG["dpi"])
        ax.text(0.5, 0.5, "No data available", ha="center", va="center", fontsize=VIZ_CONFIG["font_size"])
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    # Group small slices into "Other"
    threshold = 0.02 * total
    labels = []
    sizes = []
    colors = []
    other_count = 0

    for sf, count in subfield_counts.items():
        if count >= threshold:
            labels.append(_format_subfield_label(sf))
            sizes.append(count)
            colors.append(VIZ_CONFIG["subfield_colors"].get(sf, VIZ_CONFIG["palette"][0]))
        else:
            other_count += count

    if other_count > 0:
        labels.append("Other")
        sizes.append(other_count)
        colors.append("#999999")

    fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure_size"], dpi=VIZ_CONFIG["dpi"])

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        startangle=140,
        pctdistance=0.85,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=1.5),
    )

    # Center text for donut
    ax.text(
        0,
        0,
        f"N={total:,}",
        ha="center",
        va="center",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
    )

    for text in texts:
        text.set_fontsize(VIZ_CONFIG["font_size"] - 1)
    for autotext in autotexts:
        autotext.set_fontsize(VIZ_CONFIG["font_size"] - 2)

    ax.set_title(
        "Subfield Distribution",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
    )

    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)

    return output_path
