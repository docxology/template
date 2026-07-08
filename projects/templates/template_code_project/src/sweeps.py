"""Shared alpha-sweep and stability-matrix helpers for the code-project exemplar.

Consolidates sweep logic previously duplicated across ``figures.py``,
``dashboard.py``, and ``invariants.py`` callers.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:
    from .experiment_config import ExperimentConfig
    from .invariants import OptimizerSweepConfig
    from .optimizer import (
        gradient_descent,
        make_quadratic_problem,
        quadratic_optimum,
    )
except ImportError:  # pragma: no cover
    from experiment_config import ExperimentConfig  # type: ignore[no-redef]
    from invariants import OptimizerSweepConfig  # type: ignore[no-redef]
    from optimizer import (  # type: ignore[no-redef]
        gradient_descent,
        make_quadratic_problem,
        quadratic_optimum,
    )

# Step sizes used by the sensitivity figure (log-spaced stable regime).
DEFAULT_SENSITIVITY_ALPHAS: tuple[float, ...] = (
    0.005,
    0.01,
    0.02,
    0.05,
    0.08,
    0.1,
    0.15,
    0.2,
    0.3,
    0.4,
)


@dataclass(frozen=True)
class AlphaSweepConfig:
    """Knobs for :func:`run_alpha_sweep`."""

    A: np.ndarray
    b: np.ndarray
    initial_point: np.ndarray
    max_iterations: int
    tolerance: float
    alphas: tuple[float, ...] | None = None
    alpha_min: float | None = None
    alpha_max: float | None = None
    alpha_num: int | None = None
    divergence_threshold: float = 1e3

    def resolved_alphas(self) -> np.ndarray:
        """Process resolved alphas."""
        if self.alphas is not None:
            return np.array(self.alphas, dtype=np.float64)
        if self.alpha_min is None or self.alpha_max is None or self.alpha_num is None:
            raise ValueError("Provide either alphas or alpha_min/alpha_max/alpha_num")
        return np.linspace(self.alpha_min, self.alpha_max, self.alpha_num)


@dataclass
class AlphaSweepResult:
    """Numerical payload for an α sweep."""

    alphas: list[float]
    iterations: list[int]
    final_dist: list[float]
    final_obj: list[float]
    diverged: list[bool]


def run_alpha_sweep(cfg: AlphaSweepConfig) -> AlphaSweepResult:
    """Run gradient descent for each α and collect convergence diagnostics."""
    alphas = cfg.resolved_alphas()
    x_star = np.linalg.solve(cfg.A, cfg.b)
    sweep_cfg = OptimizerSweepConfig(
        step_sizes=tuple(float(a) for a in alphas),
        A=tuple(tuple(row) for row in cfg.A),
        b=tuple(float(v) for v in cfg.b),
        initial_point=tuple(float(v) for v in cfg.initial_point),
        max_iterations=int(cfg.max_iterations),
        tolerance=float(cfg.tolerance),
    )

    iters: list[int] = []
    final_dist: list[float] = []
    final_obj: list[float] = []
    diverged: list[bool] = []

    for alpha in alphas:
        try:
            result = sweep_cfg.run_for(float(alpha))
            dist = float(np.linalg.norm(result.solution - x_star))
            iters.append(int(result.iterations))
            final_dist.append(dist)
            final_obj.append(float(result.objective_value))
            diverged.append(dist > cfg.divergence_threshold)
        except (OverflowError, FloatingPointError, ValueError, np.linalg.LinAlgError):
            iters.append(int(cfg.max_iterations))
            final_dist.append(float("inf"))
            final_obj.append(float("inf"))
            diverged.append(True)

    return AlphaSweepResult(
        alphas=[float(a) for a in alphas],
        iterations=iters,
        final_dist=final_dist,
        final_obj=final_obj,
        diverged=diverged,
    )


def stability_error_matrix(cfg: ExperimentConfig) -> np.ndarray:
    """Build log₁₀|f(x) − f(x*)| matrix (rows=starting points, cols=step sizes)."""
    A = cfg.A_array()
    b = cfg.b_array()
    _, optimal_value = quadratic_optimum(A, b)

    starting_points = list(cfg.stability_starting_points)
    step_sizes = list(cfg.stability_step_sizes)
    max_iter = int(cfg.max_iterations)
    tol = float(cfg.tolerance)

    obj_func, grad_func = make_quadratic_problem(A, b)
    error_matrix = np.zeros((len(starting_points), len(step_sizes)))

    for i, x0 in enumerate(starting_points):
        for j, alpha in enumerate(step_sizes):
            result = gradient_descent(
                initial_point=np.array([float(x0)]),
                objective_func=obj_func,
                gradient_func=grad_func,
                step_size=float(alpha),
                max_iterations=max_iter,
                tolerance=tol,
            )
            err = abs(result.objective_value - optimal_value)
            error_matrix[i, j] = np.log10(max(err, 1e-16))

    return error_matrix


def sensitivity_sweep(cfg: ExperimentConfig, *, max_iter: int = 500) -> AlphaSweepResult:
    """α sweep for the step-size sensitivity figure (fixed stable α grid)."""
    return run_alpha_sweep(
        AlphaSweepConfig(
            alphas=DEFAULT_SENSITIVITY_ALPHAS,
            A=cfg.A_array(),
            b=cfg.b_array(),
            initial_point=cfg.x0(),
            max_iterations=max_iter,
            tolerance=float(cfg.tolerance),
        )
    )


__all__ = [
    "AlphaSweepConfig",
    "AlphaSweepResult",
    "DEFAULT_SENSITIVITY_ALPHAS",
    "run_alpha_sweep",
    "sensitivity_sweep",
    "stability_error_matrix",
]
