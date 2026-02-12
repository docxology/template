#!/usr/bin/env python3
"""Automated scientific figure generation script.

This script orchestrates the complete workflow:
1. Run simulations
2. Perform analysis
3. Generate visualizations
4. Insert figures with captions automatically
5. Update cross-references

IMPORTANT: This script follows the thin orchestrator pattern - all business
logic is in src/ modules, this script only orchestrates the workflow.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np

# Ensure src/ and infrastructure/ are on path FIRST (before infrastructure imports)
project_root = Path(__file__).parent.parent
repo_root = project_root.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(repo_root))  # Add repo root so we can import infrastructure.*

from analysis.statistics import calculate_descriptive_stats

# Import src/ modules
from data.data_generator import generate_synthetic_data, generate_time_series
from analysis.performance import analyze_convergence
from visualization.plots import (plot_bar, plot_comparison, plot_convergence, plot_line,
                   plot_scatter)
from visualization.figure_manager import FigureManager
from pipeline.reporting import (generate_pipeline_report,
                              get_error_aggregator, save_pipeline_report)
from core.validation_utils import validate_figure_registry
from core.validation_utils import validate_markdown as validate_markdown_wrapper
from visualization.visualization import VisualizationEngine

# Infra logging uses local utilities
from core.logging import get_logger, log_progress_bar, log_substep

# Optional infrastructure imports - graceful fallback if not available
try:
    from infrastructure.core.performance import PerformanceMonitor
    from infrastructure.documentation.image_manager import ImageManager
    from infrastructure.documentation.markdown_integration import \
        MarkdownIntegration
    _INFRA_AVAILABLE = True
except ImportError:
    _INFRA_AVAILABLE = False

    class _StubMetrics:
        """Stub metrics for when infrastructure is not available."""
        duration = 0.0
        class resource_usage:
            @staticmethod
            def to_dict():
                return {}

    class PerformanceMonitor:
        """Stub PerformanceMonitor for when infrastructure is not available."""
        def start(self): pass
        def update_memory(self): pass
        def stop(self): return _StubMetrics()

logger = get_logger(__name__)


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments for stage selection and dry-run support."""
    parser = argparse.ArgumentParser(
        description="Generate scientific figures with optional stage control."
    )
    stage_names = [
        "convergence",
        "timeseries",
        "stats",
        "scatter",
        "insert",
        "validate",
    ]
    parser.add_argument(
        "--only",
        nargs="+",
        choices=stage_names,
        help="Run only the selected stages (preserves execution order).",
    )
    parser.add_argument(
        "--resume",
        choices=stage_names,
        help="Resume from the given stage (skips earlier stages).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show stages that would run without executing them.",
    )
    parser.add_argument(
        "--list-stages",
        action="store_true",
        help="List available stages and exit.",
    )
    return parser.parse_args(), stage_names


def generate_convergence_figure() -> str:
    """Generate convergence analysis figure.

    Returns:
        Figure label
    """
    logger.info("Generating convergence figure...")

    # Generate convergence data
    iterations = np.arange(1, 101)
    values = 10 * np.exp(-iterations / 20) + np.random.normal(0, 0.1, len(iterations))

    # Setup visualization
    engine = VisualizationEngine(output_dir="output/figures")
    fig, ax = engine.create_figure()

    # Plot convergence
    plot_convergence(iterations, values, target=0.0, ax=ax)
    engine.apply_publication_style(
        ax, "Convergence Analysis", "Iteration", "Value", grid=True
    )

    # Save figure
    saved = engine.save_figure(fig, "convergence_analysis")
    logger.info(f"  Saved: {saved['png']}")

    # Register figure
    figure_manager = FigureManager()
    fig_meta = figure_manager.register_figure(
        filename="convergence_analysis.png",
        caption="Convergence behavior of the optimization algorithm showing exponential decay to target value",
        section="experimental_results",
        generated_by="generate_scientific_figures.py",
    )

    plt.close(fig)
    return fig_meta.label


def generate_time_series_figure() -> str:
    """Generate time series analysis figure.

    Returns:
        Figure label
    """
    logger.info("Generating time series figure...")

    # Generate time series data
    time, values = generate_time_series(
        n_points=200, trend="sinusoidal", noise_level=0.15, seed=42
    )

    # Setup visualization
    engine = VisualizationEngine(output_dir="output/figures")
    fig, ax = engine.create_figure()

    # Plot time series
    plot_line(time, values, ax=ax, label="Time Series", color=engine.get_color(0))
    engine.apply_publication_style(
        ax, "Time Series Analysis", "Time", "Value", grid=True, legend=True
    )

    # Save figure
    saved = engine.save_figure(fig, "time_series_analysis")
    logger.info(f"  Saved: {saved['png']}")

    # Register figure
    figure_manager = FigureManager()
    fig_meta = figure_manager.register_figure(
        filename="time_series_analysis.png",
        caption="Time series data showing sinusoidal trend with added noise",
        section="experimental_results",
        generated_by="generate_scientific_figures.py",
    )

    plt.close(fig)
    return fig_meta.label


def generate_statistical_comparison_figure() -> str:
    """Generate statistical comparison figure.

    Returns:
        Figure label
    """
    logger.info("Generating statistical comparison figure...")

    # Generate comparison data
    methods = ["Baseline", "Method A", "Method B", "Method C"]
    metrics = {
        "accuracy": [0.75, 0.85, 0.90, 0.88],
        "precision": [0.72, 0.83, 0.89, 0.87],
        "recall": [0.78, 0.87, 0.91, 0.89],
    }

    # Setup visualization
    engine = VisualizationEngine(output_dir="output/figures")
    fig, ax = engine.create_figure()

    # Plot comparison
    plot_comparison(methods, metrics, "accuracy", ax=ax, plot_type="bar")
    engine.apply_publication_style(
        ax, "Method Comparison", "Method", "Accuracy", grid=True
    )

    # Save figure
    saved = engine.save_figure(fig, "statistical_comparison")
    logger.info(f"  Saved: {saved['png']}")

    # Register figure
    figure_manager = FigureManager()
    fig_meta = figure_manager.register_figure(
        filename="statistical_comparison.png",
        caption="Comparison of different methods on accuracy metric",
        section="experimental_results",
        generated_by="generate_scientific_figures.py",
    )

    plt.close(fig)
    return fig_meta.label


def generate_scatter_plot_figure() -> str:
    """Generate scatter plot figure.

    Returns:
        Figure label
    """
    logger.info("Generating scatter plot figure...")

    # Generate correlated data
    x = generate_synthetic_data(100, distribution="normal", seed=42)
    y = x + generate_synthetic_data(100, distribution="normal", std=0.3, seed=43)

    # Setup visualization
    engine = VisualizationEngine(output_dir="output/figures")
    fig, ax = engine.create_figure()

    # Plot scatter
    plot_scatter(x.flatten(), y.flatten(), ax=ax, alpha=0.6, color=engine.get_color(0))
    engine.apply_publication_style(ax, "Correlation Analysis", "X", "Y", grid=True)

    # Save figure
    saved = engine.save_figure(fig, "scatter_correlation")
    logger.info(f"  Saved: {saved['png']}")

    # Register figure
    figure_manager = FigureManager()
    fig_meta = figure_manager.register_figure(
        filename="scatter_correlation.png",
        caption="Scatter plot showing correlation between two variables",
        section="experimental_results",
        generated_by="generate_scientific_figures.py",
    )

    plt.close(fig)
    return fig_meta.label


def insert_figures_into_manuscript(figure_labels: list[str]) -> None:
    """Insert figures into manuscript markdown files.

    Args:
        figure_labels: List of figure labels to insert
    """
    logger.info("\nInserting figures into manuscript...")

    if not _INFRA_AVAILABLE:
        logger.warning("  MarkdownIntegration not available (infrastructure not installed) - skipping insertion")
        return

    # Setup markdown integration
    # Use project_root/manuscript since we are in project/scripts/
    manuscript_dir = project_root / "manuscript"
    markdown_integration = MarkdownIntegration(manuscript_dir=manuscript_dir)

    # Find target markdown file (experimental results section)
    target_file = manuscript_dir / "04_experimental_results.md"

    if not target_file.exists():
        logger.warning(
            f"  Warning: Target file {target_file} not found, skipping insertion"
        )
        return

    # Insert each figure
    for label in figure_labels:
        success = markdown_integration.insert_figure_in_section(
            target_file, label, section_name="Experimental Results", position="after"
        )
        if success:
            logger.info(f"  ✅ Inserted figure: {label}")
        else:
            logger.warning(f"  ⚠️  Failed to insert figure: {label}")

    # Update references
    updated = markdown_integration.update_all_references(target_file)
    if updated == 0:
        logger.info(
            f"  Reference scan complete: {updated} updates (figures already present or no new references)"
        )
    else:
        logger.info(f"  Reference scan complete: {updated} reference(s) updated")


def validate_all_figures() -> None:
    """Validate all generated figures."""
    logger.info("\nValidating figures...")

    # Use project_root/manuscript since we are in project/scripts/
    manuscript_dir = project_root / "manuscript"

    if _INFRA_AVAILABLE:
        markdown_integration = MarkdownIntegration(manuscript_dir=manuscript_dir)

        # Validate manuscript
        validation_results = markdown_integration.validate_manuscript()

        if validation_results:
            logger.warning("  ⚠️  Validation issues found:")
            for file_path, errors in validation_results.items():
                logger.warning(f"    {file_path}:")
                for label, error in errors:
                    logger.warning(f"      - {label}: {error}")
        else:
            logger.info("  ✅ All figures validated successfully")

        # Get statistics
        stats = markdown_integration.get_figure_statistics()
        logger.info(f"  Total figures: {stats['total_figures']}")
        logger.info(f"  Figures by section: {stats['figures_by_section']}")
    else:
        logger.warning("  MarkdownIntegration not available - skipping manuscript figure validation")

    # Validate registry if present
    registry_path = Path("output/figures/figure_registry.json")
    if registry_path.exists():
        try:
            manuscript_dir = Path("manuscript")
            validate_figure_registry(registry_path, manuscript_dir)
            logger.info("  ✅ Figure registry validated")
        except Exception as exc:  # Broad to keep orchestration resilient
            logger.warning(f"  ⚠️  Figure registry validation warning: {exc}")

    # Run lightweight markdown validation for figures/refs
    try:
        validation_result = validate_markdown_wrapper(str(manuscript_dir), strict=False)
        if validation_result.get("status") == "issues_found":
            problems = validation_result.get("issues", [])
            logger.warning("  ⚠️  Markdown validation issues detected:")
            for prob in problems:
                logger.warning(f"    - {prob}")
        elif validation_result.get("status") == "error":
            logger.warning(
                f"  ⚠️  Markdown validation error: {validation_result.get('error', 'Unknown error')}"
            )
        else:
            logger.info("  ✅ Markdown references validated")
    except Exception as exc:
        logger.warning(f"  ⚠️  Markdown validation skipped: {exc}")


def main() -> None:
    """Main function orchestrating the complete figure generation workflow."""
    os.environ.setdefault("MPLBACKEND", "Agg")
    args, stage_names = _parse_args()

    staged_functions = [
        ("convergence", generate_convergence_figure),
        ("timeseries", generate_time_series_figure),
        ("stats", generate_statistical_comparison_figure),
        ("scatter", generate_scatter_plot_figure),
        # insert + validate need access to the figure label list; handled in loop
    ]

    if args.list_stages:
        logger.info("Available stages (in order):")
        for name, _ in staged_functions + [("insert", None), ("validate", None)]:
            logger.info(f"- {name}")
        return

    # Ensure output directories exist
    for dir_path in ["output/figures", "output/simulations"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    # Filter stages based on --only while preserving order
    if args.only:
        selected = [(name, fn) for name, fn in staged_functions if name in args.only]
    else:
        selected = staged_functions

    # Apply resume (skip until the requested stage)
    if args.resume:
        resume_seen = False
        filtered = []
        for name, fn in selected:
            if not resume_seen and name != args.resume:
                continue
            resume_seen = True
            filtered.append((name, fn))
        selected = filtered

    # Always append insert/validate after generation stages if requested
    post_stages = [("insert", None), ("validate", None)]
    if args.only:
        post_stages = [(n, fn) for n, fn in post_stages if n in args.only]
    if args.resume:
        post_stages = (
            [
                (n, fn)
                for n, fn in post_stages
                if stage_names.index(n) >= stage_names.index(args.resume)
            ]
            if post_stages
            else post_stages
        )

    selected_with_post = selected + post_stages

    if not selected_with_post:
        logger.info("No stages selected; nothing to do.")
        return

    if args.dry_run:
        logger.info(
            "Dry-run enabled. Stages that would run (in order): %s",
            ", ".join(name for name, _ in selected_with_post),
        )
        return

    try:
        figure_labels: list[str] = []
        error_agg = get_error_aggregator()
        stage_results = []

        for name, fn in selected_with_post:
            logger.info("Starting stage: %s", name)
            perf = PerformanceMonitor()
            perf.start()
            try:
                if name == "insert":
                    insert_figures_into_manuscript(figure_labels)
                elif name == "validate":
                    validate_all_figures()
                else:
                    label = fn()
                    figure_labels.append(label)
                exit_code = 0
            except Exception as exc:
                exit_code = 1
                error_agg.add_error(
                    error_type="stage_failure",
                    message=str(exc),
                    stage=name,
                    severity="error",
                )
                raise
            finally:
                perf.update_memory()
                metrics = perf.stop()
                stage_results.append(
                    {
                        "name": name,
                        "exit_code": exit_code,
                        "duration": metrics.duration,
                        "resource_usage": metrics.resource_usage.to_dict(),
                    }
                )
                log_substep(f"{name} duration: {metrics.duration:.2f}s", logger)
                log_progress_bar(
                    current=len(stage_results),
                    total=len(selected_with_post),
                    task=f"{name} complete",
                    logger=logger,
                )
            logger.info("Completed stage: %s", name)

        logger.info(f"\n✅ Generated {len([f for f in figure_labels if f])} figures")
        logger.info("\n✅ All scientific figure generation tasks completed!")
        logger.info("\nGenerated outputs:")
        logger.info("  - Figures: output/figures/")
        logger.info("  - Figure registry: output/figures/figure_registry.json")
        logger.info("\nFigures are ready for manuscript integration")

        # Save structured report
        report = generate_pipeline_report(
            stage_results=stage_results,
            total_duration=sum(s["duration"] for s in stage_results),
            repo_root=Path("."),
            error_summary=error_agg.get_summary(),
        )
        saved = save_pipeline_report(report, Path("output/reports"))
        log_substep(f"Saved figure pipeline report: {saved}", logger)

    except ImportError as e:
        logger.error(f"❌ Failed to import from src/ modules: {e}", exc_info=True)
        logger.error("Make sure all src/ modules are available")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error during figure generation: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    main()
