"""Regression pins for the deterministic AutoResearch 'Candidate Outcome' claims.

Manuscript: ``projects/templates/template_autoresearch_project/manuscript/03_results.md``
section ``## Candidate Outcome``. Every pinned value is re-derived here by calling
``src.ml.task.run_bounded_ml_task`` on the committed project configuration — no mock,
no hand-copied number. The bounded ML loop is deterministic (fixed seed, offline MNIST
fixture), so the re-derived values are byte-stable across runs and bind the manuscript
tokens to their source computation:

* ``{{CANDIDATE_COUNT}}``            -> ``MLTaskResult.candidate_count``
* ``{{EVALUATED_CANDIDATE_COUNT}}``  -> ``MLTaskResult.evaluated_candidate_count``
* ``{{BASELINE_ACCURACY}}``          -> ``MLTaskResult.baseline.test_accuracy`` (renders 82.6%)
* ``{{BEST_ACCURACY}}``              -> ``MLTaskResult.best_accuracy`` (renders 89.4%)
* ``{{ACCURACY_DELTA}}``             -> ``MLTaskResult.accuracy_delta`` (renders 6.8%)
* ``{{ACCEPTED_PARAMETER_COUNT}}``   -> ``MLTaskResult.accepted_candidate.parameter_count``
* ``{{BENCHMARK_SCORE}}``            -> ``MLTaskResult.benchmark_score`` (renders 1)
"""

from __future__ import annotations

import importlib
from pathlib import Path
import sys
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_autoresearch_project"


def _load_project_src() -> Any:
    """Import the project's ``src`` package for a clean re-derivation.

    Both this exemplar and ``template_code_project`` ship a top-level ``src``
    package, so a bare ``sys.path.insert`` + ``import src`` would let whichever
    regression module imports first win the cached ``src`` name in
    ``sys.modules`` and break the other's collection. To keep every project's
    re-derivation independent (and let the whole ``tests/regression/`` tier
    collect together), we insert this project root, import ``src`` fresh, and
    then invalidate the cache so the next project imports its own ``src``.
    """

    inserted = str(PROJECT_ROOT) not in sys.path
    if inserted:
        sys.path.insert(0, str(PROJECT_ROOT))
    for name in [key for key in sys.modules if key == "src" or key.startswith("src.")]:
        del sys.modules[name]
    try:
        config = importlib.import_module("src.config")
        task = importlib.import_module("src.ml.task")
    finally:
        # Drop this project's ``src`` from the module cache and the path so a
        # sibling project regression module can import its own ``src`` cleanly.
        for name in [key for key in sys.modules if key == "src" or key.startswith("src.")]:
            del sys.modules[name]
        if inserted and str(PROJECT_ROOT) in sys.path:
            sys.path.remove(str(PROJECT_ROOT))
    return config.load_loop_config, task.run_bounded_ml_task


load_loop_config, run_bounded_ml_task = _load_project_src()


def _pin(pinned: dict[str, Any], key: str) -> dict[str, Any]:
    entry = pinned[key]
    assert isinstance(entry, dict), f"{key} must be an object"
    assert "value" in entry, f"{key} must include a pinned value"
    return entry


def _assert_pin_matches(entry: dict[str, Any], observed: float | int) -> None:
    tolerance = entry.get("abs_tolerance", 0)
    assert observed == pytest.approx(entry["value"], abs=tolerance)


@pytest.fixture(scope="module")
def ml_result() -> Any:
    """Re-run the deterministic bounded ML task from the committed config."""

    config = load_loop_config(PROJECT_ROOT)
    return run_bounded_ml_task(PROJECT_ROOT, config.budget_policy)


def test_candidate_counts_rederive_from_bounded_ml_task(
    load_pinned_values: Any,
    ml_result: Any,
) -> None:
    """Bind the proposed / evaluated candidate counts to the source loop."""

    pinned = load_pinned_values("template_autoresearch_project")

    _assert_pin_matches(_pin(pinned, "candidate_outcome_candidate_count"), ml_result.candidate_count)
    _assert_pin_matches(
        _pin(pinned, "candidate_outcome_evaluated_candidate_count"),
        ml_result.evaluated_candidate_count,
    )


def test_accuracy_claims_rederive_from_bounded_ml_task(
    load_pinned_values: Any,
    ml_result: Any,
) -> None:
    """Bind baseline/selected accuracy and their delta to the source loop."""

    pinned = load_pinned_values("template_autoresearch_project")

    _assert_pin_matches(
        _pin(pinned, "candidate_outcome_baseline_accuracy"),
        float(ml_result.baseline.test_accuracy),
    )
    _assert_pin_matches(
        _pin(pinned, "candidate_outcome_best_accuracy"),
        float(ml_result.best_accuracy),
    )
    _assert_pin_matches(
        _pin(pinned, "candidate_outcome_accuracy_delta"),
        float(ml_result.accuracy_delta),
    )
    # Cross-check the delta identity so the three accuracy pins stay internally
    # consistent, not just individually equal to their committed values.
    assert float(ml_result.accuracy_delta) == pytest.approx(
        float(ml_result.best_accuracy) - float(ml_result.baseline.test_accuracy),
        abs=1e-09,
    )


def test_model_and_benchmark_claims_rederive_from_bounded_ml_task(
    load_pinned_values: Any,
    ml_result: Any,
) -> None:
    """Bind the accepted-model parameter count and benchmark score to the source loop."""

    pinned = load_pinned_values("template_autoresearch_project")

    _assert_pin_matches(
        _pin(pinned, "candidate_outcome_accepted_parameter_count"),
        int(ml_result.accepted_candidate.parameter_count),
    )
    _assert_pin_matches(
        _pin(pinned, "candidate_outcome_benchmark_score"),
        float(ml_result.benchmark_score),
    )


def test_pin_mutation_negative_control_fails(load_pinned_values: Any) -> None:
    """Changing a committed pin must fail the comparison predicate.

    This is the non-vacuity control: it proves ``_assert_pin_matches`` actually
    rejects a mutated ground-truth value rather than passing unconditionally.
    """

    pinned = load_pinned_values("template_autoresearch_project")
    entry = dict(_pin(pinned, "candidate_outcome_evaluated_candidate_count"))
    observed = entry["value"]
    entry["value"] = observed + 1

    with pytest.raises(AssertionError):
        _assert_pin_matches(entry, observed)
