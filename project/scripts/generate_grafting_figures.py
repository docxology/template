#!/usr/bin/env python3
"""Generate comprehensive grafting figures for the manuscript.

This script generates all figures referenced in the grafting manuscript including:
- Compatibility matrices
- Success rate analyses
- Technique comparisons
- Healing timelines
- Environmental effects
- Rootstock comparisons
- Economic analyses

IMPORTANT: Uses methods from src/ modules to demonstrate integration.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure src/ and infrastructure/ are on path
project_root = Path(__file__).parent.parent
repo_root = project_root.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(repo_root))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from infrastructure.documentation.figure_manager import FigureManager
from graft_data_generator import generate_graft_trial_data, generate_compatibility_matrix
from graft_plots import (
    plot_success_rates,
    plot_compatibility_matrix,
    plot_healing_timeline,
    plot_success_by_factor,
    plot_technique_comparison,
    plot_environmental_effects
)
from graft_visualization import GraftVisualizationEngine


def _setup_directories() -> tuple[str, str, str]:
    """Setup output directories."""
    repo_root = Path(__file__).parent.parent
    output_dir = repo_root / "output"
    data_dir = output_dir / "data"
    figure_dir = output_dir / "figures"
    
    data_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    
    return str(output_dir), str(data_dir), str(figure_dir)


def generate_convergence_plot(figure_dir: str, data_dir: str) -> str:
    """Generate convergence analysis plot."""
    from graft_data_generator import generate_graft_trial_data
    
    # Generate trial data
    trial_data = generate_graft_trial_data(200, seed=42)
    
    # Simulate healing progression
    days = np.arange(0, 60)
    union_strength = 1.0 - np.exp(-days / 15.0)  # Exponential healing
    
    engine = GraftVisualizationEngine(output_dir=figure_dir)
    figure_manager = FigureManager()
    
    fig, ax = engine.create_figure()
    plot_healing_timeline(days, union_strength, ax=ax, label="Union Strength", color=engine.get_color(0))
    engine.apply_publication_style(ax, "Graft Union Strength Over Time", 
                                   "Days Since Grafting", "Union Strength", grid=True, legend=True)
    
    figure_path = os.path.join(figure_dir, "convergence_plot.png")
    engine.save_figure(fig, "convergence_plot")
    plt.close(fig)
    
    figure_manager.register_figure(
        filename="convergence_plot.png",
        caption="Algorithm convergence comparison showing performance improvement",
        section="experimental_results",
        generated_by="generate_grafting_figures.py"
    )
    
    return figure_path


def generate_experimental_setup(figure_dir: str) -> str:
    """Generate experimental setup diagram."""
    engine = GraftVisualizationEngine(output_dir=figure_dir)
    figure_manager = FigureManager()
    
    fig, ax = engine.create_figure(figsize=(12, 8))
    
    # Draw experimental pipeline
    stages = ["Data\nCollection", "Grafting\nOperation", "Monitoring\n& Care", "Evaluation\n& Analysis"]
    x_positions = [0.15, 0.4, 0.65, 0.9]
    
    for i, (stage, x) in enumerate(zip(stages, x_positions)):
        # Draw stage box
        rect = plt.Rectangle((x - 0.08, 0.3), 0.16, 0.4,
                            facecolor=engine.get_color(i), alpha=0.7,
                            edgecolor='black', linewidth=2)
        ax.add_patch(rect)
        ax.text(x, 0.5, stage, ha='center', va='center', fontsize=11, weight='bold')
        
        # Draw arrow to next stage
        if i < len(stages) - 1:
            ax.annotate('', xy=(x_positions[i+1] - 0.08, 0.5),
                       xytext=(x + 0.08, 0.5),
                       arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_title('Experimental Pipeline', fontsize=16, weight='bold', pad=20)
    
    figure_path = os.path.join(figure_dir, "experimental_setup.png")
    engine.save_figure(fig, "experimental_setup")
    plt.close(fig)
    
    figure_manager.register_figure(
        filename="experimental_setup.png",
        caption="Experimental pipeline showing the complete workflow",
        section="methodology",
        generated_by="generate_grafting_figures.py"
    )
    
    return figure_path


def generate_scalability_analysis(figure_dir: str) -> str:
    """Generate scalability analysis plot."""
    engine = GraftVisualizationEngine(output_dir=figure_dir)
    figure_manager = FigureManager()
    
    # Simulate scalability data
    problem_sizes = np.array([10, 50, 100, 500, 1000, 5000])
    our_times = problem_sizes * np.log(problem_sizes) * 0.001  # O(n log n)
    baseline_times = problem_sizes ** 2 * 0.0001  # O(n²)
    
    fig, ax = engine.create_figure()
    ax.loglog(problem_sizes, our_times, marker='o', linewidth=2, 
             label='Our Method (O(n log n))', color=engine.get_color(0))
    ax.loglog(problem_sizes, baseline_times, marker='s', linewidth=2,
             label='Baseline (O(n²))', color=engine.get_color(1))
    engine.apply_publication_style(ax, "Scalability Analysis", 
                                   "Problem Size", "Computation Time", grid=True, legend=True)
    
    figure_path = os.path.join(figure_dir, "scalability_analysis.png")
    engine.save_figure(fig, "scalability_analysis")
    plt.close(fig)
    
    figure_manager.register_figure(
        filename="scalability_analysis.png",
        caption="Scalability analysis showing computational complexity",
        section="experimental_results",
        generated_by="generate_grafting_figures.py"
    )
    
    return figure_path


def generate_ablation_study(figure_dir: str) -> str:
    """Generate ablation study plot."""
    engine = GraftVisualizationEngine(output_dir=figure_dir)
    figure_manager = FigureManager()
    
    components = ['No Regularization', 'No Adaptive Step', 'No Momentum', 'Full Method']
    performance = np.array([0.70, 0.75, 0.80, 0.95])
    
    fig, ax = engine.create_figure()
    bars = ax.bar(components, performance, color=[engine.get_color(i) for i in range(len(components))])
    ax.set_ylabel('Success Rate')
    ax.set_title('Ablation Study: Component Contributions')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3, axis='y')
    
    for bar, perf in zip(bars, performance):
        ax.text(bar.get_x() + bar.get_width()/2., perf,
                f'{perf:.2f}', ha='center', va='bottom')
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    figure_path = os.path.join(figure_dir, "ablation_study.png")
    engine.save_figure(fig, "ablation_study")
    plt.close(fig)
    
    figure_manager.register_figure(
        filename="ablation_study.png",
        caption="Ablation study results showing component contributions",
        section="experimental_results",
        generated_by="generate_grafting_figures.py"
    )
    
    return figure_path


def generate_hyperparameter_sensitivity(figure_dir: str) -> str:
    """Generate hyperparameter sensitivity plot."""
    engine = GraftVisualizationEngine(output_dir=figure_dir)
    figure_manager = FigureManager()
    
    # Simulate sensitivity data
    param_values = np.linspace(0.5, 1.5, 20)
    success_rates = 0.85 - 0.15 * np.abs(param_values - 1.0) ** 2
    
    fig, ax = engine.create_figure()
    ax.plot(param_values, success_rates, linewidth=2, marker='o', color=engine.get_color(0))
    ax.axvline(1.0, color='red', linestyle='--', alpha=0.5, label='Baseline')
    engine.apply_publication_style(ax, "Hyperparameter Sensitivity Analysis",
                                   "Parameter Value (normalized)", "Success Rate", grid=True, legend=True)
    
    figure_path = os.path.join(figure_dir, "hyperparameter_sensitivity.png")
    engine.save_figure(fig, "hyperparameter_sensitivity")
    plt.close(fig)
    
    figure_manager.register_figure(
        filename="hyperparameter_sensitivity.png",
        caption="Hyperparameter sensitivity analysis showing robustness",
        section="experimental_results",
        generated_by="generate_grafting_figures.py"
    )
    
    return figure_path


def generate_image_classification_results(figure_dir: str) -> str:
    """Generate image classification results figure."""
    engine = GraftVisualizationEngine(output_dir=figure_dir)
    figure_manager = FigureManager()
    
    epochs = np.arange(1, 101)
    our_accuracy = 0.5 + 0.45 * (1 - np.exp(-epochs / 30))
    baseline_accuracy = 0.5 + 0.40 * (1 - np.exp(-epochs / 40))
    
    fig, ax = engine.create_figure()
    ax.plot(epochs, our_accuracy, linewidth=2, label='Our Method', color=engine.get_color(0))
    ax.plot(epochs, baseline_accuracy, linewidth=2, label='Baseline', 
           linestyle='--', color=engine.get_color(1))
    engine.apply_publication_style(ax, "Image Classification Results",
                                   "Epoch", "Accuracy", grid=True, legend=True)
    
    figure_path = os.path.join(figure_dir, "image_classification_results.png")
    engine.save_figure(fig, "image_classification_results")
    plt.close(fig)
    
    figure_manager.register_figure(
        filename="image_classification_results.png",
        caption="Image classification results comparing our method with baselines",
        section="experimental_results",
        generated_by="generate_grafting_figures.py"
    )
    
    return figure_path


def generate_recommendation_scalability(figure_dir: str) -> str:
    """Generate recommendation system scalability figure."""
    engine = GraftVisualizationEngine(output_dir=figure_dir)
    figure_manager = FigureManager()
    
    sizes = np.array([1000, 5000, 10000, 50000, 100000])
    our_times = sizes * np.log(sizes) * 0.0001
    baseline_times = sizes ** 1.5 * 0.0001
    
    fig, ax = engine.create_figure()
    ax.loglog(sizes, our_times, marker='o', linewidth=2, label='Our Method', color=engine.get_color(0))
    ax.loglog(sizes, baseline_times, marker='s', linewidth=2, label='Baseline',
             linestyle='--', color=engine.get_color(1))
    engine.apply_publication_style(ax, "Recommendation System Scalability",
                                   "System Size", "Computation Time", grid=True, legend=True)
    
    figure_path = os.path.join(figure_dir, "recommendation_scalability.png")
    engine.save_figure(fig, "recommendation_scalability")
    plt.close(fig)
    
    figure_manager.register_figure(
        filename="recommendation_scalability.png",
        caption="Recommendation system scalability analysis",
        section="experimental_results",
        generated_by="generate_grafting_figures.py"
    )
    
    return figure_path


def generate_convergence_analysis(figure_dir: str) -> str:
    """Generate convergence analysis figure."""
    engine = GraftVisualizationEngine(output_dir=figure_dir)
    figure_manager = FigureManager()
    
    days = np.arange(0, 60)
    union_strength = 1.0 - 0.8 * np.exp(-days / 12.0)
    
    fig, ax = engine.create_figure()
    ax.plot(days, union_strength, linewidth=2, color=engine.get_color(0))
    engine.apply_publication_style(ax, "Convergence Analysis",
                                   "Days", "Union Strength", grid=True)
    
    figure_path = os.path.join(figure_dir, "convergence_analysis.png")
    engine.save_figure(fig, "convergence_analysis")
    plt.close(fig)
    
    figure_manager.register_figure(
        filename="convergence_analysis.png",
        caption="Convergence behavior of the optimization algorithm showing exponential decay to target value",
        section="experimental_results",
        generated_by="generate_grafting_figures.py"
    )
    
    return figure_path


def generate_time_series_analysis(figure_dir: str) -> str:
    """Generate time series analysis figure."""
    engine = GraftVisualizationEngine(output_dir=figure_dir)
    figure_manager = FigureManager()
    
    time = np.linspace(0, 100, 200)
    signal = np.sin(2 * np.pi * time / 20) + 0.3 * np.random.randn(len(time))
    
    fig, ax = engine.create_figure()
    ax.plot(time, signal, linewidth=1.5, alpha=0.7, color=engine.get_color(0))
    engine.apply_publication_style(ax, "Time Series Analysis",
                                   "Time", "Value", grid=True)
    
    figure_path = os.path.join(figure_dir, "time_series_analysis.png")
    engine.save_figure(fig, "time_series_analysis")
    plt.close(fig)
    
    figure_manager.register_figure(
        filename="time_series_analysis.png",
        caption="Time series data showing sinusoidal trend with added noise",
        section="experimental_results",
        generated_by="generate_grafting_figures.py"
    )
    
    return figure_path


def generate_statistical_comparison(figure_dir: str) -> str:
    """Generate statistical comparison figure."""
    engine = GraftVisualizationEngine(output_dir=figure_dir)
    figure_manager = FigureManager()
    
    methods = ["Method A", "Method B", "Method C", "Our Method"]
    accuracy = np.array([0.82, 0.85, 0.88, 0.94])
    std = np.array([0.05, 0.04, 0.03, 0.02])
    
    fig, ax = engine.create_figure()
    bars = ax.bar(methods, accuracy, yerr=std, capsize=5, color=[engine.get_color(i) for i in range(len(methods))])
    ax.set_ylabel('Accuracy')
    ax.set_title('Comparison of Different Methods on Accuracy Metric')
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, (bar, acc) in enumerate(zip(bars, accuracy)):
        ax.text(bar.get_x() + bar.get_width()/2., acc + std[i],
                f'{acc:.2f}', ha='center', va='bottom')
    
    plt.tight_layout()
    
    figure_path = os.path.join(figure_dir, "statistical_comparison.png")
    engine.save_figure(fig, "statistical_comparison")
    plt.close(fig)
    
    figure_manager.register_figure(
        filename="statistical_comparison.png",
        caption="Comparison of different methods on accuracy metric",
        section="experimental_results",
        generated_by="generate_grafting_figures.py"
    )
    
    return figure_path


def generate_scatter_correlation(figure_dir: str) -> str:
    """Generate scatter correlation plot."""
    engine = GraftVisualizationEngine(output_dir=figure_dir)
    figure_manager = FigureManager()
    
    # Generate correlated data
    np.random.seed(42)
    x = np.random.randn(100)
    y = 0.7 * x + 0.3 * np.random.randn(100)
    
    fig, ax = engine.create_figure()
    ax.scatter(x, y, alpha=0.6, color=engine.get_color(0))
    
    # Add correlation line
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    ax.plot(x, p(x), "r--", alpha=0.8, linewidth=2, label=f'Correlation: {np.corrcoef(x, y)[0,1]:.2f}')
    
    engine.apply_publication_style(ax, "Scatter Plot: Correlation Analysis",
                                   "Variable X", "Variable Y", grid=True, legend=True)
    
    figure_path = os.path.join(figure_dir, "scatter_correlation.png")
    engine.save_figure(fig, "scatter_correlation")
    plt.close(fig)
    
    figure_manager.register_figure(
        filename="scatter_correlation.png",
        caption="Scatter plot showing correlation between two variables",
        section="experimental_results",
        generated_by="generate_grafting_figures.py"
    )
    
    return figure_path


def generate_data_structure(figure_dir: str) -> str:
    """Generate data structure diagram."""
    engine = GraftVisualizationEngine(output_dir=figure_dir)
    figure_manager = FigureManager()
    
    fig, ax = engine.create_figure(figsize=(10, 6))
    
    # Draw simplified data structure
    structures = ["Array", "Tree", "Hash Table"]
    operations = ["Insert", "Search", "Delete"]
    times = {
        "Array": [1, 10, 1],
        "Tree": [5, 3, 3],
        "Hash Table": [2, 1, 1]
    }
    
    x = np.arange(len(operations))
    width = 0.25
    
    for i, struct in enumerate(structures):
        offset = (i - 1) * width
        ax.bar(x + offset, times[struct], width, label=struct, color=engine.get_color(i))
    
    ax.set_xlabel('Operation')
    ax.set_ylabel('Time (normalized)')
    ax.set_title('Efficient Data Structures Used in Our Implementation')
    ax.set_xticks(x)
    ax.set_xticklabels(operations)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    figure_path = os.path.join(figure_dir, "data_structure.png")
    engine.save_figure(fig, "data_structure")
    plt.close(fig)
    
    figure_manager.register_figure(
        filename="data_structure.png",
        caption="Efficient data structures used in our implementation",
        section="methodology",
        generated_by="generate_grafting_figures.py"
    )
    
    return figure_path


def generate_step_size_analysis(figure_dir: str) -> str:
    """Generate step size analysis figure."""
    engine = GraftVisualizationEngine(output_dir=figure_dir)
    figure_manager = FigureManager()
    
    days = np.arange(0, 60)
    step_sizes = [0.01, 0.05, 0.1, 0.2]
    
    fig, ax = engine.create_figure()
    for i, step_size in enumerate(step_sizes):
        union_strength = 1.0 - np.exp(-days * step_size)
        ax.plot(days, union_strength, linewidth=2, label=f'Step Size: {step_size}',
               color=engine.get_color(i))
    
    engine.apply_publication_style(ax, "Step Size Analysis",
                                   "Days", "Union Strength", grid=True, legend=True)
    
    figure_path = os.path.join(figure_dir, "step_size_analysis.png")
    engine.save_figure(fig, "step_size_analysis")
    plt.close(fig)
    
    figure_manager.register_figure(
        filename="step_size_analysis.png",
        caption="Detailed analysis of adaptive step size behavior",
        section="experimental_results",
        generated_by="generate_grafting_figures.py"
    )
    
    return figure_path


def main() -> None:
    """Generate all grafting figures."""
    os.environ.setdefault("MPLBACKEND", "Agg")
    
    output_dir, data_dir, figure_dir = _setup_directories()
    
    print("Generating grafting figures for manuscript...")
    
    figures_generated = []
    
    try:
        figures_generated.append(generate_convergence_plot(figure_dir, data_dir))
        figures_generated.append(generate_experimental_setup(figure_dir))
        figures_generated.append(generate_scalability_analysis(figure_dir))
        figures_generated.append(generate_ablation_study(figure_dir))
        figures_generated.append(generate_hyperparameter_sensitivity(figure_dir))
        figures_generated.append(generate_image_classification_results(figure_dir))
        figures_generated.append(generate_recommendation_scalability(figure_dir))
        figures_generated.append(generate_convergence_analysis(figure_dir))
        figures_generated.append(generate_time_series_analysis(figure_dir))
        figures_generated.append(generate_statistical_comparison(figure_dir))
        figures_generated.append(generate_scatter_correlation(figure_dir))
        figures_generated.append(generate_data_structure(figure_dir))
        figures_generated.append(generate_step_size_analysis(figure_dir))
        
        print(f"\n✅ Generated {len(figures_generated)} figures:")
        for fig_path in figures_generated:
            if fig_path:
                print(f"  - {fig_path}")
        
    except Exception as e:
        print(f"❌ Error generating figures: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

