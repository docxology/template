"""Shared experiment configuration for the template_code_project exemplar.

Single loader for ``manuscript/config.yaml`` → ``experiment:`` block.
Used by analysis, figures, dashboard, and manuscript variable generation.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from .invariants import OptimizerSweepConfig


logger = logging.getLogger(__name__)


class _MalformedExperimentValue(ValueError):
    """Internal signal that an ``experiment`` value cannot be typed."""


def _unsupported(field: str, raw: Any) -> None:
    logger.warning(
        "config.yaml experiment.%s: unsupported value %r; using the exemplar default",
        field,
        raw,
    )


def _require_float(value: Any) -> float:
    """Return ``value`` as a finite float or raise the malformed sentinel."""

    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise _MalformedExperimentValue
    try:
        result = float(value)
    except ValueError as exc:
        raise _MalformedExperimentValue from exc
    if not math.isfinite(result):
        raise _MalformedExperimentValue
    return result


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


def _coerce_float_tuple(values: Any, default: tuple[float, ...], field: str) -> tuple[float, ...]:
    if values is None:
        return default
    if not values:
        _unsupported(field, values)
        return default
    items = values if isinstance(values, (list, tuple)) else (values,)
    try:
        coerced = tuple(_require_float(item) for item in items)
    except _MalformedExperimentValue:
        _unsupported(field, values)
        return default
    return coerced or default


def _coerce_matrix(values: Any, default: tuple[tuple[float, ...], ...], field: str) -> tuple[tuple[float, ...], ...]:
    if values is None:
        return default
    if not values:
        _unsupported(field, values)
        return default
    if isinstance(values, (list, tuple)) and values and isinstance(values[0], (list, tuple)):
        try:
            rows = [tuple(_require_float(item) for item in row) for row in values]
        except _MalformedExperimentValue:
            _unsupported(field, values)
            return default
        if any(not row for row in rows) or len({len(row) for row in rows}) != 1:
            # Empty or ragged rows cannot form a numeric matrix.
            _unsupported(field, values)
            return default
        return tuple(rows)
    # A scalar or flat list is not a matrix shape. Preserve the documented
    # fallback, but stop discarding the authored value silently.
    _unsupported(field, values)
    return default


def _coerce_float_field(field: str, value: Any, default: float) -> float:
    if isinstance(value, (list, tuple, dict)):
        _unsupported(field, value)
        return default
    try:
        return _require_float(value)
    except _MalformedExperimentValue:
        _unsupported(field, value)
        return default


def _coerce_int_field(field: str, value: Any, default: int) -> int:
    if isinstance(value, bool) or value is None or isinstance(value, (list, tuple, dict)):
        _unsupported(field, value)
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        _unsupported(field, value)
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        _unsupported(field, value)
        return default


def _coerce_int_tuple(values: Any, default: tuple[int, ...], field: str) -> tuple[int, ...]:
    if values is None:
        return default
    if not values:
        _unsupported(field, values)
        return default
    items = values if isinstance(values, (list, tuple)) else (values,)
    coerced: list[int] = []
    for item in items:
        if isinstance(item, bool):
            _unsupported(field, values)
            return default
        if isinstance(item, int):
            coerced.append(item)
        elif isinstance(item, float) and item.is_integer():
            coerced.append(int(item))
        elif isinstance(item, str):
            try:
                coerced.append(int(item))
            except ValueError:
                _unsupported(field, values)
                return default
        else:
            # Non-integral floats must not truncate silently.
            _unsupported(field, values)
            return default
    return tuple(coerced) or default


def _coerce_benchmark_dimensions(values: Any) -> tuple[int, ...]:
    dimensions = _coerce_int_tuple(values, _DEFAULT_BENCHMARK_DIMENSIONS, "benchmark_dimensions")
    if any(dimension < 1 for dimension in dimensions):
        # A sweep grid needs positive dimensions; negatives are meaningless.
        _unsupported("benchmark_dimensions", values)
        return _DEFAULT_BENCHMARK_DIMENSIONS
    return dimensions


def load_experiment_config(project_root: Path | None = None) -> ExperimentConfig:
    """Load experiment parameters from ``manuscript/config.yaml``.

    Returns defaults matching the exemplar YAML when the file is missing.
    A present-but-malformed value never raises: the affected field falls
    back to its exemplar default and a warning names the field and value.
    """
    root = project_root or Path(__file__).resolve().parent.parent.parent.parent
    config_path = root / "manuscript" / "config.yaml"
    if not config_path.exists():
        return ExperimentConfig()

    with config_path.open("r") as f:
        data = yaml.safe_load(f) or {}

    exp_raw = data.get("experiment", {})
    exp: dict[str, Any] = exp_raw if isinstance(exp_raw, dict) else {}
    if exp_raw is not None and not isinstance(exp_raw, dict):
        _unsupported("experiment (mapping expected)", exp_raw)

    raw_initial = exp.get("initial_point", 0.0)
    if isinstance(raw_initial, (list, tuple)) and not raw_initial:
        _unsupported("initial_point", raw_initial)
        initial_val = 0.0
    else:
        try:
            initial_val = _require_float(raw_initial[0] if isinstance(raw_initial, (list, tuple)) else raw_initial)
        except _MalformedExperimentValue:
            _unsupported("initial_point", raw_initial)
            initial_val = 0.0

    return ExperimentConfig(
        step_sizes=_coerce_float_tuple(exp.get("step_sizes"), _DEFAULT_STEP_SIZES, "step_sizes"),
        quadratic_A=_coerce_matrix(exp.get("quadratic_A"), ((1.0,),), "quadratic_A"),
        quadratic_b=_coerce_float_tuple(exp.get("quadratic_b"), (1.0,), "quadratic_b"),
        initial_point=initial_val,
        max_iterations=_coerce_int_field("max_iterations", exp.get("max_iterations", 1000), 1000),
        tolerance=_coerce_float_field("tolerance", exp.get("tolerance", 1e-8), 1e-8),
        convergence_tolerance=_coerce_float_field(
            "convergence_tolerance",
            exp.get("convergence_tolerance", exp.get("tolerance", 1e-8)),
            1e-8,
        ),
        stability_starting_points=_coerce_float_tuple(
            exp.get("stability_starting_points"), _DEFAULT_STABILITY_STARTING, "stability_starting_points"
        ),
        stability_step_sizes=_coerce_float_tuple(
            exp.get("stability_step_sizes"), _DEFAULT_STABILITY_STEP_SIZES, "stability_step_sizes"
        ),
        benchmark_dimensions=_coerce_benchmark_dimensions(exp.get("benchmark_dimensions")),
    )
