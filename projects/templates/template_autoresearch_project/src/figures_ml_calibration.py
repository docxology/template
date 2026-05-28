"""Calibration and probability-quality figure writers."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .figures_core import (
    _float_value,
    _mapping_list,
    hide_spines,
    palette_color,
    save_figure,
    styled_grid,
)


def write_ml_calibration_reliability_figure(
    figures_dir: Path,
    calibration: dict[str, object],
    calibration_intervals: dict[str, object] | None = None,
) -> Path:
    """Write accepted-candidate reliability and confidence-bin diagnostics."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_calibration_reliability.png"
    bins = _mapping_list(calibration.get("bins"))
    centers = [(float(row.get("lower", 0.0)) + float(row.get("upper", 0.0))) / 2.0 for row in bins]
    accuracy = [float(row.get("accuracy", 0.0)) for row in bins]
    confidence = [float(row.get("mean_confidence", 0.0)) for row in bins]
    counts = [int(row.get("count", 0)) for row in bins]
    interval_rows = _mapping_list(calibration_intervals.get("bins") if calibration_intervals else None)
    interval_by_index = {int(row.get("bin_index", -1)): row for row in interval_rows}
    lows = [
        _float_value(interval_by_index.get(index, {}).get("ci_low", accuracy[index])) for index in range(len(accuracy))
    ]
    highs = [
        _float_value(interval_by_index.get(index, {}).get("ci_high", accuracy[index])) for index in range(len(accuracy))
    ]
    yerr = [
        [max(0.0, point - low) for point, low in zip(accuracy, lows, strict=True)],
        [max(0.0, high - point) for point, high in zip(accuracy, highs, strict=True)],
    ]

    fig, (ax_top, ax_bottom) = plt.subplots(
        2,
        1,
        figsize=(7.2, 5.2),
        sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1.0]},
    )
    ax_top.plot(
        [0, 1], [0, 1], color=palette_color("reference", "#52525b"), linestyle="--", linewidth=1.0, label="ideal"
    )
    ax_top.errorbar(
        centers,
        accuracy,
        yerr=yerr,
        marker="o",
        color=palette_color("positive", "#0f766e"),
        ecolor=palette_color("positive", "#0f766e"),
        elinewidth=1.0,
        capsize=2.5,
        linewidth=1.8,
        label="bin accuracy (Wilson 95%)",
    )
    ax_top.plot(
        centers,
        confidence,
        marker="s",
        color=palette_color("accent", "#2563eb"),
        linewidth=1.5,
        label="mean confidence",
    )
    ax_top.set_title("Accepted candidate calibration")
    ax_top.set_ylabel("fraction")
    ax_top.set_ylim(0.0, 1.05)
    styled_grid(ax_top, "both")
    ax_top.legend(loc="lower right", frameon=False, fontsize=8)
    ax_top.text(
        0.02,
        0.08,
        f"ECE {_float_value(calibration.get('expected_calibration_error')):.3f}",
        transform=ax_top.transAxes,
        fontsize=9,
        color=palette_color("box_edge", "#334155"),
    )
    ax_bottom.bar(centers, counts, width=0.08, color=palette_color("rule", "#94a3b8"))
    ax_bottom.set_xlabel("prediction confidence")
    ax_bottom.set_ylabel("count")
    styled_grid(ax_bottom, "y")
    for axis in (ax_top, ax_bottom):
        axis.set_axisbelow(True)
        hide_spines(axis)
    fig.tight_layout()
    return save_figure(fig, path)


def write_ml_probability_margin_figure(figures_dir: Path, probability: dict[str, object]) -> Path:
    """Write accepted-candidate confidence and margin histograms."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_probability_margin_distribution.png"
    confidence = _mapping_list(probability.get("confidence_histogram"))
    margin = _mapping_list(probability.get("margin_histogram"))
    centers = [(float(row.get("lower", 0.0)) + float(row.get("upper", 0.0))) / 2.0 for row in confidence]
    width = 0.038

    fig, (ax_confidence, ax_margin) = plt.subplots(2, 1, figsize=(7.4, 5.4), sharex=True)
    for axis, rows, title in (
        (ax_confidence, confidence, "Confidence distribution"),
        (ax_margin, margin, "Prediction-margin distribution"),
    ):
        correct_counts = [int(row.get("correct_count", 0)) for row in rows]
        error_counts = [int(row.get("error_count", 0)) for row in rows]
        axis.bar(
            [value - width / 2.0 for value in centers],
            correct_counts,
            width,
            color=palette_color("positive", "#0f766e"),
            label="correct",
        )
        axis.bar(
            [value + width / 2.0 for value in centers],
            error_counts,
            width,
            color=palette_color("negative", "#7c2d12"),
            label="error",
        )
        axis.set_title(title, fontsize=11)
        axis.set_ylabel("count")
        styled_grid(axis, "y")
        axis.set_axisbelow(True)
        axis.legend(loc="upper left", frameon=False, fontsize=8)
        hide_spines(axis)
    ax_margin.set_xlabel("score bin")
    fig.tight_layout()
    return save_figure(fig, path)


def write_ml_probability_quality_figure(figures_dir: Path, statistical: dict[str, object]) -> Path:
    """Write candidate probability quality diagnostics."""
    from matplotlib import pyplot as plt
    from matplotlib.patches import Patch

    path = figures_dir / "ml_probability_quality.png"
    rows = sorted(
        _mapping_list(statistical.get("candidate_probability_quality")),
        key=lambda row: (_float_value(row.get("brier_score")), str(row.get("candidate_id", ""))),
    )
    accepted_id = str(statistical.get("accepted_candidate_id", ""))
    labels = [str(row.get("candidate_id", "candidate")).replace("exp-", "") for row in rows]
    brier = [_float_value(row.get("brier_score")) for row in rows]
    nll = [_float_value(row.get("negative_log_likelihood")) for row in rows]
    colors = [
        palette_color("positive", "#0f766e")
        if row.get("candidate_id") == accepted_id
        else palette_color("muted", "#64748b")
        for row in rows
    ]
    y_positions = np.arange(len(rows), dtype=float)

    fig, (ax_brier, ax_nll) = plt.subplots(1, 2, figsize=(8.4, 3.8), sharey=True)
    for axis, values, title in (
        (ax_brier, brier, "Brier score"),
        (ax_nll, nll, "Negative log likelihood"),
    ):
        axis.barh(y_positions, values, color=colors)
        axis.set_title(title, fontsize=11)
        axis.set_xlabel("lower is better")
        axis.set_xlim(0.0, max(values, default=0.0) * 1.18 + 0.02)
        styled_grid(axis, "x")
        axis.set_axisbelow(True)
        for row_index, value in enumerate(values):
            axis.text(value + 0.01, row_index, f"{value:.3f}", va="center", fontsize=8)
        hide_spines(axis)
    ax_brier.set_yticks(y_positions, labels=labels)
    ax_brier.invert_yaxis()
    ax_nll.legend(
        handles=[
            Patch(facecolor=palette_color("positive", "#0f766e"), label="accepted"),
            Patch(facecolor=palette_color("muted", "#64748b"), label="evaluated"),
        ],
        loc="upper right",
        frameon=False,
        fontsize=8,
    )
    fig.tight_layout()
    return save_figure(fig, path)


def write_ml_selective_accuracy_figure(figures_dir: Path, statistical: dict[str, object]) -> Path:
    """Write accepted-candidate selective accuracy over confidence thresholds."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_selective_accuracy.png"
    rows = _mapping_list(statistical.get("coverage_curve"))
    thresholds = [_float_value(row.get("threshold")) for row in rows]
    coverage = [_float_value(row.get("coverage")) for row in rows]
    accuracy = [_float_value(row.get("selective_accuracy")) for row in rows]
    retained = [int(_float_value(row.get("retained_count"))) for row in rows]
    overall_accuracy = _float_value(statistical.get("accuracy"))

    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    ax.plot(
        thresholds,
        accuracy,
        color=palette_color("positive", "#0f766e"),
        linewidth=2.2,
        marker="o",
        label="selective accuracy",
    )
    ax.plot(thresholds, coverage, color=palette_color("accent", "#2563eb"), linewidth=2.0, marker="s", label="coverage")
    ax.axhline(
        overall_accuracy,
        color=palette_color("reference", "#52525b"),
        linestyle="--",
        linewidth=1.0,
        label="overall accuracy",
    )
    for x_value, y_value, count in zip(thresholds, accuracy, retained, strict=True):
        ax.annotate(f"n={count}", (x_value, y_value), xytext=(4, 6), textcoords="offset points", fontsize=8)
    ax.set_title("Confidence threshold trade-off")
    ax.set_xlabel("confidence threshold")
    ax.set_ylabel("fraction of test predictions")
    if thresholds:
        ax.set_xlim(max(0.0, min(thresholds) - 0.05), min(1.0, max(thresholds) + 0.05))
    ax.set_ylim(0.0, 1.05)
    styled_grid(ax, "both")
    ax.set_axisbelow(True)
    ax.legend(loc="lower left", frameon=False, fontsize=8)
    hide_spines(ax)
    fig.tight_layout()
    return save_figure(fig, path)


__all__ = [
    "write_ml_calibration_reliability_figure",
    "write_ml_probability_margin_figure",
    "write_ml_probability_quality_figure",
    "write_ml_selective_accuracy_figure",
]
