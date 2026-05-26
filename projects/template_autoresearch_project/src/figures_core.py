"""Figure generation for the AutoResearch loop."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from .ml_task import MLTaskResult, accepted_error_examples, load_mnist_arrays, load_mnist_task_config
from .models import AutoResearchLoopResult


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def write_stage_matrix_figure(figures_dir: Path, result: AutoResearchLoopResult) -> Path:
    """Write the stage matrix bar chart."""
    from matplotlib import pyplot as plt

    path = figures_dir / "autoresearch_stage_matrix.png"
    labels = ("stages", "claims", "artifacts")
    values = (
        len(result.stage_results),
        result.supported_claim_count,
        len(result.config.required_artifacts),
    )
    colors = ("#2563eb", "#0f766e", "#7c2d12")
    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    ax.barh(labels, values, color=colors)
    ax.set_title("AutoResearch readiness matrix")
    ax.set_xlabel("count")
    ax.set_xlim(0, max(values) + 1)
    for index, value in enumerate(values):
        ax.text(value + 0.1, index, str(value), va="center", fontsize=10)
    ax.text(
        0.99,
        0.06,
        "validated run state" if result.readiness_valid else "pre-readiness state",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        color="#475569",
    )
    ax.grid(axis="x", color="#d4d4d8", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


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
    ax.hlines(y_positions, 0.0, values, color="#cbd5e1", linewidth=2.0, zorder=1)
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
        color="#52525b",
        linestyle="--",
        linewidth=1.1,
    )
    ax.set_title("Candidate accuracy with Wilson intervals")
    ax.set_xlabel("held-out accuracy (Wilson 95% interval)")
    ax.set_xlim(0.0, 1.12)
    ax.set_yticks(y_positions, labels=labels)
    ax.invert_yaxis()
    ax.grid(axis="x", color="#d4d4d8", linewidth=0.8)
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
            color="#7c2d12",
        )
    ax.legend(
        handles=[
            Line2D([0], [0], color="#52525b", marker="s", linestyle="", label="baseline"),
            Line2D([0], [0], color="#0072b2", marker="D", linestyle="", label="accepted"),
            Line2D([0], [0], color="#56b4e9", marker="o", linestyle="", label="evaluated"),
            Line2D([0], [0], color="#52525b", linestyle="--", linewidth=1.1, label="baseline line"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 1.18),
        ncol=4,
        frameon=False,
        fontsize=8,
    )
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.92))
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def write_ml_confusion_matrix_figure(figures_dir: Path, result: MLTaskResult) -> Path:
    """Write the accepted candidate confusion matrix."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_confusion_matrix.png"
    matrix = np.asarray(result.accepted_candidate.confusion_matrix, dtype=float)
    row_totals = matrix.sum(axis=1, keepdims=True)
    normalized = np.divide(matrix, row_totals, out=np.zeros_like(matrix), where=row_totals > 0)
    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    image = ax.imshow(normalized, cmap="Blues", vmin=0.0, vmax=1.0)
    ax.set_title(f"Accepted candidate confusion matrix ({_format_percent(result.best_accuracy)})")
    ax.set_xlabel("predicted digit")
    ax.set_ylabel("true digit")
    ax.set_xticks(range(10))
    ax.set_yticks(range(10))
    for row_index, row in enumerate(matrix.astype(int)):
        for col_index, value in enumerate(row):
            ax.text(
                col_index,
                row_index,
                f"{value}\n{normalized[row_index, col_index]:.0%}" if value else "0",
                ha="center",
                va="center",
                fontsize=6.5,
                color="white" if normalized[row_index, col_index] > 0.55 else "#111827",
            )
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def write_ml_learning_curve_figure(figures_dir: Path, result: MLTaskResult) -> Path:
    """Write epoch-level test accuracy curves for evaluated candidates."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_learning_curves.png"
    evaluated = [candidate for candidate in result.candidates if candidate.training_history]
    colors = ("#2563eb", "#0f766e", "#7c2d12", "#a16207", "#7c3aed")
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
                color="#f59e0b",
                s=48,
                zorder=4,
                label="accepted best epoch",
            )
    ax.axhline(
        result.baseline.test_accuracy,
        color="#52525b",
        linestyle="--",
        linewidth=1.0,
        label=f"baseline {_format_percent(result.baseline.test_accuracy)}",
    )
    ax.set_title("Candidate learning curves")
    ax.set_xlabel("epoch")
    ax.set_ylabel("held-out accuracy")
    ax.set_ylim(0.0, 1.05)
    ax.grid(axis="y", color="#d4d4d8", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def write_ml_complexity_accuracy_figure(figures_dir: Path, result: MLTaskResult) -> Path:
    """Write parameter-count versus accuracy diagnostics."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_complexity_accuracy.png"
    evaluated = [candidate for candidate in result.candidates if candidate.test_accuracy is not None]
    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    ax.scatter(
        [result.baseline.parameter_count],
        [result.baseline.test_accuracy],
        color="#52525b",
        marker="s",
        s=80,
        label="baseline",
    )
    for candidate in evaluated:
        color = "#0f766e" if candidate.status == "accepted" else "#2563eb"
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
    ax.grid(axis="both", color="#d4d4d8", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


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
    colors = ["#0f766e" if value >= result.best_accuracy else "#2563eb" for value in per_class]
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    bars = ax.bar([str(index) for index in range(10)], per_class, color=colors)
    ax.axhline(
        result.best_accuracy,
        color="#52525b",
        linestyle="--",
        linewidth=1.0,
        label=f"overall {_format_percent(result.best_accuracy)}",
    )
    ax.set_title("Accepted candidate per-class accuracy")
    ax.set_xlabel("true digit")
    ax.set_ylabel("class accuracy")
    ax.set_ylim(0.0, 1.05)
    ax.grid(axis="y", color="#d4d4d8", linewidth=0.8)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, per_class, strict=True):
        ax.text(bar.get_x() + bar.get_width() / 2.0, value + 0.025, f"{value:.2f}", ha="center", fontsize=8)
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def write_candidate_lifecycle_figure(figures_dir: Path, result: MLTaskResult) -> Path:
    """Write candidate lifecycle counts from the candidate ledger state."""
    from matplotlib import pyplot as plt

    path = figures_dir / "autoresearch_candidate_lifecycle.png"
    ordered_statuses = ("proposed", "evaluated", "accepted", "rejected", "deferred")
    lifecycle_counts: Counter[str] = Counter()
    for candidate in result.candidates:
        lifecycle_counts.update(candidate.lifecycle)
        if candidate.status not in candidate.lifecycle:
            lifecycle_counts[candidate.status] += 1
    values = [lifecycle_counts[status] for status in ordered_statuses]
    colors = ("#52525b", "#2563eb", "#0f766e", "#7c2d12", "#a16207")
    fig, ax = plt.subplots(figsize=(7.4, 3.0))
    bars = ax.bar(ordered_statuses, values, color=colors)
    ax.set_title("Candidate lifecycle ledger")
    ax.set_ylabel("candidate records")
    ax.set_ylim(0, max(values) + 1)
    ax.grid(axis="y", color="#d4d4d8", linewidth=0.8)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, values, strict=True):
        ax.text(bar.get_x() + bar.get_width() / 2.0, value + 0.06, str(value), ha="center", fontsize=9)
    ax.text(
        0.99,
        0.05,
        f"budget evaluated {result.evaluated_candidate_count} of {result.candidate_count}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        color="#475569",
    )
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def write_mnist_subset_contact_sheet_figure(project_root: Path, figures_dir: Path, result: MLTaskResult) -> Path:
    """Write a deterministic contact sheet from the local MNIST subset."""
    from matplotlib import pyplot as plt

    path = figures_dir / "mnist_subset_contact_sheet.png"
    config = load_mnist_task_config(project_root, result.task_config.source_path)
    x_train, y_train, _x_test, _y_test = load_mnist_arrays(project_root, config)
    selected_indices = [_first_label_index(y_train, label) for label in range(10)]

    fig, axes = plt.subplots(2, 5, figsize=(7.6, 3.4))
    for axis, index in zip(axes.ravel(), selected_indices, strict=True):
        label = int(y_train[index])
        axis.imshow(x_train[index], cmap="gray", vmin=0.0, vmax=1.0)
        axis.set_title(f"digit {label}", fontsize=9)
        axis.set_xticks(())
        axis.set_yticks(())
        for spine in axis.spines.values():
            spine.set_color("#334155")
            spine.set_linewidth(0.8)
    fig.suptitle("Local subset examples by class", fontsize=12)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def write_mnist_class_balance_figure(figures_dir: Path, class_balance: dict[str, object]) -> Path:
    """Write train/test class-count balance for the local MNIST fixture."""
    from matplotlib import pyplot as plt

    path = figures_dir / "mnist_class_balance.png"
    rows = _mapping_list(class_balance.get("rows"))
    labels = [str(index) for index in range(10)]
    train_counts = [_class_balance_count(rows, "train", label) for label in range(10)]
    test_counts = [_class_balance_count(rows, "test", label) for label in range(10)]
    x_positions = np.arange(10, dtype=float)
    width = 0.38

    fig, ax = plt.subplots(figsize=(7.6, 3.4))
    train_bars = ax.bar(x_positions - width / 2.0, train_counts, width, color="#0072b2", label="train")
    test_bars = ax.bar(x_positions + width / 2.0, test_counts, width, color="#e69f00", label="test")
    ax.set_title("Local MNIST fixture class balance")
    ax.set_xlabel("digit class")
    ax.set_ylabel("examples")
    ax.set_xticks(x_positions, labels=labels)
    ax.set_ylim(0, max([*train_counts, *test_counts], default=0) * 1.18)
    ax.grid(axis="y", color="#d4d4d8", linewidth=0.8)
    ax.set_axisbelow(True)
    for bars in (train_bars, test_bars):
        for bar in bars:
            height = int(bar.get_height())
            ax.text(bar.get_x() + bar.get_width() / 2.0, height + 3, str(height), ha="center", fontsize=7.5)
    ax.legend(loc="upper right", frameon=False, fontsize=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def write_mnist_error_examples_figure(project_root: Path, figures_dir: Path, result: MLTaskResult) -> Path:
    """Write deterministic accepted-candidate error examples from the test split."""
    from matplotlib import pyplot as plt

    path = figures_dir / "mnist_error_examples.png"
    config = load_mnist_task_config(project_root, result.task_config.source_path)
    _x_train, _y_train, x_test, _y_test = load_mnist_arrays(project_root, config)
    examples = accepted_error_examples(project_root, result, limit=10)
    if not examples:
        fig, ax = plt.subplots(figsize=(5.6, 2.0))
        ax.set_axis_off()
        ax.text(0.5, 0.5, "No accepted-candidate errors on the local test split", ha="center", va="center")
        fig.tight_layout()
        fig.savefig(path, dpi=160)
        plt.close(fig)
        return path

    fig, axes = plt.subplots(2, 5, figsize=(8.0, 4.6))
    for axis, example in zip(axes.ravel(), examples, strict=False):
        test_index = int(example["test_index"])
        axis.imshow(x_test[test_index], cmap="gray", vmin=0.0, vmax=1.0)
        axis.set_title(f"true {example['true_label']} / pred {example['predicted_label']}", fontsize=8, pad=7)
        axis.set_xticks(())
        axis.set_yticks(())
        for spine in axis.spines.values():
            spine.set_color("#7c2d12")
            spine.set_linewidth(0.8)
    for axis in axes.ravel()[len(examples) :]:
        axis.set_visible(False)
    fig.suptitle("Accepted candidate error examples", fontsize=12, y=0.98)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.94), h_pad=1.3, w_pad=0.8)
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def write_ml_calibration_reliability_figure(figures_dir: Path, calibration: dict[str, object]) -> Path:
    """Write accepted-candidate reliability and confidence-bin diagnostics."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_calibration_reliability.png"
    bins = _mapping_list(calibration.get("bins"))
    centers = [(float(row.get("lower", 0.0)) + float(row.get("upper", 0.0))) / 2.0 for row in bins]
    accuracy = [float(row.get("accuracy", 0.0)) for row in bins]
    confidence = [float(row.get("mean_confidence", 0.0)) for row in bins]
    counts = [int(row.get("count", 0)) for row in bins]

    fig, (ax_top, ax_bottom) = plt.subplots(
        2,
        1,
        figsize=(7.2, 5.2),
        sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1.0]},
    )
    ax_top.plot([0, 1], [0, 1], color="#52525b", linestyle="--", linewidth=1.0, label="ideal")
    ax_top.plot(centers, accuracy, marker="o", color="#0f766e", linewidth=1.8, label="bin accuracy")
    ax_top.plot(centers, confidence, marker="s", color="#2563eb", linewidth=1.5, label="mean confidence")
    ax_top.set_title("Accepted candidate calibration")
    ax_top.set_ylabel("fraction")
    ax_top.set_ylim(0.0, 1.05)
    ax_top.grid(axis="both", color="#d4d4d8", linewidth=0.8)
    ax_top.legend(loc="lower right", frameon=False, fontsize=8)
    ax_top.text(
        0.02,
        0.08,
        f"ECE {_float_value(calibration.get('expected_calibration_error')):.3f}",
        transform=ax_top.transAxes,
        fontsize=9,
        color="#334155",
    )
    ax_bottom.bar(centers, counts, width=0.08, color="#94a3b8")
    ax_bottom.set_xlabel("prediction confidence")
    ax_bottom.set_ylabel("count")
    ax_bottom.grid(axis="y", color="#d4d4d8", linewidth=0.8)
    for axis in (ax_top, ax_bottom):
        axis.set_axisbelow(True)
        for spine in axis.spines.values():
            spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def write_ml_classification_metrics_heatmap(figures_dir: Path, diagnostics: dict[str, object]) -> Path:
    """Write per-class precision/recall/F1 diagnostics as a heatmap."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_classification_metrics_heatmap.png"
    rows = _mapping_list(diagnostics.get("per_class"))
    matrix = np.asarray(
        [[float(row.get("precision", 0.0)), float(row.get("recall", 0.0)), float(row.get("f1", 0.0))] for row in rows],
        dtype=float,
    )
    fig, ax = plt.subplots(figsize=(5.8, 5.2))
    image = ax.imshow(matrix, vmin=0.0, vmax=1.0, cmap="YlGnBu")
    ax.set_title("Accepted candidate class metrics")
    ax.set_xticks(range(3), labels=("precision", "recall", "F1"))
    ax.set_yticks(range(len(rows)), labels=[str(row.get("class_label", index)) for index, row in enumerate(rows)])
    ax.set_ylabel("true digit")
    for row_index in range(matrix.shape[0]):
        for col_index in range(matrix.shape[1]):
            value = matrix[row_index, col_index]
            ax.text(
                col_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=8,
                color="white" if value > 0.72 else "#111827",
            )
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def write_ml_confusion_pairs_figure(figures_dir: Path, diagnostics: dict[str, object]) -> Path:
    """Write ranked non-diagonal confusion pairs."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_confusion_pairs.png"
    pairs = _mapping_list(diagnostics.get("top_confusion_pairs"))[:8]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    if not pairs:
        ax.set_axis_off()
        ax.text(0.5, 0.5, "No off-diagonal confusion pairs in the accepted-candidate matrix", ha="center", va="center")
    else:
        labels = [f"{row.get('true_label')} -> {row.get('predicted_label')}" for row in pairs]
        counts = [int(row.get("count", 0)) for row in pairs]
        rates = [_float_value(row.get("true_class_error_rate")) for row in pairs]
        bars = ax.barh(labels, counts, color="#7c2d12")
        ax.invert_yaxis()
        ax.set_title("Top accepted-candidate confusion pairs")
        ax.set_xlabel("count")
        max_count = max(counts, default=0)
        ax.set_xlim(0, max_count + 0.45)
        ax.set_xticks(range(0, max_count + 1))
        ax.grid(axis="x", color="#d4d4d8", linewidth=0.8)
        ax.set_axisbelow(True)
        for bar, value, rate in zip(bars, counts, rates, strict=True):
            ax.text(
                value + 0.05,
                bar.get_y() + bar.get_height() / 2.0,
                f"{value} ({rate:.0%})",
                va="center",
                fontsize=8,
            )
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def write_ml_generalization_gap_figure(figures_dir: Path, diagnostics: dict[str, object]) -> Path:
    """Write train/test accuracy and loss gaps by evaluated candidate."""
    from matplotlib import pyplot as plt

    path = figures_dir / "ml_generalization_gap.png"
    rows = _mapping_list(diagnostics.get("generalization"))
    labels = [str(row.get("candidate_id", "candidate")).replace("exp-", "") for row in rows]
    x_positions = np.arange(len(rows), dtype=float)
    width = 0.34
    fig, (ax_acc, ax_loss) = plt.subplots(2, 1, figsize=(7.4, 5.4), sharex=True)
    ax_acc.bar(
        x_positions - width / 2.0,
        [float(row.get("train_accuracy", 0.0)) for row in rows],
        width,
        color="#2563eb",
        label="train",
    )
    ax_acc.bar(
        x_positions + width / 2.0,
        [float(row.get("test_accuracy", 0.0)) for row in rows],
        width,
        color="#0f766e",
        label="test",
    )
    ax_acc.set_title("Candidate generalization diagnostics")
    ax_acc.set_ylabel("accuracy")
    ax_acc.set_ylim(0.0, 1.05)
    ax_acc.legend(loc="lower right", frameon=False, fontsize=8)
    ax_loss.bar(
        x_positions - width / 2.0,
        [float(row.get("train_loss", 0.0)) for row in rows],
        width,
        color="#60a5fa",
        label="train",
    )
    ax_loss.bar(
        x_positions + width / 2.0,
        [float(row.get("test_loss", 0.0)) for row in rows],
        width,
        color="#34d399",
        label="test",
    )
    ax_loss.set_ylabel("loss")
    ax_loss.set_xticks(x_positions, labels=labels, rotation=18, ha="right")
    ax_loss.legend(loc="upper right", frameon=False, fontsize=8)
    for axis in (ax_acc, ax_loss):
        axis.grid(axis="y", color="#d4d4d8", linewidth=0.8)
        axis.set_axisbelow(True)
        for spine in axis.spines.values():
            spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


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
    fig, ax = plt.subplots(figsize=(8.0, 3.8))
    image = ax.imshow(matrix, vmin=0.0, vmax=1.0, cmap="YlGnBu")
    ax.set_title("Deterministic robustness smoke test")
    ax.set_xticks(range(len(transforms)), labels=[value.replace("_", "\n") for value in transforms])
    ax.set_yticks(range(len(candidates)), labels=[value.replace("exp-", "") for value in candidates])
    for row_index in range(matrix.shape[0]):
        for col_index in range(matrix.shape[1]):
            value = matrix[row_index, col_index]
            ax.text(
                col_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=8,
                color="white" if value > 0.72 else "#111827",
            )
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


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
        axis.bar([value - width / 2.0 for value in centers], correct_counts, width, color="#0f766e", label="correct")
        axis.bar([value + width / 2.0 for value in centers], error_counts, width, color="#7c2d12", label="error")
        axis.set_title(title, fontsize=11)
        axis.set_ylabel("count")
        axis.grid(axis="y", color="#d4d4d8", linewidth=0.8)
        axis.set_axisbelow(True)
        axis.legend(loc="upper left", frameon=False, fontsize=8)
        for spine in axis.spines.values():
            spine.set_visible(False)
    ax_margin.set_xlabel("score bin")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


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
        ax.plot([low, high], [y_pos, y_pos], color="#2563eb", linewidth=3.0)
        ax.scatter([point], [y_pos], color="#0f766e", s=70, zorder=3)
        ax.text(high + 0.01, y_pos, f"{point:.3f}", va="center", fontsize=8, color="#334155")
    ax.set_title("Deterministic bootstrap intervals")
    ax.set_xlabel("metric value")
    ax.set_yticks(y_positions, labels=labels)
    ax.set_xlim(0.0, 1.05)
    ax.grid(axis="x", color="#d4d4d8", linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


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
    fig, ax = plt.subplots(figsize=(4.8, 4.2))
    image = ax.imshow(matrix, cmap="YlGnBu")
    ax.set_title("Matched correctness comparison")
    ax.set_xticks((0, 1), labels=("baseline wrong", "baseline correct"), rotation=20, ha="right")
    ax.set_yticks((0, 1), labels=("accepted wrong", "accepted correct"))
    for row_index in range(matrix.shape[0]):
        for col_index in range(matrix.shape[1]):
            value = int(matrix[row_index, col_index])
            ax.text(
                col_index,
                row_index,
                str(value),
                ha="center",
                va="center",
                fontsize=10,
                color="white" if value > 20 else "#111827",
            )
    ax.text(
        0.02,
        -0.18,
        f"exact McNemar p={_float_value(paired.get('exact_mcnemar_p')):.3f}",
        transform=ax.transAxes,
        fontsize=8,
        color="#334155",
    )
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


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
    ax.plot(thresholds, accuracy, color="#0f766e", linewidth=2.2, marker="o", label="selective accuracy")
    ax.plot(thresholds, coverage, color="#2563eb", linewidth=2.0, marker="s", label="coverage")
    ax.axhline(overall_accuracy, color="#52525b", linestyle="--", linewidth=1.0, label="overall accuracy")
    for x_value, y_value, count in zip(thresholds, accuracy, retained, strict=True):
        ax.annotate(f"n={count}", (x_value, y_value), xytext=(4, 6), textcoords="offset points", fontsize=8)
    ax.set_title("Confidence threshold trade-off")
    ax.set_xlabel("confidence threshold")
    ax.set_ylabel("fraction of test predictions")
    if thresholds:
        ax.set_xlim(max(0.0, min(thresholds) - 0.05), min(1.0, max(thresholds) + 0.05))
    ax.set_ylim(0.0, 1.05)
    ax.grid(color="#d4d4d8", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="lower left", frameon=False, fontsize=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


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
    colors = ["#0f766e" if row.get("candidate_id") == accepted_id else "#64748b" for row in rows]
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
        axis.grid(axis="x", color="#d4d4d8", linewidth=0.8)
        axis.set_axisbelow(True)
        for row_index, value in enumerate(values):
            axis.text(value + 0.01, row_index, f"{value:.3f}", va="center", fontsize=8)
        for spine in axis.spines.values():
            spine.set_visible(False)
    ax_brier.set_yticks(y_positions, labels=labels)
    ax_brier.invert_yaxis()
    ax_nll.legend(
        handles=[
            Patch(facecolor="#0f766e", label="accepted"),
            Patch(facecolor="#64748b", label="evaluated"),
        ],
        loc="upper right",
        frameon=False,
        fontsize=8,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


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
    colors = ["#0f766e" if row.get("candidate_id") == accepted_id else "#64748b" for row in rows]

    fig, (ax_accuracy, ax_gap) = plt.subplots(1, 2, figsize=(8.8, 3.8), sharey=True)
    ax_accuracy.barh(y_positions, final_accuracy, color=colors, label="final test accuracy")
    ax_accuracy.scatter(best_accuracy, y_positions, color="#f59e0b", s=42, zorder=3, label="best epoch")
    ax_accuracy.set_title("Final versus best epoch", fontsize=11)
    ax_accuracy.set_xlabel("held-out accuracy")
    ax_accuracy.set_xlim(0.0, 1.05)
    ax_accuracy.set_yticks(y_positions, labels=labels)
    ax_accuracy.invert_yaxis()
    for index, (final_value, best_value) in enumerate(zip(final_accuracy, best_accuracy, strict=True)):
        ax_accuracy.text(max(final_value, best_value) + 0.012, index, f"{best_value:.3f}", va="center", fontsize=8)

    ax_gap.axvline(0.0, color="#52525b", linewidth=1.0)
    ax_gap.barh(y_positions, gaps, color=colors)
    ax_gap.set_title("Train-test accuracy gap", fontsize=11)
    ax_gap.set_xlabel("train minus test")
    lower = min(0.0, min(gaps, default=0.0)) - 0.02
    upper = max(0.05, max(gaps, default=0.0)) + 0.02
    ax_gap.set_xlim(lower, upper)
    for index, gap in enumerate(gaps):
        ax_gap.text(gap + 0.004, index, f"{gap:.3f}", va="center", fontsize=8)

    for axis in (ax_accuracy, ax_gap):
        axis.grid(axis="x", color="#d4d4d8", linewidth=0.8)
        axis.set_axisbelow(True)
        for spine in axis.spines.values():
            spine.set_visible(False)
    ax_gap.legend(
        handles=[
            Patch(facecolor="#0f766e", label="accepted"),
            Patch(facecolor="#64748b", label="evaluated"),
        ],
        loc="lower right",
        frameon=False,
        fontsize=8,
    )
    ax_accuracy.legend(loc="lower right", frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def write_closure_flow_figure(figures_dir: Path, result: AutoResearchLoopResult) -> Path:
    """Write the file-backed research-process closure diagram."""
    from matplotlib import pyplot as plt

    path = figures_dir / "autoresearch_closure_flow.png"
    nodes = (
        ("Program", "program.md"),
        ("Proposals", "idea ledger"),
        ("Evaluation", f"{result.ml_task.get('evaluated_candidate_count', 'N/A')} candidates"),
        ("Ledgers", "run + artifacts"),
        ("Claims", f"{result.supported_claim_count} supported"),
        ("Manuscript", "variables + figures"),
        ("Readiness", "passed" if result.readiness_valid else "pending"),
        ("Review", "human deferred"),
    )
    fig, ax = plt.subplots(figsize=(10.4, 2.8))
    ax.set_axis_off()
    y = 0.5
    x_positions = [index / (len(nodes) - 1) for index in range(len(nodes))]
    for index, ((title, detail), x_pos) in enumerate(zip(nodes, x_positions, strict=True)):
        ax.text(
            x_pos,
            y,
            f"{title}\n{detail}",
            ha="center",
            va="center",
            fontsize=9,
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "#f8fafc",
                "edgecolor": "#334155",
                "linewidth": 1.0,
            },
        )
        if index < len(nodes) - 1:
            ax.annotate(
                "",
                xy=(x_positions[index + 1] - 0.055, y),
                xytext=(x_pos + 0.055, y),
                arrowprops={"arrowstyle": "->", "color": "#475569", "linewidth": 1.2},
            )
    ax.set_title("File-backed AutoResearch closure", fontsize=12, pad=18)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def write_security_control_matrix_figure(figures_dir: Path, threat_model: dict[str, object]) -> Path:
    """Write the local security control matrix."""
    from matplotlib import pyplot as plt

    path = figures_dir / "autoresearch_security_control_matrix.png"
    controls = _mapping_list(threat_model.get("controls"))
    labels = [str(row.get("id", "control")).removeprefix("ctrl-") for row in controls]
    frameworks = [str(row.get("framework", "framework")).replace("_", " ") for row in controls]
    statuses = [str(row.get("status", "unknown")) for row in controls]

    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    ax.set_axis_off()
    ax.set_title("Local security controls by evidence surface", fontsize=12, pad=12)
    columns = (
        ("Control", 0.03, 0.24),
        ("Evidence surface", 0.29, 0.28),
        ("Framework cue", 0.61, 0.22),
        ("Status", 0.86, 0.11),
    )
    header_y = 0.91
    for header, x_pos, _width in columns:
        ax.text(x_pos, header_y, header, transform=ax.transAxes, fontsize=9, fontweight="bold", va="center")
    ax.hlines(header_y - 0.04, 0.02, 0.98, transform=ax.transAxes, color="#94a3b8", linewidth=1.0)

    row_top = 0.81
    row_gap = 0.105 if controls else 0.1
    for index, row in enumerate(controls):
        y_pos = row_top - index * row_gap
        fill = "#f8fafc" if index % 2 == 0 else "#eef6f8"
        ax.add_patch(
            plt.Rectangle(
                (0.02, y_pos - 0.037),
                0.96,
                0.074,
                transform=ax.transAxes,
                facecolor=fill,
                edgecolor="#e2e8f0",
                linewidth=0.5,
            )
        )
        status = statuses[index]
        status_fill = "#d1fae5" if status == "implemented" else "#fef3c7"
        status_edge = "#0f766e" if status == "implemented" else "#a16207"
        status_text = "implemented" if status == "implemented" else status
        ax.text(0.03, y_pos, labels[index], transform=ax.transAxes, fontsize=8.2, va="center", color="#0f172a")
        ax.text(
            0.29,
            y_pos,
            str(row.get("evidence_key", "evidence")).replace("_", " "),
            transform=ax.transAxes,
            fontsize=8.2,
            va="center",
            color="#0f172a",
        )
        ax.text(0.61, y_pos, frameworks[index], transform=ax.transAxes, fontsize=8.2, va="center", color="#0f172a")
        ax.text(
            0.86,
            y_pos,
            status_text,
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=7.8,
            color="#064e3b" if status == "implemented" else "#713f12",
            bbox={
                "boxstyle": "round,pad=0.22",
                "facecolor": status_fill,
                "edgecolor": status_edge,
                "linewidth": 0.8,
            },
        )
    ax.text(
        0.98,
        0.045,
        "local checksum and review controls only",
        transform=ax.transAxes,
        ha="right",
        va="center",
        fontsize=8,
        color="#475569",
    )
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def write_security_integrity_chain_figure(figures_dir: Path, attestation: dict[str, object]) -> Path:
    """Write the local integrity attestation chain figure."""
    from matplotlib import pyplot as plt

    path = figures_dir / "autoresearch_integrity_chain.png"
    chain = (
        ("Inputs", "fixture + config"),
        ("Analysis", "deterministic loop"),
        ("Artifacts", "data + figures"),
        ("Checksums", "sha256"),
        ("Review", str(attestation.get("status", "pending"))),
    )
    fig, (ax_chain, ax_counts) = plt.subplots(2, 1, figsize=(9.0, 4.6), gridspec_kw={"height_ratios": [1.4, 1.0]})
    ax_chain.set_axis_off()
    x_positions = [index / (len(chain) - 1) for index in range(len(chain))]
    for index, ((title, detail), x_pos) in enumerate(zip(chain, x_positions, strict=True)):
        facecolor = "#ecfdf5" if title == "Review" and attestation.get("status") == "passed" else "#f8fafc"
        ax_chain.text(
            x_pos,
            0.55,
            f"{title}\n{detail}",
            ha="center",
            va="center",
            fontsize=9,
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": facecolor,
                "edgecolor": "#334155",
                "linewidth": 1.0,
            },
        )
        if index < len(chain) - 1:
            ax_chain.annotate(
                "",
                xy=(x_positions[index + 1] - 0.07, 0.55),
                xytext=(x_pos + 0.07, 0.55),
                arrowprops={"arrowstyle": "->", "color": "#475569", "linewidth": 1.2},
            )
    ax_chain.set_title("Local artifact integrity chain", fontsize=12, pad=8)

    labels = ("checked", "missing", "mismatch")
    values = (
        int(_float_value(attestation.get("checked_count", 0))),
        int(_float_value(attestation.get("missing_count", 0))),
        int(_float_value(attestation.get("mismatch_count", 0))),
    )
    colors = ("#0f766e", "#a16207", "#7c2d12")
    bars = ax_counts.bar(labels, values, color=colors)
    ax_counts.set_ylabel("file records")
    ax_counts.grid(axis="y", color="#d4d4d8", linewidth=0.8)
    ax_counts.set_axisbelow(True)
    ax_counts.set_ylim(0, max(values) + 1)
    for bar, value in zip(bars, values, strict=True):
        ax_counts.text(bar.get_x() + bar.get_width() / 2.0, value + 0.05, str(value), ha="center", fontsize=8)
    ax_counts.text(
        0.99,
        0.86,
        "no external signature",
        transform=ax_counts.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        color="#475569",
    )
    for spine in ax_counts.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def _first_label_index(labels: np.ndarray, label: int) -> int:
    matches = np.flatnonzero(labels == label)
    if matches.size == 0:
        raise ValueError(f"label is missing from MNIST subset: {label}")
    return int(matches[0])


def _mapping_list(value: object) -> list[dict[str, Any]]:
    return [row for row in value if isinstance(row, dict)] if isinstance(value, list) else []


def _float_value(value: object) -> float:
    return float(value) if isinstance(value, int | float | str) else 0.0


def _short_candidate_label(value: object) -> str:
    text = str(value)
    if text == "nearest_centroid_baseline":
        return "baseline"
    return text.replace("exp-", "")


def _status_color(status: str) -> str:
    return {
        "baseline": "#52525b",
        "accepted": "#0072b2",
        "rejected": "#56b4e9",
        "evaluated": "#56b4e9",
    }.get(status, "#64748b")


def _status_marker(status: str) -> str:
    return {"baseline": "s", "accepted": "D"}.get(status, "o")


def _class_balance_count(rows: list[dict[str, Any]], split: str, label: int) -> int:
    for row in rows:
        if row.get("split") == split and int(row.get("class_label", -1)) == label:
            return int(row.get("count", 0))
    return 0
