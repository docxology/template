"""Regression pins for deterministic optimization result claims."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_code_project"
sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.experiments import run_convergence_experiment  # noqa: E402
from src.experiment_config import load_experiment_config  # noqa: E402
from src.optimizer import quadratic_optimum  # noqa: E402


def _pin(pinned: dict[str, Any], key: str) -> dict[str, Any]:
    entry = pinned[key]
    assert isinstance(entry, dict), f"{key} must be an object"
    assert "value" in entry, f"{key} must include a pinned value"
    return entry


def _assert_pin_matches(entry: dict[str, Any], observed: float | int) -> None:
    tolerance = entry.get("abs_tolerance", 0)
    assert observed == pytest.approx(entry["value"], abs=tolerance)


@pytest.fixture(scope="module")
def configured_results() -> tuple[Any, dict[float, Any]]:
    """Run the deterministic experiment from the committed project config."""

    config = load_experiment_config(PROJECT_ROOT)
    return config, run_convergence_experiment(config=config)


def test_solution_accuracy_claims_rederive_from_quadratic(load_pinned_values: Any) -> None:
    """Bind the manuscript optimum claims to the source quadratic."""

    pinned = load_pinned_values("template_code_project")
    config = load_experiment_config(PROJECT_ROOT)

    optimum_x, optimum_f = quadratic_optimum(config.A_array(), config.b_array())

    _assert_pin_matches(_pin(pinned, "solution_accuracy_target_solution"), float(optimum_x[0]))
    _assert_pin_matches(_pin(pinned, "solution_accuracy_target_objective"), optimum_f)


def test_configured_grid_iteration_claims_match_pins(
    load_pinned_values: Any,
    configured_results: tuple[Any, dict[float, Any]],
) -> None:
    """Bind the configured result-table statistics to a fresh source run."""

    pinned = load_pinned_values("template_code_project")
    _, results = configured_results

    iterations = [result.iterations for result in results.values()]
    best_step_size = min(results, key=lambda step: (results[step].iterations, step))
    converged_count = sum(1 for result in results.values() if result.converged)

    _assert_pin_matches(_pin(pinned, "opt_results_best_step_size"), best_step_size)
    _assert_pin_matches(_pin(pinned, "opt_results_min_iterations"), min(iterations))
    _assert_pin_matches(_pin(pinned, "opt_results_max_iterations"), max(iterations))
    _assert_pin_matches(_pin(pinned, "opt_results_mean_iterations_rounded"), round(float(np.mean(iterations))))
    _assert_pin_matches(_pin(pinned, "opt_results_num_converged"), converged_count)


def test_pin_mutation_negative_control_fails(load_pinned_values: Any) -> None:
    """Changing a committed pin must fail the comparison predicate."""

    pinned = load_pinned_values("template_code_project")
    entry = dict(_pin(pinned, "opt_results_num_converged"))
    observed = entry["value"]
    entry["value"] = observed + 1

    with pytest.raises(AssertionError):
        _assert_pin_matches(entry, observed)
