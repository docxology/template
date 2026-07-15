"""Temporal trend visualizations for the literature corpus.

Provides growth curve plots (annual and cumulative) and stacked area
charts showing subfield evolution over time.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from visualization.style import VIZ_CONFIG, SUBFIELD_NAMES


def _format_subfield_label(sf: str) -> str:
    """Standardize subfield label using SUBFIELD_NAMES."""
    return str(SUBFIELD_NAMES.get(sf, sf.replace("_", " ").title()))


def plot_growth_curve(
    year_counts: dict[int, int],
    cumulative: dict[int, int],
    output_path: Path,
    smoothed_annual: dict[int, float] | None = None,
) -> Path:
    """Dual-axis plot: bar chart of annual counts + line of cumulative.

    The left y-axis shows annual publication counts as bars.
    The right y-axis shows cumulative publications as a line.
    An optional smoothed trendline (e.g., moving average) can be drawn.

    Args:
        year_counts: Mapping of year to publication count.
        cumulative: Mapping of year to cumulative count.
        output_path: File path to save the figure.
        smoothed_annual: Optional mapping of year to smoothed count.

    Returns:
        The output_path after saving.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not year_counts:
        fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure_size"], dpi=VIZ_CONFIG["dpi"])
        ax.text(0.5, 0.5, "No temporal data available", ha="center", va="center", fontsize=VIZ_CONFIG["font_size"])
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    years = sorted(year_counts.keys())
    annual = [year_counts[y] for y in years]
    cumul = [cumulative.get(y, 0) for y in years]

    fig, ax1 = plt.subplots(figsize=VIZ_CONFIG["figure_size"], dpi=VIZ_CONFIG["dpi"])

    # Bar chart for annual counts
    bar_color = VIZ_CONFIG["palette"][0]
    ax1.bar(years, annual, color=bar_color, alpha=0.7, label="Annual Publications")

    # Optional smoothed trendline
    if smoothed_annual:
        smooth_vals = [smoothed_annual.get(y, 0) for y in years]
        trend_color = VIZ_CONFIG["palette"][5]  # Red-orange
        ax1.plot(years, smooth_vals, color=trend_color, linewidth=2.5, linestyle="--", label="Trend (Moving Avg)")

    ax1.set_xlabel("Year", fontsize=VIZ_CONFIG["font_size"])
    ax1.set_ylabel("Annual Publications", color=bar_color, fontsize=VIZ_CONFIG["font_size"])
    ax1.tick_params(axis="y", labelcolor=bar_color)

    # Line chart for cumulative on right axis
    ax2 = ax1.twinx()
    line_color = VIZ_CONFIG["palette"][3]
    ax2.plot(years, cumul, color=line_color, linewidth=2.5, marker="o", markersize=5, label="Cumulative")
    ax2.set_ylabel("Cumulative Publications", color=line_color, fontsize=VIZ_CONFIG["font_size"])
    ax2.tick_params(axis="y", labelcolor=line_color)

    ax1.set_title(
        "Publication Growth Over Time",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
    )

    # Annotate peak year
    if annual:
        peak_idx = int(np.argmax(annual))
        peak_year = years[peak_idx]
        peak_count = annual[peak_idx]
        ax1.annotate(
            f"Peak: {peak_year}\n({peak_count} papers)",
            xy=(peak_year, peak_count),
            xytext=(peak_year - 5, peak_count * 1.15),
            fontsize=max(VIZ_CONFIG["font_size"] - 2, 16),
            fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=bar_color, lw=1.5),
            ha="center",
        )

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=max(VIZ_CONFIG["font_size"] - 2, 16))

    # CAGR and total N annotation.
    # IMPORTANT: this MUST match the canonical CAGR in analysis/temporal_analysis.py
    # (annualised growth of yearly publication VOLUME, end-year vs first-year annual
    # count) so the figure and the manuscript's injected {{CAGR_PCT}} agree. Computing
    # it from CUMULATIVE counts here previously produced a different number under the
    # same "CAGR" label — an internal contradiction within the same paper.
    total_n = sum(annual)
    if len(years) >= 2:
        ratio = annual[-1] / max(annual[0], 1)
        span = years[-1] - years[0]
        cagr = (ratio ** (1.0 / span) - 1) * 100 if span > 0 else 0
        ax1.text(
            0.98,
            0.55,
            f"N = {total_n:,}\nCAGR = {cagr:.1f}%\nSpan: {years[0]}–{years[-1]}",
            transform=ax1.transAxes,
            ha="right",
            va="top",
            fontsize=max(VIZ_CONFIG["font_size"] - 2, 16),
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray", alpha=0.85),
        )

    # Annotate median year
    if annual:
        weighted_years = []
        for y, c in zip(years, annual):
            weighted_years.extend([y] * c)
        if weighted_years:
            median_year = int(np.median(weighted_years))
            ax1.axvline(median_year, color="gray", linestyle=":", linewidth=1.5, alpha=0.7)
            ax1.text(
                median_year + 0.3,
                max(annual) * 0.5,
                f"Median: {median_year}",
                fontsize=max(VIZ_CONFIG["font_size"] - 3, 16),
                color="gray",
                rotation=90,
                va="center",
            )

    ax1.grid(axis="y", alpha=VIZ_CONFIG["grid_alpha"])

    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)

    return output_path


def plot_subfield_timeline(
    subfield_year_counts: dict[str, dict[int, int]],
    output_path: Path,
) -> Path:
    """Stacked area chart showing subfield growth over time.

    Each subfield is a colored band stacked on top of the others,
    so the total height at any year equals the total publication count.

    Args:
        subfield_year_counts: Mapping of subfield name to a dict
            of year -> count.
        output_path: File path to save the figure.

    Returns:
        The output_path after saving.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Collect all years across subfields
    all_years: set[int] = set()
    for year_dict in subfield_year_counts.values():
        all_years.update(year_dict.keys())

    if not all_years:
        fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure_size"], dpi=VIZ_CONFIG["dpi"])
        ax.text(0.5, 0.5, "No temporal data", ha="center", va="center", fontsize=VIZ_CONFIG["font_size"])
        ax.set_axis_off()
        fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
        plt.close(fig)
        return output_path

    years = sorted(all_years)
    subfields = list(subfield_year_counts.keys())

    # Build data arrays
    data = np.zeros((len(subfields), len(years)), dtype=float)
    for i, sf in enumerate(subfields):
        for j, yr in enumerate(years):
            data[i, j] = subfield_year_counts[sf].get(yr, 0)

    colors = [
        VIZ_CONFIG["subfield_colors"].get(sf, VIZ_CONFIG["palette"][i % len(VIZ_CONFIG["palette"])])
        for i, sf in enumerate(subfields)
    ]

    fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure_size"], dpi=VIZ_CONFIG["dpi"])

    ax.stackplot(
        years,
        data,
        labels=[_format_subfield_label(sf) for sf in subfields],
        colors=colors,
        alpha=0.85,
    )

    ax.set_xlabel("Year", fontsize=VIZ_CONFIG["font_size"])
    ax.set_ylabel("Number of Papers", fontsize=VIZ_CONFIG["font_size"])
    ax.set_title(
        "Subfield Growth Over Time",
        fontsize=VIZ_CONFIG["title_size"],
        fontweight="bold",
    )
    ax.legend(loc="upper left", fontsize=max(VIZ_CONFIG["font_size"] - 2, 16), ncol=2, framealpha=0.9)
    ax.grid(axis="y", alpha=VIZ_CONFIG["grid_alpha"])

    # Total N annotation
    total_n = int(sum(data.sum(axis=0)))
    ax.text(
        0.98,
        0.95,
        f"N = {total_n:,}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=max(VIZ_CONFIG["font_size"] - 1, 16),
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8),
    )

    plt.tight_layout()
    fig.savefig(output_path, dpi=VIZ_CONFIG["dpi"], bbox_inches="tight")
    plt.close(fig)

    return output_path
