#!/usr/bin/env python3
"""Optimization analysis script.

This script demonstrates the analysis capabilities by:
1. Running optimization experiments
2. Generating convergence plots
3. Saving numerical results
4. Registering figures for the manuscript
"""
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Any, Optional

# Add project src to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from optimizer import (
    quadratic_function,
    compute_gradient,
    gradient_descent,
    OptimizationResult,
)

# Add infrastructure imports for scientific analysis
try:
    # Ensure repo root is on path for infrastructure imports
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root))

    from infrastructure.scientific import (
        check_numerical_stability,
        benchmark_function,
    )
    from infrastructure.reporting import (
        generate_output_summary,
        get_error_aggregator,
        collect_output_statistics,
    )
    from infrastructure.publishing import (
        extract_publication_metadata,
        generate_citation_bibtex,
        generate_citation_apa,
        generate_citation_mla,
    )
    from infrastructure.publishing.models import PublicationMetadata
    from infrastructure.validation import (
        verify_output_integrity,
        generate_integrity_report,
    )
    from infrastructure.core import (
        monitor_performance,
        ProgressBar,
        get_logger,
        log_operation,
        log_success,
        log_stage,
    )
    from infrastructure.core.exceptions import (
        TemplateError,
        ScriptExecutionError,
    )
    INFRASTRUCTURE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Infrastructure modules not available: {e}")
    INFRASTRUCTURE_AVAILABLE = False


def run_convergence_experiment():
    """Run gradient descent with different step sizes and track convergence."""
    print("Running convergence experiments...")

    # Define test problem: f(x) = (1/2) x^2 - x, optimum at x = 1
    def obj_func(x):
        return quadratic_function(x, np.array([[1.0]]), np.array([1.0]))

    def grad_func(x):
        return compute_gradient(x, np.array([[1.0]]), np.array([1.0]))

    # Different step sizes to test
    step_sizes = [0.01, 0.05, 0.1, 0.2]
    initial_point = np.array([0.0])  # Start far from optimum

    results = {}

    for step_size in step_sizes:
        print(f"Testing step size: {step_size}")

        result = gradient_descent(
            initial_point=initial_point,
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=step_size,
            max_iterations=100,
            tolerance=1e-8,
            verbose=False
        )

        results[step_size] = result
        print(f"  Converged: {result.converged}, Final value: {result.objective_value:.4f}")
    return results


def run_convergence_experiment_with_progress(progress_bar):
    """Run gradient descent with different step sizes and track convergence with progress bar."""
    print("Running convergence experiments...")

    # Define test problem: f(x) = (1/2) x^2 - x, optimum at x = 1
    def obj_func(x):
        return quadratic_function(x, np.array([[1.0]]), np.array([1.0]))

    def grad_func(x):
        return compute_gradient(x, np.array([[1.0]]), np.array([1.0]))

    # Different step sizes to test
    step_sizes = [0.01, 0.05, 0.1, 0.2]
    initial_point = np.array([0.0])  # Start far from optimum

    results = {}

    for step_size in step_sizes:
        print(f"Testing step size: {step_size}")

        result = gradient_descent(
            initial_point=initial_point,
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=step_size,
            max_iterations=100,
            tolerance=1e-8,
            verbose=False
        )

        results[step_size] = result
        print(f"  Converged: {result.converged}, Final value: {result.objective_value:.4f}")

        # Update progress bar
        if progress_bar:
            progress_bar.update(1)

    return results


def generate_convergence_plot(results):
    """Generate convergence plot showing objective value vs iteration."""
    print("Generating convergence plot...")

    plt.figure(figsize=(10, 6))

    colors = ['blue', 'red', 'green', 'orange']
    step_sizes = list(results.keys())

    for i, step_size in enumerate(step_sizes):
        result = results[step_size]

        # Simulate the trajectory to get intermediate values
        trajectory = simulate_trajectory(step_size, max_iter=result.iterations + 10)

        plt.plot(trajectory['iterations'], trajectory['objectives'],
                color=colors[i], linewidth=2, label=f'α = {step_size}')

    plt.xlabel('Iteration')
    plt.ylabel('Objective Value f(x)')
    plt.title('Gradient Descent Convergence for Different Step Sizes')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Save plot
    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    plot_path = output_dir / "convergence_plot.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved convergence plot to: {plot_path}")
    return plot_path


def simulate_trajectory(step_size, max_iter=50):
    """Simulate gradient descent trajectory to collect intermediate values."""
    def obj_func(x):
        return quadratic_function(x, np.array([[1.0]]), np.array([1.0]))

    def grad_func(x):
        return compute_gradient(x, np.array([[1.0]]), np.array([1.0]))

    x = np.array([0.0])  # Initial point
    objectives = [obj_func(x)]
    iterations = [0]

    for i in range(max_iter):
        grad = grad_func(x)
        x = x - step_size * grad

        objectives.append(obj_func(x))
        iterations.append(i + 1)

        # Check for convergence
        if np.linalg.norm(grad) < 1e-8:
            break

    return {
        'iterations': iterations,
        'objectives': objectives
    }


def save_optimization_results(results):
    """Save optimization results to CSV file."""
    print("Saving optimization results...")

    output_dir = project_root / "output" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    data_path = output_dir / "optimization_results.csv"

    with open(data_path, 'w') as f:
        f.write("step_size,solution,objective_value,iterations,converged,gradient_norm\n")

        for step_size, result in results.items():
            f.write(f"{step_size},{result.solution[0]:.6f},{result.objective_value:.6f},"
                   f"{result.iterations},{result.converged},{result.gradient_norm:.2e}\n")

    print(f"Saved results to: {data_path}")
    return data_path


def generate_step_size_sensitivity_plot(results):
    """Generate plot showing step size sensitivity analysis."""
    print("Generating step size sensitivity plot...")

    step_sizes = list(results.keys())
    iterations = [results[step_size].iterations for step_size in step_sizes]
    objective_values = [results[step_size].objective_value for step_size in step_sizes]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Iterations vs step size
    ax1.plot(step_sizes, iterations, 'bo-', linewidth=2, markersize=8)
    ax1.set_xlabel('Step Size (α)')
    ax1.set_ylabel('Iterations to Convergence')
    ax1.set_title('Step Size vs Convergence Speed')
    ax1.grid(True, alpha=0.3)
    ax1.set_xscale('log')

    # Final objective value vs step size
    ax2.plot(step_sizes, objective_values, 'ro-', linewidth=2, markersize=8)
    ax2.axhline(y=-0.5, color='green', linestyle='--', alpha=0.7, label='Optimal Value (-0.5)')
    ax2.set_xlabel('Step Size (α)')
    ax2.set_ylabel('Final Objective Value')
    ax2.set_title('Step Size vs Solution Quality')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xscale('log')

    plt.tight_layout()

    # Save plot
    output_dir = project_root / "output" / "figures"
    plot_path = output_dir / "step_size_sensitivity.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved step size sensitivity plot to: {plot_path}")
    return plot_path


def generate_convergence_rate_plot(results):
    """Generate convergence rate comparison plot."""
    print("Generating convergence rate comparison plot...")

    plt.figure(figsize=(10, 6))

    colors = ['blue', 'red', 'green', 'orange']
    step_sizes = list(results.keys())

    for i, step_size in enumerate(step_sizes):
        # Simulate trajectory with more points for rate analysis
        trajectory = simulate_trajectory(step_size, max_iter=100)

        iterations = trajectory['iterations']
        objectives = trajectory['objectives']

        # Calculate error relative to optimal value (-0.5)
        errors = [abs(obj + 0.5) for obj in objectives]  # Absolute error

        # Only plot until convergence or reasonable iterations
        max_plot_iter = min(50, len(iterations))
        plt.plot(iterations[:max_plot_iter], errors[:max_plot_iter],
                color=colors[i], linewidth=2, label=f'α = {step_size}',
                marker='o', markersize=3, markevery=5)

    plt.xlabel('Iteration')
    plt.ylabel('Absolute Error |f(x) - f(x*)|')
    plt.title('Convergence Rate Comparison (Log Scale)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.yscale('log')
    plt.ylim(1e-8, 1e1)

    # Save plot
    output_dir = project_root / "output" / "figures"
    plot_path = output_dir / "convergence_rate_comparison.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved convergence rate comparison plot to: {plot_path}")
    return plot_path


def generate_complexity_visualization(results):
    """Generate algorithm complexity visualization."""
    print("Generating algorithm complexity visualization...")

    step_sizes = list(results.keys())
    iterations = [results[step_size].iterations for step_size in step_sizes]
    converged = [results[step_size].converged for step_size in step_sizes]

    # Calculate theoretical complexity metrics
    theoretical_complexity = []
    for step_size in step_sizes:
        # For quadratic functions, complexity relates to step size
        # Smaller step sizes require more iterations
        complexity = 1.0 / (2 * step_size * (1 - step_size)) if step_size < 0.5 else float('inf')
        theoretical_complexity.append(complexity)

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

    # Empirical iterations
    ax1.bar(range(len(step_sizes)), iterations,
            tick_label=[f'{s}' for s in step_sizes], color='skyblue')
    ax1.set_xlabel('Step Size (α)')
    ax1.set_ylabel('Iterations')
    ax1.set_title('Empirical Convergence Iterations')
    ax1.grid(True, alpha=0.3)

    # Convergence status
    colors = ['green' if c else 'red' for c in converged]
    ax2.bar(range(len(step_sizes)), [1 if c else 0 for c in converged],
            tick_label=[f'{s}' for s in step_sizes], color=colors)
    ax2.set_xlabel('Step Size (α)')
    ax2.set_ylabel('Converged (1=Yes, 0=No)')
    ax2.set_title('Convergence Success')
    ax2.set_ylim(-0.1, 1.1)
    ax2.grid(True, alpha=0.3)

    # Theoretical vs empirical comparison
    ax3.plot(step_sizes, iterations, 'bo-', linewidth=2, markersize=8, label='Empirical')
    ax3.plot(step_sizes, theoretical_complexity, 'r--', linewidth=2, markersize=8, label='Theoretical Estimate')
    ax3.set_xlabel('Step Size (α)')
    ax3.set_ylabel('Iterations')
    ax3.set_title('Theoretical vs Empirical Complexity')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, max(step_sizes) * 1.1)

    # Performance summary
    performance_scores = []
    for step_size, iters, conv in zip(step_sizes, iterations, converged):
        if conv:
            # Score based on iterations (lower is better) and stability
            score = 1.0 / (iters + 1)  # +1 to avoid division by zero
            if step_size >= 0.01 and step_size <= 0.2:  # Stable range
                score *= 1.2
        else:
            score = 0.0
        performance_scores.append(score)

    ax4.bar(range(len(step_sizes)), performance_scores,
            tick_label=[f'{s}' for s in step_sizes], color='purple', alpha=0.7)
    ax4.set_xlabel('Step Size (α)')
    ax4.set_ylabel('Performance Score')
    ax4.set_title('Overall Performance Ranking')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save plot
    output_dir = project_root / "output" / "figures"
    plot_path = output_dir / "algorithm_complexity.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved algorithm complexity visualization to: {plot_path}")
    return plot_path


def run_stability_analysis():
    """Assess numerical stability of optimization algorithms."""
    if not INFRASTRUCTURE_AVAILABLE:
        print("⚠️  Skipping stability analysis - infrastructure not available")
        return None

    print("Running numerical stability analysis...")

    # Define test function for stability analysis
    def test_func(x):
        return quadratic_function(x, np.array([[1.0]]), np.array([1.0]))

    # Test different input ranges for stability
    test_inputs = [
        np.array([0.0]),      # Standard start point
        np.array([10.0]),     # Far from optimum
        np.array([-5.0]),     # Negative values
        np.array([0.1]),      # Close to optimum
    ]

    # Run stability check
    stability_report = check_numerical_stability(
        func=test_func,
        test_inputs=test_inputs,
        tolerance=1e-10
    )

    # Save stability report
    output_dir = project_root / "output" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    import json
    stability_data = {
        "function_name": stability_report.function_name,
        "stability_score": stability_report.stability_score,
        "expected_behavior": stability_report.expected_behavior,
        "actual_behavior": stability_report.actual_behavior,
        "recommendations": stability_report.recommendations,
    }

    stability_path = output_dir / "stability_analysis.json"
    with open(stability_path, 'w') as f:
        json.dump(stability_data, f, indent=2)

    print(f"Stability analysis complete - Score: {stability_report.stability_score:.2f}")
    print(f"Saved stability report to: {stability_path}")

    return stability_path


def run_performance_benchmarking():
    """Benchmark gradient descent performance."""
    if not INFRASTRUCTURE_AVAILABLE:
        print("⚠️  Skipping performance benchmarking - infrastructure not available")
        return None

    print("Running performance benchmarking...")

    # Define test function
    def test_func(x):
        return quadratic_function(x, np.array([[1.0]]), np.array([1.0]))

    # Different problem scales
    test_inputs = [
        np.array([0.0]),      # Standard case
        np.array([5.0]),      # Moderate distance
        np.array([20.0]),     # Large distance
    ]

    # Run benchmarking
    benchmark_report = benchmark_function(
        func=test_func,
        test_inputs=test_inputs,
        iterations=50  # Multiple runs for reliable measurement
    )

    # Save benchmark report
    output_dir = project_root / "output" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    import json
    benchmark_data = {
        "function_name": benchmark_report.function_name,
        "execution_time": benchmark_report.execution_time,
        "memory_usage": benchmark_report.memory_usage,
        "iterations": benchmark_report.iterations,
        "result_summary": benchmark_report.result_summary,
        "timestamp": benchmark_report.timestamp,
    }

    benchmark_path = output_dir / "performance_benchmark.json"
    with open(benchmark_path, 'w') as f:
        json.dump(benchmark_data, f, indent=2, default=str)

    print(f"Performance benchmarking complete - Avg time: {benchmark_report.execution_time:.6f}s")
    print(f"Saved benchmark report to: {benchmark_path}")

    return benchmark_path


def generate_stability_visualization(stability_path):
    """Generate visualization of stability analysis results."""
    if not stability_path or not INFRASTRUCTURE_AVAILABLE:
        return None

    print("Generating stability visualization...")

    # Load stability data
    import json
    with open(stability_path, 'r') as f:
        stability_data = json.load(f)

    # Create visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Stability score gauge
    stability_score = stability_data["stability_score"]
    colors = ['red', 'orange', 'yellow', 'lightgreen', 'green']
    color_idx = min(int(stability_score * len(colors)), len(colors) - 1)

    ax1.pie([stability_score, 1-stability_score],
            colors=[colors[color_idx], 'lightgray'],
            startangle=90, counterclock=False)
    ax1.text(0, 0, 'Stable', ha='center', va='center', fontsize=12, fontweight='bold')
    ax1.set_title('Numerical Stability Score')

    # Recommendations text
    recommendations_text = "\n".join(stability_data["recommendations"][:3])  # Top 3
    ax2.text(0.1, 0.9, "Recommendations:", fontsize=12, fontweight='bold',
             transform=ax2.transAxes, va='top')
    ax2.text(0.1, 0.8, recommendations_text, fontsize=10,
             transform=ax2.transAxes, va='top', wrap=True)
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis('off')
    ax2.set_title('Stability Analysis Summary')

    plt.tight_layout()

    # Save plot
    output_dir = project_root / "output" / "figures"
    plot_path = output_dir / "stability_analysis.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved stability visualization to: {plot_path}")
    return plot_path


def generate_benchmark_visualization(benchmark_path):
    """Generate visualization of benchmark results."""
    if not benchmark_path or not INFRASTRUCTURE_AVAILABLE:
        return None

    print("Generating benchmark visualization...")

    # Load benchmark data
    import json
    with open(benchmark_path, 'r') as f:
        benchmark_data = json.load(f)

    # Create simple visualization
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))

    # Performance metrics
    metrics = ['Execution Time', 'Memory Usage']
    values = [benchmark_data["execution_time"],
              benchmark_data["memory_usage"] or 0]

    colors = ['skyblue', 'lightcoral']
    bars = ax.bar(metrics, values, color=colors, alpha=0.7)

    ax.set_ylabel('Value')
    ax.set_title('Performance Benchmark Results')
    ax.grid(True, alpha=0.3)

    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.01,
                    f'{value:.4f}' if isinstance(value, float) else f'{value}',
                    ha='center', va='bottom')

    plt.tight_layout()

    # Save plot
    output_dir = project_root / "output" / "figures"
    plot_path = output_dir / "performance_benchmark.png"
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved benchmark visualization to: {plot_path}")
    return plot_path


def generate_analysis_dashboard(results, stability_path=None, benchmark_path=None):
    """Generate comprehensive analysis dashboard."""
    if not INFRASTRUCTURE_AVAILABLE:
        print("⚠️  Skipping dashboard generation - infrastructure not available")
        return None

    print("Generating analysis dashboard...")

    try:
        from infrastructure.reporting import generate_output_summary

        # Collect output summary
        output_dir = project_root / "output"
        output_statistics = collect_output_statistics(output_dir)
        generate_output_summary(output_dir, stats=output_statistics)  # Logging function, returns None

        # Create dashboard HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Optimization Analysis Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ background: #f0f0f0; padding: 10px; margin: 10px; border-radius: 5px; }}
                .metric h3 {{ margin-top: 0; }}
                .status-good {{ color: green; }}
                .status-warning {{ color: orange; }}
                .status-error {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Optimization Analysis Dashboard</h1>

            <div class="metric">
                <h3>Optimization Results</h3>
                <p>Step sizes tested: {len(results)}</p>
                <p>Convergence achieved: {sum(1 for r in results.values() if r.converged)}/{len(results)}</p>
            </div>
        """

        if stability_path:
            html_content += f"""
            <div class="metric">
                <h3>Numerical Stability</h3>
                <p>Stability analysis completed</p>
                <p>Report: <a href="reports/stability_analysis.json">stability_analysis.json</a></p>
            </div>
            """

        if benchmark_path:
            html_content += f"""
            <div class="metric">
                <h3>Performance Benchmark</h3>
                <p>Benchmarking completed</p>
                <p>Report: <a href="reports/performance_benchmark.json">performance_benchmark.json</a></p>
            </div>
            """

        # Use output_statistics for dashboard content
        figures_count = output_statistics.get('figures', {}).get('files', 0)
        data_count = output_statistics.get('data', {}).get('files', 0)
        reports_count = output_statistics.get('reports', {}).get('files', 0)

        html_content += f"""
        <div class="metric">
            <h3>Output Summary</h3>
            <p>Figures generated: {figures_count}</p>
            <p>Data files: {data_count}</p>
            <p>Reports: {reports_count}</p>
        </div>
        """

        html_content += """
        </body>
        </html>
        """

        # Save dashboard
        output_dir = project_root / "output" / "reports"
        dashboard_path = output_dir / "analysis_dashboard.html"
        with open(dashboard_path, 'w') as f:
            f.write(html_content)

        print(f"Saved analysis dashboard to: {dashboard_path}")
        return dashboard_path

    except Exception as e:
        print(f"⚠️  Failed to generate dashboard: {e}")
        return None


def validate_generated_outputs():
    """Validate integrity of generated analysis outputs."""
    print("Validating generated outputs...")

    try:
        output_dir = project_root / "output"

        # Run integrity validation
        integrity_report = verify_output_integrity(output_dir)

        # Generate validation summary
        validation_summary = {
            'integrity_check': {
                'total_files': len(integrity_report.file_integrity),
                'integrity_passed': sum(integrity_report.file_integrity.values()),
                'issues_found': len(integrity_report.issues),
                'warnings': len(integrity_report.warnings),
                'recommendations': len(integrity_report.recommendations)
            }
        }

        if integrity_report.issues:
            print(f"⚠️  Found {len(integrity_report.issues)} integrity issues")
            for issue in integrity_report.issues[:3]:  # Show first 3
                print(f"   • {issue}")
        else:
            print("✅ Output integrity validation passed")

        return validation_summary

    except Exception as e:
        print(f"⚠️  Output validation failed: {e}")
        return None


def save_validation_report(validation_report):
    """Save validation report to file."""
    if not validation_report:
        return None

    try:
        output_dir = project_root / "output" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        report_path = output_dir / "output_validation.json"
        import json
        with open(report_path, 'w') as f:
            json.dump(validation_report, f, indent=2, default=str)

        print(f"Saved validation report to: {report_path}")
        return report_path

    except Exception as e:
        print(f"⚠️  Failed to save validation report: {e}")
        return None


def register_figure():
    """Register the generated figures for manuscript reference."""
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
            ("convergence_plot.png", "Gradient descent convergence for different step sizes", "fig:convergence"),
            ("step_size_sensitivity.png", "Step size sensitivity analysis showing iterations and solution quality", "fig:step_sensitivity"),
            ("convergence_rate_comparison.png", "Convergence rate comparison on logarithmic scale", "fig:convergence_rate"),
            ("algorithm_complexity.png", "Algorithm complexity visualization with performance metrics", "fig:complexity")
        ]

        # Add scientific analysis figures if available
        if INFRASTRUCTURE_AVAILABLE:
            figures.extend([
                ("stability_analysis.png", "Numerical stability analysis results and recommendations", "fig:stability"),
                ("performance_benchmark.png", "Performance benchmarking results and metrics", "fig:benchmark")
            ])

        for filename, caption, label in figures:
            fm.register_figure(
                filename=filename,
                caption=caption,
                label=label,
                section="Results",
                generated_by="optimization_analysis.py"
            )
            print(f"✅ Registered figure with label: {label}")

    except ImportError as e:
        print(f"⚠️  Figure manager not available: {e}")
    except Exception as e:
        print(f"⚠️  Failed to register figures: {e}")


def main():
    """Main analysis function."""
    # Initialize logger and performance monitoring
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    print("Starting optimization analysis...")
    if logger:
        logger.info(f"Project root: {project_root}")

    try:
        # Performance monitoring context
        with monitor_performance("Optimization analysis pipeline") as monitor:
            if logger:
                logger.info("Performance monitoring enabled")

            # Run experiments with progress tracking
            with log_operation("Running convergence experiments", logger=logger):
                if INFRASTRUCTURE_AVAILABLE:
                    progress = ProgressBar(total=4, task="Step sizes")
                    results = run_convergence_experiment_with_progress(progress)
                    progress.finish()
                else:
                    results = run_convergence_experiment()

            # Generate traditional outputs
            with log_operation("Generating traditional analysis outputs", logger=logger):
                convergence_plot = generate_convergence_plot(results)
                sensitivity_plot = generate_step_size_sensitivity_plot(results)
                rate_plot = generate_convergence_rate_plot(results)
                complexity_plot = generate_complexity_visualization(results)
                data_path = save_optimization_results(results)

            # Run scientific analysis (if infrastructure available)
            stability_path = None
            benchmark_path = None
            stability_plot = None
            benchmark_plot = None
            dashboard_path = None

            if INFRASTRUCTURE_AVAILABLE:
                with log_operation("Running scientific analysis", logger=logger):
                    with log_operation("Numerical stability analysis", logger=logger):
                        stability_path = run_stability_analysis()

                    with log_operation("Performance benchmarking", logger=logger):
                        benchmark_path = run_performance_benchmarking()

                    # Generate scientific visualizations
                    with log_operation("Generating scientific visualizations", logger=logger):
                        stability_plot = generate_stability_visualization(stability_path)
                        benchmark_plot = generate_benchmark_visualization(benchmark_path)

                    # Generate comprehensive dashboard
                    with log_operation("Generating analysis dashboard", logger=logger):
                        dashboard_path = generate_analysis_dashboard(results, stability_path, benchmark_path)
            else:
                if logger:
                    logger.warning("Infrastructure not available - skipping scientific analysis")

            # Register figures if possible
            register_figure()

            # Validate generated outputs
            validation_report_path = None
            with log_operation("Validating generated outputs", logger=logger):
                validation_report = validate_generated_outputs()
                if validation_report:
                    validation_report_path = save_validation_report(validation_report)

            # Generate publishing materials
            with log_operation("Generating publishing materials", logger=logger):
                publishing_metadata = extract_optimization_metadata(results)
                if publishing_metadata:
                    citations = generate_citations_from_metadata(publishing_metadata)
                    save_publishing_materials(publishing_metadata, citations)

        # Log final performance metrics
        if monitor and INFRASTRUCTURE_AVAILABLE:
            performance_metrics = monitor.stop()
            if logger:
                logger.info("Performance Summary:")
                logger.info(".2f")
                logger.info(".1f")

            # Save performance data
            output_dir = project_root / "output" / "reports"
            output_dir.mkdir(parents=True, exist_ok=True)

            import json
            perf_path = output_dir / "analysis_performance.json"
            with open(perf_path, 'w') as f:
                json.dump(performance_metrics.to_dict(), f, indent=2, default=str)
            if logger:
                logger.info(f"Performance data saved to: {perf_path}")

        # Log final results
        log_success("Analysis completed successfully!", logger=logger)
        if logger:
            logger.info(f"Generated convergence plot: {convergence_plot}")
            logger.info(f"Generated sensitivity plot: {sensitivity_plot}")
            logger.info(f"Generated rate comparison plot: {rate_plot}")
            logger.info(f"Generated complexity visualization: {complexity_plot}")
            logger.info(f"Generated data: {data_path}")

            if INFRASTRUCTURE_AVAILABLE:
                logger.info(f"Generated stability report: {stability_path}")
                logger.info(f"Generated benchmark report: {benchmark_path}")
                logger.info(f"Generated stability visualization: {stability_plot}")
                logger.info(f"Generated benchmark visualization: {benchmark_plot}")
                logger.info(f"Generated analysis dashboard: {dashboard_path}")
                logger.info(f"Generated validation report: {validation_report_path}")
                logger.info("Generated publishing materials and citations")

            logger.info("Optimization analysis pipeline completed successfully")

    except ScriptExecutionError as e:
        # Handle script-specific errors with recovery suggestions
        print(f"\n❌ Script execution failed: {e}")
        if e.recovery_commands:
            print("Suggested recovery commands:")
            for cmd in e.recovery_commands:
                print(f"  {cmd}")
        if logger:
            logger.error(f"Script execution error: {e}", exc_info=True)
        raise

    except TemplateError as e:
        # Handle infrastructure template errors
        print(f"\n❌ Infrastructure error: {e}")
        if e.suggestions:
            print("Suggestions:")
            for suggestion in e.suggestions:
                print(f"  • {suggestion}")
        if logger:
            logger.error(f"Infrastructure error: {e}", exc_info=True)
        raise

    except ImportError as e:
        # Handle missing dependencies
        print(f"\n❌ Import error: {e}")
        print("Suggestions:")
        print("  • Install missing dependencies: pip install -r requirements.txt")
        print("  • Check infrastructure module availability")
        if logger:
            logger.error(f"Import error: {e}", exc_info=True)
        raise

    except FileNotFoundError as e:
        # Handle missing files
        print(f"\n❌ File not found: {e}")
        print("Suggestions:")
        print("  • Ensure project structure is correct")
        print("  • Check that source code exists in src/ directory")
        if logger:
            logger.error(f"File not found error: {e}", exc_info=True)
        raise

    except Exception as e:
        # Handle unexpected errors with context
        error_msg = f"Unexpected error during optimization analysis: {e}"
        print(f"\n❌ {error_msg}")
        print("Suggestions:")
        print("  • Check system requirements and dependencies")
        print("  • Review error logs for detailed information")
        print("  • Ensure sufficient disk space and memory")
        if logger:
            logger.error(error_msg, exc_info=True)
        raise


def extract_optimization_metadata(results: Dict[float, OptimizationResult]) -> Optional[Dict[str, Any]]:
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

        # Create publication metadata
        metadata = {
            'title': 'Optimization Algorithm Performance Analysis',
            'description': f'Comparative analysis of gradient descent optimization with step sizes {list(results.keys())}',
            'algorithm': 'Gradient Descent',
            'objective_function': 'Quadratic Function f(x) = x²',
            'step_sizes_tested': list(results.keys()),
            'best_step_size': best_step_size,
            'final_objective': best_result.objective_value,
            'iterations_to_convergence': len(best_result.objective_history),
            'convergence_rate': abs(best_result.objective_history[-1] - best_result.objective_history[0]) / len(best_result.objective_history),
            'analysis_type': 'Numerical Optimization',
            'methodology': 'Gradient descent with fixed step sizes',
        }

        return metadata

    except Exception as e:
        if INFRASTRUCTURE_AVAILABLE:
            logger = get_logger(__name__)
            logger.warning(f"Failed to extract optimization metadata: {e}")
        return None


def generate_citations_from_metadata(metadata: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Generate citations from optimization metadata.

    Args:
        metadata: Publication metadata dictionary

    Returns:
        Dictionary with citation formats, or None if generation fails
    """
    try:
        # Create a PublicationMetadata object for citation generation
        pub_metadata = PublicationMetadata(
            title=metadata['title'],
            authors=['Optimization Analysis Pipeline'],  # List of strings, not dicts
            abstract=metadata.get('description', 'Optimization algorithm performance analysis'),
            keywords=['optimization', 'gradient descent', 'numerical analysis'],
            publication_date='2024-01-01',  # Default date
            license='MIT',
        )

        # Generate citations in different formats
        citations = {}
        if INFRASTRUCTURE_AVAILABLE:
            citations['bibtex'] = generate_citation_bibtex(pub_metadata)
            citations['apa'] = generate_citation_apa(pub_metadata)
            citations['mla'] = generate_citation_mla(pub_metadata)

        return citations

    except Exception as e:
        if INFRASTRUCTURE_AVAILABLE:
            logger = get_logger(__name__)
            logger.warning(f"Failed to generate citations: {e}")
        return None


def save_publishing_materials(metadata: Dict[str, Any], citations: Optional[Dict[str, str]] = None) -> None:
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
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)

        # Save citations if available
        if citations:
            for format_name, citation_text in citations.items():
                citation_path = output_dir / f"citation_{format_name}.txt"
                with open(citation_path, 'w') as f:
                    f.write(citation_text)

        # Create publication summary
        summary_path = output_dir / "publication_summary.md"
        with open(summary_path, 'w') as f:
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

    except Exception as e:
        if INFRASTRUCTURE_AVAILABLE:
            logger = get_logger(__name__)
            logger.warning(f"Failed to save publishing materials: {e}")


if __name__ == "__main__":
    main()