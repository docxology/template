"""Full optimization analysis workflow (invoked by scripts/optimization_analysis.py)."""

from __future__ import annotations


def run_analysis_pipeline() -> None:
    """Execute the full optimization analysis workflow."""
    from . import (
        INFRASTRUCTURE_AVAILABLE,
        ProgressBar,
        ScriptExecutionError,
        SystemHealthChecker,
        TemplateError,
        _get_logger,
        extract_optimization_metadata,
        generate_citations_from_metadata,
        log_success,
        register_figure,
        run_convergence_experiment,
        run_performance_benchmarking,
        run_stability_analysis,
        save_optimization_results,
        save_publishing_materials,
        save_validation_report,
        validate_generated_outputs,
    )
    from .experiments import _project_root
    from ..experiment_config import load_experiment_config
    from ..figures import (
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
    exp_config = load_experiment_config(_project_root())

    def log_info(msg: str) -> None:
        logger.info(msg)

    def log_warning(msg: str) -> None:
        logger.warning(msg)

    if INFRASTRUCTURE_AVAILABLE:
        log_success("Starting optimization analysis pipeline", logger=logger)
    log_info(f"Project root: {_project_root()}")

    try:
        if INFRASTRUCTURE_AVAILABLE and SystemHealthChecker is not None:
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

        log_info("Running convergence experiments...")
        if INFRASTRUCTURE_AVAILABLE and ProgressBar is not None:
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

        log_info("Running scientific analysis...")
        stability_path = run_stability_analysis(config=exp_config)
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
            log_success("Optimization analysis pipeline completed successfully", logger=logger)
        else:
            log_info("Optimization analysis pipeline completed successfully")

    except ImportError as e:
        logger.error("Import error: %s", e, exc_info=True)
        raise

    except FileNotFoundError as e:
        logger.error("File not found: %s", e, exc_info=True)
        raise

    except Exception as e:  # noqa: BLE001
        if INFRASTRUCTURE_AVAILABLE:
            if isinstance(e, ScriptExecutionError):
                logger.error("Script execution failed: %s", e, exc_info=True)
                if hasattr(e, "recovery_commands") and e.recovery_commands:
                    for cmd in e.recovery_commands:
                        logger.error("  %s", cmd)
                raise
            if isinstance(e, TemplateError):
                logger.error("Infrastructure error: %s", e, exc_info=True)
                if hasattr(e, "suggestions") and e.suggestions:
                    for suggestion in e.suggestions:
                        logger.error("  • %s", suggestion)
                raise
        logger.error("Unexpected error during optimization analysis: %s", e, exc_info=True)
        raise


def main() -> None:
    """Run the full optimization analysis pipeline."""
    run_analysis_pipeline()


__all__ = ["main", "run_analysis_pipeline"]
