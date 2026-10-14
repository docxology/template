"""Independent scalar quadratic facts, never native or Original authority.

The fixed Code exemplar computes f(x) = a*x*x/2 - b*x and updates
x <- x - alpha*(a*x-b). This module uses stdlib binary64 arithmetic rather
than the project's optimizer, NumPy, callbacks, result objects or generator.
All configured rows and signed serialized fields are compared exactly.
"""

from __future__ import annotations

import math
import sys
import time
from collections.abc import Mapping
from dataclasses import dataclass

CSV_HEADER = "step_size,solution,objective_value,iterations,converged,gradient_norm,termination_reason\n"
MAX_CSV_BYTES = 1024 * 1024
MAX_VARIABLE_BYTES = 4 * 1024 * 1024
MAX_STEPS = 64
MAX_ITERATIONS = 10000


def _clock(deadline: float | None) -> None:
    if deadline is not None:
        if type(deadline) not in (int, float) or not math.isfinite(deadline):
            raise ValueError("Code scalar predicate requires a finite original deadline")
        if time.monotonic() >= deadline:
            raise TimeoutError("Code scalar predicate exhausted its original deadline")


def _finite(value: float, field: str, *, positive: bool = False) -> None:
    if type(value) not in (float, int) or not math.isfinite(value) or positive and value <= 0:
        raise ValueError(f"Code scalar {field} must be finite" + (" and positive" if positive else ""))


@dataclass(frozen=True)
class ScalarQuadraticConfig:
    """Normalized configuration DATA; its Source origin is admitted elsewhere."""

    step_sizes: tuple[float, ...]
    coefficient: float
    linear: float
    initial_point: float
    max_iterations: int
    tolerance: float
    convergence_tolerance: float
    stability_starting_points: tuple[float, ...]
    stability_step_sizes: tuple[float, ...]
    benchmark_dimensions: tuple[int, ...]

    def __post_init__(self) -> None:
        for name, positive in (
            ("coefficient", True),
            ("linear", False),
            ("initial_point", False),
            ("tolerance", True),
            ("convergence_tolerance", True),
        ):
            _finite(getattr(self, name), name, positive=positive)
        if type(self.max_iterations) is not int or not 0 < self.max_iterations <= MAX_ITERATIONS:
            raise ValueError("Code scalar iteration cap is absent or exceeds its fixed bound")
        for name, positive in (
            ("step_sizes", True),
            ("stability_starting_points", False),
            ("stability_step_sizes", True),
        ):
            values = getattr(self, name)
            if type(values) is not tuple or not 0 < len(values) <= MAX_STEPS:
                raise ValueError(f"Code scalar {name} needs a complete bounded tuple")
            for value in values:
                _finite(value, name, positive=positive)
            if len(set(values)) != len(values):
                raise ValueError(f"Code scalar {name} repeats a configured condition")
        if (
            type(self.benchmark_dimensions) is not tuple
            or not 0 < len(self.benchmark_dimensions) <= MAX_STEPS
            or any(type(value) is not int or value <= 0 for value in self.benchmark_dimensions)
            or len(set(self.benchmark_dimensions)) != len(self.benchmark_dimensions)
        ):
            raise ValueError("Code scalar benchmark dimensions need a complete unique positive grid")


def _authored_float(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Code authored {field} needs an explicit finite numeric value")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError(f"Code authored {field} is outside finite binary64") from exc
    _finite(result, field)
    return result


def _authored_tuple(value: object, field: str) -> tuple[float, ...]:
    if not isinstance(value, list) or not 0 < len(value) <= MAX_STEPS:
        raise ValueError(f"Code authored {field} needs an explicit complete bounded list")
    return tuple(_authored_float(item, field) for item in value)


def _exact_config_data(config: ScalarQuadraticConfig) -> tuple[object, ...]:
    # Equality on floats would silently equate -0.0 and +0.0. Their exact
    # binary64 signs are part of the authored config and signed CSV contract.
    return (
        tuple(float(value).hex() for value in config.step_sizes),
        float(config.coefficient).hex(),
        float(config.linear).hex(),
        float(config.initial_point).hex(),
        config.max_iterations,
        float(config.tolerance).hex(),
        float(config.convergence_tolerance).hex(),
        tuple(float(value).hex() for value in config.stability_starting_points),
        tuple(float(value).hex() for value in config.stability_step_sizes),
        config.benchmark_dimensions,
    )


def validate_explicit_scalar_config(config: ScalarQuadraticConfig, experiment: Mapping[str, object]) -> None:
    """Bind typed loader DATA to every explicit authored scalar experiment field.

    This check is independent of the mutable project module/class globals.
    It accepts no fallback policy or callback. The enclosing Source adapter
    independently authenticates and parses the actual unambiguous YAML bytes;
    passing declaration DATA here does not create Source/native authority.
    Missing, malformed, string-coerced or nonscalar declarations stay blocked.
    """
    required = {
        "step_sizes",
        "quadratic_A",
        "quadratic_b",
        "initial_point",
        "max_iterations",
        "tolerance",
        "convergence_tolerance",
        "stability_starting_points",
        "stability_step_sizes",
        "benchmark_dimensions",
    }
    if (
        not isinstance(config, ScalarQuadraticConfig)
        or not isinstance(experiment, Mapping)
        or not required <= set(experiment)
    ):
        raise ValueError("Code numeric qualification requires every explicit authored experiment field")
    matrix = experiment["quadratic_A"]
    if not isinstance(matrix, list) or len(matrix) != 1:
        raise ValueError("Code authored quadratic_A requires the complete scalar matrix")
    coefficient = _authored_tuple(matrix[0], "quadratic_A")
    linear = _authored_tuple(experiment["quadratic_b"], "quadratic_b")
    if len(coefficient) != 1 or len(linear) != 1:
        raise ValueError("Code authored quadratic_A/quadratic_b require dimension one")
    maximum = experiment["max_iterations"]
    dimensions = experiment["benchmark_dimensions"]
    if isinstance(maximum, bool) or not isinstance(maximum, int):
        raise ValueError("Code authored max_iterations requires its explicit integer cap")
    if not isinstance(dimensions, list) or any(
        isinstance(value, bool) or not isinstance(value, int) for value in dimensions
    ):
        raise ValueError("Code authored benchmark_dimensions requires its explicit integer grid")
    expected = ScalarQuadraticConfig(
        step_sizes=_authored_tuple(experiment["step_sizes"], "step_sizes"),
        coefficient=coefficient[0],
        linear=linear[0],
        initial_point=_authored_float(experiment["initial_point"], "initial_point"),
        max_iterations=maximum,
        tolerance=_authored_float(experiment["tolerance"], "tolerance"),
        convergence_tolerance=_authored_float(experiment["convergence_tolerance"], "convergence_tolerance"),
        stability_starting_points=_authored_tuple(experiment["stability_starting_points"], "stability_starting_points"),
        stability_step_sizes=_authored_tuple(experiment["stability_step_sizes"], "stability_step_sizes"),
        benchmark_dimensions=tuple(dimensions),
    )
    if _exact_config_data(config) != _exact_config_data(expected):
        raise ValueError("Code typed loader DATA differs from the complete independently held authored experiment")


@dataclass(frozen=True)
class _ScalarResult:
    alpha: float
    solution: float
    objective: float
    iterations: int
    converged: bool
    gradient_norm: float
    termination: str

    def fields(self) -> tuple[str, ...]:
        return (
            str(float(self.alpha)),
            f"{self.solution:.6f}",
            f"{self.objective:.6f}",
            str(self.iterations),
            str(self.converged),
            f"{self.gradient_norm:.2e}",
            self.termination,
        )


def _objective(config: ScalarQuadraticConfig, x: float) -> float:
    # Keep the authored scalar binary64 product order, with no optimizer call.
    # The identity follows directly from 1/2*x^T*A*x - b^T*x, dimension one.
    return ((0.5 * x) * config.coefficient) * x - config.linear * x


def _result(config: ScalarQuadraticConfig, alpha: float, deadline: float | None) -> _ScalarResult:
    x = float(config.initial_point)
    value = _objective(config, x)
    if not math.isfinite(value):
        raise ValueError("Code scalar initial objective is non-finite")
    iterations = 0
    converged = False
    termination = "max_iterations"
    while iterations < config.max_iterations:
        _clock(deadline)
        gradient = config.coefficient * x - config.linear
        if not math.isfinite(gradient):
            termination = "non_finite"
            break
        if abs(gradient) < config.tolerance:
            converged, termination = True, "converged"
            break
        candidate = x - alpha * gradient
        if not math.isfinite(candidate):
            termination = "non_finite"
            break
        candidate_value = _objective(config, candidate)
        if not math.isfinite(candidate_value):
            termination = "non_finite"
            break
        x, value = candidate, candidate_value
        iterations += 1
    gradient = config.coefficient * x - config.linear
    gradient_norm = abs(gradient) if math.isfinite(gradient) else math.inf
    if math.isfinite(gradient) and not math.isfinite(gradient_norm):
        gradient_norm = sys.float_info.max
    _clock(deadline)
    return _ScalarResult(alpha, x, value, iterations, converged, gradient_norm, termination)


def _rows(config: ScalarQuadraticConfig, deadline: float | None) -> tuple[_ScalarResult, ...]:
    if not isinstance(config, ScalarQuadraticConfig):
        raise ValueError("Code scalar predicate requires its normalized bounded config DATA")
    _clock(deadline)
    return tuple(_result(config, float(alpha), deadline) for alpha in config.step_sizes)


def validate_scalar_csv(
    config: ScalarQuadraticConfig, actual_csv: bytes, *, deadline: float | None = None
) -> tuple[tuple[str, ...], ...]:
    """Require every row/field/order/sign/precision from independent recurrence.

    This predicate does not infer a process, accepted run, unit conversion or
    source identity from CSV data. Extra rows, duplicate headers/conditions,
    unit strings, noncanonical booleans, non-finite states and late alterations
    all fail exact comparison with the fixed Source serialization contract.
    """
    _clock(deadline)
    if not isinstance(actual_csv, bytes) or not 0 < len(actual_csv) <= MAX_CSV_BYTES:
        raise ValueError("Code scalar CSV requires a nonempty bounded complete byte body")
    rows = tuple(row.fields() for row in _rows(config, deadline))
    expected = (CSV_HEADER + "".join(",".join(row) + "\n" for row in rows)).encode("utf-8")
    if actual_csv != expected:
        raise ValueError("Code scalar CSV differs from the entire independent configured recurrence")
    _clock(deadline)
    return rows


def _scientific(value: float) -> str:
    if value == 0:
        return "0"
    exponent = math.floor(math.log10(abs(value)))
    coefficient = value / 10**exponent
    if abs(coefficient - 1.0) < 1e-9:
        return f"10^{{{exponent}}}"
    return f"{coefficient:.1f} \\times 10^{{{exponent}}}"


def _agency(alpha: float) -> str:
    if alpha < 0.3:
        return "conservative"
    if alpha <= 1:
        return "near-optimal"
    if alpha < 2:
        return "aggressive"
    return "divergent (expected unstable for H = I)"


def _expected_variables(
    config: ScalarQuadraticConfig, rows: tuple[tuple[str, ...], ...], deadline: float | None
) -> dict[str, str]:
    steps = list(config.step_sizes)
    starts, stability_steps, dimensions = (
        config.stability_starting_points,
        config.stability_step_sizes,
        config.benchmark_dimensions,
    )
    values = {
        "CONFIG_NUM_STEP_SIZES": str(len(steps)),
        "CONFIG_STEP_SIZES_CSV": ", ".join(str(float(alpha)) for alpha in steps),
        "CONFIG_MIN_STEP_SIZE": str(float(min(steps))),
        "CONFIG_MAX_STEP_SIZE": str(float(max(steps))),
        "CONFIG_STEP_SIZES_BULLETS": "\n".join(f"- $\\alpha = {float(s)}$ ({_agency(float(s))})" for s in steps),
        "CONFIG_INITIAL_POINT": str(float(config.initial_point)),
        "CONFIG_MAX_ITERATIONS": str(config.max_iterations),
        "CONFIG_TOLERANCE": _scientific(config.tolerance),
        "CONFIG_CONVERGENCE_TOL": _scientific(config.convergence_tolerance),
        "CONFIG_QUADRATIC_A": str([(float(config.coefficient),)]),
        "CONFIG_QUADRATIC_B": str([float(config.linear)]),
        "CONFIG_NUM_STABILITY_STARTS": str(len(starts)),
        "CONFIG_NUM_STABILITY_STEPS": str(len(stability_steps)),
        "CONFIG_STABILITY_CELLS": str(len(starts) * len(stability_steps)),
        "CONFIG_STABILITY_MIN_STEP": str(float(min(stability_steps))),
        "CONFIG_STABILITY_MAX_STEP": str(float(max(stability_steps))),
        "CONFIG_BENCHMARK_DIMS": ", ".join(str(d) for d in dimensions),
        "CONFIG_BENCHMARK_MIN_DIM": str(min(dimensions)),
        "CONFIG_BENCHMARK_MAX_DIM": str(max(dimensions)),
    }
    optimum = config.linear / config.coefficient
    optimum_value = _objective(config, optimum)
    if not math.isfinite(optimum) or not math.isfinite(optimum_value):
        raise ValueError("Code scalar closed-form optimum is non-finite")
    iterations = [int(row[3]) for row in rows]
    converged = [row[4] == "True" for row in rows]
    values.update(
        {
            "RESULT_OPTIMUM_X": f"{optimum:.1f}",
            "RESULT_OPTIMUM_F": f"{optimum_value:.1f}",
            "RESULT_MIN_ITERATIONS": str(min(iterations)),
            "RESULT_MAX_ITERATIONS": str(max(iterations)),
            "RESULT_AVG_ITERATIONS": f"{sum(iterations) / len(iterations):.0f}",
            "RESULT_ALL_CONVERGED": "Yes" if all(converged) else "No",
            "RESULT_NUM_CONVERGED": str(sum(converged)),
            "RESULT_CONVERGED_STEP_SIZES": ", ".join(row[0] for row in rows if row[4] == "True"),
            "RESULT_DIVERGED_STEP_SIZES": ", ".join(row[0] for row in rows if row[4] != "True"),
            "RESULT_BEST_STEP_SIZE": rows[iterations.index(min(iterations))][0],
            "RESULT_WORST_STEP_SIZE": rows[iterations.index(max(iterations))][0],
        }
    )
    table, factors = [], []
    for row in rows:
        _clock(deadline)
        alpha = float(row[0])
        # Independently derive the declared compact display from the signed CSV.
        solution_value, objective_value = float(row[1]), float(row[2])
        solution = format(solution_value, ".4e" if abs(solution_value) >= 1e6 else ".4f")
        objective = format(objective_value, ".4e" if abs(objective_value) >= 1e6 else ".4f")
        table.append(
            f"| {alpha:.2f}          | {solution:<16} | {objective}          "
            f"| {int(row[3]):<10} | {'Yes' if row[4] == 'True' else 'No':<9} | {row[6]:<16} |"
        )
        rho = abs(1 - alpha * config.coefficient)
        if 0 < rho < 1:
            updates = math.ceil(math.log(1e-6) / math.log(rho))
            status = f"requiring ~{updates} iterations for $\\epsilon = 10^{{-6}}$"
        elif rho >= 1:
            status = "**divergent**"
        else:
            status = "converges in one step ($\\rho = 0$)"
        factors.append(f"- $\\alpha = {alpha}$: $\\rho \\approx {rho:.2f}$, {status}")
    values["RESULT_TABLE_ROWS"] = "\n".join(table)
    values["RESULT_CONVERGENCE_FACTORS"] = "\n".join(factors)
    return values


def validate_scalar_values(
    config: ScalarQuadraticConfig,
    verified_csv: bytes,
    variables: Mapping[str, str],
    *,
    deadline: float | None = None,
) -> tuple[tuple[tuple[str, ...], ...], dict[str, str]]:
    """Require complete recognized config/result tokens against independent math.

    Unrecognized variables remain explicit unqualified axes in the enclosing
    graph. Config stability/benchmark grid labels are checked as declarations;
    their generated scientific reports are not qualified by these labels.
    """
    rows = validate_scalar_csv(config, verified_csv, deadline=deadline)
    if (
        not isinstance(variables, Mapping)
        or len(variables) > 1000
        or any(not isinstance(k, str) or not isinstance(v, str) for k, v in variables.items())
        or sum(len(k.encode()) + len(v.encode()) for k, v in variables.items()) > MAX_VARIABLE_BYTES
    ):
        raise ValueError("Code scalar variables require the bounded actual flat string-valued map")
    expected = _expected_variables(config, rows, deadline)
    for name, value in expected.items():
        _clock(deadline)
        if variables.get(name) != value:
            raise ValueError(f"Code scalar variable {name} differs from its independent config/result meaning")
    _clock(deadline)
    return rows, expected


def validate_scalar_variables(
    config: ScalarQuadraticConfig,
    verified_csv: bytes,
    variables: Mapping[str, str],
    *,
    deadline: float | None = None,
) -> tuple[str, ...]:
    """Preserve the existing API; share its one complete recurrence/formatter."""
    return tuple(validate_scalar_values(config, verified_csv, variables, deadline=deadline)[1])
