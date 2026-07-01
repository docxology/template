"""Regression pins for the deterministic analytical Active-Inference track.

Manuscript: projects/templates/template_active_inference/manuscript/
10_results_mi_sweep.md, 11_results_free_energy.md, 05_methods_analytical.md.

This exemplar is multi-track (analytical + pymdp + sheaf + Lean/GNN/ontology).
Its pymdp/jax tracks are NOT importable from the repo root ``.venv`` (numpy +
scipy only), so these pins bind the **analytical** track exclusively: the
closed-form K=2 Bernoulli/Ising toy that backs the MI-sweep and free-energy
Results sections. Each value is re-derived by calling the exact same ``src``
functions the analysis pipeline uses -- ``orchestration.analysis`` writes the
parameter sweep with ``ising_mutual_information`` / ``empirical_mutual_information``
over ``lambda_grid(hp)``, and ``manuscript.variables`` reduces those rows into
the manuscript tokens (``param_sweep_grid_points``, ``lambda_max``,
``ising_mi_saturation``, ``sweep_max_residual``, ``free_energy_argmin_lambda``).
We reproduce that reduction here from source -- never by hand-copying a
manuscript number.

No mocks: real deterministic (no-sampling) closed-form objects only, in line
with the repo no-mock policy.
"""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[5]
PROJECT_ROOT = REPO_ROOT / "projects" / "templates" / "template_active_inference"

_PKG_ALIAS = "_active_inference_src"


def _load_src_package() -> ModuleType:
    """Load this exemplar's ``src`` package under a project-unique alias.

    Every public exemplar ships a top-level ``src`` package, so a bare
    ``sys.path.insert`` + ``from src...`` collides on ``sys.modules['src']``
    once a second project's regression test joins the same pytest session.
    Registering under a namespaced key keeps the real tested functions in
    scope (no mocks) and stays collision-free regardless of collection order.
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


_hp_mod = _import_submodule("analytical.hyperparameters")
load_hyperparameters = _hp_mod.load_hyperparameters
lambda_grid = _hp_mod.lambda_grid

_toy_mod = _import_submodule("analytical.bernoulli_toy")
ising_mutual_information = _toy_mod.ising_mutual_information
empirical_mutual_information = _toy_mod.empirical_mutual_information
ising_coupling = _toy_mod.ising_coupling
ising_joint_posterior = _toy_mod.ising_joint_posterior
symmetric_mean_field_prior = _toy_mod.symmetric_mean_field_prior

_decomp_mod = _import_submodule("analytical.decomposition")
free_energy_against_entangled_prior = _decomp_mod.free_energy_against_entangled_prior


def _pin(pinned: dict[str, Any], key: str) -> dict[str, Any]:
    entry = pinned[key]
    assert isinstance(entry, dict), f"{key} must be an object"
    assert "value" in entry, f"{key} must include a pinned value"
    return entry


def _assert_pin_matches(entry: dict[str, Any], observed: float | int) -> None:
    tolerance = entry.get("abs_tolerance", 0)
    assert observed == pytest.approx(entry["value"], abs=tolerance)


@pytest.fixture(scope="module")
def sweep_rows() -> list[dict[str, float]]:
    """Re-derive the parameter-sweep rows exactly as orchestration.analysis writes them.

    ``write_parameter_sweep`` iterates ``lambda_grid(load_hyperparameters())`` and,
    per lambda, records ``closed_form_mi = ising_mutual_information(lam)`` and
    ``empirical_mi = empirical_mutual_information(lam)`` (an independent exact
    recomputation via total correlation). We rebuild the same rows from source.
    """

    hp = load_hyperparameters()
    return [
        {
            "lambda": float(lam),
            "closed_form_mi": ising_mutual_information(lam),
            "empirical_mi": empirical_mutual_information(lam),
        }
        for lam in lambda_grid(hp)
    ]


def test_mi_sweep_grid_claims_rederive_from_source(
    load_pinned_values: Any,
    sweep_rows: list[dict[str, float]],
) -> None:
    """Bind the sweep grid size and lambda_max to source.

    10_results_mi_sweep.md / 05_methods_analytical.md: "We sweep coupling
    strength lambda on a grid of {{param_sweep_grid_points}} points up to
    lambda_max = {{lambda_max}}."
    """

    pinned = load_pinned_values("template_active_inference")
    hp = load_hyperparameters()

    # param_sweep_grid_points token: the manuscript reports len(sweep_rows).
    _assert_pin_matches(_pin(pinned, "mi_sweep_grid_points"), len(sweep_rows))
    # lambda_max token: the single-source-of-truth hyperparameter.
    _assert_pin_matches(_pin(pinned, "mi_sweep_lambda_max"), hp.lambda_max)


def test_ising_mi_saturation_claim_rederives_from_source(
    load_pinned_values: Any,
    sweep_rows: list[dict[str, float]],
) -> None:
    """Bind the saturation-MI headline to a fresh source run.

    11_results_free_energy.md: "Saturation MI (grid maximum on the measured
    lambda sweep): {{ising_mi_saturation}} nats." Re-derived as the grid maximum
    of the closed-form MI, exactly as manuscript.variables._ising_mi_saturation_from_sweep.
    """

    pinned = load_pinned_values("template_active_inference")
    saturation = max(row["closed_form_mi"] for row in sweep_rows)
    _assert_pin_matches(_pin(pinned, "ising_mi_saturation"), saturation)


def test_mi_sweep_agreement_residual_claim_rederives_from_source(
    load_pinned_values: Any,
    sweep_rows: list[dict[str, float]],
) -> None:
    """Bind the cross-implementation agreement claim to source.

    10_results_mi_sweep.md: "both are deterministic (no sampling) and agree to
    {{sweep_max_residual}} nats." Re-derived as the max absolute residual
    between the closed-form MI and the independent exact recomputation via total
    correlation, exactly as analytical.sweep_io.summarize_sweep_rows computes it.
    A genuine regression (the two code paths diverging) blows through the
    machine-epsilon-scale residual and fails loudly.
    """

    pinned = load_pinned_values("template_active_inference")
    max_residual = max(abs(row["empirical_mi"] - row["closed_form_mi"]) for row in sweep_rows)
    _assert_pin_matches(_pin(pinned, "mi_sweep_max_residual"), max_residual)


def test_free_energy_argmin_lambda_claim_rederives_from_source(
    load_pinned_values: Any,
) -> None:
    """Bind the free-energy argmin lambda to source.

    11_results_free_energy.md: "its minimum at lambda={{free_energy_argmin_lambda}}
    is where the entangled posterior coincides with the factorized mean-field
    product." Replicates manuscript.variables._free_energy_argmin_lambda: evaluate
    free energy of the entangled posterior against the mean-field prior across the
    grid and take the grid lambda at the minimum, rounded to grid precision (4dp).
    """

    import numpy as np

    pinned = load_pinned_values("template_active_inference")
    hp = load_hyperparameters()
    lambdas = lambda_grid(hp)
    mf = symmetric_mean_field_prior()
    g0 = [np.zeros(2), np.zeros(2)]
    j = ising_coupling()
    kc = np.zeros((2, 2))
    values = [
        free_energy_against_entangled_prior(ising_joint_posterior(float(lam)), mf, g0, j, kc, gamma=1.0, lam=float(lam))
        for lam in lambdas
    ]
    argmin_lambda = round(float(lambdas[int(np.argmin(values))]), 4)
    _assert_pin_matches(_pin(pinned, "free_energy_argmin_lambda"), argmin_lambda)


def test_pin_mutation_negative_control_fails(load_pinned_values: Any) -> None:
    """Changing a committed pin must fail the comparison predicate.

    Non-vacuity control (feedback-verify-not-trust-machine-proof): proves the
    assertions above can actually fail, so a green run means the re-derivation
    genuinely matched the pin -- not that the comparison is a no-op.
    """

    pinned = load_pinned_values("template_active_inference")
    entry = dict(_pin(pinned, "ising_mi_saturation"))
    observed = entry["value"]
    entry["value"] = observed + 1.0  # perturb the pinned ground truth
    entry["abs_tolerance"] = 1e-12

    with pytest.raises(AssertionError):
        _assert_pin_matches(entry, observed)
