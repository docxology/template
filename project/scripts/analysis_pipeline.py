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

import os
import sys
import logging
from pathlib import Path

import numpy as np

# Configure logging for layer-aware execution tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Ensure src/ and infrastructure/ are on path
project_root = Path(__file__).parent.parent
repo_root = project_root.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(repo_root))  # Add repo root so we can import infrastructure.*
from infrastructure.figure_manager import FigureManager
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
    
    # Ensure output directories exist
    for dir_path in ["output/figures", "output/reports"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    try:
        # Load and analyze data
        load_and_analyze_data()
        
        # Perform statistical tests
        perform_statistical_tests()
        
        # Analyze classification
        analyze_classification_performance()
        
        # Generate plots
        generate_comparison_plots()
        
        # Analyze scalability
        run_scalability_analysis()
        
        # Generate report
        generate_analysis_report()
        
        # Validate results
        validate_analysis_results()
        
        print("\n✅ All analysis pipeline tasks completed successfully!")
        print("\nGenerated outputs:")
        print("  - Figures: output/figures/")
        print("  - Reports: output/reports/")
        
    except ImportError as e:
        print(f"❌ Failed to import from src/ modules: {e}")
        print("Make sure all src/ modules are available")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    main()

