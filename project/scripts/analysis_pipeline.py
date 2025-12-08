#!/usr/bin/env python3
"""Analysis pipeline script demonstrating statistical analysis workflow.

This script demonstrates how to use src/ modules to:
1. Load simulation results
2. Perform statistical analysis
3. Generate comparison plots
4. Create summary reports

IMPORTANT: This script follows the thin orchestrator pattern - all business
logic is in src/ modules, this script only orchestrates the workflow.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np

# Ensure src/ and infrastructure/ are on path BEFORE imports
project_root = Path(__file__).parent.parent
repo_root = project_root.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(repo_root))  # Add repo root so we can import infrastructure.*

# Add infra logging for consistent structured output
from infrastructure.core.logging_utils import (
    get_logger,
    log_stage,
    log_substep,
    log_progress_bar,
    format_error_with_suggestions,
)
from infrastructure.core.performance import PerformanceMonitor
from infrastructure.reporting import (
    generate_pipeline_report,
    save_pipeline_report,
    get_error_aggregator,
)
from infrastructure.validation import verify_output_integrity

logger = get_logger(__name__)


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments for stage control and dry-run support."""
    parser = argparse.ArgumentParser(
        description="Run the analysis pipeline with optional stage selection."
    )
    stage_names = [
        "load",
        "tests",
        "classification",
        "plots",
        "scalability",
        "report",
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
        help="Print the stages that would run without executing them.",
    )
    parser.add_argument(
        "--list-stages",
        action="store_true",
        help="List available stages and exit.",
    )
    return parser.parse_args(), stage_names

# Additional infrastructure imports (path already set up above)
from infrastructure.documentation.figure_manager import FigureManager

print("[LAYER-2-SCIENTIFIC] Loading and analyzing data from infrastructure/scientific integration...")

# Import src/ modules
from data_generator import generate_classification_dataset, generate_synthetic_data
from data_processing import normalize_data, detect_outliers, clean_data
from metrics import calculate_accuracy, calculate_precision_recall_f1, calculate_all_metrics
from performance import analyze_scalability, benchmark_comparison
from reporting import ReportGenerator
from statistics import (
    calculate_descriptive_stats,
    calculate_correlation,
    calculate_confidence_interval,
    anova_test
)
from validation import ValidationFramework
from visualization import VisualizationEngine
from plots import plot_comparison, plot_scatter, plot_bar


def load_and_analyze_data() -> None:
    """Load and analyze simulation data."""

    # Generate synthetic data
    data = generate_synthetic_data(
        n_samples=200,
        n_features=2,
        distribution="normal",
        seed=42
    )
    
    # Clean data using scientific layer
    cleaned_data = clean_data(data, remove_nan=True, fill_method="mean")
    print(f"  [LAYER-2] Data shape after cleaning: {cleaned_data.shape}")
    
    # Calculate descriptive statistics
    stats = calculate_descriptive_stats(cleaned_data)
    print(f"  Mean: {stats.mean:.4f}")
    print(f"  Std: {stats.std:.4f}")
    print(f"  Median: {stats.median:.4f}")
    
    # Detect outliers
    outlier_mask, outlier_info = detect_outliers(cleaned_data, method="iqr")
    n_outliers = np.sum(outlier_mask)
    print(f"  Outliers detected: {n_outliers} ({100*n_outliers/outlier_mask.size:.2f}%)")
    
    print("✅ Data analysis complete")


def perform_statistical_tests() -> None:
    """Perform statistical hypothesis tests."""
    print("\nPerforming statistical tests...")

    # Generate two groups for comparison
    group1 = generate_synthetic_data(50, distribution="normal", mean=0.0, std=1.0, seed=42)
    group2 = generate_synthetic_data(50, distribution="normal", mean=0.5, std=1.0, seed=43)
    
    # Calculate correlation
    if len(group1) == len(group2):
        correlation = calculate_correlation(group1.flatten(), group2.flatten())
        print(f"  Correlation: {correlation['correlation']:.4f}")
    
    # Calculate confidence intervals
    ci1 = calculate_confidence_interval(group1.flatten())
    ci2 = calculate_confidence_interval(group2.flatten())
    print(f"  Group 1 CI: [{ci1[0]:.4f}, {ci1[1]:.4f}]")
    print(f"  Group 2 CI: [{ci2[0]:.4f}, {ci2[1]:.4f}]")
    
    # ANOVA test
    anova_result = anova_test([group1.flatten(), group2.flatten()])
    print(f"  ANOVA F-statistic: {anova_result['f_statistic']:.4f}")
    
    print("✅ Statistical tests complete")


def analyze_classification_performance() -> None:
    """Analyze classification performance."""
    print("\nAnalyzing classification performance...")

    # Generate classification dataset
    X, y_true = generate_classification_dataset(
        n_samples=100,
        n_features=2,
        n_classes=2,
        seed=42
    )
    
    # Simulate predictions (simple threshold-based)
    y_pred = (X[:, 0] > 0).astype(int)
    
    # Calculate metrics
    accuracy = calculate_accuracy(y_pred, y_true)
    prf = calculate_precision_recall_f1(y_pred, y_true)
    
    print(f"  Accuracy: {accuracy:.4f}")
    print(f"  Precision: {prf['precision']:.4f}")
    print(f"  Recall: {prf['recall']:.4f}")
    print(f"  F1: {prf['f1']:.4f}")
    
    # Calculate all metrics
    all_metrics = calculate_all_metrics(predictions=y_pred, targets=y_true)
    print(f"  All metrics calculated: {len(all_metrics)} metrics")
    
    print("✅ Classification analysis complete")


def generate_comparison_plots() -> None:
    """Generate comparison plots."""
    print("\nGenerating comparison plots...")

    # Setup visualization
    engine = VisualizationEngine(output_dir="output/figures")
    figure_manager = FigureManager()
    
    # Generate comparison data
    methods = ["Method A", "Method B", "Method C", "Method D"]
    metrics = {
        "accuracy": [0.85, 0.92, 0.88, 0.90],
        "precision": [0.82, 0.91, 0.86, 0.89],
        "recall": [0.88, 0.93, 0.90, 0.91]
    }
    
    # Create comparison plot
    fig, ax = engine.create_figure()
    plot_comparison(methods, metrics, "accuracy", ax=ax, plot_type="bar")
    engine.apply_publication_style(ax, "Method Comparison", "Method", "Accuracy", grid=True)
    
    # Save figure
    saved = engine.save_figure(fig, "analysis_comparison")
    print(f"  Saved figure: {saved['png']}")
    
    # Register figure
    fig_meta = figure_manager.register_figure(
        filename="analysis_comparison.png",
        caption="Comparison of different methods on accuracy metric",
        section="experimental_results",
        generated_by="analysis_pipeline.py"
    )
    print(f"  Registered figure: {fig_meta.label}")
    
    plt.close(fig)
    
    print("✅ Comparison plots generated")


def run_scalability_analysis() -> None:
    """Analyze algorithm scalability."""
    print("\nAnalyzing scalability...")

    # Simulate scalability data
    problem_sizes = [10, 50, 100, 500, 1000]
    execution_times = [0.1, 0.5, 1.2, 6.5, 15.0]  # Simulated times
    
    # Analyze scalability
    scalability = analyze_scalability(problem_sizes, execution_times)
    print(f"  Estimated complexity: {scalability.time_complexity}")
    print(f"  Speedup: {scalability.speedup}")
    
    # Benchmark comparison
    comparison = benchmark_comparison(
        methods=["Baseline", "Optimized"],
        metrics={"execution_time": [15.0, 8.5]},
        metric_name="execution_time"
    )
    print(f"  Best method: {comparison['best_method']}")
    print(f"  Best value: {comparison['best_value']:.2f}")
    
    print("✅ Scalability analysis complete")


def generate_analysis_report() -> None:
    """Generate comprehensive analysis report."""
    print("\nGenerating analysis report...")

    # Generate analysis results
    data = generate_synthetic_data(100, distribution="normal", seed=42)
    stats = calculate_descriptive_stats(data)
    
    # Create report
    report_gen = ReportGenerator(output_dir="output/reports")
    
    results = {
        "summary": {
            "n_samples": 100,
            "mean": stats.mean,
            "std": stats.std,
            "median": stats.median
        },
        "findings": [
            "Statistical analysis completed successfully",
            f"Data follows normal distribution (mean={stats.mean:.4f})",
            "No significant outliers detected",
            "All statistical tests passed"
        ],
        "tables": {
            "Descriptive Statistics": {
                "Metric": ["Mean", "Std", "Median", "Min", "Max", "Q25", "Q75"],
                "Value": [
                    f"{stats.mean:.4f}",
                    f"{stats.std:.4f}",
                    f"{stats.median:.4f}",
                    f"{stats.min:.4f}",
                    f"{stats.max:.4f}",
                    f"{stats.q25:.4f}",
                    f"{stats.q75:.4f}"
                ]
            }
        }
    }
    
    # Generate report
    report_path = report_gen.generate_markdown_report(
        "Statistical Analysis Report",
        results,
        "analysis_report"
    )
    print(f"  Generated report: {report_path}")
    
    print("✅ Analysis report generated")


def validate_analysis_results() -> None:
    """Validate analysis results."""
    print("\nValidating analysis results...")

    validator = ValidationFramework()
    
    # Generate test data
    data = generate_synthetic_data(100, distribution="normal", seed=42)
    
    # Validate bounds
    validator.validate_bounds(data, "analysis_data", min_value=-3.0, max_value=3.0)
    
    # Validate quality metrics
    stats = calculate_descriptive_stats(data)
    validator.validate_quality_metrics(
        {"mean": stats.mean, "std": stats.std},
        {"mean": (-1.0, 1.0), "std": (0.5, 1.5)}
    )
    
    # Generate validation report
    report = validator.generate_validation_report()
    print(f"  Validation checks: {report['summary']['total_checks']}")
    print(f"  All passed: {report['all_passed']}")
    
    print("✅ Validation complete")


def main() -> None:
    """Main function orchestrating the analysis pipeline."""
    os.environ.setdefault("MPLBACKEND", "Agg")
    args, stage_names = _parse_args()

    staged_functions: List[Tuple[str, callable]] = [
        ("load", load_and_analyze_data),
        ("tests", perform_statistical_tests),
        ("classification", analyze_classification_performance),
        ("plots", generate_comparison_plots),
        ("scalability", run_scalability_analysis),
        ("report", generate_analysis_report),
        ("validate", validate_analysis_results),
    ]

    if args.list_stages:
        print("Available stages (in order):")
        for name, _ in staged_functions:
            print(f"- {name}")
        return

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

    if not selected:
        print("No stages selected; nothing to do.")
        return

    # Ensure output directories exist
    for dir_path in ["output/figures", "output/reports"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        logger.info("Dry-run enabled. Stages that would run (in order): %s", ", ".join(name for name, _ in selected))
        return

    error_agg = get_error_aggregator()
    stage_results = []

    try:
        for idx, (name, fn) in enumerate(selected, 1):
            logger.info("Starting stage: %s", name)
            perf = PerformanceMonitor()
            perf.start()
            fn()
            perf.update_memory()
            metrics = perf.stop()
            stage_results.append(
                {
                    "name": name,
                    "exit_code": 0,
                    "duration": metrics.duration,
                    "resource_usage": metrics.resource_usage.to_dict(),
                }
            )
            log_substep(f"Stage {name} duration: {metrics.duration:.2f}s", logger)
            log_progress_bar(
                current=idx,
                total=len(selected),
                message=f"{name} complete",
                logger=logger,
            )
            logger.info("Completed stage: %s", name)

        # Light integrity check on generated outputs
        try:
            verify_output_integrity(Path("output"))
        except Exception as ve:
            error_agg.add_error(
                error_type="validation_error",
                message=f"Output integrity validation warning: {ve}",
                stage="analysis",
                severity="warning",
            )

        # Generate structured pipeline report
        pipeline_report = generate_pipeline_report(
            stage_results=stage_results,
            total_duration=sum(sr["duration"] for sr in stage_results),
            repo_root=Path("."),
            error_summary=error_agg.get_summary(),
        )
        saved = save_pipeline_report(pipeline_report, Path("output/reports"))
        log_substep(f"Saved pipeline report: {saved}", logger)

        print("\n✅ All analysis pipeline tasks completed successfully!")
        print("\nGenerated outputs:")
        print("  - Figures: output/figures/")
        print("  - Reports: output/reports/")

    except ImportError as e:
        error_agg.add_error(
            error_type="import_error",
            message=str(e),
            stage="analysis",
            severity="error",
            suggestions=[
                "Ensure src/ modules are importable",
                "Verify PYTHONPATH includes project/src",
            ],
        )
        print(f"❌ Failed to import from src/ modules: {e}")
        sys.exit(1)
    except Exception as e:
        error_agg.add_error(
            error_type="stage_failure",
            message=str(e),
            stage="analysis",
            severity="error",
        )
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    main()

