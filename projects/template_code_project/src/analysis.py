"""Optimization analysis implementation for the code-project exemplar.

The public functions in this module contain the project-specific experiment,
figure, dashboard, and publishing-material behavior. The corresponding script
(``scripts/optimization_analysis.py``) is intentionally just a command-line
wrapper so the reusable logic remains importable and directly testable.
"""
# ruff: noqa: E402

import functools
import json
import logging
import sys
import time as _time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

try:
    from .experiment_config import ExperimentConfig, load_experiment_config
    from .optimizer import (
        OptimizationResult,
        compute_gradient,
        gradient_descent,
        make_quadratic_problem,
        quadratic_function,
        quadratic_optimum,
    )
except ImportError:  # pragma: no cover - supports direct module execution
    from experiment_config import ExperimentConfig, load_experiment_config  # type: ignore[no-redef]
    from optimizer import (  # type: ignore[no-redef]
        OptimizationResult,
        compute_gradient,
        gradient_descent,
        make_quadratic_problem,
        quadratic_function,
        quadratic_optimum,
    )


# -------------------------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------------------------
def _setup_fallback_logging() -> logging.Logger:
    """Configure stdlib logging for standalone (no-infrastructure) runs."""
    logger = logging.getLogger("template_code_project.optimization_analysis")
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


# Infrastructure imports (optional — PYTHONPATH must include repo root)
try:
    from infrastructure.core import ProgressBar, SystemHealthChecker, get_logger, log_success
    from infrastructure.core.exceptions import ScriptExecutionError, TemplateError, ValidationError
    from infrastructure.publishing import generate_citation_apa, generate_citation_bibtex, generate_citation_mla
    from infrastructure.publishing.models import PublicationMetadata
    from infrastructure.scientific import benchmark_function, check_numerical_stability
    from infrastructure.validation import verify_output_integrity

    INFRASTRUCTURE_AVAILABLE = True
except ImportError as e:
    _fallback_logger = _setup_fallback_logging()
    _fallback_logger.warning(f"Infrastructure modules not available: {e}")
    INFRASTRUCTURE_AVAILABLE = False


def _get_logger() -> logging.Logger:
    """Return infrastructure logger if available, otherwise a configured stdlib logger."""
    if INFRASTRUCTURE_AVAILABLE:
        return get_logger(__name__)
    return _setup_fallback_logging()


# Project root: projects/template_code_project/
project_root = Path(__file__).resolve().parent.parent


def run_convergence_experiment(
    *,
    on_step: Callable[[float, OptimizationResult], None] | None = None,
    config: ExperimentConfig | None = None,
) -> dict[float, OptimizationResult]:
    """Run gradient descent with different step sizes and track convergence."""
    logger = _get_logger()
    logger.info("Running convergence experiments...")

    cfg = config or load_experiment_config(project_root)
    A = cfg.A_array()
    b = cfg.b_array()
    obj_func, grad_func = make_quadratic_problem(A, b)
    initial_point = cfg.x0()

    results: dict[float, OptimizationResult] = {}

    for step_size in cfg.step_sizes:
        logger.info(f"Testing step size: {step_size}")

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
        logger.info(f"  Converged: {result.converged}, Final value: {result.objective_value:.4f}")

        if on_step is not None:
            on_step(float(step_size), result)

    return results


def save_optimization_results(results: dict[float, OptimizationResult]) -> Path:
    """Save optimization results to CSV file."""
    logger = _get_logger()
    logger.info("Saving optimization results...")

    output_dir = project_root / "output" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    data_path = output_dir / "optimization_results.csv"

    with open(data_path, "w") as f:
        f.write("step_size,solution,objective_value,iterations,converged,gradient_norm\n")

        for step_size, result in results.items():
            solution_str = ";".join(f"{v:.6f}" for v in result.solution)
            f.write(
                f"{step_size},{solution_str},{result.objective_value:.6f},"
                f"{result.iterations},{result.converged},{result.gradient_norm:.2e}\n"
            )

    logger.info(f"Saved results to: {data_path}")
    return data_path


def _stability_score_from_runs(
    test_inputs: list[np.ndarray],
    A: np.ndarray,
    b: np.ndarray,
    step_size: float = 0.1,
) -> tuple[float, float, list[str]]:
    """Compute stability score from gradient-descent runs at known optimum."""
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
    """Time gradient_descent calls across inputs; return mean seconds."""
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


def run_stability_analysis(config: ExperimentConfig | None = None) -> Path:
    """Assess numerical stability of optimization algorithms."""
    logger = _get_logger()
    log = logger.info
    log("Running numerical stability analysis...")

    cfg = config or load_experiment_config(project_root)
    A = cfg.A_array()
    b = cfg.b_array()
    _, optimal_value = quadratic_optimum(A, b)

    test_inputs = [np.array([float(x)]) for x in cfg.stability_starting_points[:4]]

    if INFRASTRUCTURE_AVAILABLE:
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

    # Save stability report
    output_dir = project_root / "output" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    stability_path = output_dir / "stability_analysis.json"
    with open(stability_path, "w") as f:
        json.dump(stability_data, f, indent=2)

    log(f"Stability analysis complete - Score: {stability_data['stability_score']:.2f}")
    log(f"Saved stability report to: {stability_path}")

    return stability_path


def run_performance_benchmarking(config: ExperimentConfig | None = None) -> Path:
    """Benchmark gradient descent performance."""
    logger = _get_logger()
    log = logger.info
    log("Running performance benchmarking...")

    cfg = config or load_experiment_config(project_root)
    A = cfg.A_array()
    b = cfg.b_array()

    test_inputs = [
        np.array([0.0]),
        np.array([5.0]),
        np.array([20.0]),
    ]

    if INFRASTRUCTURE_AVAILABLE:
        benchmark_report = benchmark_function(
            func=functools.partial(quadratic_function, A=A, b=b),
            test_inputs=test_inputs,
            iterations=50,
        )
        benchmark_data = {
            "function_name": benchmark_report.function_name,
            "execution_time": benchmark_report.execution_time,
            "memory_usage": benchmark_report.memory_usage,
            "iterations": benchmark_report.iterations,
            "result_summary": benchmark_report.result_summary,
            "timestamp": benchmark_report.timestamp,
        }
        avg_time = benchmark_report.execution_time
    else:
        avg_time = _benchmark_timings(test_inputs, A, b)
        benchmark_data = {
            "function_name": "quadratic_function",
            "execution_time": avg_time,
            "memory_usage": 0.0,
            "iterations": 50,
            "result_summary": f"Avg {avg_time * 1e6:.1f}μs across {len(test_inputs)} inputs",
            "timestamp": _time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

    # Save benchmark report
    output_dir = project_root / "output" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    benchmark_path = output_dir / "performance_benchmark.json"
    with open(benchmark_path, "w") as f:
        json.dump(benchmark_data, f, indent=2, default=str)

    log(f"Performance benchmarking complete - Avg time: {avg_time:.6f}s")
    log(f"Saved benchmark report to: {benchmark_path}")

    return benchmark_path


def validate_generated_outputs() -> Any:
    """Validate integrity of generated analysis outputs."""
    logger = _get_logger()
    if not INFRASTRUCTURE_AVAILABLE:
        logger.info("Skipping output validation (infrastructure not available)")
        return None

    logger.info("Validating generated outputs...")

    try:
        output_dir = project_root / "output"

        # Run integrity validation
        integrity_report = verify_output_integrity(output_dir)

        # Generate validation summary
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
            if logger:
                logger.warning(f"Found {len(integrity_report.issues)} integrity issues")
                for issue in integrity_report.issues[:3]:  # Show first 3
                    logger.warning(f"   • {issue}")
        else:
            if logger:
                logger.info("Output integrity validation passed")

        return validation_summary

    except ValidationError as e:
        logger.warning(f"Output validation failed: {e}")
        return None
    except (OSError, ValueError, TypeError) as e:
        logger.warning(f"Unexpected error during output validation: {e}")
        return None


def save_validation_report(validation_report: Any) -> Any:
    """Save validation report to file."""
    logger = _get_logger()

    if not validation_report:
        return None

    try:
        output_dir = project_root / "output" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        report_path = output_dir / "output_validation.json"

        with open(report_path, "w") as f:
            json.dump(validation_report, f, indent=2, default=str)

        logger.info(f"Saved validation report to: {report_path}")
        return report_path

    except (OSError, json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning(f"Failed to save validation report: {e}")
        return None


def register_figure() -> None:
    """Register the generated figures for manuscript reference."""
    logger = _get_logger()

    try:
        # Ensure repo root is on path for infrastructure imports
        repo_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(repo_root))

        from infrastructure.documentation.figure_manager import FigureManager

        # Use project-specific registry path
        registry_file = project_root / "output" / "figures" / "figure_registry.json"
        fm = FigureManager(registry_file=str(registry_file))

        # Register all figures
        figures = [
            (
                "convergence_plot.png",
                "Gradient descent convergence for different step sizes",
                "fig:convergence",
            ),
            (
                "step_size_sensitivity.png",
                "Step size sensitivity analysis showing iterations and solution quality",
                "fig:step_sensitivity",
            ),
            (
                "convergence_rate_comparison.png",
                "Convergence rate comparison on logarithmic scale",
                "fig:convergence_rate",
            ),
            (
                "algorithm_complexity.png",
                "Algorithm complexity visualization with performance metrics",
                "fig:complexity",
            ),
        ]

        # Add scientific analysis figures (always generated)
        figures.extend(
            [
                (
                    "stability_analysis.png",
                    "Numerical stability analysis results and recommendations",
                    "fig:stability",
                ),
                (
                    "performance_benchmark.png",
                    "Performance benchmarking results and metrics",
                    "fig:benchmark",
                ),
            ]
        )

        for filename, caption, label in figures:
            fm.register_figure(
                filename=filename,
                caption=caption,
                label=label,
                section="Results",
                generated_by="optimization_analysis.py",
            )
            logger.info(f"Registered figure with label: {label}")

    except ImportError as e:
        logger.warning(f"Figure manager not available: {e}")
    except (OSError, ValueError, TypeError) as e:
        logger.warning(f"Failed to register figures: {e}")


def main() -> None:
    """Main analysis function."""
    try:
        from .figures import (
            apply_visualization_style,
            generate_benchmark_visualization,
            generate_complexity_visualization,
            generate_convergence_plot,
            generate_convergence_rate_plot,
            generate_stability_visualization,
            generate_step_size_sensitivity_plot,
        )
    except ImportError:  # pragma: no cover
        from figures import (  # type: ignore[no-redef]
            apply_visualization_style,
            generate_benchmark_visualization,
            generate_complexity_visualization,
            generate_convergence_plot,
            generate_convergence_rate_plot,
            generate_stability_visualization,
            generate_step_size_sensitivity_plot,
        )

    apply_visualization_style()
    logger = _get_logger()
    exp_config = load_experiment_config(project_root)

    def log_info(msg: str) -> None:
        logger.info(msg)

    def log_warning(msg: str) -> None:
        logger.warning(msg)

    if INFRASTRUCTURE_AVAILABLE:
        log_success("Starting optimization analysis pipeline", logger=logger)
    log_info(f"Project root: {project_root}")

    try:
        if INFRASTRUCTURE_AVAILABLE:
            health_checker = SystemHealthChecker()
            log_info("Running system health check...")
            health_status = health_checker.get_health_status()
            if health_status.get("overall_status") != "healthy":
                log_warning("System health check failed:")
                for check_name, check_result in health_status.get("checks", {}).items():
                    if check_result.get("status") != "healthy":
                        log_warning(f"  - {check_name}: {check_result.get('error', 'unknown error')}")
            else:
                log_info("System health check passed")

        if INFRASTRUCTURE_AVAILABLE:
            log_info("Performance monitoring available")
        else:
            log_info("Running without performance monitoring")

        log_info("Running convergence experiments...")
        if INFRASTRUCTURE_AVAILABLE:
            progress = ProgressBar(total=len(exp_config.step_sizes), task="Step sizes")
            results = run_convergence_experiment(
                on_step=lambda _alpha, _result: progress.update(1),
                config=exp_config,
            )
            progress.finish()
        else:
            results = run_convergence_experiment(config=exp_config)

        log_info("Generating traditional analysis outputs...")
        convergence_plot = generate_convergence_plot(results, config=exp_config)
        sensitivity_plot = generate_step_size_sensitivity_plot(results, config=exp_config)
        rate_plot = generate_convergence_rate_plot(results, config=exp_config)
        complexity_plot = generate_complexity_visualization(results, config=exp_config)
        data_path = save_optimization_results(results)

        stability_plot = None
        benchmark_plot = None

        log_info("Running scientific analysis...")
        log_info("Numerical stability analysis...")
        stability_path = run_stability_analysis(config=exp_config)

        log_info("Performance benchmarking...")
        benchmark_path = run_performance_benchmarking(config=exp_config)

        log_info("Generating scientific visualizations...")
        stability_plot = generate_stability_visualization(stability_path)
        benchmark_plot = generate_benchmark_visualization(benchmark_path)

        register_figure()

        validation_report_path = None
        log_info("Validating generated outputs...")
        if INFRASTRUCTURE_AVAILABLE:
            validation_report = validate_generated_outputs()
            if validation_report:
                validation_report_path = save_validation_report(validation_report)

        log_info("Generating publishing materials...")
        publishing_metadata = extract_optimization_metadata(results)
        if publishing_metadata and INFRASTRUCTURE_AVAILABLE:
            citations = generate_citations_from_metadata(publishing_metadata)
            save_publishing_materials(publishing_metadata, citations)
        elif publishing_metadata:
            log_info("Skipping citation generation (infrastructure not available)")

        if INFRASTRUCTURE_AVAILABLE:
            log_info("Publishing integration demonstration...")
            try:
                if publishing_metadata:
                    log_info("Publishing interfaces available: Zenodo, arXiv, GitHub releases")
                    log_info("Publication metadata extracted and formatted")
            except (OSError, ImportError, ValueError) as e:
                log_warning(f"Publishing demonstration failed: {e}")

        if INFRASTRUCTURE_AVAILABLE:
            log_info("Pipeline completed with infrastructure support")

        log_info(f"Generated convergence plot: {convergence_plot}")
        log_info(f"Generated sensitivity plot: {sensitivity_plot}")
        log_info(f"Generated rate comparison plot: {rate_plot}")
        log_info(f"Generated complexity visualization: {complexity_plot}")
        log_info(f"Generated data: {data_path}")

        if INFRASTRUCTURE_AVAILABLE:
            log_info(f"Generated stability report: {stability_path}")
            log_info(f"Generated benchmark report: {benchmark_path}")
            log_info(f"Generated stability visualization: {stability_plot}")
            log_info(f"Generated benchmark visualization: {benchmark_plot}")
            log_info(f"Generated validation report: {validation_report_path}")
            log_info("Generated publishing materials and citations")

        if INFRASTRUCTURE_AVAILABLE:
            log_success("Optimization analysis pipeline completed successfully", logger=logger)
        else:
            log_info("Optimization analysis pipeline completed successfully")

    except ImportError as e:
        logger.error(f"Import error: {e}", exc_info=True)
        logger.error("Suggestions:")
        logger.error("  - Run from repo root so infrastructure is importable")
        logger.error("  - Ensure dependencies are installed (use `uv sync`)")
        raise

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}", exc_info=True)
        logger.error("Suggestions:")
        logger.error("  - Ensure project structure is correct")
        logger.error("  - Ensure analysis outputs directory is writable")
        raise

    except Exception as e:  # noqa: BLE001 - top-level main safety net — see below
        # TOP-LEVEL MAIN SAFETY NET. By design we catch the broad Exception here
        # because main() must produce actionable diagnostics for any failure
        # before re-raising. The isinstance dispatch below narrows to the
        # specific infrastructure exception types (ScriptExecutionError,
        # TemplateError) for tailored recovery hints; anything else still gets
        # the generic "unexpected error" path and re-raises. Narrowing the
        # except clause would force missing-type silence which is worse than
        # this annotated breadth.
        # Handle infrastructure-specific errors if available
        if INFRASTRUCTURE_AVAILABLE:
            if isinstance(e, ScriptExecutionError):
                # Handle script-specific errors with recovery suggestions
                if logger:
                    logger.error(f"Script execution failed: {e}", exc_info=True)
                    if hasattr(e, "recovery_commands") and e.recovery_commands:
                        logger.error("Suggested recovery commands:")
                        for cmd in e.recovery_commands:
                            logger.error(f"  {cmd}")
                raise

            if isinstance(e, TemplateError):
                # Handle infrastructure template errors
                if logger:
                    logger.error(f"Infrastructure error: {e}", exc_info=True)
                    if hasattr(e, "suggestions") and e.suggestions:
                        logger.error("Suggestions:")
                        for suggestion in e.suggestions:
                            logger.error(f"  • {suggestion}")
                raise

        # Handle unexpected errors with context
        error_msg = f"Unexpected error during optimization analysis: {e}"
        logger.error(error_msg, exc_info=True)
        logger.error("Suggestions:")
        logger.error("  - Check system requirements and dependencies")
        logger.error("  - Review error logs for detailed information")
        logger.error("  - Ensure sufficient disk space and memory")
        raise


def extract_optimization_metadata(
    results: dict[float, OptimizationResult],
) -> dict[str, Any] | None:
    """Extract publication metadata from optimization results.

    Args:
        results: Dictionary of step sizes to optimization results

    Returns:
        Dictionary with publication metadata, or None if extraction fails
    """
    try:
        # Extract key performance metrics
        best_step_size = min(results.keys(), key=lambda k: results[k].objective_value)
        best_result = results[best_step_size]

        # Extract objective history metrics; objective_history may be None when
        # gradient_descent is called without history recording.
        objective_history: list[float] = best_result.objective_history or []
        iterations_to_convergence = len(objective_history)
        convergence_rate = (
            abs(objective_history[-1] - objective_history[0]) / len(objective_history)
            if len(objective_history) >= 2
            else 0.0
        )

        # Create publication metadata
        metadata = {
            "title": "Optimization Algorithm Performance Analysis",
            "description": f"Comparative analysis of gradient descent optimization with step sizes {list(results.keys())}",
            "algorithm": "Gradient Descent",
            "objective_function": "Quadratic Function f(x) = x²",
            "step_sizes_tested": list(results.keys()),
            "best_step_size": best_step_size,
            "final_objective": best_result.objective_value,
            "iterations_to_convergence": iterations_to_convergence,
            "convergence_rate": convergence_rate,
            "analysis_type": "Numerical Optimization",
            "methodology": "Gradient descent with fixed step sizes",
        }

        return metadata

    except (KeyError, ValueError, TypeError, AttributeError) as e:
        if INFRASTRUCTURE_AVAILABLE:
            logger = get_logger(__name__)
            logger.warning(f"Failed to extract optimization metadata: {e}")
        return None


def generate_citations_from_metadata(
    metadata: dict[str, Any],
) -> dict[str, str] | None:
    """Generate citations from optimization metadata.

    Args:
        metadata: Publication metadata dictionary

    Returns:
        Dictionary with citation formats, or None if generation fails
    """
    try:
        # Create a PublicationMetadata object for citation generation
        pub_metadata = PublicationMetadata(
            title=metadata["title"],
            authors=["Optimization Analysis Pipeline"],  # List of strings, not dicts
            abstract=metadata.get("description", "Optimization algorithm performance analysis"),
            keywords=["optimization", "gradient descent", "numerical analysis"],
            publication_date="2026-01-01",  # Default date
            license="MIT",
        )

        # Generate citations in different formats
        citations = {}
        if INFRASTRUCTURE_AVAILABLE:
            citations["bibtex"] = generate_citation_bibtex(pub_metadata)
            citations["apa"] = generate_citation_apa(pub_metadata)
            citations["mla"] = generate_citation_mla(pub_metadata)

        return citations

    except (KeyError, ValueError, TypeError, ImportError, NameError) as e:
        if INFRASTRUCTURE_AVAILABLE:
            logger = get_logger(__name__)
            logger.warning(f"Failed to generate citations: {e}")
        return None


def save_publishing_materials(metadata: dict[str, Any], citations: dict[str, str] | None = None) -> None:
    """Save publishing materials to output directory.

    Args:
        metadata: Publication metadata
        citations: Optional citation formats
    """
    try:
        output_dir = project_root / "output" / "citations"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save metadata
        metadata_path = output_dir / "optimization_metadata.json"

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

        # Save citations if available
        if citations:
            for format_name, citation_text in citations.items():
                citation_path = output_dir / f"citation_{format_name}.txt"
                with open(citation_path, "w") as f:
                    f.write(citation_text)

        # Create publication summary
        summary_path = output_dir / "publication_summary.md"
        with open(summary_path, "w") as f:
            f.write("# Optimization Analysis Publication Summary\n\n")
            f.write(f"**Title:** {metadata['title']}\n\n")
            f.write(f"**Description:** {metadata['description']}\n\n")
            f.write(f"**Algorithm:** {metadata['algorithm']}\n\n")
            f.write(f"**Best Step Size:** {metadata['best_step_size']}\n\n")
            f.write(f"**Final Objective:** {metadata['final_objective']:.6f}\n\n")
            f.write(f"**Iterations:** {metadata['iterations_to_convergence']}\n\n")

            if citations:
                f.write("## Citations\n\n")
                for format_name, citation in citations.items():
                    f.write(f"### {format_name.upper()}\n\n")
                    f.write(f"{citation}\n\n")

        if INFRASTRUCTURE_AVAILABLE:
            logger = get_logger(__name__)
            logger.info(f"Publishing materials saved to: {output_dir}")

    except (OSError, json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
        if INFRASTRUCTURE_AVAILABLE:
            logger = get_logger(__name__)
            logger.warning(f"Failed to save publishing materials: {e}")


if __name__ == "__main__":
    main()
