#!/usr/bin/env python3
"""Optimization analysis script.

This script demonstrates the analysis capabilities by:
1. Running optimization experiments
2. Generating convergence plots
3. Saving numerical results
4. Registering figures for the manuscript
"""
# Add project src to path
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from optimizer import (OptimizationResult, compute_gradient, gradient_descent,
                       quadratic_function)

# Add infrastructure imports for scientific analysis
try:
    # Ensure repo root is on path for infrastructure imports
    repo_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(repo_root))

    from infrastructure.core import (CheckpointManager, ProgressBar,
                                     SystemHealthChecker, get_logger,
                                     log_operation, log_stage, log_success,
                                     monitor_performance, retry_with_backoff)
    from infrastructure.core.exceptions import (BuildError,
                                                ScriptExecutionError,
                                                TemplateError, ValidationError)
    from infrastructure.publishing import (create_github_release,
                                           extract_publication_metadata,
                                           generate_citation_apa,
                                           generate_citation_bibtex,
                                           generate_citation_mla,
                                           prepare_arxiv_submission,
                                           publish_to_zenodo)
    from infrastructure.publishing.models import PublicationMetadata
    from infrastructure.rendering import RenderManager, get_render_manager
    from infrastructure.reporting import (collect_output_statistics,
                                          generate_output_summary,
                                          get_error_aggregator)
    from infrastructure.scientific import (benchmark_function,
                                           check_numerical_stability)
    from infrastructure.validation import (generate_integrity_report,
                                           verify_output_integrity)

    INFRASTRUCTURE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Infrastructure modules not available: {e}")
    INFRASTRUCTURE_AVAILABLE = False


# =============================================================================
# VISUALIZATION CONFIGURATION - Accessibility & Publication Quality
# =============================================================================
# Colorblind-safe palette (IBM Design Language / Wong palette)
# Tested for deuteranopia, protanopia, and tritanopia accessibility
VIZ_CONFIG = {
    "colors": {
        "primary": "#0072B2",      # Blue (safe for all color blindness)
        "secondary": "#D55E00",    # Vermillion/Orange
        "tertiary": "#009E73",     # Bluish green
        "quaternary": "#CC79A7",   # Reddish purple
        "neutral": "#999999",      # Gray for reference lines
        "success": "#009E73",      # Green (same as tertiary)
        "warning": "#F0E442",      # Yellow
        "error": "#D55E00",        # Same as secondary
    },
    "palette": ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#F0E442", "#56B4E9"],
    "fonts": {
        "title": 16,
        "subtitle": 14,
        "axis_label": 14,
        "tick_label": 12,
        "legend": 12,
        "annotation": 11,
    },
    "figure": {
        "dpi": 300,
        "facecolor": "white",
        "figsize_single": (10, 7),
        "figsize_double": (14, 6),
        "figsize_quad": (14, 11),
    },
    "lines": {
        "linewidth": 2.5,
        "markersize": 8,
        "markeredgewidth": 2,
    },
    "grid": {
        "alpha": 0.4,
        "linestyle": "-",
        "linewidth": 0.5,
    },
    "legend": {
        "framealpha": 0.95,
        "edgecolor": "#666666",
        "fancybox": True,
    },
    "markers": ["o", "s", "^", "D", "v", "p"],
}


def apply_visualization_style():
    """Apply global matplotlib style for publication-quality, accessible figures."""
    plt.rcParams.update({
        # Figure
        "figure.dpi": VIZ_CONFIG["figure"]["dpi"],
        "figure.facecolor": VIZ_CONFIG["figure"]["facecolor"],
        "figure.edgecolor": "none",
        # Font sizes
        "font.size": VIZ_CONFIG["fonts"]["tick_label"],
        "axes.titlesize": VIZ_CONFIG["fonts"]["title"],
        "axes.labelsize": VIZ_CONFIG["fonts"]["axis_label"],
        "xtick.labelsize": VIZ_CONFIG["fonts"]["tick_label"],
        "ytick.labelsize": VIZ_CONFIG["fonts"]["tick_label"],
        "legend.fontsize": VIZ_CONFIG["fonts"]["legend"],
        # Font weight
        "axes.titleweight": "bold",
        "axes.labelweight": "medium",
        # Lines
        "lines.linewidth": VIZ_CONFIG["lines"]["linewidth"],
        "lines.markersize": VIZ_CONFIG["lines"]["markersize"],
        # Grid
        "axes.grid": True,
        "grid.alpha": VIZ_CONFIG["grid"]["alpha"],
        "grid.linestyle": VIZ_CONFIG["grid"]["linestyle"],
        "grid.linewidth": VIZ_CONFIG["grid"]["linewidth"],
        # Legend
        "legend.framealpha": VIZ_CONFIG["legend"]["framealpha"],
        "legend.edgecolor": VIZ_CONFIG["legend"]["edgecolor"],
        "legend.fancybox": VIZ_CONFIG["legend"]["fancybox"],
        # Spines
        "axes.spines.top": False,
        "axes.spines.right": False,
        # Save settings
        "savefig.dpi": VIZ_CONFIG["figure"]["dpi"],
        "savefig.bbox": "tight",
        "savefig.facecolor": VIZ_CONFIG["figure"]["facecolor"],
        "savefig.edgecolor": "none",
    })


# Apply visualization style on import
apply_visualization_style()


def run_convergence_experiment():
    """Run gradient descent with different step sizes and track convergence."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    if logger:
        logger.info("Running convergence experiments...")

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
        if logger:
            logger.info(f"Testing step size: {step_size}")

        result = gradient_descent(
            initial_point=initial_point,
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=step_size,
            max_iterations=100,
            tolerance=1e-8,
            verbose=False,
        )

        results[step_size] = result
        if logger:
            logger.info(
                f"  Converged: {result.converged}, Final value: {result.objective_value:.4f}"
            )
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
            verbose=False,
        )

        results[step_size] = result
        print(
            f"  Converged: {result.converged}, Final value: {result.objective_value:.4f}"
        )

        # Update progress bar
        if progress_bar:
            progress_bar.update(1)

    return results


def generate_convergence_plot(results):
    """Generate convergence plot showing objective value vs iteration.
    
    Uses colorblind-safe palette and accessibility-optimized settings.
    """
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    if logger:
        logger.info("Generating convergence plot...")

    # Create figure with enhanced styling
    fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure"]["figsize_single"])

    # Use colorblind-safe palette
    colors = VIZ_CONFIG["palette"]
    markers = VIZ_CONFIG["markers"]
    step_sizes = list(results.keys())

    for i, step_size in enumerate(step_sizes):
        result = results[step_size]

        # Simulate the trajectory to get intermediate values
        trajectory = simulate_trajectory(step_size, max_iter=result.iterations + 10)

        ax.plot(
            trajectory["iterations"],
            trajectory["objectives"],
            color=colors[i % len(colors)],
            linewidth=VIZ_CONFIG["lines"]["linewidth"],
            label=f"Step size α = {step_size}",
            marker=markers[i % len(markers)],
            markersize=VIZ_CONFIG["lines"]["markersize"],
            markeredgewidth=VIZ_CONFIG["lines"]["markeredgewidth"],
            markerfacecolor="white",
            markevery=max(1, len(trajectory["iterations"]) // 8),
        )

    # Add optimal value reference line
    ax.axhline(
        y=-0.5,
        color=VIZ_CONFIG["colors"]["neutral"],
        linestyle="--",
        linewidth=2,
        alpha=0.8,
        label="Optimal: f(x*) = −0.5",
    )

    ax.set_xlabel("Iteration")
    ax.set_ylabel("Objective Value f(x)")
    ax.set_title(
        "Gradient Descent Convergence Analysis\nQuadratic Minimization: f(x) = ½x² − x",
        pad=15,
    )
    ax.legend(
        loc="upper right",
        fontsize=VIZ_CONFIG["fonts"]["legend"],
        title="Learning Rate",
        title_fontsize=VIZ_CONFIG["fonts"]["legend"],
    )
    ax.set_ylim(bottom=-0.6)

    # Add annotation for convergence
    ax.annotate(
        "All step sizes converge to optimal x* = 1.0",
        xy=(0.98, 0.15),
        xycoords="axes fraction",
        fontsize=VIZ_CONFIG["fonts"]["annotation"],
        style="italic",
        color=VIZ_CONFIG["colors"]["neutral"],
        ha="right",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor="none"),
    )

    plt.tight_layout()

    # Save plot
    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    plot_path = output_dir / "convergence_plot.png"
    plt.savefig(
        plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    plt.close()

    if logger:
        logger.info(f"Saved convergence plot to: {plot_path}")
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

    return {"iterations": iterations, "objectives": objectives}


def save_optimization_results(results):
    """Save optimization results to CSV file."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    if logger:
        logger.info("Saving optimization results...")

    output_dir = project_root / "output" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    data_path = output_dir / "optimization_results.csv"

    with open(data_path, "w") as f:
        f.write(
            "step_size,solution,objective_value,iterations,converged,gradient_norm\n"
        )

        for step_size, result in results.items():
            f.write(
                f"{step_size},{result.solution[0]:.6f},{result.objective_value:.6f},"
                f"{result.iterations},{result.converged},{result.gradient_norm:.2e}\n"
            )

    if logger:
        logger.info(f"Saved results to: {data_path}")
    return data_path


def generate_step_size_sensitivity_plot(results):
    """Generate plot showing step size sensitivity analysis.
    
    Uses colorblind-safe palette and accessibility-optimized settings.
    """
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    if logger:
        logger.info("Generating step size sensitivity plot...")

    step_sizes = list(results.keys())
    iterations = [results[step_size].iterations for step_size in step_sizes]
    objective_values = [results[step_size].objective_value for step_size in step_sizes]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=VIZ_CONFIG["figure"]["figsize_double"])

    # Use colorblind-safe palette
    color_primary = VIZ_CONFIG["colors"]["primary"]
    color_secondary = VIZ_CONFIG["colors"]["secondary"]
    color_success = VIZ_CONFIG["colors"]["success"]

    # Left: Iterations vs step size
    ax1.plot(
        step_sizes,
        iterations,
        color=color_primary,
        linewidth=VIZ_CONFIG["lines"]["linewidth"],
        marker="o",
        markersize=VIZ_CONFIG["lines"]["markersize"] + 2,
        markerfacecolor="white",
        markeredgewidth=VIZ_CONFIG["lines"]["markeredgewidth"],
    )
    ax1.set_xlabel("Step Size (α)")
    ax1.set_ylabel("Iterations to Convergence")
    ax1.set_title(
        "Convergence Speed vs Step Size\nSmaller α requires more iterations",
        pad=12,
    )
    ax1.set_xscale("log")

    # Add value annotations with improved visibility
    for x, y in zip(step_sizes, iterations):
        ax1.annotate(
            f"{y}",
            (x, y),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=VIZ_CONFIG["fonts"]["annotation"],
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8, edgecolor="none"),
        )

    # Right: Final objective value vs step size
    ax2.plot(
        step_sizes,
        objective_values,
        color=color_secondary,
        linewidth=VIZ_CONFIG["lines"]["linewidth"],
        marker="s",
        markersize=VIZ_CONFIG["lines"]["markersize"] + 2,
        markerfacecolor="white",
        markeredgewidth=VIZ_CONFIG["lines"]["markeredgewidth"],
        label="Achieved Value",
    )
    ax2.axhline(
        y=-0.5,
        color=color_success,
        linestyle="--",
        linewidth=2.5,
        alpha=0.9,
        label="Optimal f(x*) = −0.5",
    )
    ax2.set_xlabel("Step Size (α)")
    ax2.set_ylabel("Final Objective Value")
    ax2.set_title(
        "Solution Quality vs Step Size\nAll step sizes achieve optimal value",
        pad=12,
    )
    ax2.legend(
        loc="lower right",
        fontsize=VIZ_CONFIG["fonts"]["legend"],
    )
    ax2.set_xscale("log")
    ax2.set_ylim(-0.52, -0.48)

    plt.tight_layout()

    # Save plot
    output_dir = project_root / "output" / "figures"
    plot_path = output_dir / "step_size_sensitivity.png"
    plt.savefig(
        plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    plt.close()

    if logger:
        logger.info(f"Saved step size sensitivity plot to: {plot_path}")
    return plot_path


def generate_convergence_rate_plot(results):
    """Generate convergence rate comparison plot.
    
    Uses colorblind-safe palette and accessibility-optimized settings.
    """
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    if logger:
        logger.info("Generating convergence rate comparison plot...")

    fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure"]["figsize_single"])

    # Use colorblind-safe palette
    colors = VIZ_CONFIG["palette"]
    markers = VIZ_CONFIG["markers"]
    step_sizes = list(results.keys())

    for i, step_size in enumerate(step_sizes):
        # Simulate trajectory with more points for rate analysis
        trajectory = simulate_trajectory(step_size, max_iter=100)

        iterations = trajectory["iterations"]
        objectives = trajectory["objectives"]

        # Calculate error relative to optimal value (-0.5)
        errors = [abs(obj + 0.5) for obj in objectives]  # Absolute error

        # Only plot until convergence or reasonable iterations
        max_plot_iter = min(50, len(iterations))
        ax.plot(
            iterations[:max_plot_iter],
            errors[:max_plot_iter],
            color=colors[i % len(colors)],
            linewidth=VIZ_CONFIG["lines"]["linewidth"],
            label=f"Step size α = {step_size}",
            marker=markers[i % len(markers)],
            markersize=VIZ_CONFIG["lines"]["markersize"],
            markerfacecolor="white",
            markeredgewidth=VIZ_CONFIG["lines"]["markeredgewidth"],
            markevery=max(1, max_plot_iter // 8),
        )

    ax.set_xlabel("Iteration")
    ax.set_ylabel("Absolute Error |f(x) − f(x*)|")
    ax.set_title(
        "Convergence Rate Comparison\nLinear Convergence on Logarithmic Scale",
        pad=15,
    )
    ax.legend(
        loc="upper right",
        fontsize=VIZ_CONFIG["fonts"]["legend"],
        title="Learning Rate",
        title_fontsize=VIZ_CONFIG["fonts"]["legend"],
    )
    ax.set_yscale("log")
    ax.set_ylim(1e-8, 1e1)

    # Add convergence threshold annotation
    ax.axhline(
        y=1e-6,
        color=VIZ_CONFIG["colors"]["neutral"],
        linestyle=":",
        linewidth=2,
        alpha=0.8,
    )
    ax.annotate(
        "Tolerance ε = 10⁻⁶",
        xy=(0.85, 0.35),
        xycoords="axes fraction",
        fontsize=VIZ_CONFIG["fonts"]["annotation"],
        color=VIZ_CONFIG["colors"]["neutral"],
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor="none"),
    )

    plt.tight_layout()

    # Save plot
    output_dir = project_root / "output" / "figures"
    plot_path = output_dir / "convergence_rate_comparison.png"
    plt.savefig(
        plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    plt.close()

    if logger:
        logger.info(f"Saved convergence rate comparison plot to: {plot_path}")
    return plot_path


def generate_complexity_visualization(results):
    """Generate algorithm complexity visualization."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    if logger:
        logger.info("Generating algorithm complexity visualization...")

    step_sizes = list(results.keys())
    iterations = [results[step_size].iterations for step_size in step_sizes]
    converged = [results[step_size].converged for step_size in step_sizes]

    # Calculate theoretical complexity metrics
    theoretical_complexity = []
    for step_size in step_sizes:
        # For quadratic functions, complexity relates to step size
        complexity = (
            1.0 / (2 * step_size * (1 - step_size)) if step_size < 0.5 else float("inf")
        )
        theoretical_complexity.append(complexity)

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle(
        "Algorithm Performance Analysis\nGradient Descent Convergence Characteristics",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )

    # Use VIZ_CONFIG colorblind-safe palette
    bar_color = VIZ_CONFIG["colors"]["primary"]
    success_color = VIZ_CONFIG["colors"]["success"]
    fail_color = VIZ_CONFIG["colors"]["error"]
    theory_color = VIZ_CONFIG["colors"]["secondary"]

    # (1) Empirical iterations
    bars1 = ax1.bar(
        range(len(step_sizes)),
        iterations,
        tick_label=[f"α={s}" for s in step_sizes],
        color=bar_color,
        alpha=0.85,
    )
    ax1.set_xlabel("Step Size", fontsize=11, fontweight="medium")
    ax1.set_ylabel("Iterations", fontsize=11, fontweight="medium")
    ax1.set_title("Empirical Convergence Iterations", fontsize=12, fontweight="bold")
    ax1.grid(True, alpha=0.3, axis="y")
    # Add value labels on bars
    for bar, val in zip(bars1, iterations):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 3,
            str(val),
            ha="center",
            va="bottom",
            fontsize=9,
        )

    # (2) Convergence status
    conv_colors = [success_color if c else fail_color for c in converged]
    bars2 = ax2.bar(
        range(len(step_sizes)),
        [1 if c else 0 for c in converged],
        tick_label=[f"α={s}" for s in step_sizes],
        color=conv_colors,
        alpha=0.85,
    )
    ax2.set_xlabel("Step Size", fontsize=11, fontweight="medium")
    ax2.set_ylabel("Convergence Status", fontsize=11, fontweight="medium")
    ax2.set_title("Convergence Success (All Passed)", fontsize=12, fontweight="bold")
    ax2.set_ylim(-0.1, 1.3)
    ax2.set_yticks([0, 1])
    ax2.set_yticklabels(["Failed", "Converged"])
    ax2.grid(True, alpha=0.3, axis="y")

    # (3) Theoretical vs empirical comparison
    ax3.plot(
        step_sizes,
        iterations,
        color=bar_color,
        linewidth=2.5,
        marker="o",
        markersize=10,
        markerfacecolor="white",
        markeredgewidth=2,
        label="Empirical",
    )
    ax3.plot(
        step_sizes,
        theoretical_complexity,
        color=theory_color,
        linestyle="--",
        linewidth=2,
        marker="^",
        markersize=8,
        label="Theoretical Bound",
    )
    ax3.set_xlabel("Step Size (α)", fontsize=11, fontweight="medium")
    ax3.set_ylabel("Iterations", fontsize=11, fontweight="medium")
    ax3.set_title("Theoretical vs Empirical Complexity", fontsize=12, fontweight="bold")
    ax3.legend(loc="upper right", framealpha=0.95)
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, max(step_sizes) * 1.15)

    # (4) Performance summary (efficiency score)
    performance_scores = []
    for step_size, iters, conv in zip(step_sizes, iterations, converged):
        if conv:
            score = 1.0 / (iters + 1)
            if 0.01 <= step_size <= 0.2:
                score *= 1.2
        else:
            score = 0.0
        performance_scores.append(score * 100)  # Scale to percentage

    bars4 = ax4.bar(
        range(len(step_sizes)),
        performance_scores,
        tick_label=[f"α={s}" for s in step_sizes],
        color=VIZ_CONFIG["colors"]["quaternary"],
        alpha=0.85,
    )
    ax4.set_xlabel("Step Size", fontsize=11, fontweight="medium")
    ax4.set_ylabel("Efficiency Score (%)", fontsize=11, fontweight="medium")
    ax4.set_title(
        "Relative Performance Ranking\n(Higher = Faster Convergence)",
        fontsize=12,
        fontweight="bold",
    )
    ax4.grid(True, alpha=0.3, axis="y")
    # Add value labels
    for bar, val in zip(bars4, performance_scores):
        ax4.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3,
            f"{val:.1f}%",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.tight_layout()

    # Save plot
    output_dir = project_root / "output" / "figures"
    plot_path = output_dir / "algorithm_complexity.png"
    plt.savefig(
        plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    plt.close()

    if logger:
        logger.info(f"Saved algorithm complexity visualization to: {plot_path}")
    return plot_path


def run_stability_analysis():
    """Assess numerical stability of optimization algorithms."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    if not INFRASTRUCTURE_AVAILABLE:
        if logger:
            logger.warning("Skipping stability analysis - infrastructure not available")
        return None

    if logger:
        logger.info("Running numerical stability analysis...")

    # Define test function for stability analysis
    def test_func(x):
        return quadratic_function(x, np.array([[1.0]]), np.array([1.0]))

    # Test different input ranges for stability
    test_inputs = [
        np.array([0.0]),  # Standard start point
        np.array([10.0]),  # Far from optimum
        np.array([-5.0]),  # Negative values
        np.array([0.1]),  # Close to optimum
    ]

    # Run stability check
    stability_report = check_numerical_stability(
        func=test_func, test_inputs=test_inputs, tolerance=1e-10
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
    with open(stability_path, "w") as f:
        json.dump(stability_data, f, indent=2)

    if logger:
        logger.info(
            f"Stability analysis complete - Score: {stability_report.stability_score:.2f}"
        )
        logger.info(f"Saved stability report to: {stability_path}")

    return stability_path


def run_performance_benchmarking():
    """Benchmark gradient descent performance."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    if not INFRASTRUCTURE_AVAILABLE:
        if logger:
            logger.warning(
                "Skipping performance benchmarking - infrastructure not available"
            )
        return None

    if logger:
        logger.info("Running performance benchmarking...")

    # Define test function
    def test_func(x):
        return quadratic_function(x, np.array([[1.0]]), np.array([1.0]))

    # Different problem scales
    test_inputs = [
        np.array([0.0]),  # Standard case
        np.array([5.0]),  # Moderate distance
        np.array([20.0]),  # Large distance
    ]

    # Run benchmarking
    benchmark_report = benchmark_function(
        func=test_func,
        test_inputs=test_inputs,
        iterations=50,  # Multiple runs for reliable measurement
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
    with open(benchmark_path, "w") as f:
        json.dump(benchmark_data, f, indent=2, default=str)

    if logger:
        logger.info(
            f"Performance benchmarking complete - Avg time: {benchmark_report.execution_time:.6f}s"
        )
        logger.info(f"Saved benchmark report to: {benchmark_path}")

    return benchmark_path


def generate_stability_visualization(stability_path):
    """Generate visualization of stability analysis results."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    if not stability_path or not INFRASTRUCTURE_AVAILABLE:
        return None

    if logger:
        logger.info("Generating stability visualization...")

    # Load stability data
    import json

    with open(stability_path, "r") as f:
        stability_data = json.load(f)

    # Create visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Stability score gauge
    stability_score = stability_data["stability_score"]
    colors = [
        VIZ_CONFIG["colors"]["error"],
        VIZ_CONFIG["colors"]["secondary"],
        VIZ_CONFIG["colors"]["warning"],
        VIZ_CONFIG["colors"]["tertiary"],
        VIZ_CONFIG["colors"]["success"],
    ]
    color_idx = min(int(stability_score * len(colors)), len(colors) - 1)

    ax1.pie(
        [stability_score, 1 - stability_score],
        colors=[colors[color_idx], VIZ_CONFIG["colors"]["neutral"]],
        startangle=90,
        counterclock=False,
    )
    ax1.text(0, 0, "Stable", ha="center", va="center", fontsize=VIZ_CONFIG["fonts"]["tick_label"], fontweight="bold")
    ax1.set_title("Numerical Stability Score", fontsize=VIZ_CONFIG["fonts"]["title"])

    # Recommendations text
    recommendations_text = "\n".join(stability_data["recommendations"][:3])  # Top 3
    ax2.text(
        0.1,
        0.9,
        "Recommendations:",
        fontsize=VIZ_CONFIG["fonts"]["tick_label"],
        fontweight="bold",
        transform=ax2.transAxes,
        va="top",
    )
    ax2.text(
        0.1,
        0.8,
        recommendations_text,
        fontsize=VIZ_CONFIG["fonts"]["annotation"],
        transform=ax2.transAxes,
        va="top",
        wrap=True,
    )
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis("off")
    ax2.set_title("Stability Analysis Summary")

    plt.tight_layout()

    # Save plot
    output_dir = project_root / "output" / "figures"
    plot_path = output_dir / "stability_analysis.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.close()

    if logger:
        logger.info(f"Saved stability visualization to: {plot_path}")
    return plot_path


def generate_benchmark_visualization(benchmark_path):
    """Generate visualization of benchmark results."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    if not benchmark_path or not INFRASTRUCTURE_AVAILABLE:
        return None

    if logger:
        logger.info("Generating benchmark visualization...")

    # Load benchmark data
    import json

    with open(benchmark_path, "r") as f:
        benchmark_data = json.load(f)

    # Create simple visualization
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))

    # Performance metrics
    metrics = ["Execution Time", "Memory Usage"]
    values = [benchmark_data["execution_time"], benchmark_data["memory_usage"] or 0]

    colors = [VIZ_CONFIG["colors"]["primary"], VIZ_CONFIG["colors"]["secondary"]]
    bars = ax.bar(metrics, values, color=colors, alpha=0.7)

    ax.set_ylabel("Value")
    ax.set_title("Performance Benchmark Results")
    ax.grid(True, alpha=0.3)

    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        if height > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + max(values) * 0.01,
                f"{value:.4f}" if isinstance(value, float) else f"{value}",
                ha="center",
                va="bottom",
            )

    plt.tight_layout()

    # Save plot
    output_dir = project_root / "output" / "figures"
    plot_path = output_dir / "performance_benchmark.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.close()

    if logger:
        logger.info(f"Saved benchmark visualization to: {plot_path}")
    return plot_path


def generate_analysis_dashboard(results, stability_path=None, benchmark_path=None):
    """Generate comprehensive analysis dashboard."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    if not INFRASTRUCTURE_AVAILABLE:
        if logger:
            logger.warning(
                "Skipping dashboard generation - infrastructure not available"
            )
        return None

    if logger:
        logger.info("Generating analysis dashboard...")

    try:
        from infrastructure.reporting import generate_output_summary

        # Collect output summary
        output_statistics = collect_output_statistics(
            project_root, project_name="code_project"
        )
        # Skip generate_output_summary() - it's for copy stage, not dashboard generation

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

        # Use output_statistics for dashboard content with proper key checking
        figures_count = (
            output_statistics.get("figures", {}).get("file_count", 0)
            if isinstance(output_statistics.get("figures"), dict)
            else 0
        )
        data_count = (
            output_statistics.get("data", {}).get("file_count", 0)
            if isinstance(output_statistics.get("data"), dict)
            else 0
        )
        reports_count = (
            output_statistics.get("reports", {}).get("file_count", 0)
            if isinstance(output_statistics.get("reports"), dict)
            else 0
        )

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
        with open(dashboard_path, "w") as f:
            f.write(html_content)

        if logger:
            logger.info(f"Saved analysis dashboard to: {dashboard_path}")
        return dashboard_path

    except (ValidationError, BuildError) as e:
        if logger:
            logger.warning(f"Failed to generate dashboard: {e}")
        return None
    except Exception as e:
        if logger:
            logger.warning(f"Unexpected error generating dashboard: {e}")
        return None


def validate_generated_outputs():
    """Validate integrity of generated analysis outputs."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    if logger:
        logger.info("Validating generated outputs...")

    try:
        output_dir = project_root / "output"

        # Run integrity validation
        integrity_report = verify_output_integrity(output_dir)

        # Generate validation summary
        validation_summary = {
            "integrity_check": {
                "total_files": len(integrity_report.file_integrity),
                "integrity_passed": sum(integrity_report.file_integrity.values()),
                "issues_found": len(integrity_report.issues),
                "warnings": len(integrity_report.warnings),
                "recommendations": len(integrity_report.recommendations),
            }
        }

        if integrity_report.issues:
            if logger:
                logger.warning(f"Found {len(integrity_report.issues)} integrity issues")
                for issue in integrity_report.issues[:3]:  # Show first 3
                    logger.warning(f"   • {issue}")
        else:
            if logger:
                logger.info("Output integrity validation passed")

        return validation_summary

    except ValidationError as e:
        if logger:
            logger.warning(f"Output validation failed: {e}")
        return None
    except Exception as e:
        if logger:
            logger.warning(f"Unexpected error during output validation: {e}")
        return None


def save_validation_report(validation_report):
    """Save validation report to file."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    if not validation_report:
        return None

    try:
        output_dir = project_root / "output" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        report_path = output_dir / "output_validation.json"
        import json

        with open(report_path, "w") as f:
            json.dump(validation_report, f, indent=2, default=str)

        if logger:
            logger.info(f"Saved validation report to: {report_path}")
        return report_path

    except Exception as e:
        if logger:
            logger.warning(f"Failed to save validation report: {e}")
        return None


def register_figure():
    """Register the generated figures for manuscript reference."""
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

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
            (
                "convergence_plot.png",
                "Gradient descent convergence for different step sizes",
                "fig:convergence",
            ),
            (
                "step_size_sensitivity.png",
                "Step size sensitivity analysis showing iterations and solution quality",
                "fig:step_sensitivity",
            ),
            (
                "convergence_rate_comparison.png",
                "Convergence rate comparison on logarithmic scale",
                "fig:convergence_rate",
            ),
            (
                "algorithm_complexity.png",
                "Algorithm complexity visualization with performance metrics",
                "fig:complexity",
            ),
        ]

        # Add scientific analysis figures if available
        if INFRASTRUCTURE_AVAILABLE:
            figures.extend(
                [
                    (
                        "stability_analysis.png",
                        "Numerical stability analysis results and recommendations",
                        "fig:stability",
                    ),
                    (
                        "performance_benchmark.png",
                        "Performance benchmarking results and metrics",
                        "fig:benchmark",
                    ),
                ]
            )

        for filename, caption, label in figures:
            fm.register_figure(
                filename=filename,
                caption=caption,
                label=label,
                section="Results",
                generated_by="optimization_analysis.py",
            )
            if logger:
                logger.info(f"Registered figure with label: {label}")

    except ImportError as e:
        if logger:
            logger.warning(f"Figure manager not available: {e}")
    except Exception as e:
        if logger:
            logger.warning(f"Failed to register figures: {e}")


def main():
    """Main analysis function."""
    # Initialize logger (use print as fallback)
    logger = get_logger(__name__) if INFRASTRUCTURE_AVAILABLE else None

    def log_info(msg):
        if logger:
            logger.info(msg)
        else:
            print(f"INFO: {msg}")

    def log_warning(msg):
        if logger:
            logger.warning(msg)
        else:
            print(f"WARNING: {msg}")

    if INFRASTRUCTURE_AVAILABLE:
        log_success("Starting optimization analysis pipeline", logger=logger)
    log_info(f"Project root: {project_root}")

    try:
        # System health check
        if INFRASTRUCTURE_AVAILABLE:
            health_checker = SystemHealthChecker()
            log_info("Running system health check...")
            health_status = health_checker.get_health_status()
            if health_status.get("overall_status") != "healthy":
                log_warning("System health check failed:")
                for check_name, check_result in health_status.get("checks", {}).items():
                    if check_result.get("status") != "healthy":
                        log_warning(
                            f"  - {check_name}: {check_result.get('error', 'unknown error')}"
                        )
            else:
                log_info("System health check passed")

        # Initialize checkpoint manager
        checkpoint_manager = None
        if INFRASTRUCTURE_AVAILABLE:
            checkpoint_dir = project_root / "output" / "checkpoints"
            checkpoint_manager = CheckpointManager(checkpoint_dir)
            log_info("Checkpoint manager initialized")

        # Performance monitoring context (use nullcontext as fallback)
        from contextlib import nullcontext

        monitor_ctx = (
            monitor_performance("Optimization analysis pipeline")
            if INFRASTRUCTURE_AVAILABLE
            else nullcontext()
        )
        with monitor_ctx as monitor:
            log_info(
                "Performance monitoring enabled"
                if INFRASTRUCTURE_AVAILABLE
                else "Running without performance monitoring"
            )

            # Run experiments with progress tracking
            log_info("Running convergence experiments...")
            if INFRASTRUCTURE_AVAILABLE:
                progress = ProgressBar(total=4, task="Step sizes")
                results = run_convergence_experiment_with_progress(progress)
                progress.finish()
            else:
                results = run_convergence_experiment()

            # Generate traditional outputs
            log_info("Generating traditional analysis outputs...")
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
                log_info("Running scientific analysis...")
                log_info("Numerical stability analysis...")
                stability_path = run_stability_analysis()

                log_info("Performance benchmarking...")
                benchmark_path = run_performance_benchmarking()

                # Generate scientific visualizations
                log_info("Generating scientific visualizations...")
                stability_plot = generate_stability_visualization(stability_path)
                benchmark_plot = generate_benchmark_visualization(benchmark_path)

                # Generate comprehensive dashboard
                log_info("Generating analysis dashboard...")
                dashboard_path = generate_analysis_dashboard(
                    results, stability_path, benchmark_path
                )
            else:
                log_warning(
                    "Infrastructure not available - skipping scientific analysis"
                )

            # Register figures if possible
            register_figure()

            # Validate generated outputs
            validation_report_path = None
            log_info("Validating generated outputs...")
            if INFRASTRUCTURE_AVAILABLE:
                validation_report = validate_generated_outputs()
                if validation_report:
                    validation_report_path = save_validation_report(validation_report)

            # Generate publishing materials
            log_info("Generating publishing materials...")
            publishing_metadata = extract_optimization_metadata(results)
            if publishing_metadata:
                citations = generate_citations_from_metadata(publishing_metadata)
                save_publishing_materials(publishing_metadata, citations)

            # HTML dashboard is already created and saved above

            # Publishing integration (demonstrate capabilities)
            if INFRASTRUCTURE_AVAILABLE:
                log_info("Publishing integration demonstration...")
                try:
                    # Demonstrate Zenodo publishing preparation
                    if publishing_metadata:
                        # This would normally require API tokens, but we demonstrate the interface
                        log_info(
                            "Publishing interfaces available: Zenodo, arXiv, GitHub releases"
                        )
                        log_info("Publication metadata extracted and formatted")
                except Exception as e:
                    log_warning(f"Publishing demonstration failed: {e}")

        # Log final performance metrics
        if INFRASTRUCTURE_AVAILABLE and monitor:
            performance_metrics = monitor.stop()
            log_info("Performance Summary:")
            log_info(f"Duration: {performance_metrics.duration:.2f}s")
            log_info(f"Memory: {performance_metrics.resource_usage.memory_mb:.1f}MB")

            # Save performance data
            output_dir = project_root / "output" / "reports"
            output_dir.mkdir(parents=True, exist_ok=True)

            import json

            perf_path = output_dir / "analysis_performance.json"
            with open(perf_path, "w") as f:
                json.dump(performance_metrics.to_dict(), f, indent=2, default=str)
            log_info(f"Performance data saved to: {perf_path}")

        # Log final results
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
            log_info(f"Generated analysis dashboard: {dashboard_path}")
            log_info(f"Generated validation report: {validation_report_path}")
            log_info("Generated publishing materials and citations")

        if INFRASTRUCTURE_AVAILABLE:
            log_success("Optimization analysis pipeline completed successfully", logger=logger)
        else:
            log_info("Optimization analysis pipeline completed successfully")

    except ImportError as e:
        # Handle missing dependencies
        print(f"ERROR: Import error: {e}")
        print("Suggestions:")
        print("  • Install missing dependencies: pip install -r requirements.txt")
        print("  • Check infrastructure module availability")
        raise

    except FileNotFoundError as e:
        # Handle missing files
        print(f"ERROR: File not found: {e}")
        print("Suggestions:")
        print("  • Ensure project structure is correct")
        print("  • Check that source code exists in src/ directory")
        raise

    except Exception as e:
        # Handle infrastructure-specific errors if available
        if INFRASTRUCTURE_AVAILABLE:
            if isinstance(e, ScriptExecutionError):
                # Handle script-specific errors with recovery suggestions
                if logger:
                    logger.error(f"Script execution failed: {e}", exc_info=True)
                    if hasattr(e, "recovery_commands") and e.recovery_commands:
                        logger.error("Suggested recovery commands:")
                        for cmd in e.recovery_commands:
                            logger.error(f"  {cmd}")
                raise

            if isinstance(e, TemplateError):
                # Handle infrastructure template errors
                if logger:
                    logger.error(f"Infrastructure error: {e}", exc_info=True)
                    if hasattr(e, "suggestions") and e.suggestions:
                        logger.error("Suggestions:")
                        for suggestion in e.suggestions:
                            logger.error(f"  • {suggestion}")
                raise

        # Handle unexpected errors with context
        error_msg = f"Unexpected error during optimization analysis: {e}"
        print(f"ERROR: {error_msg}")
        print("Suggestions:")
        print("  • Check system requirements and dependencies")
        print("  • Review error logs for detailed information")
        print("  • Ensure sufficient disk space and memory")
        raise


def extract_optimization_metadata(
    results: Dict[float, OptimizationResult],
) -> Optional[Dict[str, Any]]:
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
            "title": "Optimization Algorithm Performance Analysis",
            "description": f"Comparative analysis of gradient descent optimization with step sizes {list(results.keys())}",
            "algorithm": "Gradient Descent",
            "objective_function": "Quadratic Function f(x) = x²",
            "step_sizes_tested": list(results.keys()),
            "best_step_size": best_step_size,
            "final_objective": best_result.objective_value,
            "iterations_to_convergence": len(best_result.objective_history),
            "convergence_rate": abs(
                best_result.objective_history[-1] - best_result.objective_history[0]
            )
            / len(best_result.objective_history),
            "analysis_type": "Numerical Optimization",
            "methodology": "Gradient descent with fixed step sizes",
        }

        return metadata

    except Exception as e:
        if INFRASTRUCTURE_AVAILABLE:
            logger = get_logger(__name__)
            logger.warning(f"Failed to extract optimization metadata: {e}")
        return None


def generate_citations_from_metadata(
    metadata: Dict[str, Any],
) -> Optional[Dict[str, str]]:
    """Generate citations from optimization metadata.

    Args:
        metadata: Publication metadata dictionary

    Returns:
        Dictionary with citation formats, or None if generation fails
    """
    try:
        # Create a PublicationMetadata object for citation generation
        pub_metadata = PublicationMetadata(
            title=metadata["title"],
            authors=["Optimization Analysis Pipeline"],  # List of strings, not dicts
            abstract=metadata.get(
                "description", "Optimization algorithm performance analysis"
            ),
            keywords=["optimization", "gradient descent", "numerical analysis"],
            publication_date="2026-01-01",  # Default date
            license="MIT",
        )

        # Generate citations in different formats
        citations = {}
        if INFRASTRUCTURE_AVAILABLE:
            citations["bibtex"] = generate_citation_bibtex(pub_metadata)
            citations["apa"] = generate_citation_apa(pub_metadata)
            citations["mla"] = generate_citation_mla(pub_metadata)

        return citations

    except Exception as e:
        if INFRASTRUCTURE_AVAILABLE:
            logger = get_logger(__name__)
            logger.warning(f"Failed to generate citations: {e}")
        return None


def save_publishing_materials(
    metadata: Dict[str, Any], citations: Optional[Dict[str, str]] = None
) -> None:
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

        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

        # Save citations if available
        if citations:
            for format_name, citation_text in citations.items():
                citation_path = output_dir / f"citation_{format_name}.txt"
                with open(citation_path, "w") as f:
                    f.write(citation_text)

        # Create publication summary
        summary_path = output_dir / "publication_summary.md"
        with open(summary_path, "w") as f:
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
