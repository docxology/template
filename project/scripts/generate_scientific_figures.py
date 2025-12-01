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

import os
import sys
from pathlib import Path

import numpy as np

# Ensure src/ and infrastructure/ are on path
project_root = Path(__file__).parent.parent
repo_root = project_root.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(repo_root))  # Add repo root so we can import infrastructure.*
from infrastructure.documentation.figure_manager import FigureManager
from infrastructure.documentation.image_manager import ImageManager
from infrastructure.documentation.markdown_integration import MarkdownIntegration
# Import src/ modules
from data_generator import generate_time_series, generate_synthetic_data
from performance import analyze_convergence
from plots import (
    plot_line,
    plot_scatter,
    plot_bar,
    plot_convergence,
    plot_comparison
)
from statistics import calculate_descriptive_stats
from visualization import VisualizationEngine


def generate_convergence_figure() -> str:
    """Generate convergence analysis figure.
    
    Returns:
        Figure label
    """
    print("Generating convergence figure...")
    
    # Generate convergence data
    iterations = np.arange(1, 101)
    values = 10 * np.exp(-iterations / 20) + np.random.normal(0, 0.1, len(iterations))
    
    # Setup visualization
    engine = VisualizationEngine(output_dir="output/figures")
    fig, ax = engine.create_figure()
    
    # Plot convergence
    plot_convergence(iterations, values, target=0.0, ax=ax)
    engine.apply_publication_style(ax, "Convergence Analysis", "Iteration", "Value", grid=True)
    
    # Save figure
    saved = engine.save_figure(fig, "convergence_analysis")
    print(f"  Saved: {saved['png']}")
    
    # Register figure
    figure_manager = FigureManager()
    fig_meta = figure_manager.register_figure(
        filename="convergence_analysis.png",
        caption="Convergence behavior of the optimization algorithm showing exponential decay to target value",
        section="experimental_results",
        generated_by="generate_scientific_figures.py"
    )
    
    plt.close(fig)
    return fig_meta.label


def generate_time_series_figure() -> str:
    """Generate time series analysis figure.
    
    Returns:
        Figure label
    """
    print("Generating time series figure...")
    
    # Generate time series data
    time, values = generate_time_series(
        n_points=200,
        trend="sinusoidal",
        noise_level=0.15,
        seed=42
    )
    
    # Setup visualization
    engine = VisualizationEngine(output_dir="output/figures")
    fig, ax = engine.create_figure()
    
    # Plot time series
    plot_line(time, values, ax=ax, label="Time Series", color=engine.get_color(0))
    engine.apply_publication_style(ax, "Time Series Analysis", "Time", "Value", grid=True, legend=True)
    
    # Save figure
    saved = engine.save_figure(fig, "time_series_analysis")
    print(f"  Saved: {saved['png']}")
    
    # Register figure
    figure_manager = FigureManager()
    fig_meta = figure_manager.register_figure(
        filename="time_series_analysis.png",
        caption="Time series data showing sinusoidal trend with added noise",
        section="experimental_results",
        generated_by="generate_scientific_figures.py"
    )
    
    plt.close(fig)
    return fig_meta.label


def generate_statistical_comparison_figure() -> str:
    """Generate statistical comparison figure.
    
    Returns:
        Figure label
    """
    print("Generating statistical comparison figure...")
    
    # Generate comparison data
    methods = ["Baseline", "Method A", "Method B", "Method C"]
    metrics = {
        "accuracy": [0.75, 0.85, 0.90, 0.88],
        "precision": [0.72, 0.83, 0.89, 0.87],
        "recall": [0.78, 0.87, 0.91, 0.89]
    }
    
    # Setup visualization
    engine = VisualizationEngine(output_dir="output/figures")
    fig, ax = engine.create_figure()
    
    # Plot comparison
    plot_comparison(methods, metrics, "accuracy", ax=ax, plot_type="bar")
    engine.apply_publication_style(ax, "Method Comparison", "Method", "Accuracy", grid=True)
    
    # Save figure
    saved = engine.save_figure(fig, "statistical_comparison")
    print(f"  Saved: {saved['png']}")
    
    # Register figure
    figure_manager = FigureManager()
    fig_meta = figure_manager.register_figure(
        filename="statistical_comparison.png",
        caption="Comparison of different methods on accuracy metric",
        section="experimental_results",
        generated_by="generate_scientific_figures.py"
    )
    
    plt.close(fig)
    return fig_meta.label


def generate_scatter_plot_figure() -> str:
    """Generate scatter plot figure.
    
    Returns:
        Figure label
    """
    print("Generating scatter plot figure...")
    
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
    print(f"  Saved: {saved['png']}")
    
    # Register figure
    figure_manager = FigureManager()
    fig_meta = figure_manager.register_figure(
        filename="scatter_correlation.png",
        caption="Scatter plot showing correlation between two variables",
        section="experimental_results",
        generated_by="generate_scientific_figures.py"
    )
    
    plt.close(fig)
    return fig_meta.label


def insert_figures_into_manuscript(figure_labels: list[str]) -> None:
    """Insert figures into manuscript markdown files.
    
    Args:
        figure_labels: List of figure labels to insert
    """
    print("\nInserting figures into manuscript...")
    
    # Setup markdown integration
    # Use project_root/manuscript since we are in project/scripts/
    manuscript_dir = project_root / "manuscript"
    markdown_integration = MarkdownIntegration(manuscript_dir=manuscript_dir)
    
    # Find target markdown file (experimental results section)
    target_file = manuscript_dir / "04_experimental_results.md"
    
    if not target_file.exists():
        print(f"  Warning: Target file {target_file} not found, skipping insertion")
        return
    
    # Insert each figure
    for label in figure_labels:
        success = markdown_integration.insert_figure_in_section(
            target_file,
            label,
            section_name="Experimental Results",
            position="after"
        )
        if success:
            print(f"  ✅ Inserted figure: {label}")
        else:
            print(f"  ⚠️  Failed to insert figure: {label}")
    
    # Update references
    updated = markdown_integration.update_all_references(target_file)
    if updated == 0:
        print(f"  Reference scan complete: {updated} updates (figures already present or no new references)")
    else:
        print(f"  Reference scan complete: {updated} reference(s) updated")


def validate_all_figures() -> None:
    """Validate all generated figures."""
    print("\nValidating figures...")
    
    # Use project_root/manuscript since we are in project/scripts/
    manuscript_dir = project_root / "manuscript"
    markdown_integration = MarkdownIntegration(manuscript_dir=manuscript_dir)
    
    # Validate manuscript
    validation_results = markdown_integration.validate_manuscript()
    
    if validation_results:
        print("  ⚠️  Validation issues found:")
        for file_path, errors in validation_results.items():
            print(f"    {file_path}:")
            for label, error in errors:
                print(f"      - {label}: {error}")
    else:
        print("  ✅ All figures validated successfully")
    
    # Get statistics
    stats = markdown_integration.get_figure_statistics()
    print(f"  Total figures: {stats['total_figures']}")
    print(f"  Figures by section: {stats['figures_by_section']}")


def main() -> None:
    """Main function orchestrating the complete figure generation workflow."""
    os.environ.setdefault("MPLBACKEND", "Agg")
    
    # Ensure output directories exist
    for dir_path in ["output/figures", "output/simulations"]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    try:
        # Generate all figures
        figure_labels = []
        
        figure_labels.append(generate_convergence_figure())
        figure_labels.append(generate_time_series_figure())
        figure_labels.append(generate_statistical_comparison_figure())
        figure_labels.append(generate_scatter_plot_figure())
        
        print(f"\n✅ Generated {len(figure_labels)} figures")
        
        # Insert figures into manuscript
        insert_figures_into_manuscript(figure_labels)
        
        # Validate figures
        validate_all_figures()
        
        print("\n✅ All scientific figure generation tasks completed!")
        print("\nGenerated outputs:")
        print("  - Figures: output/figures/")
        print("  - Figure registry: output/figures/figure_registry.json")
        print("\nFigures are ready for manuscript integration")
        
    except ImportError as e:
        print(f"❌ Failed to import from src/ modules: {e}")
        print("Make sure all src/ modules are available")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during figure generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    main()

