"""Numerical invariants for the gradient-descent optimization exemplar.

Pure-compute checks (zero I/O, no infrastructure imports) that validate the
actual numerical behaviour of the gradient descent in :mod:`optimizer`.

Each ``check_*`` function returns a list of :class:`InvariantResult`
records. The companion script (``scripts/build_dashboard.py``) converts
these to :class:`infrastructure.reporting.Invariant` instances for the
interactive dashboard and the plaintext invariants report; the test suite
asserts on them directly.

Design rule: this module **must not** import ``infrastructure.*`` (per
``src/AGENTS.md`` rule "src/ is infrastructure-independent").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

# Support both bare-imports (after `sys.path.insert(0, ".../src")`)
# and package-imports (`from src.invariants import ...` from tests).
try:
    from .optimizer import (
        OptimizationResult,
        compute_gradient,
        gradient_descent,
        quadratic_function,
        simulate_trajectory,
    )
except ImportError:  # pragma: no cover - resolved by sys.path
    from optimizer import (  # type: ignore[no-redef]
        OptimizationResult,
        compute_gradient,
        gradient_descent,
        quadratic_function,
        simulate_trajectory,
    )

ArrayF = NDArray[np.float64]


@dataclass
class InvariantResult:
    """Witness record for one numerical invariant.

    ``kind`` ∈ {``"equal"``, ``"le"``, ``"ge"``, ``"in_range"``,
    ``"monotone_increasing"``, ``"monotone_decreasing"``,
    ``"finite"``, ``"nonneg"``}; mirrors
    :class:`infrastructure.reporting.interactive_dashboard.Invariant`.
    """

    name: str
    kind: str
    actual: Any
    expected: Any = None
    tol: float = 1e-9
    description: str = ""
    extra: dict = field(default_factory=dict)


@dataclass(frozen=True)
class OptimizerSweepConfig:
    """Configurable knobs driving every optimization invariant.

    Defaults reproduce the exemplar 1-D quadratic ``f(x) = (1/2)x^2 − x``
    minimised by gradient descent with step size α.
    """

    step_sizes: tuple[float, ...]
    A: tuple[tuple[float, ...], ...] = ((1.0,),)
    b: tuple[float, ...] = (1.0,)
    initial_point: tuple[float, ...] = (0.0,)
    max_iterations: int = 1000
    tolerance: float = 1e-8

    def A_array(self) -> ArrayF:
        return np.array(self.A, dtype=np.float64)

    def b_array(self) -> ArrayF:
        return np.array(self.b, dtype=np.float64)

    def x0(self) -> ArrayF:
        return np.array(self.initial_point, dtype=np.float64)

    def closed_form_minimum(self) -> ArrayF:
        return np.asarray(
            np.linalg.solve(self.A_array(), self.b_array()),
            dtype=np.float64,
        )

    def stable_step_bound(self) -> float:
        """``2 / λ_max(A)`` — convergence bound for fixed-step GD on a quadratic."""
        eig = np.linalg.eigvalsh(self.A_array())
        return float(2.0 / eig.max())

    def run_for(self, alpha: float) -> OptimizationResult:
        return gradient_descent(
            initial_point=self.x0(),
            objective_func=lambda x: quadratic_function(x, A=self.A_array(), b=self.b_array()),
            gradient_func=lambda x: compute_gradient(x, A=self.A_array(), b=self.b_array()),
            max_iterations=self.max_iterations,
            tolerance=self.tolerance,
            step_size=alpha,
        )


# ---------------------------------------------------------------------------
# Per-family invariant builders
# ---------------------------------------------------------------------------


def convergence_invariants(cfg: OptimizerSweepConfig) -> list[InvariantResult]:
    """For every step size α with ``α < 2/λ_max(A)``: gradient descent must
    converge to ``x* = A^{-1} b`` and the objective history must be
    monotone non-increasing.
    """
    out: list[InvariantResult] = []
    x_star = cfg.closed_form_minimum()
    f_star = float(quadratic_function(x_star, A=cfg.A_array(), b=cfg.b_array()))
    bound = cfg.stable_step_bound()

    finals_stable: list[float] = []
    for alpha in cfg.step_sizes:
        result = cfg.run_for(float(alpha))
        history = result.objective_history or []
        if alpha < bound:
            finals_stable.append(float(result.objective_value))
            out.append(
                InvariantResult(
                    name=f"reached_minimum_alpha={alpha:g}",
                    kind="equal",
                    actual=float(np.linalg.norm(result.solution - x_star)),
                    expected=0.0,
                    tol=max(1e-3, 100 * cfg.tolerance),
                    description=(f"||x_final − x*|| ≤ {max(1e-3, 100 * cfg.tolerance):.1e} with x* = A^{{-1}} b"),
                )
            )
            out.append(
                InvariantResult(
                    name=f"objective_at_minimum_alpha={alpha:g}",
                    kind="equal",
                    actual=float(result.objective_value - f_star),
                    expected=0.0,
                    tol=1e-3,
                    description=f"f(x_final) − f(x*) ≤ 1e-3 (f* = {f_star:.6g})",
                )
            )
            out.append(
                InvariantResult(
                    name=f"objective_monotone_alpha={alpha:g}",
                    kind="monotone_decreasing",
                    actual=history,
                    tol=1e-9,
                    description=(f"objective history is monotone non-increasing for stable α={alpha:g}"),
                )
            )
    out.append(
        InvariantResult(
            name="optimizer_finite_after_run_stable",
            kind="finite",
            actual=finals_stable,
            description=(
                "every stable step size (α < 2/λ_max) yields a finite final "
                "objective (no NaN/Inf); divergent α intentionally not checked"
            ),
        )
    )
    return out


def gradient_consistency_invariants(
    cfg: OptimizerSweepConfig,
    eps: float = 1e-6,
    seed: int = 20260506,
) -> list[InvariantResult]:
    """Numerical-vs-analytical gradient agreement to floating tolerance."""
    A = cfg.A_array()
    b = cfg.b_array()
    rng = np.random.default_rng(seed=seed)
    n = len(b)
    x = rng.normal(size=n)
    g_analytic = compute_gradient(x, A=A, b=b)
    g_fd = np.empty_like(g_analytic)
    for i in range(n):
        e = np.zeros_like(x)
        e[i] = eps
        g_fd[i] = (quadratic_function(x + e, A=A, b=b) - quadratic_function(x - e, A=A, b=b)) / (2.0 * eps)
    return [
        InvariantResult(
            name="gradient_finite_difference_agreement",
            kind="equal",
            actual=float(np.max(np.abs(g_analytic - g_fd))),
            expected=0.0,
            tol=1e-5,
            description=(
                f"max |∇f_analytic − ∇f_finite_diff| < 1e-5 at a random test point (seed={seed}, eps={eps:g})"
            ),
        )
    ]


def trajectory_invariants(
    cfg: OptimizerSweepConfig,
    max_iter: int = 100,
) -> list[InvariantResult]:
    """``simulate_trajectory`` is monotone for every stable step size."""
    out: list[InvariantResult] = []
    bound = cfg.stable_step_bound()
    for alpha in cfg.step_sizes:
        if float(alpha) >= bound:
            continue
        traj = simulate_trajectory(float(alpha), max_iter=max_iter)
        out.append(
            InvariantResult(
                name=f"trajectory_monotone_alpha={alpha:g}",
                kind="monotone_decreasing",
                actual=list(traj["objectives"]),
                tol=1e-9,
                description=(f"simulate_trajectory(α={alpha:g}, max_iter={max_iter}) is monotone non-increasing"),
            )
        )
    return out


def all_invariants(cfg: OptimizerSweepConfig) -> list[InvariantResult]:
    """Every invariant the dashboard / plaintext report should display."""
    out: list[InvariantResult] = []
    out.extend(gradient_consistency_invariants(cfg))
    out.extend(convergence_invariants(cfg))
    out.extend(trajectory_invariants(cfg))
    return out


__all__ = [
    "InvariantResult",
    "OptimizerSweepConfig",
    "all_invariants",
    "convergence_invariants",
    "gradient_consistency_invariants",
    "trajectory_invariants",
]
