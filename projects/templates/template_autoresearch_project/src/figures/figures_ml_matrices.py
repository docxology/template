"""Confusion, robustness, and interval matrix figure writers."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .figure_style import get_active_style
from .figures_core import (
    _float_value,
    _format_percent,
    _mapping_list,
    annotate_imshow_matrix,
    dual_vertical_bars,
    hide_spines,
    horizontal_bar_panel,
    palette_color,
    save_figure,
    styled_grid,
)
from src.ml.task import MLTaskResult


def write_ml_confusion_matrix_figure(figures_dir: Path, result: MLTaskResult) -> Path:
    """Write the accepted candidate confusion matrix."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_confusion_matrix.png"
    matrix = np.asarray(result.accepted_candidate.confusion_matrix, dtype=float)
    row_totals = matrix.sum(axis=1, keepdims=True)
    normalized = np.divide(matrix, row_totals, out=np.zeros_like(matrix), where=row_totals > 0)
    cell_text = [
        [
            f"{int(value)}\n{normalized[row_index, col_index]:.0%}" if value else "0"
            for col_index, value in enumerate(row.astype(int))
        ]
        for row_index, row in enumerate(matrix.astype(int))
    ]
    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    image = annotate_imshow_matrix(
        ax,
        normalized,
        [str(index) for index in range(10)],
        [str(index) for index in range(10)],
        vmin=0.0,
        vmax=1.0,
        cmap=get_active_style().heatmap_colormap,
        cell_text=cell_text,
        color_threshold=0.55,
        fontsize=6.5,
    )
    ax.set_title(f"Accepted candidate confusion matrix ({_format_percent(result.best_accuracy)})")
    ax.set_xlabel("predicted digit")
    ax.set_ylabel("true digit")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    return save_figure(fig, path)


def write_ml_per_class_accuracy_figure(figures_dir: Path, result: MLTaskResult) -> Path:
    """Write per-class accepted-candidate accuracy from the confusion matrix."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_per_class_accuracy.png"
    matrix = np.asarray(result.accepted_candidate.confusion_matrix, dtype=float)
    totals = matrix.sum(axis=1)
    per_class = np.divide(
        np.diag(matrix),
        totals,
        out=np.zeros_like(totals, dtype=float),
        where=totals > 0,
    )
    colors = [
        palette_color("positive", "#0f766e") if value >= result.best_accuracy else palette_color("accent", "#2563eb")
        for value in per_class
    ]
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    bars = ax.bar([str(index) for index in range(10)], per_class, color=colors)
    ax.axhline(
        result.best_accuracy,
        color=palette_color("reference", "#52525b"),
        linestyle="--",
        linewidth=1.0,
        label=f"overall {_format_percent(result.best_accuracy)}",
    )
    ax.set_title("Accepted candidate per-class accuracy")
    ax.set_xlabel("true digit")
    ax.set_ylabel("class accuracy")
    ax.set_ylim(0.0, 1.05)
    styled_grid(ax, "y")
    ax.set_axisbelow(True)
    for bar, value in zip(bars, per_class, strict=True):
        ax.text(bar.get_x() + bar.get_width() / 2.0, value + 0.025, f"{value:.2f}", ha="center", fontsize=8)
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    hide_spines(ax)
    fig.tight_layout()
    return save_figure(fig, path)


def write_ml_classification_metrics_heatmap(figures_dir: Path, diagnostics: dict[str, object]) -> Path:
    """Write per-class precision/recall/F1 diagnostics as a heatmap."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_classification_metrics_heatmap.png"
    rows = _mapping_list(diagnostics.get("per_class"))
    matrix = np.asarray(
        [[float(row.get("precision", 0.0)), float(row.get("recall", 0.0)), float(row.get("f1", 0.0))] for row in rows],
        dtype=float,
    )
    cell_text = [[f"{value:.2f}" for value in row] for row in matrix]
    fig, ax = plt.subplots(figsize=(5.8, 5.2))
    image = annotate_imshow_matrix(
        ax,
        matrix,
        [str(row.get("class_label", index)) for index, row in enumerate(rows)],
        ["precision", "recall", "F1"],
        vmin=0.0,
        vmax=1.0,
        cell_text=cell_text,
        color_threshold=0.72,
    )
    ax.set_title("Accepted candidate class metrics")
    ax.set_ylabel("true digit")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    return save_figure(fig, path)


def write_ml_confusion_pairs_figure(figures_dir: Path, diagnostics: dict[str, object]) -> Path:
    """Write ranked non-diagonal confusion pairs."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_confusion_pairs.png"
    pairs = _mapping_list(diagnostics.get("top_confusion_pairs"))[:8]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    if not pairs:
        ax.axis("off")
        ax.text(0.5, 0.5, "No off-diagonal confusion pairs in the accepted-candidate matrix", ha="center", va="center")
    else:
        labels = [f"{row.get('true_label')} -> {row.get('predicted_label')}" for row in pairs]
        counts = [int(row.get("count", 0)) for row in pairs]
        rates = [_float_value(row.get("true_class_error_rate")) for row in pairs]
        annotations = [f"{value} ({rate:.0%})" for value, rate in zip(counts, rates, strict=True)]
        horizontal_bar_panel(ax, labels, [float(value) for value in counts], annotations=annotations)
        ax.set_title("Top accepted-candidate confusion pairs")
        ax.set_xlabel("count")
        max_count = max(counts, default=0)
        ax.set_xlim(0, max_count + 0.45)
        ax.set_xticks(range(0, max_count + 1))
        styled_grid(ax, "x")
        ax.set_axisbelow(True)
    hide_spines(ax)
    fig.tight_layout()
    return save_figure(fig, path)


def write_ml_generalization_gap_figure(figures_dir: Path, diagnostics: dict[str, object]) -> Path:
    """Write train/test accuracy and loss gaps by evaluated candidate."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_generalization_gap.png"
    rows = _mapping_list(diagnostics.get("generalization"))
    fig = plt.figure(figsize=(7.4, 5.4))
    ax_acc, ax_loss = dual_vertical_bars(
        fig,
        rows,
        (
            (("train_accuracy", "accent", "#2563eb"), ("test_accuracy", "positive", "#0f766e")),
            (("train_loss", "accent_light", "#60a5fa"), ("test_loss", "positive_light", "#34d399")),
        ),
        label_formatter=lambda value: str(value).replace("exp-", ""),
    )
    ax_acc.set_title("Candidate generalization diagnostics")
    ax_acc.set_ylabel("accuracy")
    ax_acc.set_ylim(0.0, 1.05)
    ax_loss.set_ylabel("loss")
    fig.tight_layout()
    return save_figure(fig, path)


def write_ml_robustness_matrix_figure(figures_dir: Path, robustness: dict[str, object]) -> Path:
    """Write candidate accuracy under deterministic no-retrain perturbations."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_robustness_matrix.png"
    rows = _mapping_list(robustness.get("rows"))
    candidates = list(dict.fromkeys(str(row.get("candidate_id", "")) for row in rows if row.get("candidate_id")))
    raw_transforms = robustness.get("transforms", [])
    transforms = [str(value) for value in raw_transforms if value] if isinstance(raw_transforms, list) else []
    matrix = np.zeros((len(candidates), len(transforms)), dtype=float)
    for row in rows:
        candidate_id = str(row.get("candidate_id", ""))
        transform = str(row.get("transform", ""))
        if candidate_id in candidates and transform in transforms:
            matrix[candidates.index(candidate_id), transforms.index(transform)] = float(row.get("accuracy", 0.0))
    cell_text = [[f"{value:.2f}" for value in row] for row in matrix]
    fig, ax = plt.subplots(figsize=(8.0, 3.8))
    image = annotate_imshow_matrix(
        ax,
        matrix,
        [value.replace("exp-", "") for value in candidates],
        [value.replace("_", "\n") for value in transforms],
        vmin=0.0,
        vmax=1.0,
        cell_text=cell_text,
        color_threshold=0.72,
    )
    ax.set_title("Deterministic robustness smoke test")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    return save_figure(fig, path)


def write_ml_bootstrap_intervals_figure(figures_dir: Path, bootstrap: dict[str, object]) -> Path:
    """Write deterministic bootstrap intervals for accepted-candidate metrics."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_bootstrap_intervals.png"
    intervals = _mapping_list(bootstrap.get("intervals"))
    labels = [str(row.get("metric", "metric")).replace("_", " ") for row in intervals]
    observed = [_float_value(row.get("observed")) for row in intervals]
    ci_low = [_float_value(row.get("ci_low")) for row in intervals]
    ci_high = [_float_value(row.get("ci_high")) for row in intervals]
    y_positions = np.arange(len(intervals), dtype=float)

    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    for y_pos, low, high, point in zip(y_positions, ci_low, ci_high, observed, strict=True):
        ax.plot([low, high], [y_pos, y_pos], color=palette_color("accent", "#2563eb"), linewidth=3.0)
        ax.scatter([point], [y_pos], color=palette_color("positive", "#0f766e"), s=70, zorder=3)
        ax.text(high + 0.01, y_pos, f"{point:.3f}", va="center", fontsize=8, color=palette_color("box_edge", "#334155"))
    ax.set_title("Deterministic bootstrap intervals")
    ax.set_xlabel("metric value")
    ax.set_yticks(y_positions, labels=labels)
    ax.set_xlim(0.0, 1.05)
    styled_grid(ax, "x")
    ax.set_axisbelow(True)
    hide_spines(ax)
    fig.tight_layout()
    return save_figure(fig, path)


def write_ml_paired_correctness_figure(figures_dir: Path, paired: dict[str, object]) -> Path:
    """Write matched baseline-vs-accepted correctness counts."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_paired_correctness.png"
    matrix = np.asarray(
        [
            [_float_value(paired.get("both_wrong")), _float_value(paired.get("baseline_only_correct"))],
            [_float_value(paired.get("accepted_only_correct")), _float_value(paired.get("both_correct"))],
        ],
        dtype=float,
    )
    cell_text = [[str(int(value)) for value in row] for row in matrix]
    fig, ax = plt.subplots(figsize=(4.8, 4.2))
    image = annotate_imshow_matrix(
        ax,
        matrix,
        ["accepted wrong", "accepted correct"],
        ["baseline wrong", "baseline correct"],
        vmin=None,
        vmax=None,
        cell_text=cell_text,
        color_threshold=20.0,
        fontsize=10.0,
    )
    ax.set_title("Matched correctness comparison")
    ax.set_xticks((0, 1), labels=("baseline wrong", "baseline correct"), rotation=20, ha="right")
    ax.set_yticks((0, 1), labels=("accepted wrong", "accepted correct"))
    ax.text(
        0.02,
        -0.18,
        f"exact McNemar p={_float_value(paired.get('exact_mcnemar_p')):.3f}",
        transform=ax.transAxes,
        fontsize=8,
        color=palette_color("box_edge", "#334155"),
    )
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    return save_figure(fig, path)


__all__ = [
    "write_ml_bootstrap_intervals_figure",
    "write_ml_classification_metrics_heatmap",
    "write_ml_confusion_matrix_figure",
    "write_ml_confusion_pairs_figure",
    "write_ml_generalization_gap_figure",
    "write_ml_paired_correctness_figure",
    "write_ml_per_class_accuracy_figure",
    "write_ml_robustness_matrix_figure",
]
