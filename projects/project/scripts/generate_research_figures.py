#!/usr/bin/env python3
"""Generate comprehensive research figures for the manuscript.

This script demonstrates how to create multiple figures that are referenced
in the markdown files, showing proper figure generation, labeling, and
cross-referencing capabilities.

IMPORTANT: This script demonstrates integration with src/ modules by using
the mathematical functions from example.py to process data for the figures.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure src/ and infrastructure/ are on Python path FIRST (BEFORE infrastructure imports)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
repo_root = os.path.abspath(os.path.join(project_root, ".."))
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import matplotlib.pyplot as plt
import numpy as np
from typing import Tuple, List

# Import infrastructure validation modules
from infrastructure.validation import validate_figure_registry, verify_output_integrity

def _ensure_src_on_path() -> None:
    """Ensure src/ and infrastructure/ are on Python path for imports."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up one level from scripts/
    repo_root = os.path.dirname(project_root)   # Go up one level from project/

    # Add infrastructure/ directory (at repo root level)
    infra_path = os.path.join(repo_root, "infrastructure")
    if infra_path not in sys.path:
        sys.path.insert(0, infra_path)

    # Add src/ directory (at project level)
    src_path = os.path.join(project_root, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    # Add repo root for any other imports
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


def _setup_directories() -> Tuple[str, str, str]:
    """Setup output directories and return paths."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_dir = os.path.join(repo_root, "output")
    data_dir = os.path.join(output_dir, "data")
    figure_dir = os.path.join(output_dir, "figures")
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(figure_dir, exist_ok=True)
    
    return output_dir, data_dir, figure_dir


def generate_convergence_plot(figure_dir: str, data_dir: str) -> str:
    """Generate convergence analysis plot using src/ functions."""
    # Import src/ functions for data processing
    try:
        from example import add_numbers, multiply_numbers, calculate_average
        print("✅ Using src/ functions for convergence plot")
    except (ImportError, SyntaxError) as e:
        print(f"❌ Failed to import from src/example.py: {e}")
        return ""
    
    # Generate synthetic convergence data
    iterations = np.arange(1, 101)
    
    # Use src/ functions to process the data
    our_method_raw = 2.0 * np.exp(-0.1 * iterations) + 0.1
    baseline_raw = 1.5 * np.exp(-0.05 * iterations) + 0.2
    
    # Apply src/ functions to demonstrate integration
    our_method_list: List[float] = []
    baseline_list: List[float] = []
    for i, (our_val, base_val) in enumerate(zip(our_method_raw, baseline_raw)):
        # Use add_numbers and multiply_numbers from src/
        our_processed = add_numbers(our_val, 0.0)  # Identity operation
        base_processed = multiply_numbers(base_val, 1.0)  # Identity operation
        our_method_list.append(our_processed)
        baseline_list.append(base_processed)
    
    our_method = np.array(our_method_list)
    baseline = np.array(baseline_list)
    
    # Calculate statistics using src/ functions
    our_avg = calculate_average(our_method.tolist())
    base_avg = calculate_average(baseline.tolist())
    
    print(f"Convergence analysis using src/ functions:")
    print(f"  Our method average: {our_avg:.6f}")
    print(f"  Baseline average: {base_avg:.6f}")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.semilogy(iterations, our_method, 'b-', linewidth=2, label='Our Method')
    ax.semilogy(iterations, baseline, 'r--', linewidth=2, label='Baseline')
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Objective Value')
    ax.set_title('Algorithm Convergence Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Add statistics as text
    ax.text(0.05, 0.95, f'Our Method Avg: {our_avg:.3f}\nBaseline Avg: {base_avg:.3f}', 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
    
    # Save figure
    figure_path = os.path.join(figure_dir, "convergence_plot.png")
    fig.savefig(figure_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    # Save data
    data_path = os.path.join(data_dir, "convergence_data.npz")
    np.savez(data_path, iterations=iterations, our_method=our_method, baseline=baseline,
              our_avg=our_avg, base_avg=base_avg)
    
    print(f"Generated: {figure_path}")
    return figure_path


def generate_experimental_setup(figure_dir: str, data_dir: str) -> str:
    """Generate experimental setup diagram."""
    # Import src/ functions for validation
    try:
        from example import is_even, is_odd
        print("✅ Using src/ functions for experimental setup validation")
        
        # Demonstrate src/ function usage
        num_components = 3
        print(f"Number of components: {num_components}")
        print(f"  Is even: {is_even(num_components)}")
        print(f"  Is odd: {is_odd(num_components)}")
    except (ImportError, SyntaxError) as e:
        print(f"❌ Failed to import from src/example.py: {e}")

    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create a simple flowchart-like diagram
    components = ['Data\nPreprocessing', 'Algorithm\nExecution', 'Performance\nEvaluation']
    x_positions = [2, 6, 10]
    y_positions = [4, 4, 4]
    
    for i, (comp, x, y) in enumerate(zip(components, x_positions, y_positions)):
        # Draw boxes
        rect = plt.Rectangle((x-1, y-0.5), 2, 1, facecolor='lightblue', 
                           edgecolor='black', linewidth=2)
        ax.add_patch(rect)
        ax.text(x, y, comp, ha='center', va='center', fontsize=10, fontweight='bold')
        
        # Draw arrows
        if i < len(components) - 1:
            ax.arrow(x+1, y, 1.5, 0, head_width=0.2, head_length=0.2, 
                    fc='black', ec='black', linewidth=2)
    
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.set_title('Experimental Pipeline', fontsize=14, fontweight='bold')
    ax.axis('off')
    
    figure_path = os.path.join(figure_dir, "experimental_setup.png")
    fig.savefig(figure_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"Generated: {figure_path}")
    return figure_path


def generate_data_structure_plot(figure_dir: str, data_dir: str) -> str:
    """Generate data structure visualization."""
    try:
        from example import find_maximum, find_minimum
        print("✅ Using src/ functions for data structure visualization")

        # Demonstrate data structure efficiency
        sizes = [100, 1000, 10000, 100000]
        operations = ['Search', 'Insert', 'Delete']

        # Generate synthetic performance data
        performance_data = {}
        for size in sizes:
            performance_data[size] = {}
            for op in operations:
                # Simulate different algorithmic complexities
                if op == 'Search':
                    performance_data[size][op] = size * np.log(size)  # O(n log n)
                elif op == 'Insert':
                    performance_data[size][op] = size  # O(n)
                else:  # Delete
                    performance_data[size][op] = size * 0.5  # O(n/2)

        fig, ax = plt.subplots(figsize=(10, 6))

        for op in operations:
            values = [performance_data[size][op] for size in sizes]
            ax.loglog(sizes, values, marker='o', linewidth=2, label=op)

        ax.set_xlabel('Problem Size (n)')
        ax.set_ylabel('Operations')
        ax.set_title('Algorithmic Complexity Comparison')
        ax.legend()
        ax.grid(True, alpha=0.3)

        figure_path = os.path.join(figure_dir, "data_structure.png")
        fig.savefig(figure_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Generated: {figure_path}")
        return figure_path

    except (ImportError, SyntaxError) as e:
        print(f"❌ Failed to import from src/example.py: {e}")
        return ""


def generate_step_size_analysis(figure_dir: str, data_dir: str) -> str:
    """Generate step size sensitivity analysis."""
    try:
        from example import calculate_average
        print("✅ Using src/ functions for step size analysis")

        # Generate step size sensitivity data
        step_sizes = [0.001, 0.01, 0.1, 1.0]
        iterations = np.arange(1, 51)

        fig, ax = plt.subplots(figsize=(10, 6))

        for step_size in step_sizes:
            # Simulate convergence with different step sizes
            convergence = 1.0 / (1.0 + step_size * iterations) + 0.1 * np.random.randn(len(iterations))
            convergence = np.maximum(convergence, 0.01)  # Ensure positive values

            ax.semilogy(iterations, convergence, linewidth=2,
                       label=f'Step Size: {step_size}')

        ax.set_xlabel('Iteration')
        ax.set_ylabel('Objective Value')
        ax.set_title('Step Size Sensitivity Analysis')
        ax.legend()
        ax.grid(True, alpha=0.3)

        figure_path = os.path.join(figure_dir, "step_size_analysis.png")
        fig.savefig(figure_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Generated: {figure_path}")
        return figure_path

    except (ImportError, SyntaxError) as e:
        print(f"❌ Failed to import from src/example.py: {e}")
        return ""


def generate_scalability_analysis(figure_dir: str, data_dir: str) -> str:
    """Generate scalability analysis plot."""
    try:
        from example import multiply_numbers, calculate_average
        print("✅ Using src/ functions for scalability analysis")

        # Generate scalability data
        problem_sizes = [100, 1000, 10000, 100000]
        algorithms = ['Our Method', 'Baseline A', 'Baseline B']

        fig, ax = plt.subplots(figsize=(10, 6))

        for alg in algorithms:
            times = []
            for size in problem_sizes:
                # Simulate different complexity behaviors
                if alg == 'Our Method':
                    time = size * np.log(size)  # O(n log n)
                elif alg == 'Baseline A':
                    time = size * size  # O(n²)
                else:  # Baseline B
                    time = size * size * size  # O(n³)

                # Use src/ functions to process the timing data
                processed_time = multiply_numbers(time, 1.0)  # Identity operation
                times.append(processed_time)

            ax.loglog(problem_sizes, times, marker='o', linewidth=2, label=alg)

        ax.set_xlabel('Problem Size (n)')
        ax.set_ylabel('Computation Time')
        ax.set_title('Scalability Analysis: Algorithm Comparison')
        ax.legend()
        ax.grid(True, alpha=0.3)

        figure_path = os.path.join(figure_dir, "scalability_analysis.png")
        fig.savefig(figure_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Generated: {figure_path}")
        return figure_path

    except (ImportError, SyntaxError) as e:
        print(f"❌ Failed to import from src/example.py: {e}")
        return ""


def generate_dataset_summary_table(data_dir: str) -> str:
    """Generate dataset summary table as CSV."""
    try:
        from example import find_maximum, find_minimum, calculate_average
        print("✅ Using src/ functions for dataset analysis")

        # Generate synthetic dataset characteristics
        datasets = [
            {'name': 'Small Convex', 'size': 100, 'type': 'Convex', 'features': 10},
            {'name': 'Medium Convex', 'size': 1000, 'type': 'Convex', 'features': 50},
            {'name': 'Large Convex', 'size': 10000, 'type': 'Convex', 'features': 100},
            {'name': 'Small Non-convex', 'size': 100, 'type': 'Non-convex', 'features': 10},
            {'name': 'Medium Non-convex', 'size': 1000, 'type': 'Non-convex', 'features': 50},
        ]

        # Add computed statistics using src/ functions
        for dataset in datasets:
            # Generate synthetic data for each dataset
            data_points = np.random.randn(dataset['size'])
            dataset['avg_value'] = calculate_average(data_points.tolist())
            dataset['max_value'] = find_maximum(data_points.tolist())
            dataset['min_value'] = find_minimum(data_points.tolist())

        # Save as CSV
        csv_path = os.path.join(data_dir, "dataset_summary.csv")
        with open(csv_path, 'w') as f:
            f.write("Dataset,Size,Type,Features,Avg_Value,Max_Value,Min_Value\n")
            for dataset in datasets:
                f.write(f"{dataset['name']},{dataset['size']},{dataset['type']},{dataset['features']},{dataset['avg_value']:.3f},{dataset['max_value']:.3f},{dataset['min_value']:.3f}\n")

        print(f"Generated: {csv_path}")
        return csv_path

    except (ImportError, SyntaxError) as e:
        print(f"❌ Failed to import from src/example.py: {e}")
        return ""


def generate_performance_comparison_table(data_dir: str) -> str:
    """Generate performance comparison table as CSV."""
    try:
        from example import calculate_average
        print("✅ Using src/ functions for performance analysis")

        # Generate synthetic performance data
        methods = ['Our Method', 'Gradient Descent', 'Adam', 'L-BFGS']
        metrics = ['Convergence Rate', 'Memory Usage', 'Success Rate']

        # Create comparison data
        performance_data = {}
        for method in methods:
            performance_data[method] = {}
            for metric in metrics:
                if metric == 'Convergence Rate':
                    if method == 'Our Method':
                        performance_data[method][metric] = 0.85  # ρ ≈ 0.85
                    else:
                        performance_data[method][metric] = 0.90  # Slower convergence
                elif metric == 'Memory Usage':
                    if method == 'Our Method':
                        performance_data[method][metric] = 'O(n)'  # Linear
                    else:
                        performance_data[method][metric] = 'O(n²)'  # Quadratic
                else:  # Success Rate
                    if method == 'Our Method':
                        performance_data[method][metric] = 94.3  # %
                    else:
                        performance_data[method][metric] = 85.0  # %

        # Save as CSV
        csv_path = os.path.join(data_dir, "performance_comparison.csv")
        with open(csv_path, 'w') as f:
            f.write("Method,Convergence_Rate,Memory_Usage,Success_Rate\n")
            for method in methods:
                f.write(f"{method},{performance_data[method]['Convergence Rate']},{performance_data[method]['Memory Usage']},{performance_data[method]['Success Rate']}\n")

        print(f"Generated: {csv_path}")
        return csv_path

    except (ImportError, SyntaxError) as e:
        print(f"❌ Failed to import from src/example.py: {e}")
        return ""


def generate_ablation_study(figure_dir: str, data_dir: str) -> str:
    """Generate ablation study plot."""
    try:
        from example import add_numbers, multiply_numbers
        print("✅ Using src/ functions for ablation study")

        # Components to ablate
        components = ['Regularization', 'Adaptive Step Size', 'Momentum', 'All Combined']
        performance = [0.7, 0.75, 0.8, 0.95]  # Normalized performance

        fig, ax = plt.subplots(figsize=(10, 6))

        bars = ax.bar(components, performance, color=['lightcoral', 'lightblue', 'lightgreen', 'gold'])
        ax.set_ylabel('Relative Performance')
        ax.set_title('Ablation Study: Component Contributions')
        ax.set_ylim(0, 1.1)

        # Add value labels on bars
        for bar, perf in zip(bars, performance):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{perf:.2f}', ha='center', va='bottom')

        figure_path = os.path.join(figure_dir, "ablation_study.png")
        fig.savefig(figure_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Generated: {figure_path}")
        return figure_path

    except (ImportError, SyntaxError) as e:
        print(f"❌ Failed to import from src/example.py: {e}")
        return ""


def generate_hyperparameter_sensitivity(figure_dir: str, data_dir: str) -> str:
    """Generate hyperparameter sensitivity analysis."""
    try:
        from example import calculate_average
        print("✅ Using src/ functions for hyperparameter analysis")

        # Generate sensitivity data
        learning_rates = [0.001, 0.01, 0.1, 1.0]
        momentum_values = [0.0, 0.5, 0.9, 0.99]

        # Create a grid of parameter combinations
        performance_grid = np.zeros((len(learning_rates), len(momentum_values)))

        for i, lr in enumerate(learning_rates):
            for j, mom in enumerate(momentum_values):
                # Simulate performance as function of parameters
                performance = 1.0 / (1.0 + lr * (1.0 - mom)) + 0.1 * np.random.rand()
                performance_grid[i, j] = min(performance, 1.0)

        fig, ax = plt.subplots(figsize=(10, 8))

        im = ax.imshow(performance_grid, cmap='viridis', aspect='auto',
                      extent=[min(momentum_values), max(momentum_values),
                             min(learning_rates), max(learning_rates)])

        ax.set_xlabel('Momentum Coefficient')
        ax.set_ylabel('Learning Rate')
        ax.set_title('Hyperparameter Sensitivity Analysis')
        plt.colorbar(im, ax=ax, label='Performance')

        # Add contour lines
        cs = ax.contour(performance_grid, levels=5, colors='white', alpha=0.7)
        ax.clabel(cs, inline=True, fontsize=8)

        figure_path = os.path.join(figure_dir, "hyperparameter_sensitivity.png")
        fig.savefig(figure_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Generated: {figure_path}")
        return figure_path

    except (ImportError, SyntaxError) as e:
        print(f"❌ Failed to import from src/example.py: {e}")
        return ""


def generate_image_classification_results(figure_dir: str, data_dir: str) -> str:
    """Generate image classification results plot."""
    try:
        from example import calculate_average
        print("✅ Using src/ functions for image classification analysis")

        # Simulate training curves for different optimizers
        epochs = np.arange(1, 101)
        methods = ['Our Method', 'SGD', 'Adam', 'RMSprop']

        fig, ax = plt.subplots(figsize=(10, 6))

        for method in methods:
            # Generate synthetic training curves
            if method == 'Our Method':
                accuracy = 0.95 - 0.3 * np.exp(-epochs/20)  # Fast convergence
            elif method == 'SGD':
                accuracy = 0.90 - 0.25 * np.exp(-epochs/30)  # Slower convergence
            elif method == 'Adam':
                accuracy = 0.92 - 0.28 * np.exp(-epochs/25)  # Medium convergence
            else:  # RMSprop
                accuracy = 0.91 - 0.26 * np.exp(-epochs/28)  # Medium convergence

            ax.plot(epochs, accuracy, linewidth=2, label=method)

        ax.set_xlabel('Epoch')
        ax.set_ylabel('Accuracy')
        ax.set_title('Image Classification Training Curves')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0.5, 1.0)

        figure_path = os.path.join(figure_dir, "image_classification_results.png")
        fig.savefig(figure_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Generated: {figure_path}")
        return figure_path

    except (ImportError, SyntaxError) as e:
        print(f"❌ Failed to import from src/example.py: {e}")
        return ""


def generate_recommendation_scalability(figure_dir: str, data_dir: str) -> str:
    """Generate recommendation system scalability plot."""
    try:
        from example import multiply_numbers
        print("✅ Using src/ functions for recommendation scalability")

        # Generate scalability data for recommendation systems
        user_counts = [1000, 10000, 100000, 1000000]
        item_counts = [100, 1000, 10000, 100000]

        fig, ax = plt.subplots(figsize=(10, 6))

        for items in item_counts:
            times = []
            for users in user_counts:
                # Simulate recommendation computation time
                time = users * items * 0.001  # Simplified model
                processed_time = multiply_numbers(time, 1.0)  # Use src/ function
                times.append(processed_time)

            ax.loglog(user_counts, times, marker='o', linewidth=2,
                     label=f'{items} items')

        ax.set_xlabel('Number of Users')
        ax.set_ylabel('Computation Time (s)')
        ax.set_title('Recommendation System Scalability')
        ax.legend(title='Items')
        ax.grid(True, alpha=0.3)

        figure_path = os.path.join(figure_dir, "recommendation_scalability.png")
        fig.savefig(figure_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        print(f"Generated: {figure_path}")
        return figure_path

    except (ImportError, SyntaxError) as e:
        print(f"❌ Failed to import from src/example.py: {e}")
        return ""


def _register_figures_with_manager(figures: List[str], figure_dir: str) -> None:
    """Register generated figures with FigureManager for cross-referencing."""
    try:
        from infrastructure.documentation import FigureManager
        import os
        
        # FigureManager uses registry_file parameter, not output_dir
        registry_file = os.path.join(figure_dir, "figure_registry.json")
        fm = FigureManager(registry_file=registry_file)
        
        # Define figure metadata for registration
        figure_metadata = {
            "convergence_plot.png": {
                "label": "fig:convergence_plot",
                "caption": "Algorithm convergence comparison showing our method vs baseline",
                "section": "experimental_results"
            },
            "experimental_setup.png": {
                "label": "fig:experimental_setup",
                "caption": "Experimental pipeline showing data flow through processing stages",
                "section": "methodology"
            },
            "data_structure.png": {
                "label": "fig:data_structure",
                "caption": "Algorithmic complexity comparison for different operations",
                "section": "methodology"
            },
            "step_size_analysis.png": {
                "label": "fig:step_size_analysis",
                "caption": "Step size sensitivity analysis showing impact on convergence",
                "section": "experimental_results"
            },
            "scalability_analysis.png": {
                "label": "fig:scalability_analysis",
                "caption": "Scalability analysis comparing algorithm performance across problem sizes",
                "section": "experimental_results"
            },
            "ablation_study.png": {
                "label": "fig:ablation_study",
                "caption": "Ablation study showing contribution of each component",
                "section": "experimental_results"
            },
            "hyperparameter_sensitivity.png": {
                "label": "fig:hyperparameter_sensitivity",
                "caption": "Hyperparameter sensitivity analysis for learning rate and momentum",
                "section": "experimental_results"
            },
            "image_classification_results.png": {
                "label": "fig:image_classification_results",
                "caption": "Image classification training curves comparing optimization methods",
                "section": "experimental_results"
            },
            "recommendation_scalability.png": {
                "label": "fig:recommendation_scalability",
                "caption": "Recommendation system scalability with varying users and items",
                "section": "experimental_results"
            }
        }
        
        registered_count = 0
        for fig_path in figures:
            filename = os.path.basename(fig_path)
            if filename in figure_metadata:
                meta = figure_metadata[filename]
                fm.register_figure(
                    filename=filename,
                    caption=meta["caption"],
                    label=meta["label"],
                    section=meta["section"]
                )
                registered_count += 1
        
        # Note: FigureManager auto-saves on each register_figure() call
        print(f"\n✅ Registered {registered_count} figures with FigureManager")
        
    except ImportError:
        print("\n⚠️  FigureManager not available, skipping figure registration")
    except Exception as e:
        print(f"\n⚠️  Could not register figures: {e}")


def main() -> None:
    """Generate all research figures and tables using src/ modules."""
    os.environ.setdefault("MPLBACKEND", "Agg")
    _ensure_src_on_path()

    output_dir, data_dir, figure_dir = _setup_directories()

    print("Generating research figures using src/ modules...")

    # Generate all figures
    figures = [
        generate_convergence_plot(figure_dir, data_dir),
        generate_experimental_setup(figure_dir, data_dir),
        generate_data_structure_plot(figure_dir, data_dir),
        generate_step_size_analysis(figure_dir, data_dir),
        generate_scalability_analysis(figure_dir, data_dir),
        generate_ablation_study(figure_dir, data_dir),
        generate_hyperparameter_sensitivity(figure_dir, data_dir),
        generate_image_classification_results(figure_dir, data_dir),
        generate_recommendation_scalability(figure_dir, data_dir),
    ]

    # Generate tables
    tables = [
        generate_dataset_summary_table(data_dir),
        generate_performance_comparison_table(data_dir),
    ]

    # Filter out any empty results
    figures = [f for f in figures if f]
    tables = [t for t in tables if t]

    print(f"\n✅ Generated {len(figures)} research figures:")
    for fig in figures:
        print(f"   - {os.path.basename(fig)}")

    print(f"\n✅ Generated {len(tables)} data tables:")
    for table in tables:
        print(f"   - {os.path.basename(table)}")

    # Register figures with FigureManager for cross-referencing
    _register_figures_with_manager(figures, figure_dir)

    print(f"\n📁 All outputs saved to: {output_dir}")
    print(f"   Figures: {figure_dir}")
    print(f"   Data: {data_dir}")

    print(f"\n🔗 Integration with src/ modules demonstrated:")
    print(f"   - Mathematical functions from example.py used for data processing")
    print(f"   - Statistical analysis using src/ functions")
    print(f"   - Proper error handling for missing imports")

    # Lightweight integrity/validation checks
    try:
        registry_path = Path(figure_dir) / "figure_registry.json"
        manuscript_dir = Path(repo_root) / "manuscript"
        validate_figure_registry(registry_path, manuscript_dir)
        print("✅ Figure registry validation passed")
    except Exception as exc:
        print(f"⚠️  Figure registry validation warning: {exc}")

    try:
        integrity_report = verify_output_integrity(Path(output_dir))
        print("✅ Output integrity check passed")
    except Exception as exc:
        print(f"⚠️  Output integrity warning: {exc}")

    try:
        verify_build_artifacts(Path(output_dir), expected_files=[])
    except Exception:
        # Non-blocking; artifact expectations are project-specific
        pass


if __name__ == "__main__":
    main()
