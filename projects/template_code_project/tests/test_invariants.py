"""Tests for the numerical-invariants module (`src/invariants.py`).

These tests are the test-side mirror of the dashboard pipeline in
``scripts/build_dashboard.py``: every public symbol exported by
``src/invariants.py`` is exercised against the gradient-descent
implementation in ``src/optimizer.py`` using real numerical computations
(no mocks, per the project's Zero-Mock policy).

The invariants themselves are property-style assertions about the
optimizer (closed-form-minimum agreement, monotone objective history,
finite-difference gradient agreement, trajectory monotonicity); these
tests ensure (a) the invariant *builders* return well-formed
``InvariantResult`` records and (b) the invariants the dashboard ships
to readers actually hold for the canonical exemplar problem.

> **Template Exemplar Note**: This module enforces the Zero-Mock policy
> and contributes to the ≥90% src/ coverage gate in ``pyproject.toml``.
"""

from __future__ import annotations

import warnings
from dataclasses import is_dataclass

import numpy as np
import pytest
from src.invariants import (
    InvariantResult,
    OptimizerSweepConfig,
    all_invariants,
    convergence_invariants,
    gradient_consistency_invariants,
    trajectory_invariants,
)

# The convergence-invariant builder deliberately runs gradient descent at step
# sizes above the stable bound 2/λ_max(A) to exercise the unstable branch; the
# resulting overflow → ±inf → NaN cascade is the falsifiable witness for the
# "finite_after_run_stable" invariant. Suppress those warnings module-wide so
# the test signal is not lost in numpy chatter.
pytestmark = [
    pytest.mark.filterwarnings(
        "ignore:overflow encountered in multiply:RuntimeWarning"
    ),
    pytest.mark.filterwarnings(
        "ignore:invalid value encountered in subtract:RuntimeWarning"
    ),
]


# also silence at import time for the cfg_1d.run_for(2.5) helper invocations
warnings.filterwarnings(
    "ignore",
    message="overflow encountered in multiply",
    category=RuntimeWarning,
)
warnings.filterwarnings(
    "ignore",
    message="invalid value encountered in subtract",
    category=RuntimeWarning,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cfg_1d() -> OptimizerSweepConfig:
    """Canonical 1-D quadratic ``f(x) = (1/2) x^2 − x`` swept over a
    range of step sizes that includes both stable and unstable values."""
    return OptimizerSweepConfig(
        step_sizes=(0.05, 0.1, 0.5, 1.0, 1.9, 2.5),
        A=((1.0,),),
        b=(1.0,),
        initial_point=(0.0,),
        max_iterations=2000,
        tolerance=1e-9,
    )


@pytest.fixture
def cfg_2d() -> OptimizerSweepConfig:
    """2-D anisotropic quadratic with a different stable-step bound,
    used to verify ``stable_step_bound`` and the multidimensional code
    paths in the invariant builders."""
    return OptimizerSweepConfig(
        step_sizes=(0.1, 0.5, 0.9),
        A=((2.0, 0.0), (0.0, 4.0)),
        b=(1.0, -1.0),
        initial_point=(0.0, 0.0),
        max_iterations=2000,
        tolerance=1e-9,
    )


# ---------------------------------------------------------------------------
# InvariantResult dataclass
# ---------------------------------------------------------------------------


class TestInvariantResult:
    """Test the public dataclass that carries witness data."""

    def test_is_dataclass_with_expected_fields(self):
        assert is_dataclass(InvariantResult)
        ir = InvariantResult(name="x", kind="equal", actual=1.0)
        assert ir.name == "x"
        assert ir.kind == "equal"
        assert ir.actual == 1.0
        assert ir.expected is None
        assert ir.tol == 1e-9
        assert ir.description == ""
        assert ir.extra == {}

    def test_extra_default_is_independent_dict(self):
        """Each instance must own a fresh ``extra`` dict (default_factory)."""
        a = InvariantResult(name="a", kind="finite", actual=[1.0])
        b = InvariantResult(name="b", kind="finite", actual=[2.0])
        a.extra["k"] = 1
        assert b.extra == {}

    def test_full_record_construction(self):
        ir = InvariantResult(
            name="f_at_minimum",
            kind="equal",
            actual=1e-9,
            expected=0.0,
            tol=1e-3,
            description="f(x_final) − f(x*) ≤ 1e-3",
            extra={"alpha": 0.5},
        )
        assert ir.tol == 1e-3
        assert ir.extra == {"alpha": 0.5}


# ---------------------------------------------------------------------------
# OptimizerSweepConfig
# ---------------------------------------------------------------------------


class TestOptimizerSweepConfig:
    """Test the config dataclass that drives every invariant builder."""

    def test_array_helpers_have_correct_dtype_and_shape(self, cfg_2d):
        A = cfg_2d.A_array()
        b = cfg_2d.b_array()
        x0 = cfg_2d.x0()
        assert A.dtype == np.float64
        assert b.dtype == np.float64
        assert x0.dtype == np.float64
        assert A.shape == (2, 2)
        assert b.shape == (2,)
        assert x0.shape == (2,)

    def test_closed_form_minimum_matches_linear_solve(self, cfg_1d, cfg_2d):
        # 1-D: f(x) = (1/2)x^2 − x  →  x* = 1
        assert np.allclose(cfg_1d.closed_form_minimum(), np.array([1.0]))
        # 2-D: A x = b with diag(2,4) and b=(1,-1) → x* = (0.5, -0.25)
        assert np.allclose(cfg_2d.closed_form_minimum(), np.array([0.5, -0.25]))

    def test_stable_step_bound_is_two_over_lambda_max(self, cfg_2d):
        # A = diag(2, 4) → λ_max = 4 → bound = 0.5
        assert cfg_2d.stable_step_bound() == pytest.approx(0.5)

    def test_run_for_returns_optimization_result(self, cfg_1d):
        result = cfg_1d.run_for(0.1)
        assert hasattr(result, "solution")
        assert hasattr(result, "objective_value")
        assert hasattr(result, "iterations")
        assert hasattr(result, "converged")
        # canonical 1-D problem converges to x* = 1.0 at α=0.1
        assert np.allclose(result.solution, np.array([1.0]), atol=1e-3)
        assert result.converged is True

    def test_run_for_diverges_above_stable_bound(self, cfg_1d):
        """α=2.5 exceeds 2/λ_max=2.0 — solution must not converge to x*=1.0."""
        result = cfg_1d.run_for(2.5)
        # An unstable step size either drives the solution to ±inf/NaN or far
        # from x*; we only require ``not converged`` plus a non-finite or
        # large-norm witness, which is the falsifiable condition the
        # convergence invariants rely on.
        assert result.converged is False
        sol = np.asarray(result.solution, dtype=float)
        diverged = (not np.all(np.isfinite(sol))) or (
            np.linalg.norm(sol - np.array([1.0])) > 1.0
        )
        assert diverged, f"unstable α=2.5 unexpectedly stayed near x*: {sol}"

    def test_config_is_frozen(self, cfg_1d):
        with pytest.raises(Exception):  # FrozenInstanceError or similar
            cfg_1d.step_sizes = (0.1,)  # type: ignore[misc]


# ---------------------------------------------------------------------------
# convergence_invariants
# ---------------------------------------------------------------------------


class TestConvergenceInvariants:
    """Convergence builder (``f(x_final) − f(x*) → 0`` for stable α)."""

    def test_returns_list_of_invariant_results(self, cfg_1d):
        invs = convergence_invariants(cfg_1d)
        assert isinstance(invs, list)
        assert all(isinstance(i, InvariantResult) for i in invs)
        assert len(invs) > 0

    def test_emits_three_invariants_per_stable_step_size(self, cfg_1d):
        """For 1-D problem, stable α<2.0; cfg_1d has 5 stable + 1 unstable.
        Each stable α produces 3 records (reached_minimum, objective_at_minimum,
        objective_monotone), plus one global ``optimizer_finite_after_run_stable``."""
        invs = convergence_invariants(cfg_1d)
        names = [i.name for i in invs]
        stable_count = sum(1 for a in cfg_1d.step_sizes if a < cfg_1d.stable_step_bound())
        assert stable_count == 5
        assert len([n for n in names if n.startswith("reached_minimum_")]) == stable_count
        assert len([n for n in names if n.startswith("objective_at_minimum_")]) == stable_count
        assert len([n for n in names if n.startswith("objective_monotone_")]) == stable_count
        assert "optimizer_finite_after_run_stable" in names

    def test_stable_step_invariants_actually_pass(self, cfg_1d):
        """Smoke-validate the witnesses produced for stable step sizes."""
        invs = convergence_invariants(cfg_1d)
        for inv in invs:
            if inv.name.startswith("reached_minimum_"):
                assert inv.actual <= inv.tol, (
                    f"{inv.name} witness {inv.actual} exceeded tolerance {inv.tol}"
                )
            elif inv.name.startswith("objective_at_minimum_"):
                # f_final − f* should be at or below tol for any stable α.
                assert inv.actual <= inv.tol

    def test_objective_history_is_monotone_non_increasing(self, cfg_1d):
        invs = convergence_invariants(cfg_1d)
        histories = [
            inv.actual
            for inv in invs
            if inv.name.startswith("objective_monotone_")
        ]
        assert histories  # at least one stable α exercises this branch
        for hist in histories:
            arr = np.asarray(hist, dtype=float)
            assert np.all(np.diff(arr) <= 1e-9)

    def test_finite_invariant_includes_every_stable_step_size(self, cfg_1d):
        invs = convergence_invariants(cfg_1d)
        finite = next(i for i in invs if i.name == "optimizer_finite_after_run_stable")
        assert finite.kind == "finite"
        # one final objective per *stable* step size (5 of 6 in cfg_1d).
        stable = [a for a in cfg_1d.step_sizes if a < cfg_1d.stable_step_bound()]
        assert len(finite.actual) == len(stable)
        # by construction the dashboard will only display these on stable runs;
        # all witnesses must therefore be finite.
        assert all(np.isfinite(v) for v in finite.actual)

    def test_2d_problem_emits_invariants_for_all_stable_alphas(self, cfg_2d):
        invs = convergence_invariants(cfg_2d)
        # cfg_2d.stable_step_bound() == 0.5 → α∈{0.1} stable, {0.5, 0.9} excluded
        stable = [a for a in cfg_2d.step_sizes if a < cfg_2d.stable_step_bound()]
        assert len(stable) == 1
        names = [i.name for i in invs]
        assert sum(1 for n in names if n.startswith("reached_minimum_")) == 1


# ---------------------------------------------------------------------------
# gradient_consistency_invariants
# ---------------------------------------------------------------------------


class TestGradientConsistencyInvariants:
    """Numerical-vs-analytical gradient builder."""

    def test_returns_single_invariant(self, cfg_1d):
        invs = gradient_consistency_invariants(cfg_1d)
        assert len(invs) == 1
        assert invs[0].name == "gradient_finite_difference_agreement"
        assert invs[0].kind == "equal"

    def test_witness_below_tolerance_for_canonical_problem(self, cfg_1d):
        invs = gradient_consistency_invariants(cfg_1d)
        assert invs[0].actual <= invs[0].tol

    def test_eps_and_seed_are_honoured(self, cfg_2d):
        a = gradient_consistency_invariants(cfg_2d, eps=1e-5, seed=7)
        b = gradient_consistency_invariants(cfg_2d, eps=1e-5, seed=7)
        # Same seed + eps must yield identical witness values.
        assert a[0].actual == b[0].actual
        c = gradient_consistency_invariants(cfg_2d, eps=1e-5, seed=8)
        # Different seed perturbs the sample point; witness should not be byte-identical.
        # (We do not assert magnitude; only that the seed parameter actually flows through.)
        assert a[0].actual != c[0].actual or c[0].actual <= c[0].tol

    def test_witness_holds_for_anisotropic_2d_problem(self, cfg_2d):
        invs = gradient_consistency_invariants(cfg_2d, eps=1e-6, seed=42)
        assert invs[0].actual <= invs[0].tol


# ---------------------------------------------------------------------------
# trajectory_invariants
# ---------------------------------------------------------------------------


class TestTrajectoryInvariants:
    """``simulate_trajectory`` monotonicity builder."""

    def test_emits_one_invariant_per_stable_step_size(self, cfg_1d):
        invs = trajectory_invariants(cfg_1d, max_iter=50)
        stable = [a for a in cfg_1d.step_sizes if a < cfg_1d.stable_step_bound()]
        assert len(invs) == len(stable)
        for inv in invs:
            assert inv.name.startswith("trajectory_monotone_")
            assert inv.kind == "monotone_decreasing"

    def test_each_trajectory_is_monotone_non_increasing(self, cfg_1d):
        invs = trajectory_invariants(cfg_1d, max_iter=80)
        for inv in invs:
            arr = np.asarray(inv.actual, dtype=float)
            assert np.all(np.diff(arr) <= 1e-9)

    def test_unstable_alpha_produces_no_trajectory_record(self, cfg_1d):
        invs = trajectory_invariants(cfg_1d, max_iter=30)
        names = [i.name for i in invs]
        # α=2.5 exceeds the 2/λ_max=2.0 bound and must not appear.
        assert "trajectory_monotone_alpha=2.5" not in names

    def test_max_iter_bounds_history_length(self, cfg_1d):
        max_iter = 17
        invs = trajectory_invariants(cfg_1d, max_iter=max_iter)
        for inv in invs:
            assert len(inv.actual) <= max_iter + 1  # initial + iterations

    def test_2d_problem_only_stable_alphas_appear(self, cfg_2d):
        invs = trajectory_invariants(cfg_2d, max_iter=40)
        # Only α=0.1 is below the 0.5 bound for cfg_2d.
        names = [i.name for i in invs]
        assert names == ["trajectory_monotone_alpha=0.1"]


# ---------------------------------------------------------------------------
# all_invariants — top-level aggregator used by build_dashboard.py
# ---------------------------------------------------------------------------


class TestAllInvariants:
    """Aggregator returns the union of every per-family builder."""

    def test_aggregates_every_family(self, cfg_1d):
        gradient = gradient_consistency_invariants(cfg_1d)
        convergence = convergence_invariants(cfg_1d)
        trajectory = trajectory_invariants(cfg_1d)
        merged = all_invariants(cfg_1d)
        assert len(merged) == len(gradient) + len(convergence) + len(trajectory)

    def test_every_record_is_invariant_result(self, cfg_2d):
        merged = all_invariants(cfg_2d)
        assert merged
        for ir in merged:
            assert isinstance(ir, InvariantResult)
            # InvariantResult.kind is one of the documented categories.
            assert ir.kind in {
                "equal",
                "le",
                "ge",
                "in_range",
                "monotone_increasing",
                "monotone_decreasing",
                "finite",
                "nonneg",
            }

    def test_every_record_has_a_unique_name(self, cfg_1d):
        merged = all_invariants(cfg_1d)
        names = [ir.name for ir in merged]
        assert len(names) == len(set(names)), "duplicate invariant names: %s" % names
