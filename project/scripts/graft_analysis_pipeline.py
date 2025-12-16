#!/usr/bin/env python3
"""Grafting analysis pipeline script demonstrating complete grafting workflow.

This script demonstrates how to use src/ modules to:
1. Generate grafting trial data
2. Perform compatibility analysis
3. Analyze success factors
4. Generate comparison plots
5. Create summary reports

IMPORTANT: This script follows the thin orchestrator pattern - all business
logic is in src/ modules, this script only orchestrates the workflow.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np

# Ensure src/ and infrastructure/ are on path BEFORE imports
project_root = Path(__file__).parent.parent
repo_root = project_root.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(repo_root))

# Infrastructure imports
from infrastructure.core.logging_utils import (
    get_logger,
    log_stage,
    log_substep,
)
from infrastructure.core.performance import PerformanceMonitor
from infrastructure.documentation.figure_manager import FigureManager
from infrastructure.reporting import (
    generate_pipeline_report,
    save_pipeline_report,
)
from infrastructure.validation import verify_output_integrity

logger = get_logger(__name__)


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments for stage control and dry-run support."""
    parser = argparse.ArgumentParser(
        description="Run the grafting analysis pipeline with optional stage selection."
    )
    stage_names = [
        "data",
        "compatibility",
        "statistics",
        "techniques",
        "plots",
        "report",
        "validate",
    ]
    parser.add_argument(
        "--only",
        nargs="+",
        choices=stage_names,
        help="Run only the selected stages.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the stages that would run without executing them.",
    )
    return parser.parse_args(), stage_names


# Import grafting modules from src/
from graft_data_generator import (
    generate_graft_trial_data,
    generate_compatibility_matrix,
    generate_environmental_data
)
from graft_data_processing import (
    clean_graft_data,
    normalize_graft_parameters,
    extract_graft_features
)
from graft_statistics import (
    calculate_graft_statistics,
    compare_technique_success,
    calculate_success_correlation
)
from graft_metrics import (
    calculate_success_rate,
    calculate_all_graft_metrics
)
from graft_analysis import (
    analyze_graft_outcomes,
    compare_techniques,
    analyze_factor_importance
)
from graft_plots import (
    plot_success_rates,
    plot_compatibility_matrix,
    plot_healing_timeline
)
from graft_reporting import GraftReportGenerator
from graft_validation import GraftValidationFramework
from graft_visualization import GraftVisualizationEngine


def generate_graft_data() -> dict:
    """Generate grafting trial data."""
    log_substep("Generating grafting trial data")
    
    # Generate trial data
    trial_data = generate_graft_trial_data(
        n_trials=500,
        n_species=15,
        success_rate=0.75,
        seed=42
    )
    
    logger.info(f"  Generated {len(trial_data['success'])} trials")
    logger.info(f"  Success rate: {np.mean(trial_data['success']):.2%}")
    
    return trial_data


def analyze_compatibility() -> np.ndarray:
    """Analyze species compatibility."""
    log_substep("Analyzing species compatibility")
    
    # Generate compatibility matrix
    compat_matrix = generate_compatibility_matrix(
        n_species=15,
        phylogenetic_structure=True,
        seed=42
    )
    
    logger.info(f"  Compatibility matrix shape: {compat_matrix.shape}")
    logger.info(f"  Average compatibility: {np.mean(compat_matrix):.3f}")
    
    return compat_matrix


def perform_statistical_analysis(trial_data: dict) -> None:
    """Perform statistical analysis of grafting outcomes."""
    log_substep("Performing statistical analysis")
    
    # Calculate statistics
    stats = calculate_graft_statistics(
        trial_data["success"],
        trial_data.get("union_strength"),
        trial_data.get("healing_time")
    )
    
    logger.info(f"  Success rate: {stats['success'].success_rate:.2%}")
    if "union_strength" in stats:
        logger.info(f"  Mean union strength: {stats['union_strength'].mean:.3f}")
    
    # Analyze outcomes
    outcomes = analyze_graft_outcomes(
        trial_data["success"],
        trial_data.get("union_strength"),
        trial_data.get("healing_time")
    )
    logger.info(f"  Total successful: {outcomes.n_successful}/{outcomes.n_trials}")


def compare_grafting_techniques(trial_data: dict) -> None:
    """Compare different grafting techniques."""
    log_substep("Comparing grafting techniques")
    
    # Simulate technique groups (in practice, would come from data)
    techniques = {
        "whip": trial_data["success"][:125],
        "cleft": trial_data["success"][125:250],
        "bark": trial_data["success"][250:375],
        "bud": trial_data["success"][375:]
    }
    
    comparison = compare_techniques(techniques)
    logger.info(f"  Best technique: {comparison['best_technique']}")
    logger.info(f"  Best success rate: {comparison['best_technique_success_rate']:.2%}")


def generate_analysis_plots(trial_data: dict, compat_matrix: np.ndarray) -> None:
    """Generate analysis plots."""
    log_substep("Generating analysis plots")
    
    engine = GraftVisualizationEngine(output_dir="output/figures")
    figure_manager = FigureManager()
    
    # Success rates by technique
    techniques = ["Whip", "Cleft", "Bark", "Bud"]
    success_rates = np.array([
        np.mean(trial_data["success"][:125]),
        np.mean(trial_data["success"][125:250]),
        np.mean(trial_data["success"][250:375]),
        np.mean(trial_data["success"][375:])
    ])
    
    fig, ax = engine.create_figure()
    plot_success_rates(techniques, success_rates, ax=ax)
    engine.apply_publication_style(ax, "Graft Success Rates by Technique", 
                                   "Technique", "Success Rate", grid=True)
    saved = engine.save_figure(fig, "success_rate_analysis")
    logger.info(f"  Saved: {saved['png']}")
    figure_manager.register_figure(
        filename="success_rate_analysis.png",
        caption="Success rates across different grafting techniques",
        section="experimental_results",
        generated_by="graft_analysis_pipeline.py"
    )
    plt.close(fig)
    
    # Compatibility matrix
    fig, ax = engine.create_figure(figsize=(10, 8))
    plot_compatibility_matrix(compat_matrix, ax=ax)
    saved = engine.save_figure(fig, "compatibility_matrix")
    logger.info(f"  Saved: {saved['png']}")
    figure_manager.register_figure(
        filename="compatibility_matrix.png",
        caption="Species compatibility matrix showing graft success probabilities",
        section="experimental_results",
        generated_by="graft_analysis_pipeline.py"
    )
    plt.close(fig)


def generate_analysis_report(trial_data: dict) -> None:
    """Generate analysis report."""
    log_substep("Generating analysis report")
    
    generator = GraftReportGenerator(output_dir="output/reports")
    
    report_path = generator.generate_trial_report(
        trial_data["success"],
        trial_data.get("union_strength"),
        trial_data.get("healing_time")
    )
    
    logger.info(f"  Generated report: {report_path}")


def validate_outputs() -> None:
    """Validate generated outputs."""
    log_substep("Validating outputs")
    
    framework = GraftValidationFramework()
    
    # Validate compatibility
    compat_matrix = generate_compatibility_matrix(10, seed=42)
    for i in range(10):
        for j in range(10):
            if i != j:
                result = framework.validate_compatibility(
                    np.array([compat_matrix[i, j]]),
                    min_compatibility=0.3
                )
    
    summary = framework.get_validation_summary()
    logger.info(f"  Validation checks: {summary['total_checks']}")
    logger.info(f"  All passed: {summary['all_passed']}")


def main() -> None:
    """Main analysis pipeline."""
    args, stage_names = _parse_args()
    
    if args.dry_run:
        logger.info("Dry run - would execute stages:")
        for stage in stage_names:
            logger.info(f"  - {stage}")
        return
    
    monitor = PerformanceMonitor()
    monitor.start()
    
    try:
        logger.info("=" * 60)
        logger.info("  Grafting Analysis Pipeline")
        logger.info("=" * 60)
        
        trial_data = None
        compat_matrix = None
        
        # Stage 1: Generate data
        if not args.only or "data" in args.only:
            log_substep("Data Generation")
            trial_data = generate_graft_data()
            compat_matrix = analyze_compatibility()
        
        # Stage 2: Compatibility analysis
        if not args.only or "compatibility" in args.only:
            log_substep("Compatibility Analysis")
            if compat_matrix is None:
                compat_matrix = analyze_compatibility()
        
        # Stage 3: Statistical analysis
        if not args.only or "statistics" in args.only:
            log_substep("Statistical Analysis")
            if trial_data is None:
                trial_data = generate_graft_data()
            perform_statistical_analysis(trial_data)
        
        # Stage 4: Technique comparison
        if not args.only or "techniques" in args.only:
            log_substep("Technique Comparison")
            if trial_data is None:
                trial_data = generate_graft_data()
            compare_grafting_techniques(trial_data)
        
        # Stage 5: Generate plots
        if not args.only or "plots" in args.only:
            log_substep("Plot Generation")
            if trial_data is None:
                trial_data = generate_graft_data()
            if compat_matrix is None:
                compat_matrix = analyze_compatibility()
            generate_analysis_plots(trial_data, compat_matrix)
        
        # Stage 6: Generate report
        if not args.only or "report" in args.only:
            log_substep("Report Generation")
            if trial_data is None:
                trial_data = generate_graft_data()
            generate_analysis_report(trial_data)
        
        # Stage 7: Validate outputs
        if not args.only or "validate" in args.only:
            log_substep("Output Validation")
            validate_outputs()
        
        metrics = monitor.stop()
        logger.info(f"✅ Pipeline complete in {metrics.duration:.2f}s")
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    main()

