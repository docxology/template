"""Regression pins for deterministic optimization result claims."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_code_project"

_PKG_ALIAS = "_code_project_src"


def _load_src_package() -> ModuleType:
    """Load this exemplar's ``src`` package under a project-unique alias.

    Every public exemplar ships a top-level ``src`` package, so a bare
    ``sys.path.insert`` + ``from src...`` (the single-project pattern this
    file used before) collides on ``sys.modules['src']`` once a second
    project's regression test joins the same pytest session — whichever
    module collects first wins the cached ``src`` entry and every other
    project fails collection with ``ModuleNotFoundError``. Registering the
    package under a namespaced key keeps the real tested functions in scope
    (no mocks), lets the package's own internal imports resolve via
    ``submodule_search_locations``, and stays collision-free regardless of
    collection order.
    """

    if _PKG_ALIAS in sys.modules:
        return sys.modules[_PKG_ALIAS]
    src_init = PROJECT_ROOT / "src" / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        _PKG_ALIAS,
        src_init,
        submodule_search_locations=[str(PROJECT_ROOT / "src")],
    )
    assert spec is not None and spec.loader is not None, f"cannot load {src_init}"
    package = importlib.util.module_from_spec(spec)
    sys.modules[_PKG_ALIAS] = package
    spec.loader.exec_module(package)
    return package


def _import_submodule(dotted: str) -> ModuleType:
    _load_src_package()
    return importlib.import_module(f"{_PKG_ALIAS}.{dotted}")


run_convergence_experiment = _import_submodule("analysis.experiments").run_convergence_experiment
load_experiment_config = _import_submodule("experiment_config").load_experiment_config
quadratic_optimum = _import_submodule("optimizer").quadratic_optimum


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
