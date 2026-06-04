"""MNIST fixture figure writers."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .figures_core import (
    _class_balance_count,
    _first_label_index,
    _mapping_list,
    grouped_vertical_bars,
    hide_spines,
    palette_color,
    save_figure,
    styled_grid,
)
from src.ml.task import MLTaskResult, accepted_error_examples, load_mnist_arrays, load_mnist_task_config


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
            spine.set_color(palette_color("box_edge", "#334155"))
            spine.set_linewidth(0.8)
    fig.suptitle("Local subset examples by class", fontsize=12)
    fig.tight_layout()
    return save_figure(fig, path)


def write_mnist_class_balance_figure(figures_dir: Path, class_balance: dict[str, object]) -> Path:
    """Write train/test class-count balance for the local MNIST fixture."""
    from matplotlib import pyplot as plt

    path = figures_dir / "mnist_class_balance.png"
    rows = _mapping_list(class_balance.get("rows"))
    labels = [str(index) for index in range(10)]
    train_counts = [_class_balance_count(rows, "train", label) for label in range(10)]
    test_counts = [_class_balance_count(rows, "test", label) for label in range(10)]
    x_positions = np.arange(10, dtype=float)

    fig, ax = plt.subplots(figsize=(7.6, 3.4))
    grouped_vertical_bars(
        ax,
        x_positions,
        [
            ([float(v) for v in train_counts], "accepted", "#0072b2", "train"),
            ([float(v) for v in test_counts], "series_warn", "#e69f00", "test"),
        ],
        annotate=True,
    )
    ax.set_title("Local MNIST fixture class balance")
    ax.set_xlabel("digit class")
    ax.set_ylabel("examples")
    ax.set_xticks(x_positions, labels=labels)
    ax.set_ylim(0, max([*train_counts, *test_counts], default=0) * 1.18)
    styled_grid(ax, "y")
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", frameon=False, fontsize=8)
    hide_spines(ax)
    fig.tight_layout()
    return save_figure(fig, path)


def write_mnist_error_examples_figure(project_root: Path, figures_dir: Path, result: MLTaskResult) -> Path:
    """Write deterministic accepted-candidate error examples from the test split."""
    from matplotlib import pyplot as plt

    path = figures_dir / "mnist_error_examples.png"
    config = load_mnist_task_config(project_root, result.task_config.source_path)
    _x_train, _y_train, x_test, _y_test = load_mnist_arrays(project_root, config)
    examples = accepted_error_examples(project_root, result, limit=10)
    if not examples:
        fig, ax = plt.subplots(figsize=(5.6, 2.0))
        ax.axis("off")
        ax.text(0.5, 0.5, "No accepted-candidate errors on the local test split", ha="center", va="center")
        fig.tight_layout()
        return save_figure(fig, path)

    fig, axes = plt.subplots(2, 5, figsize=(8.0, 4.6))
    for axis, example in zip(axes.ravel(), examples, strict=False):
        test_index = int(example["test_index"])
        axis.imshow(x_test[test_index], cmap="gray", vmin=0.0, vmax=1.0)
        axis.set_title(f"true {example['true_label']} / pred {example['predicted_label']}", fontsize=8, pad=7)
        axis.set_xticks(())
        axis.set_yticks(())
        for spine in axis.spines.values():
            spine.set_color(palette_color("negative", "#7c2d12"))
            spine.set_linewidth(0.8)
    for axis in axes.ravel()[len(examples) :]:
        axis.set_visible(False)
    fig.suptitle("Accepted candidate error examples", fontsize=12, y=0.98)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.94), h_pad=1.3, w_pad=0.8)
    return save_figure(fig, path)


__all__ = [
    "write_mnist_class_balance_figure",
    "write_mnist_error_examples_figure",
    "write_mnist_subset_contact_sheet_figure",
]
