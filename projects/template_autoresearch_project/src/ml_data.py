"""Data-loading compatibility exports for the MNIST AutoResearch task."""

from __future__ import annotations

from .ml_training import (
    DatasetSummary,
    DiagnosticConfig,
    MNISTTaskConfig,
    RobustnessTransformSpec,
    TrainingConfig,
    load_mnist_arrays,
    load_mnist_task_config,
    summarize_dataset,
)

__all__ = [
    "DatasetSummary",
    "DiagnosticConfig",
    "MNISTTaskConfig",
    "RobustnessTransformSpec",
    "TrainingConfig",
    "load_mnist_arrays",
    "load_mnist_task_config",
    "summarize_dataset",
]
