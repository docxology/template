"""Project test fixtures."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from pathlib import Path
import sys
from typing import Any

import pytest

from src.models import AutoResearchLoopResult

_FIGURE_WRITER_NAMES = (
    "write_candidate_lifecycle_figure",
    "write_closure_flow_figure",
    "write_mnist_class_balance_figure",
    "write_mnist_error_examples_figure",
    "write_mnist_subset_contact_sheet_figure",
    "write_ml_bootstrap_intervals_figure",
    "write_ml_calibration_reliability_figure",
    "write_ml_candidate_rank_stability_figure",
    "write_ml_candidate_scores_figure",
    "write_ml_classification_metrics_heatmap",
    "write_ml_complexity_accuracy_figure",
    "write_ml_confusion_matrix_figure",
    "write_ml_confusion_pairs_figure",
    "write_ml_generalization_gap_figure",
    "write_ml_learning_curve_figure",
    "write_ml_paired_correctness_figure",
    "write_ml_per_class_accuracy_figure",
    "write_ml_probability_margin_figure",
    "write_ml_probability_quality_figure",
    "write_ml_robustness_matrix_figure",
    "write_ml_selective_accuracy_figure",
    "write_ml_training_dynamics_figure",
    "write_stage_matrix_figure",
)


def _current_coverage() -> object | None:
    coverage_module = sys.modules.get("coverage")
    coverage_class = getattr(coverage_module, "Coverage", None)
    return coverage_class.current() if coverage_class is not None else None


def _without_coverage(function: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(function)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        coverage_controller = _current_coverage()
        if coverage_controller is not None:
            coverage_controller.stop()  # type: ignore[attr-defined]
        try:
            return function(*args, **kwargs)
        finally:
            if coverage_controller is not None:
                coverage_controller.start()  # type: ignore[attr-defined]

    return wrapped


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def repo_root(project_root: Path) -> Path:
    """Return the template repository root."""
    return project_root.parents[1]


@pytest.fixture(scope="session")
def autoresearch_loop_result(project_root: Path, repo_root: Path) -> AutoResearchLoopResult:
    """Run the full deterministic loop once for read-only output assertions."""
    from src.loop import run_autoresearch_loop
    import src.writers as writers

    originals = {name: getattr(writers, name) for name in _FIGURE_WRITER_NAMES}
    for name, function in originals.items():
        setattr(writers, name, _without_coverage(function))
    try:
        return run_autoresearch_loop(project_root, repo_root)
    finally:
        for name, function in originals.items():
            setattr(writers, name, function)
