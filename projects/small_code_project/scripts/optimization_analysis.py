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


def register_figure():
    """Register the generated figure for manuscript reference."""
    try:
        # Ensure repo root is on path for infrastructure imports
        repo_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(repo_root))
        
        from infrastructure.documentation.figure_manager import FigureManager
        
        # Use project-specific registry path
        registry_file = project_root / "output" / "figures" / "figure_registry.json"
        fm = FigureManager(registry_file=str(registry_file))
        
        fm.register_figure(
            filename="convergence_plot.png",
            caption="Gradient descent convergence for different step sizes",
            label="fig:convergence",
            section="Results",
            generated_by="optimization_analysis.py"
        )
        
        print("✅ Registered figure with label: fig:convergence")
    except ImportError as e:
        print(f"⚠️  Figure manager not available: {e}")
    except Exception as e:
        print(f"⚠️  Failed to register figure: {e}")


def main():
    """Main analysis function."""
    print("Starting optimization analysis...")
    print(f"Project root: {project_root}")

    # Run experiments
    results = run_convergence_experiment()

    # Generate outputs
    plot_path = generate_convergence_plot(results)
    data_path = save_optimization_results(results)

    # Register figure if possible
    register_figure()

    print("\nAnalysis complete!")
    print(f"Generated plot: {plot_path}")
    print(f"Generated data: {data_path}")


if __name__ == "__main__":
    main()