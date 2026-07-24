"""Stability, benchmarking, validation, and figure registration."""

from __future__ import annotations

import functools
import json
import time as _time
from pathlib import Path
from typing import Any

import numpy as np

try:
    from ..experiment_config import ExperimentConfig, load_experiment_config
    from ..optimizer import compute_gradient, gradient_descent, quadratic_function, quadratic_optimum
except ImportError:  # pragma: no cover
    from experiment_config import ExperimentConfig, load_experiment_config  # type: ignore[no-redef]
    from optimizer import compute_gradient, gradient_descent, quadratic_function, quadratic_optimum  # type: ignore[no-redef]

from ._infra import ValidationError, infrastructure_available
from ._logging import get_logger
from .experiments import _project_root


BENCHMARK_TIMING_POLICY = (
    "Wall-clock timing and memory measurements are environment-dependent runtime "
    "diagnostics and are intentionally omitted from this tracked artifact."
)


def _root() -> Path:
    return _project_root()


def _stability_score_from_runs(
    test_inputs: list[np.ndarray],
    A: np.ndarray,
    b: np.ndarray,
    step_size: float = 0.1,
) -> tuple[float, float, list[str]]:
    _, optimal_value = quadratic_optimum(A, b)
    errors = []
    for x0 in test_inputs:
        result = gradient_descent(
            initial_point=x0,
            objective_func=lambda x: quadratic_function(x, A, b),
            gradient_func=lambda x: compute_gradient(x, A, b),
            step_size=step_size,
            max_iterations=500,
            tolerance=1e-12,
        )
        errors.append(abs(result.objective_value - optimal_value))
    max_error = max(errors)
    score = 1.0 if max_error < 1e-6 else max(0.0, 1.0 - np.log10(max_error + 1e-16) / 16)
    recommendations = [] if max_error < 1e-6 else ["Consider adaptive step size"]
    return float(score), max_error, recommendations


def _benchmark_timings(
    test_inputs: list[np.ndarray],
    A: np.ndarray,
    b: np.ndarray,
    iterations: int = 50,
) -> float:
    timings = []
    for x0 in test_inputs:
        elapsed = []
        for _ in range(iterations):
            t0 = _time.perf_counter()
            gradient_descent(
                initial_point=x0,
                objective_func=lambda x: quadratic_function(x, A, b),
                gradient_func=lambda x: compute_gradient(x, A, b),
                step_size=0.1,
                max_iterations=500,
                tolerance=1e-12,
            )
            elapsed.append(_time.perf_counter() - t0)
        timings.append(np.mean(elapsed))
    return float(np.mean(timings))


def _canonical_benchmark_payload(
    test_inputs: list[np.ndarray],
    A: np.ndarray,
    b: np.ndarray,
    *,
    diagnostic_iterations: int,
) -> dict[str, Any]:
    """Build byte-stable benchmark facts without host-dependent measurements."""
    objective_values = [float(quadratic_function(test_input, A, b)) for test_input in test_inputs]
    observations = [
        {
            "input": [float(value) for value in test_input],
            "objective_value": objective_value,
        }
        for test_input, objective_value in zip(test_inputs, objective_values, strict=True)
    ]
    return {
        "schema_version": "template_code_project/performance_benchmark/v2",
        "function_name": "quadratic_function",
        "diagnostic_iterations_per_input": diagnostic_iterations,
        "input_count": len(test_inputs),
        "observations": observations,
        "checks": {
            "all_inputs_evaluated": len(observations) == len(test_inputs),
            "all_objective_values_finite": all(np.isfinite(objective_value) for objective_value in objective_values),
        },
        "timing_policy": BENCHMARK_TIMING_POLICY,
        "result_summary": (
            f"{len(observations)} deterministic objective evaluations; runtime timing omitted from tracked artifact"
        ),
    }


def run_stability_analysis(config: ExperimentConfig | None = None) -> Path:
    """Assess numerical stability of optimization algorithms."""
    from . import check_numerical_stability

    logger = get_logger()
    logger.info("Running numerical stability analysis...")

    cfg = config or load_experiment_config(_root())
    A = cfg.A_array()
    b = cfg.b_array()
    _, optimal_value = quadratic_optimum(A, b)
    test_inputs = [np.array([float(x)]) for x in cfg.stability_starting_points[:4]]

    if infrastructure_available() and check_numerical_stability is not None:
        stability_report = check_numerical_stability(
            func=functools.partial(quadratic_function, A=A, b=b),
            test_inputs=test_inputs,
            tolerance=1e-10,
        )
        stability_data = {
            "function_name": stability_report.function_name,
            "stability_score": stability_report.stability_score,
            "expected_behavior": stability_report.expected_behavior,
            "actual_behavior": stability_report.actual_behavior,
            "recommendations": stability_report.recommendations,
        }
    else:
        score, max_error, recommendations = _stability_score_from_runs(test_inputs, A, b)
        stability_data = {
            "function_name": "quadratic_function",
            "stability_score": score,
            "expected_behavior": f"Converge to f(x*)={optimal_value:.4g} for all starting points",
            "actual_behavior": f"Max error: {max_error:.2e} across {len(test_inputs)} inputs",
            "recommendations": recommendations,
        }

    output_dir = _root() / "output" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    stability_path = output_dir / "stability_analysis.json"
    with open(stability_path, "w") as f:
        json.dump(stability_data, f, indent=2)

    logger.info("Stability analysis complete - Score: %.2f", stability_data["stability_score"])
    logger.info("Saved stability report to: %s", stability_path)
    return stability_path


def run_performance_benchmarking(config: ExperimentConfig | None = None) -> Path:
    """Run timing diagnostics and write a deterministic benchmark contract."""
    from . import benchmark_function

    logger = get_logger()
    logger.info("Running performance benchmarking...")

    cfg = config or load_experiment_config(_root())
    A = cfg.A_array()
    b = cfg.b_array()
    test_inputs = [np.array([0.0]), np.array([5.0]), np.array([20.0])]
    diagnostic_iterations = 50

    if infrastructure_available() and benchmark_function is not None:
        benchmark_report = benchmark_function(
            func=functools.partial(quadratic_function, A=A, b=b),
            test_inputs=test_inputs,
            iterations=diagnostic_iterations,
        )
        avg_time = benchmark_report.execution_time
    else:
        avg_time = _benchmark_timings(test_inputs, A, b, iterations=diagnostic_iterations)

    benchmark_data = _canonical_benchmark_payload(
        test_inputs,
        A,
        b,
        diagnostic_iterations=diagnostic_iterations,
    )

    output_dir = _root() / "output" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    benchmark_path = output_dir / "performance_benchmark.json"
    benchmark_path.write_text(
        json.dumps(benchmark_data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    logger.info("Runtime-only benchmark diagnostic complete - Avg time: %.6fs", avg_time)
    logger.info("Saved benchmark report to: %s", benchmark_path)
    return benchmark_path


def validate_generated_outputs(*, integrity_validator: Any = None) -> Any:
    """Validate integrity of generated analysis outputs."""
    from . import verify_output_integrity

    logger = get_logger()
    validate_integrity = integrity_validator or verify_output_integrity
    if not infrastructure_available() or validate_integrity is None:
        logger.info("Skipping output validation (infrastructure not available)")
        return None

    logger.info("Validating generated outputs...")
    try:
        integrity_report = validate_integrity(_root() / "output")
        validation_summary = {
            "integrity_check": {
                "total_files": len(integrity_report.file_integrity),
                "integrity_passed": sum(integrity_report.file_integrity.values()),
                "issues_found": len(integrity_report.issues),
                "warnings": len(integrity_report.warnings),
                "recommendations": len(integrity_report.recommendations),
            }
        }
        if integrity_report.issues:
            logger.warning("Found %d integrity issues", len(integrity_report.issues))
            for issue in integrity_report.issues[:3]:
                logger.warning("   • %s", issue)
        else:
            logger.info("Output integrity validation passed")
        return validation_summary
    except ValidationError as e:
        logger.warning("Output validation failed: %s", e)
        return None
    except (OSError, ValueError, TypeError) as e:
        logger.warning("Unexpected error during output validation: %s", e)
        return None


def save_validation_report(validation_report: Any, *, file_opener: Any = open) -> Any:
    """Save validation report to file."""
    logger = get_logger()
    if not validation_report:
        return None
    try:
        output_dir = _root() / "output" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "output_validation.json"
        with file_opener(report_path, "w") as f:
            json.dump(validation_report, f, indent=2, default=str)
        logger.info("Saved validation report to: %s", report_path)
        return report_path
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning("Failed to save validation report: %s", e)
        return None


def register_figure(*, figure_manager_factory: Any = None) -> None:
    """Register generated figures for manuscript reference."""
    logger = get_logger()
    try:
        from ._infra import FigureManager

        manager_factory = figure_manager_factory or FigureManager
        if manager_factory is None:
            raise ImportError("FigureManager unavailable")
        registry_file = _root() / "output" / "figures" / "figure_registry.json"
        fm = manager_factory(registry_file=str(registry_file))
        figures = [
            (
                "convergence_plot.png",
                "Gradient descent convergence for different step sizes",
                "fig:convergence",
                "Objective value over iterations for each declared step size; lower curves indicate faster convergence.",
            ),
            (
                "step_size_sensitivity.png",
                "Step size sensitivity analysis showing iterations and solution quality",
                "fig:step_sensitivity",
                "Comparison of convergence iterations and final solution quality across the configured step-size grid.",
            ),
            (
                "convergence_rate_comparison.png",
                "Convergence rate comparison on logarithmic scale",
                "fig:convergence_rate",
                "Log-scale comparison of convergence error across step sizes, showing the stable and aggressive regimes.",
            ),
            (
                "algorithm_complexity.png",
                "Algorithm complexity visualization with performance metrics",
                "fig:complexity",
                "Deterministic proxy for optimization work by problem dimension and recorded iteration count.",
            ),
            (
                "stability_analysis.png",
                "Numerical stability analysis results and recommendations",
                "fig:stability",
                "Numerical stability score and recommendations produced by the configured stability checks.",
            ),
            (
                "performance_benchmark.png",
                "Performance benchmarking results and metrics",
                "fig:benchmark",
                "Deterministic objective-evaluation observations; host-dependent wall-clock timing is excluded from the claim.",
            ),
        ]
        for filename, caption, label, alt_text in figures:
            fm.register_figure(
                filename=filename,
                caption=caption,
                label=label,
                section="Results",
                generated_by="optimization_analysis.py",
                metadata={"alt_text": alt_text, "source": "template_code_project analysis pipeline"},
            )
            logger.info("Registered figure with label: %s", label)
    except ImportError as e:
        logger.warning("Figure manager not available: %s", e)
    except (OSError, ValueError, TypeError) as e:
        logger.warning("Failed to register figures: %s", e)


__all__ = [
    "BENCHMARK_TIMING_POLICY",
    "_benchmark_timings",
    "_canonical_benchmark_payload",
    "_stability_score_from_runs",
    "register_figure",
    "run_performance_benchmarking",
    "run_stability_analysis",
    "save_validation_report",
    "validate_generated_outputs",
]
