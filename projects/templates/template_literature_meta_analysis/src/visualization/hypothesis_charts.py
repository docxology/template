"""Hypothesis scoring visualizations.

Provides dashboard bar charts and evidence timeline plots for
tracking hypothesis support/contradiction across the
literature.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from visualization.style import VIZ_CONFIG, HYPOTHESIS_NAMES


def _format_hypothesis_label(key: str) -> str:
    """Convert hypothesis key to readable label using HYPOTHESIS_NAMES."""
    # Try direct upper-case lookup (H1, H2, ...)
    upper = key.upper().split("_")[0] if "_" in key else key.upper()
    if upper in HYPOTHESIS_NAMES:
        return f"{upper}: {HYPOTHESIS_NAMES[upper]}"
    # Fallback to title-casing the raw key
    return key.replace("_", " ").title()


def plot_hypothesis_dashboard(
    scores: dict[str, float],
    output_path: Path,
) -> Path:
    """Horizontal bar chart of hypothesis scores in the range [-1, 1].

    Bars are colored green for positive scores (evidence supports
    the hypothesis) and red for negative scores (evidence contradicts).
    A vertical line at x=0 marks the neutral boundary.

    Args:
        scores: Mapping of hypothesis name/id to score in [-1, 1].
        output_path: File path to save the figure.

    Returns:
        The output_path after saving.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not scores:
        fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure_size"], dpi=VIZ_CONFIG["dpi"])
        ax.text(0.5, 0.5, "No hypothesis scores available", ha="center", va="center", fontsize=VIZ_CONFIG["font_size"])
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    # Sort hypotheses by score so the highest is at the top of the chart
    sorted_pairs = sorted(scores.items(), key=lambda x: x[1])
    hypotheses = [p[0] for p in sorted_pairs]
    values = [p[1] for p in sorted_pairs]

    # Color: green for positive, red for negative
    colors = ["#009E73" if v >= 0 else "#D55E00" for v in values]

    fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure_size"], dpi=VIZ_CONFIG["dpi"])

    y_positions = range(len(hypotheses))
    ax.barh(y_positions, values, color=colors, edgecolor="white", linewidth=0.5, height=0.6)

    ax.set_yticks(list(y_positions))
    ax.set_yticklabels(
        [_format_hypothesis_label(h) for h in hypotheses],
        fontsize=max(VIZ_CONFIG["font_size"] - 1, 16),
    )

    # Add score labels
    for i, (val, hyp) in enumerate(zip(values, hypotheses)):
        offset = 0.02 if val >= 0 else -0.02
        ha = "left" if val >= 0 else "right"
        ax.text(
            val + offset,
            i,
            f"{val:+.2f}",
            va="center",
            ha=ha,
            fontsize=max(VIZ_CONFIG["font_size"] - 2, 16),
            fontweight="bold",
        )

    # Neutral line
    ax.axvline(x=0, color="black", linewidth=1.0, linestyle="-")

    ax.set_xlim(-1.1, 1.1)
    ax.set_xlabel("Evidence Score", fontsize=VIZ_CONFIG["font_size"])
    ax.set_title(
        "Hypothesis Evidence Dashboard",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
    )
    # Add N= subtitle
    n_hypotheses = len(scores)
    ax.text(
        0.5,
        1.0,
        f"N = {n_hypotheses} hypotheses",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=max(VIZ_CONFIG["font_size"] - 2, 16),
        color="gray",
    )
    ax.grid(axis="x", alpha=VIZ_CONFIG["grid_alpha"])
    ax.invert_yaxis()

    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)

    return output_path


def plot_evidence_timeline(
    yearly_scores: dict[str, dict[int, float]],
    output_path: Path,
) -> Path:
    """Line chart showing hypothesis score evolution over time.

    One line per hypothesis, with distinct colors from the palette.
    A horizontal dashed line at y=0 marks the neutral boundary.

    Args:
        yearly_scores: Mapping of hypothesis name/id to a dict
            of year -> score.
        output_path: File path to save the figure.

    Returns:
        The output_path after saving.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure_size"], dpi=VIZ_CONFIG["dpi"])

    if not yearly_scores:
        ax.text(0.5, 0.5, "No temporal evidence data", ha="center", va="center", fontsize=VIZ_CONFIG["font_size"])
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    palette = VIZ_CONFIG["palette"]

    for i, (hypothesis, year_data) in enumerate(yearly_scores.items()):
        if not year_data:
            continue
        years = sorted(year_data.keys())
        values = [year_data[y] for y in years]
        color = palette[i % len(palette)]
        label = _format_hypothesis_label(hypothesis)
        ax.plot(years, values, color=color, linewidth=2.0, marker="o", markersize=5, label=label, alpha=0.85)

    # Neutral line and shaded region
    ax.axhline(y=0, color="black", linewidth=1.0, linestyle="--", alpha=0.6)
    ax.axhspan(-0.1, 0.1, color="gray", alpha=0.1, zorder=0)

    ax.set_ylim(-1.1, 1.1)
    ax.set_xlabel("Year", fontsize=VIZ_CONFIG["font_size"])
    ax.set_ylabel("Cumulative Evidence Score", fontsize=VIZ_CONFIG["font_size"])
    ax.set_title(
        "Hypothesis Evidence Over Time",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
    )
    ax.legend(loc="best", fontsize=max(VIZ_CONFIG["font_size"] - 2, 16), framealpha=0.9)
    ax.grid(alpha=VIZ_CONFIG["grid_alpha"])

    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)

    return output_path


def plot_assertion_type_breakdown(
    assertion_counts: dict[str, dict[str, int]],
    output_path: Path,
) -> Path:
    """Stacked bar chart of assertion types (supports/contradicts/neutral) per hypothesis.

    Args:
        assertion_counts: Mapping of hypothesis_id to a dict with keys
            'supports', 'contradicts', 'neutral' and integer count values.
        output_path: File path to save the figure.

    Returns:
        The output_path after saving.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure_size"], dpi=VIZ_CONFIG["dpi"])

    if not assertion_counts:
        ax.text(0.5, 0.5, "No assertion data", ha="center", va="center", fontsize=VIZ_CONFIG["font_size"])
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    hypotheses = list(assertion_counts.keys())
    supports = [assertion_counts[h].get("supports", 0) for h in hypotheses]
    contradicts = [assertion_counts[h].get("contradicts", 0) for h in hypotheses]
    neutrals = [assertion_counts[h].get("neutral", 0) for h in hypotheses]

    y_pos = range(len(hypotheses))
    bar_height = 0.6

    # Stacked horizontal bars
    ax.barh(y_pos, supports, height=bar_height, color="#009E73", label="Supports", edgecolor="white", linewidth=0.5)
    ax.barh(
        y_pos,
        contradicts,
        height=bar_height,
        left=supports,
        color="#D55E00",
        label="Contradicts",
        edgecolor="white",
        linewidth=0.5,
    )
    left_offset = [s + c for s, c in zip(supports, contradicts)]
    ax.barh(
        y_pos,
        neutrals,
        height=bar_height,
        left=left_offset,
        color="#56B4E9",
        label="Neutral",
        edgecolor="white",
        linewidth=0.5,
    )

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(
        [_format_hypothesis_label(h) for h in hypotheses],
        fontsize=max(VIZ_CONFIG["font_size"] - 2, 16),
    )

    ax.set_xlabel("Number of Assertions", fontsize=VIZ_CONFIG["font_size"])
    ax.set_title(
        "Assertion Type Breakdown by Hypothesis",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
    )
    ax.legend(loc="lower right", fontsize=max(VIZ_CONFIG["font_size"] - 2, 16), framealpha=0.9)
    ax.grid(axis="x", alpha=VIZ_CONFIG["grid_alpha"])
    ax.invert_yaxis()

    # Total count and support% labels at bar ends
    for i, h in enumerate(hypotheses):
        total = sum(assertion_counts[h].get(k, 0) for k in ("supports", "contradicts", "neutral"))
        sup = assertion_counts[h].get("supports", 0)
        pct = 100 * sup / total if total > 0 else 0
        ax.text(
            total + max(1, max(supports) + max(contradicts) + max(neutrals)) * 0.01,
            i,
            f"{total} ({pct:.0f}% support)",
            va="center",
            fontsize=max(VIZ_CONFIG["font_size"] - 2, 16),
            fontweight="bold",
        )

    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)

    return output_path


def plot_assertion_summary(
    total_assertions: int,
    type_counts: dict[str, int],
    hypothesis_counts: dict[str, int],
    output_path: Path,
) -> Path:
    """Summary panel with assertion statistics: total count, type pie, and per-hypothesis bars.

    Args:
        total_assertions: Total number of assertions extracted.
        type_counts: Mapping of assertion_type ('supports', 'contradicts',
            'neutral') to count.
        hypothesis_counts: Mapping of hypothesis_id to total assertion count.
        output_path: File path to save the figure.

    Returns:
        The output_path after saving.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), dpi=VIZ_CONFIG["dpi"])

    # Left panel: Type breakdown pie chart
    if type_counts and total_assertions > 0:
        labels = []
        sizes = []
        colors_pie = {"supports": "#009E73", "contradicts": "#D55E00", "neutral": "#56B4E9"}
        for t in ["supports", "contradicts", "neutral"]:
            count = type_counts.get(t, 0)
            if count > 0:
                labels.append(t.title())
                sizes.append(count)

        pie_colors = [colors_pie.get(l.lower(), "#999999") for l in labels]
        wedges, texts, autotexts = ax1.pie(
            sizes,
            labels=labels,
            colors=pie_colors,
            autopct="%1.1f%%",
            startangle=140,
            pctdistance=0.85,
        )
        for text in texts:
            text.set_fontsize(max(VIZ_CONFIG["font_size"] - 2, 16))
        for autotext in autotexts:
            autotext.set_fontsize(max(VIZ_CONFIG["font_size"] - 3, 16))
        ax1.set_title(
            f"Assertion Types (N={total_assertions:,})",
            fontsize=VIZ_CONFIG["title_size"],
            fontweight="bold",
        )
    else:
        ax1.text(0.5, 0.5, "No assertions", ha="center", va="center", fontsize=VIZ_CONFIG["font_size"])
        ax1.set_axis_off()

    # Right panel: Per-hypothesis assertion counts
    if hypothesis_counts:
        hyps = list(hypothesis_counts.keys())
        counts = list(hypothesis_counts.values())
        colors_bar = [VIZ_CONFIG["palette"][i % len(VIZ_CONFIG["palette"])] for i in range(len(hyps))]

        y_pos = range(len(hyps))
        bars = ax2.barh(y_pos, counts, color=colors_bar, edgecolor="white", linewidth=0.5, height=0.6)

        # Add count labels
        for bar, count in zip(bars, counts):
            ax2.text(
                bar.get_width() + max(counts) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                str(count),
                va="center",
                fontsize=max(VIZ_CONFIG["font_size"] - 2, 16),
            )

        ax2.set_yticks(list(y_pos))
        ax2.set_yticklabels(
            [_format_hypothesis_label(h) for h in hyps],
            fontsize=max(VIZ_CONFIG["font_size"] - 2, 16),
        )
        ax2.set_xlabel("Assertions", fontsize=VIZ_CONFIG["font_size"])
        ax2.set_title(
            "Assertions per Hypothesis",
            fontsize=VIZ_CONFIG["title_size"],
            fontweight="bold",
        )
        ax2.grid(axis="x", alpha=VIZ_CONFIG["grid_alpha"])
        ax2.invert_yaxis()
    else:
        ax2.text(0.5, 0.5, "No hypothesis data", ha="center", va="center", fontsize=VIZ_CONFIG["font_size"])
        ax2.set_axis_off()

    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)

    return output_path
