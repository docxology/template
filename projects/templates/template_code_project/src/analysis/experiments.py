"""Convergence experiments and result persistence."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

try:
    from ..experiment_config import ExperimentConfig, load_experiment_config
    from ..optimizer import OptimizationResult, make_quadratic_problem, gradient_descent
except ImportError:  # pragma: no cover
    from experiment_config import ExperimentConfig, load_experiment_config  # type: ignore[no-redef]
    from optimizer import OptimizationResult, make_quadratic_problem, gradient_descent  # type: ignore[no-redef]

from ._logging import get_logger
from ..project_paths import resolve_project_root


def _project_root() -> Path:
    return resolve_project_root("src.analysis")


def run_convergence_experiment(
    *,
    on_step: Callable[[float, OptimizationResult], None] | None = None,
    config: ExperimentConfig | None = None,
) -> dict[float, OptimizationResult]:
    """Run gradient descent with different step sizes and track convergence."""
    logger = get_logger()
    logger.info("Running convergence experiments...")

    cfg = config or load_experiment_config(_project_root())
    A = cfg.A_array()
    b = cfg.b_array()
    obj_func, grad_func = make_quadratic_problem(A, b)
    initial_point = cfg.x0()
    results: dict[float, OptimizationResult] = {}

    for step_size in cfg.step_sizes:
        logger.info("Testing step size: %s", step_size)
        result = gradient_descent(
            initial_point=initial_point,
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=float(step_size),
            max_iterations=cfg.max_iterations,
            tolerance=cfg.tolerance,
            verbose=False,
        )
        results[float(step_size)] = result
        logger.info("  Converged: %s, Final value: %.4f", result.converged, result.objective_value)
        if on_step is not None:
            on_step(float(step_size), result)

    return results


def save_optimization_results(results: dict[float, OptimizationResult]) -> Path:
    """Save optimization results to CSV file."""
    logger = get_logger()
    logger.info("Saving optimization results...")

    output_dir = _project_root() / "output" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    data_path = output_dir / "optimization_results.csv"

    with open(data_path, "w", encoding="utf-8", newline="") as f:
        f.write("step_size,solution,objective_value,iterations,converged,gradient_norm,termination_reason\n")
        for step_size, result in results.items():
            solution_str = ";".join(f"{v:.6f}" for v in result.solution)
            f.write(
                f"{step_size},{solution_str},{result.objective_value:.6f},"
                f"{result.iterations},{result.converged},{result.gradient_norm:.2e},"
                f"{result.termination_reason}\n"
            )

    logger.info("Saved results to: %s", data_path)
    return data_path


__all__ = ["run_convergence_experiment", "save_optimization_results"]
