"""Shared experiment configuration for the template_code_project exemplar.

Single loader for ``manuscript/config.yaml`` → ``experiment:`` block.
Used by analysis, figures, dashboard, and manuscript variable generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml

try:
    from .invariants import OptimizerSweepConfig
except ImportError:  # pragma: no cover
    from invariants import OptimizerSweepConfig  # type: ignore[no-redef]


_DEFAULT_STEP_SIZES: tuple[float, ...] = (0.01, 0.1, 0.5, 1.0, 1.5, 2.5)
_DEFAULT_STABILITY_STARTING: tuple[float, ...] = (-50.0, -10.0, -5.0, 0.0, 0.1, 5.0, 10.0, 50.0)
_DEFAULT_STABILITY_STEP_SIZES: tuple[float, ...] = (0.01, 0.05, 0.1, 0.2, 0.5, 0.9)
_DEFAULT_BENCHMARK_DIMENSIONS: tuple[int, ...] = (1, 2, 5, 10, 20, 50)


@dataclass(frozen=True)
class ExperimentConfig:
    """Frozen experiment parameters from ``config.yaml`` → ``experiment:``."""

    step_sizes: tuple[float, ...] = _DEFAULT_STEP_SIZES
    quadratic_A: tuple[tuple[float, ...], ...] = ((1.0,),)
    quadratic_b: tuple[float, ...] = (1.0,)
    initial_point: float = 0.0
    max_iterations: int = 1000
    tolerance: float = 1e-8
    convergence_tolerance: float = 1e-8
    stability_starting_points: tuple[float, ...] = _DEFAULT_STABILITY_STARTING
    stability_step_sizes: tuple[float, ...] = _DEFAULT_STABILITY_STEP_SIZES
    benchmark_dimensions: tuple[int, ...] = _DEFAULT_BENCHMARK_DIMENSIONS

    def A_array(self) -> np.ndarray:
        """Process A array."""
        return np.array(self.quadratic_A, dtype=np.float64)

    def b_array(self) -> np.ndarray:
        """Process b array."""
        return np.array(self.quadratic_b, dtype=np.float64)

    def x0(self) -> np.ndarray:
        """Process x0."""
        return np.array([self.initial_point], dtype=np.float64)

    def to_sweep_config(self) -> OptimizerSweepConfig:
        """Bridge to :class:`OptimizerSweepConfig` for invariant checks."""
        return OptimizerSweepConfig(
            step_sizes=self.step_sizes,
            A=self.quadratic_A,
            b=self.quadratic_b,
            initial_point=(self.initial_point,),
            max_iterations=self.max_iterations,
            tolerance=self.tolerance,
        )


def _coerce_float_tuple(values: Any, default: tuple[float, ...]) -> tuple[float, ...]:
    if not values:
        return default
    if isinstance(values, (list, tuple)):
        return tuple(float(v) for v in values)
    return (float(values),)


def _coerce_matrix(values: Any, default: tuple[tuple[float, ...], ...]) -> tuple[tuple[float, ...], ...]:
    if not values:
        return default
    if isinstance(values, (list, tuple)) and values and isinstance(values[0], (list, tuple)):
        return tuple(tuple(float(v) for v in row) for row in values)
    return default


def _coerce_int_tuple(values: Any, default: tuple[int, ...]) -> tuple[int, ...]:
    if not values:
        return default
    if isinstance(values, (list, tuple)):
        return tuple(int(v) for v in values)
    return (int(values),)


def load_experiment_config(project_root: Path | None = None) -> ExperimentConfig:
    """Load experiment parameters from ``manuscript/config.yaml``.

    Returns defaults matching the exemplar YAML when the file is missing.
    """
    root = project_root or Path(__file__).resolve().parent.parent
    config_path = root / "manuscript" / "config.yaml"
    if not config_path.exists():
        return ExperimentConfig()

    with config_path.open("r") as f:
        data = yaml.safe_load(f) or {}

    exp: dict[str, Any] = data.get("experiment", {}) or {}

    initial = exp.get("initial_point", 0.0)
    if isinstance(initial, (list, tuple)):
        initial_val = float(initial[0]) if initial else 0.0
    else:
        initial_val = float(initial)

    return ExperimentConfig(
        step_sizes=_coerce_float_tuple(exp.get("step_sizes"), _DEFAULT_STEP_SIZES),
        quadratic_A=_coerce_matrix(exp.get("quadratic_A"), ((1.0,),)),
        quadratic_b=_coerce_float_tuple(exp.get("quadratic_b"), (1.0,)),
        initial_point=initial_val,
        max_iterations=int(exp.get("max_iterations", 1000)),
        tolerance=float(exp.get("tolerance", 1e-8)),
        convergence_tolerance=float(exp.get("convergence_tolerance", exp.get("tolerance", 1e-8))),
        stability_starting_points=_coerce_float_tuple(
            exp.get("stability_starting_points"), _DEFAULT_STABILITY_STARTING
        ),
        stability_step_sizes=_coerce_float_tuple(exp.get("stability_step_sizes"), _DEFAULT_STABILITY_STEP_SIZES),
        benchmark_dimensions=_coerce_int_tuple(exp.get("benchmark_dimensions"), _DEFAULT_BENCHMARK_DIMENSIONS),
    )
