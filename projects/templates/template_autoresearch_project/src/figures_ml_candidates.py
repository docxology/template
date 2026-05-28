"""Candidate comparison and training-dynamics figure writers."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .figures_core import (
    _float_value,
    _format_percent,
    _mapping_list,
    _short_candidate_label,
    _status_color,
    _status_marker,
    hide_spines,
    palette_color,
    save_figure,
    styled_grid,
)
from .ml_task import MLTaskResult


def write_ml_candidate_scores_figure(
    figures_dir: Path,
    result: MLTaskResult,
    intervals: dict[str, object] | None = None,
) -> Path:
    """Write a lollipop chart comparing baseline and evaluated candidate accuracy."""
    from matplotlib import pyplot as plt
    from matplotlib.lines import Line2D

    path = figures_dir / "ml_candidate_scores.png"
    rows = _mapping_list(intervals.get("rows") if intervals else None)
    if not rows:
        evaluated = [candidate for candidate in result.candidates if candidate.test_accuracy is not None]
        rows = [
            {
                "candidate_id": result.baseline.identifier,
                "status": "baseline",
                "accuracy": result.baseline.test_accuracy,
                "ci_low": result.baseline.test_accuracy,
                "ci_high": result.baseline.test_accuracy,
            },
            *[
                {
                    "candidate_id": candidate.identifier,
                    "status": candidate.status,
                    "accuracy": float(candidate.test_accuracy or 0.0),
                    "ci_low": float(candidate.test_accuracy or 0.0),
                    "ci_high": float(candidate.test_accuracy or 0.0),
                }
                for candidate in evaluated
            ],
        ]
    labels = [_short_candidate_label(row.get("candidate_id", "candidate")) for row in rows]
    values = [_float_value(row.get("accuracy")) for row in rows]
    lows = [_float_value(row.get("ci_low")) for row in rows]
    highs = [_float_value(row.get("ci_high")) for row in rows]
    statuses = [str(row.get("status", "evaluated")) for row in rows]
    colors = [_status_color(status) for status in statuses]
    markers = [_status_marker(status) for status in statuses]
    y_positions = np.arange(len(labels), dtype=float)
    fig, ax = plt.subplots(figsize=(8.6, 4.3))
    ax.hlines(y_positions, 0.0, values, color=palette_color("connector", "#cbd5e1"), linewidth=2.0, zorder=1)
    for y_pos, value, low, high, color, marker, status in zip(
        y_positions,
        values,
        lows,
        highs,
        colors,
        markers,
        statuses,
        strict=True,
    ):
        ax.errorbar(
            value,
            y_pos,
            xerr=[[max(0.0, value - low)], [max(0.0, high - value)]],
            fmt=marker,
            color=color,
            ecolor=color,
            elinewidth=1.2,
            capsize=3,
            markersize=8 if status == "accepted" else 6,
            zorder=3,
        )
    ax.axvline(
        result.baseline.test_accuracy,
        color=palette_color("reference", "#52525b"),
        linestyle="--",
        linewidth=1.1,
    )
    ax.set_title("Candidate accuracy with Wilson intervals")
    ax.set_xlabel("held-out accuracy (Wilson 95% interval)")
    ax.set_xlim(0.0, 1.12)
    ax.set_yticks(y_positions, labels=labels)
    ax.invert_yaxis()
    styled_grid(ax, "x")
    ax.set_axisbelow(True)
    for y_pos, value, low, high in zip(y_positions, values, lows, highs, strict=True):
        delta = value - result.baseline.test_accuracy
        label = f"{value:.3f} [{low:.3f}, {high:.3f}]" if y_pos == 0 else f"{value:.3f} ({delta:+.3f})"
        ax.text(min(high + 0.015, 1.06), y_pos, label, ha="left", va="center", fontsize=8.3)
    if any(candidate.status == "deferred" for candidate in result.candidates):
        ax.text(
            0.01,
            -0.16,
            "deferred candidates recorded in ledger",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=8,
            color=palette_color("negative", "#7c2d12"),
        )
    ax.legend(
        handles=[
            Line2D([0], [0], color=palette_color("reference", "#52525b"), marker="s", linestyle="", label="baseline"),
            Line2D([0], [0], color=palette_color("accepted", "#0072b2"), marker="D", linestyle="", label="accepted"),
            Line2D([0], [0], color=palette_color("evaluated", "#56b4e9"), marker="o", linestyle="", label="evaluated"),
            Line2D(
                [0],
                [0],
                color=palette_color("reference", "#52525b"),
                linestyle="--",
                linewidth=1.1,
                label="baseline line",
            ),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 1.18),
        ncol=4,
        frameon=False,
        fontsize=8,
    )
    hide_spines(ax)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.92))
    return save_figure(fig, path)


def write_ml_learning_curve_figure(figures_dir: Path, result: MLTaskResult) -> Path:
    """Write epoch-level test accuracy curves for evaluated candidates."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_learning_curves.png"
    evaluated = [candidate for candidate in result.candidates if candidate.training_history]
    colors = (
        palette_color("accent", "#2563eb"),
        palette_color("positive", "#0f766e"),
        palette_color("negative", "#7c2d12"),
        palette_color("warning", "#a16207"),
        palette_color("accent2", "#7c3aed"),
    )
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    for index, candidate in enumerate(evaluated):
        epochs = [int(row["epoch"]) for row in candidate.training_history]
        test_accuracy = [float(row["test_accuracy"]) for row in candidate.training_history]
        linewidth = 2.4 if candidate.status == "accepted" else 1.6
        ax.plot(
            epochs,
            test_accuracy,
            label=candidate.identifier.replace("exp-", ""),
            color=colors[index % len(colors)],
            linewidth=linewidth,
        )
        if candidate.status == "accepted" and test_accuracy:
            best_index = int(np.argmax(test_accuracy))
            ax.scatter(
                [epochs[best_index]],
                [test_accuracy[best_index]],
                color=palette_color("highlight", "#f59e0b"),
                s=48,
                zorder=4,
                label="accepted best epoch",
            )
    ax.axhline(
        result.baseline.test_accuracy,
        color=palette_color("reference", "#52525b"),
        linestyle="--",
        linewidth=1.0,
        label=f"baseline {_format_percent(result.baseline.test_accuracy)}",
    )
    ax.set_title("Candidate learning curves")
    ax.set_xlabel("epoch")
    ax.set_ylabel("held-out accuracy")
    ax.set_ylim(0.0, 1.05)
    styled_grid(ax, "y")
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    hide_spines(ax)
    fig.tight_layout()
    return save_figure(fig, path)


def write_ml_complexity_accuracy_figure(figures_dir: Path, result: MLTaskResult) -> Path:
    """Write parameter-count versus accuracy diagnostics."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_complexity_accuracy.png"
    evaluated = [candidate for candidate in result.candidates if candidate.test_accuracy is not None]
    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    ax.scatter(
        [result.baseline.parameter_count],
        [result.baseline.test_accuracy],
        color=palette_color("reference", "#52525b"),
        marker="s",
        s=80,
        label="baseline",
    )
    for candidate in evaluated:
        color = (
            palette_color("positive", "#0f766e")
            if candidate.status == "accepted"
            else palette_color("accent", "#2563eb")
        )
        size = 110 if candidate.status == "accepted" else 70
        ax.scatter(candidate.parameter_count, float(candidate.test_accuracy or 0.0), color=color, s=size)
        ax.annotate(
            candidate.identifier.replace("exp-", ""),
            (candidate.parameter_count, float(candidate.test_accuracy or 0.0)),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )
    ax.set_xscale("log")
    ax.set_title("Accuracy versus model size")
    ax.set_xlabel("parameters (log scale)")
    ax.set_ylabel("held-out accuracy")
    ax.set_ylim(0.0, 1.05)
    styled_grid(ax, "both")
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    hide_spines(ax)
    fig.tight_layout()
    return save_figure(fig, path)


def write_ml_candidate_rank_stability_figure(figures_dir: Path, rank_stability: dict[str, object]) -> Path:
    """Write candidate bootstrap top-rank stability diagnostics."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_candidate_rank_stability.png"
    rows = _mapping_list(rank_stability.get("rank_frequencies"))
    labels = [_short_candidate_label(row.get("candidate_id", "candidate")) for row in rows]
    top_frequency = [_float_value(row.get("rank_1_frequency")) for row in rows]
    mean_rank = [_float_value(row.get("mean_rank")) for row in rows]
    accepted = str(rank_stability.get("accepted_candidate_id", ""))
    colors = [
        palette_color("positive", "#0f766e")
        if row.get("candidate_id") == accepted
        else palette_color("accent", "#2563eb")
        for row in rows
    ]
    positions = np.arange(len(labels), dtype=float)
    fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.8), gridspec_kw={"width_ratios": [1.3, 1.0]})
    axes[0].barh(positions, top_frequency, color=colors)
    axes[0].set_yticks(positions, labels=labels)
    axes[0].invert_yaxis()
    axes[0].set_xlim(0.0, 1.05)
    axes[0].set_xlabel("top-rank frequency")
    axes[0].set_title("Bootstrap rank stability")
    for y_pos, value in zip(positions, top_frequency, strict=True):
        axes[0].text(min(value + 0.02, 1.0), y_pos, f"{value:.2f}", va="center", fontsize=8)
    axes[1].barh(positions, mean_rank, color=colors)
    axes[1].set_yticks(positions, labels=[])
    axes[1].invert_yaxis()
    axes[1].invert_xaxis()
    axes[1].set_xlabel("mean rank")
    axes[1].set_title("Lower is better")
    for y_pos, value in zip(positions, mean_rank, strict=True):
        axes[1].text(value - 0.04, y_pos, f"{value:.2f}", va="center", ha="right", fontsize=8)
    runner_up = str(rank_stability.get("runner_up_id", ""))
    frequency = _float_value(rank_stability.get("accepted_top_rank_frequency"))
    fig.text(
        0.5,
        0.01,
        f"accepted top-rank frequency {frequency:.2f}; runner-up {runner_up.replace('exp-', '')}",
        ha="center",
        va="bottom",
        fontsize=8,
        color=palette_color("annotation", "#475569"),
    )
    for axis in axes:
        styled_grid(axis, "x")
        axis.set_axisbelow(True)
        hide_spines(axis)
    fig.tight_layout(rect=(0.0, 0.05, 1.0, 1.0))
    return save_figure(fig, path)


def write_ml_training_dynamics_figure(figures_dir: Path, training: dict[str, object]) -> Path:
    """Write configured-training dynamics from the training diagnostics payload."""
    from matplotlib import pyplot as plt
    from matplotlib.patches import Patch

    path = figures_dir / "ml_training_dynamics.png"
    rows = _mapping_list(training.get("rows"))
    accepted_id = str(training.get("accepted_candidate_id", ""))
    labels = [str(row.get("candidate_id", "candidate")).replace("exp-", "") for row in rows]
    y_positions = np.arange(len(rows), dtype=float)
    final_accuracy = [_float_value(row.get("final_test_accuracy")) for row in rows]
    best_accuracy = [_float_value(row.get("best_test_accuracy")) for row in rows]
    gaps = [_float_value(row.get("train_test_accuracy_gap")) for row in rows]
    colors = [
        palette_color("positive", "#0f766e")
        if row.get("candidate_id") == accepted_id
        else palette_color("muted", "#64748b")
        for row in rows
    ]

    fig, (ax_accuracy, ax_gap) = plt.subplots(1, 2, figsize=(8.8, 3.8), sharey=True)
    ax_accuracy.barh(y_positions, final_accuracy, color=colors, label="final test accuracy")
    ax_accuracy.scatter(
        best_accuracy, y_positions, color=palette_color("highlight", "#f59e0b"), s=42, zorder=3, label="best epoch"
    )
    ax_accuracy.set_title("Final versus best epoch", fontsize=11)
    ax_accuracy.set_xlabel("held-out accuracy")
    ax_accuracy.set_xlim(0.0, 1.05)
    ax_accuracy.set_yticks(y_positions, labels=labels)
    ax_accuracy.invert_yaxis()
    for index, (final_value, best_value) in enumerate(zip(final_accuracy, best_accuracy, strict=True)):
        ax_accuracy.text(max(final_value, best_value) + 0.012, index, f"{best_value:.3f}", va="center", fontsize=8)

    ax_gap.axvline(0.0, color=palette_color("reference", "#52525b"), linewidth=1.0)
    ax_gap.barh(y_positions, gaps, color=colors)
    ax_gap.set_title("Train-test accuracy gap", fontsize=11)
    ax_gap.set_xlabel("train minus test")
    lower = min(0.0, min(gaps, default=0.0)) - 0.02
    upper = max(0.05, max(gaps, default=0.0)) + 0.02
    ax_gap.set_xlim(lower, upper)
    for index, gap in enumerate(gaps):
        ax_gap.text(gap + 0.004, index, f"{gap:.3f}", va="center", fontsize=8)

    for axis in (ax_accuracy, ax_gap):
        styled_grid(axis, "x")
        axis.set_axisbelow(True)
        hide_spines(axis)
    ax_gap.legend(
        handles=[
            Patch(facecolor=palette_color("positive", "#0f766e"), label="accepted"),
            Patch(facecolor=palette_color("muted", "#64748b"), label="evaluated"),
        ],
        loc="lower right",
        frameon=False,
        fontsize=8,
    )
    ax_accuracy.legend(loc="lower right", frameon=False, fontsize=8)
    fig.tight_layout()
    return save_figure(fig, path)


__all__ = [
    "write_ml_candidate_rank_stability_figure",
    "write_ml_candidate_scores_figure",
    "write_ml_complexity_accuracy_figure",
    "write_ml_learning_curve_figure",
    "write_ml_training_dynamics_figure",
]
