#!/usr/bin/env python3
"""Optimization analysis script - A Template Exemplar "Thin Orchestrator".

This script demonstrates the strict separation of concerns required by the 
Generalized Research Template. It acts as a bridge, importing pure, 
zero-mock-tested mathematical logic from `projects/code_project/src/` and 
coupling it directly with the root `infrastructure.scientific` and 
`infrastructure.reporting` modules.

Capabilities demonstrated:
1. Orchestrating optimization experiments (logic in `src/`)
2. Generating convergence plots and accessible visualizations in `output/`
3. Saving numerical results securely via `infrastructure.validation`
4. Registering figures for automated `infrastructure.rendering` into the PDF
"""
import functools
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import yaml

# Add project src/ to path for optimizer imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from optimizer import (OptimizationResult, compute_gradient, gradient_descent,
                       make_quadratic_problem, quadratic_function,
                       simulate_trajectory)

# -------------------------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------------------------
def _setup_fallback_logging() -> logging.Logger:
    """Configure stdlib logging for standalone (no-infrastructure) runs."""
    logger = logging.getLogger("code_project.optimization_analysis")
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


# Infrastructure imports (optional — PYTHONPATH must include repo root)
try:
    from infrastructure.core import (CheckpointManager, ProgressBar,
                                     SystemHealthChecker, get_logger,
                                     log_success)
    from infrastructure.core.exceptions import (ScriptExecutionError,
                                                TemplateError, ValidationError)
    from infrastructure.publishing import (generate_citation_apa,
                                           generate_citation_bibtex,
                                           generate_citation_mla)
    from infrastructure.publishing.models import PublicationMetadata
    from infrastructure.reporting import collect_output_statistics
    from infrastructure.scientific import (benchmark_function,
                                           check_numerical_stability)
    from infrastructure.validation import verify_output_integrity

    INFRASTRUCTURE_AVAILABLE = True
except ImportError as e:
    _fallback_logger = _setup_fallback_logging()
    _fallback_logger.warning(f"Infrastructure modules not available: {e}")
    INFRASTRUCTURE_AVAILABLE = False


def _get_logger() -> logging.Logger:
    """Return infrastructure logger if available, otherwise a configured stdlib logger."""
    if INFRASTRUCTURE_AVAILABLE:
        return get_logger(__name__)
    return _setup_fallback_logging()


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

# Project root: projects/code_project/
project_root = Path(__file__).resolve().parent.parent


def apply_visualization_style() -> None:
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


def _load_experiment_config():
    """Load experiment parameters from config.yaml."""
    config_path = project_root / "manuscript" / "config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config.get("experiment", {})
    return {}


def _agency_category(alpha):
    """Classify a step size into its agency category for H=I quadratic.

    For the quadratic f(x) = 0.5*x^T*x - b^T*x with Hessian H=I,
    the contraction factor is rho = |1 - alpha|.
      rho < 1  => converges
      rho >= 1 => diverges
    """
    if alpha < 0.3:
        return "Conservative", "#2196F3"  # blue
    elif alpha <= 1.0:
        return "Near-optimal", "#4CAF50"  # green
    elif alpha < 2.0:
        return "Aggressive", "#FF9800"  # amber
    else:
        return "Divergent", "#F44336"  # red


def _save_figure_data(data, name, output_dir):
    """Save companion data file alongside a figure."""
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    data_path = data_dir / f"{name}.json"
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    return data_path


def run_convergence_experiment() -> Any:
    """Run gradient descent with different step sizes and track convergence."""
    logger = _get_logger()
    logger.info("Running convergence experiments...")

    exp_config = _load_experiment_config()
    A = np.array(exp_config.get("quadratic_A", [[1.0]]), dtype=float)
    b = np.array(exp_config.get("quadratic_b", [1.0]), dtype=float)
    obj_func, grad_func = make_quadratic_problem(A, b)

    step_sizes = exp_config.get("step_sizes", [0.01, 0.1, 0.5, 1.0, 1.5, 2.5])
    initial_point = np.array([exp_config.get("initial_point", 0.0)])
    max_iter = exp_config.get("max_iterations", 1000)
    tol = exp_config.get("tolerance", 1e-8)

    results = {}

    for step_size in step_sizes:
        logger.info(f"Testing step size: {step_size}")

        result = gradient_descent(
            initial_point=initial_point,
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=step_size,
            max_iterations=max_iter,
            tolerance=tol,
            verbose=False,
        )

        results[step_size] = result
        logger.info(
            f"  Converged: {result.converged}, Final value: {result.objective_value:.4f}"
        )
    return results


def run_convergence_experiment_with_progress(progress_bar: Any) -> Any:
    """Run gradient descent with different step sizes and track convergence with progress bar."""
    logger = _get_logger()
    logger.info("Running convergence experiments...")

    exp_config = _load_experiment_config()
    A = np.array(exp_config.get("quadratic_A", [[1.0]]), dtype=float)
    b = np.array(exp_config.get("quadratic_b", [1.0]), dtype=float)
    obj_func, grad_func = make_quadratic_problem(A, b)

    step_sizes = exp_config.get("step_sizes", [0.01, 0.1, 0.5, 1.0, 1.5, 2.5])
    initial_point = np.array([exp_config.get("initial_point", 0.0)])
    max_iter = exp_config.get("max_iterations", 1000)
    tol = exp_config.get("tolerance", 1e-8)

    results = {}

    for step_size in step_sizes:
        logger.info(f"Testing step size: {step_size}")

        result = gradient_descent(
            initial_point=initial_point,
            objective_func=obj_func,
            gradient_func=grad_func,
            step_size=step_size,
            max_iterations=max_iter,
            tolerance=tol,
            verbose=False,
        )

        results[step_size] = result
        logger.info(
            f"  Converged: {result.converged}, Final value: {result.objective_value:.4f}"
        )

        # Update progress bar
        if progress_bar:
            progress_bar.update(1)

    return results


def generate_convergence_plot(results: Any) -> Any:
    """Generate convergence plot showing objective value vs iteration.
    
    Uses agency-category colors and handles divergent trajectories.
    """
    logger = _get_logger()
    logger.info("Generating convergence plot...")

    # Create figure with enhanced styling
    fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure"]["figsize_single"])

    step_sizes = list(results.keys())
    plot_data = {}

    for step_size in step_sizes:
        result = results[step_size]
        category, color = _agency_category(step_size)

        # Limit trajectory length for readability
        max_plot_iters = min(result.iterations + 5, 50)
        trajectory = simulate_trajectory(step_size, max_iter=max_plot_iters)

        # Clip extreme values for divergent cases
        objectives = np.array(trajectory["objectives"], dtype=float)
        objectives = np.clip(objectives, -10, 100)

        ax.plot(
            trajectory["iterations"],
            objectives,
            color=color,
            linewidth=VIZ_CONFIG["lines"]["linewidth"],
            label=f"α = {step_size} ({category})",
            marker="o",
            markersize=VIZ_CONFIG["lines"]["markersize"],
            markeredgewidth=VIZ_CONFIG["lines"]["markeredgewidth"],
            markerfacecolor="white",
            markevery=max(1, len(trajectory["iterations"]) // 8),
        )
        plot_data[str(step_size)] = {
            "category": category,
            "iterations": trajectory["iterations"],
            "objectives": [float(o) for o in objectives],
        }

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
    ax.set_ylim(bottom=-0.7, top=10)

    plt.tight_layout()

    # Save plot
    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    plot_path = output_dir / "convergence_plot.png"
    plt.savefig(
        plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    plt.close()

    # Save companion data
    _save_figure_data(plot_data, "convergence_plot", project_root / "output")

    logger.info(f"Saved convergence plot to: {plot_path}")
    return plot_path


# simulate_trajectory is imported from src/optimizer — no reimplementation here.
# It delegates to gradient_descent() and returns {"iterations": [...], "objectives": [...]}.


def save_optimization_results(results: Any) -> Any:
    """Save optimization results to CSV file."""
    logger = _get_logger()
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

    logger.info(f"Saved results to: {data_path}")
    return data_path


def generate_step_size_sensitivity_plot(results: Any) -> Any:
    """Generate step size sensitivity analysis with expanded range.

    Left: iterations to convergence vs step size (log-x), sweeping α from
    0.005 to 0.4 in 10 steps to reveal the full curve shape.
    Right: final objective value vs step size with y-axis showing the full
    descent from f(x₀)=0 to f(x*)=−0.5, making the solution quality
    genuinely visible rather than zoomed into a trivial band.
    """
    logger = _get_logger()
    logger.info("Generating step size sensitivity plot...")

    # Sweep a wider range of step sizes for a more informative curve
    sweep_alphas = [0.005, 0.01, 0.02, 0.05, 0.08, 0.1, 0.15, 0.2, 0.3, 0.4]
    sweep_iters = []
    sweep_obj_vals = []

    for alpha in sweep_alphas:
        traj = simulate_trajectory(alpha, max_iter=500)
        sweep_iters.append(len(traj["iterations"]))
        sweep_obj_vals.append(traj["objectives"][-1])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=VIZ_CONFIG["figure"]["figsize_double"])

    color_primary = VIZ_CONFIG["colors"]["primary"]
    color_secondary = VIZ_CONFIG["colors"]["secondary"]
    color_success = VIZ_CONFIG["colors"]["success"]

    # Left: Iterations vs step size (full curve)
    ax1.plot(
        sweep_alphas,
        sweep_iters,
        color=color_primary,
        linewidth=VIZ_CONFIG["lines"]["linewidth"],
        marker="o",
        markersize=VIZ_CONFIG["lines"]["markersize"],
        markerfacecolor="white",
        markeredgewidth=VIZ_CONFIG["lines"]["markeredgewidth"],
    )
    ax1.set_xlabel("Step Size (α)")
    ax1.set_ylabel("Iterations to Convergence")
    ax1.set_title(
        "Convergence Speed vs Step Size\nIterations decrease geometrically with α",
        pad=12,
    )
    ax1.set_xscale("log")
    ax1.set_yscale("log")

    # Annotate a few key points
    for x, y in [(sweep_alphas[0], sweep_iters[0]),
                 (sweep_alphas[4], sweep_iters[4]),
                 (sweep_alphas[-1], sweep_iters[-1])]:
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

    # Right: Final objective value — show full descent range
    ax2.plot(
        sweep_alphas,
        sweep_obj_vals,
        color=color_secondary,
        linewidth=VIZ_CONFIG["lines"]["linewidth"],
        marker="s",
        markersize=VIZ_CONFIG["lines"]["markersize"],
        markerfacecolor="white",
        markeredgewidth=VIZ_CONFIG["lines"]["markeredgewidth"],
        label="Achieved f(x)",
    )
    ax2.axhline(
        y=-0.5,
        color=color_success,
        linestyle="--",
        linewidth=2.5,
        alpha=0.9,
        label="Optimal f(x*) = −0.5",
    )
    ax2.axhline(
        y=0.0,
        color=VIZ_CONFIG["colors"]["neutral"],
        linestyle=":",
        linewidth=1,
        alpha=0.5,
        label="Initial f(x₀) = 0",
    )
    ax2.set_xlabel("Step Size (α)")
    ax2.set_ylabel("Final Objective Value")
    ax2.set_title(
        "Solution Quality vs Step Size\nAll step sizes reach the optimum f(x*)=−0.5",
        pad=12,
    )
    ax2.legend(
        loc="upper right",
        fontsize=VIZ_CONFIG["fonts"]["legend"],
    )
    ax2.set_xscale("log")
    ax2.set_ylim(-0.6, 0.1)  # Full range from initial to below optimum

    plt.tight_layout()

    output_dir = project_root / "output" / "figures"
    plot_path = output_dir / "step_size_sensitivity.png"
    plt.savefig(
        plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    plt.close()

    logger.info(f"Saved step size sensitivity plot to: {plot_path}")
    return plot_path


def generate_convergence_rate_plot(results: Any) -> Any:
    """Generate convergence rate comparison plot.
    
    Uses colorblind-safe palette and accessibility-optimized settings.
    """
    logger = _get_logger()
    logger.info("Generating convergence rate comparison plot...")

    exp_config = _load_experiment_config()
    conv_tol = float(exp_config.get("convergence_tolerance", exp_config.get("tolerance", 1e-8)))

    fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure"]["figsize_single"])

    step_sizes = list(results.keys())

    for step_size in step_sizes:
        category, color = _agency_category(step_size)
        # Limit trajectory to avoid overflow for divergent step sizes
        trajectory = simulate_trajectory(step_size, max_iter=30)

        iterations = trajectory["iterations"]
        objectives = trajectory["objectives"]

        # Calculate error relative to optimal value (-0.5)
        errors = [abs(obj + 0.5) for obj in objectives]  # Absolute error

        # Only plot until convergence or reasonable iterations
        max_plot_iter = min(50, len(iterations))
        ax.plot(
            iterations[:max_plot_iter],
            errors[:max_plot_iter],
            color=color,
            linewidth=VIZ_CONFIG["lines"]["linewidth"],
            label=f"α = {step_size} ({category})",
            marker="o",
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
    ax.set_ylim(1e-12, 1e4)

    # Horizontal reference at manuscript / config convergence tolerance
    ax.axhline(
        y=conv_tol,
        color=VIZ_CONFIG["colors"]["neutral"],
        linestyle=":",
        linewidth=2,
        alpha=0.8,
    )
    tol_str = f"{conv_tol:.0e}".replace("e-0", "e-").replace("e+0", "e+")
    ax.annotate(
        f"Tolerance ε = {tol_str}",
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

    logger.info(f"Saved convergence rate comparison plot to: {plot_path}")
    return plot_path


def generate_complexity_visualization(results: Any) -> Any:
    """Generate algorithm performance analysis with 4 informative panels.

    (TL) Empirical iterations bar chart.
    (TR) Solution quality: log₁₀ absolute error from optimum per step size.
    (BL) Empirical iterations vs step size compared to 1/(2α(1−α)) proxy curve.
    (BR) Per-step error contraction ρ = |1 − α| for the unit Hessian quadratic.
    """
    logger = _get_logger()
    logger.info("Generating algorithm complexity visualization...")

    exp_config = _load_experiment_config()
    conv_tol = float(exp_config.get("convergence_tolerance", exp_config.get("tolerance", 1e-8)))
    log_tol = float(np.log10(conv_tol))

    step_sizes = list(results.keys())
    iterations = [results[step_size].iterations for step_size in step_sizes]

    # Compute solution quality: log₁₀ of absolute error from optimum
    optimal_value = -0.5
    log_errors = []
    for step_size in step_sizes:
        obj_val = results[step_size].objective_value
        err = abs(obj_val - optimal_value)
        log_errors.append(np.log10(max(err, 1e-16)))  # floor at 1e-16

    # Compute theoretical complexity and contraction factor: ρ = |1 - α|
    theoretical_complexity = []
    contraction_factors = []
    for alpha in step_sizes:
        rho = abs(1 - alpha)
        contraction_factors.append(rho)
        if rho > 0 and rho < 1:
            theoretical_complexity.append(1.0 / (2 * alpha * (1 - alpha)))
        else:
            theoretical_complexity.append(float("inf"))

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(13, 10))
    fig.suptitle(
        "Algorithm Performance Analysis\nGradient Descent Convergence Characteristics",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )

    bar_color = VIZ_CONFIG["colors"]["primary"]
    theory_color = VIZ_CONFIG["colors"]["secondary"]
    success_color = VIZ_CONFIG["colors"]["success"]
    quaternary_color = VIZ_CONFIG["colors"]["quaternary"]

    # Use agency-category colors for bars
    bar_colors = [_agency_category(s)[1] for s in step_sizes]
    bars1 = ax1.bar(
        range(len(step_sizes)),
        iterations,
        tick_label=[f"α={s}" for s in step_sizes],
        color=bar_colors,
        alpha=0.85,
    )
    ax1.set_xlabel("Step Size", fontsize=11, fontweight="medium")
    ax1.set_ylabel("Iterations", fontsize=11, fontweight="medium")
    ax1.set_title("Empirical Convergence Iterations", fontsize=12, fontweight="bold")
    ax1.grid(True, alpha=0.3, axis="y")
    for bar, val in zip(bars1, iterations):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            str(val),
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    # (2) Solution quality: log₁₀ |f(x) − f(x*)|
    bar_colors_2 = [
        success_color if le < log_tol else theory_color if le < -3 else bar_color
        for le in log_errors
    ]
    bars2 = ax2.bar(
        range(len(step_sizes)),
        log_errors,
        tick_label=[f"α={s}" for s in step_sizes],
        color=bar_colors_2,
        alpha=0.85,
    )
    ax2.axhline(
        y=log_tol,
        color=VIZ_CONFIG["colors"]["neutral"],
        linestyle="--",
        linewidth=1,
        alpha=0.7,
        label=f"ε = {conv_tol:.0e} tolerance",
    )
    ax2.set_xlabel("Step Size", fontsize=11, fontweight="medium")
    ax2.set_ylabel("log₁₀ |f(x) − f(x*)|")
    ax2.set_title("Solution Accuracy\n(Lower = More Accurate)", fontsize=12, fontweight="bold")
    ax2.legend(loc="upper right", fontsize=9, framealpha=0.95)
    ax2.grid(True, alpha=0.3, axis="y")
    for bar, val in zip(bars2, log_errors):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            min(val, 0) - 0.5,
            f"{val:.1f}",
            ha="center",
            va="top",
            fontsize=9,
            fontweight="bold",
        )

    # (3) Theory vs empirical on log scale
    ax3.semilogy(
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
    ax3.semilogy(
        step_sizes,
        theoretical_complexity,
        color=theory_color,
        linestyle="--",
        linewidth=2,
        marker="^",
        markersize=8,
        label="Theoretical 1/(2α(1−α))",
    )
    ax3.set_xlabel("Step Size (α)", fontsize=11, fontweight="medium")
    ax3.set_ylabel("Iterations (log)", fontsize=11, fontweight="medium")
    ax3.set_title("Theoretical vs Empirical Complexity", fontsize=12, fontweight="bold")
    ax3.legend(loc="upper right", framealpha=0.95, fontsize=9)
    ax3.grid(True, alpha=0.3)

    # (4) Scalar unit-Hessian contraction: |x_{k+1}−x*| / |x_k−x*| = |1−α|
    bars4 = ax4.bar(
        range(len(step_sizes)),
        contraction_factors,
        tick_label=[f"α={s}" for s in step_sizes],
        color=quaternary_color,
        alpha=0.85,
    )
    ax4.set_xlabel("Step Size", fontsize=11, fontweight="medium")
    ax4.set_ylabel("Contraction Factor ρ", fontsize=11, fontweight="medium")
    ax4.set_title(
        "Error contraction per step (H = I)\nρ = |1 − α|  (smaller ρ ⇒ faster)",
        fontsize=12,
        fontweight="bold",
    )
    ax4.set_ylim(0, max(1.05, max(contraction_factors, default=1.0) * 1.15))
    ax4.axhline(y=0.5, color=VIZ_CONFIG["colors"]["neutral"], linestyle=":",
                linewidth=1, alpha=0.6, label="ρ = 0.5 (α = 0.5)")
    ax4.legend(loc="upper right", fontsize=9, framealpha=0.95)
    ax4.grid(True, alpha=0.3, axis="y")
    for bar, val in zip(bars4, contraction_factors):
        ax4.text(
            bar.get_x() + bar.get_width() / 2,
            val + 0.02,
            f"{val:.3f}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    plt.tight_layout()

    output_dir = project_root / "output" / "figures"
    plot_path = output_dir / "algorithm_complexity.png"
    plt.savefig(
        plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    plt.close()

    logger.info(f"Saved algorithm complexity visualization to: {plot_path}")
    return plot_path


def run_stability_analysis() -> Any:
    """Assess numerical stability of optimization algorithms."""
    logger = _get_logger()
    log = logger.info
    log("Running numerical stability analysis...")

    # Test different input ranges for stability
    test_inputs = [
        np.array([0.0]),  # Standard start point
        np.array([10.0]),  # Far from optimum
        np.array([-5.0]),  # Negative values
        np.array([0.1]),  # Close to optimum
    ]

    if INFRASTRUCTURE_AVAILABLE:
        # Use infrastructure scientific module
        stability_report = check_numerical_stability(
            func=functools.partial(quadratic_function, A=np.array([[1.0]]), b=np.array([1.0])),
            test_inputs=test_inputs,
            tolerance=1e-10,
        )
        stability_data = {
            "function_name": stability_report.function_name,
            "stability_score": stability_report.stability_score,
            "expected_behavior": stability_report.expected_behavior,
            "actual_behavior": stability_report.actual_behavior,
            "recommendations": stability_report.recommendations,
        }
    else:
        # Standalone stability analysis: run gradient descent for each test input
        # and compute stability score based on convergence to known optimum
        optimal_value = -0.5
        errors = []
        for x0 in test_inputs:
            result = gradient_descent(
                initial_point=x0,
                objective_func=lambda x: quadratic_function(x, np.array([[1.0]]), np.array([1.0])),
                gradient_func=lambda x: compute_gradient(x, np.array([[1.0]]), np.array([1.0])),
                step_size=0.1,
                max_iterations=500,
                tolerance=1e-12,
            )
            errors.append(abs(result.objective_value - optimal_value))
        max_error = max(errors)
        score = 1.0 if max_error < 1e-6 else max(0.0, 1.0 - np.log10(max_error + 1e-16) / 16)
        stability_data = {
            "function_name": "quadratic_function",
            "stability_score": float(score),
            "expected_behavior": "Converge to f(x*)=-0.5 for all starting points",
            "actual_behavior": f"Max error: {max_error:.2e} across {len(test_inputs)} inputs",
            "recommendations": [] if max_error < 1e-6 else ["Consider adaptive step size"],
        }

    # Save stability report
    output_dir = project_root / "output" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    import json

    stability_path = output_dir / "stability_analysis.json"
    with open(stability_path, "w") as f:
        json.dump(stability_data, f, indent=2)

    log(f"Stability analysis complete - Score: {stability_data['stability_score']:.2f}")
    log(f"Saved stability report to: {stability_path}")

    return stability_path


def run_performance_benchmarking() -> Any:
    """Benchmark gradient descent performance."""
    logger = _get_logger()
    log = logger.info
    log("Running performance benchmarking...")

    import time as _time

    # Different problem scales
    test_inputs = [
        np.array([0.0]),  # Standard case
        np.array([5.0]),  # Moderate distance
        np.array([20.0]),  # Large distance
    ]

    if INFRASTRUCTURE_AVAILABLE:
        # Use infrastructure scientific module
        benchmark_report = benchmark_function(
            func=functools.partial(quadratic_function, A=np.array([[1.0]]), b=np.array([1.0])),
            test_inputs=test_inputs,
            iterations=50,
        )
        benchmark_data = {
            "function_name": benchmark_report.function_name,
            "execution_time": benchmark_report.execution_time,
            "memory_usage": benchmark_report.memory_usage,
            "iterations": benchmark_report.iterations,
            "result_summary": benchmark_report.result_summary,
            "timestamp": benchmark_report.timestamp,
        }
        avg_time = benchmark_report.execution_time
    else:
        # Standalone benchmark: time gradient_descent calls across inputs
        timings = []
        for x0 in test_inputs:
            elapsed = []
            for _ in range(50):
                t0 = _time.perf_counter()
                gradient_descent(
                    initial_point=x0,
                    objective_func=lambda x: quadratic_function(x, np.array([[1.0]]), np.array([1.0])),
                    gradient_func=lambda x: compute_gradient(x, np.array([[1.0]]), np.array([1.0])),
                    step_size=0.1,
                    max_iterations=500,
                    tolerance=1e-12,
                )
                elapsed.append(_time.perf_counter() - t0)
            timings.append(np.mean(elapsed))
        avg_time = float(np.mean(timings))
        benchmark_data = {
            "function_name": "quadratic_function",
            "execution_time": avg_time,
            "memory_usage": 0.0,
            "iterations": 50,
            "result_summary": f"Avg {avg_time*1e6:.1f}μs across {len(test_inputs)} inputs",
            "timestamp": _time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

    # Save benchmark report
    output_dir = project_root / "output" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    import json

    benchmark_path = output_dir / "performance_benchmark.json"
    with open(benchmark_path, "w") as f:
        json.dump(benchmark_data, f, indent=2, default=str)

    log(f"Performance benchmarking complete - Avg time: {avg_time:.6f}s")
    log(f"Saved benchmark report to: {benchmark_path}")

    return benchmark_path


def generate_stability_visualization(stability_path: Any) -> Any:
    """Generate heatmap of optimizer accuracy across starting points and step sizes.

    Runs gradient_descent from multiple starting points with multiple step sizes,
    recording log₁₀|f(x) − f(x*)| for each combination. This directly exercises
    the package's core functions and reveals how numerical stability varies across
    the parameter space.
    """
    logger = _get_logger()

    if not stability_path:
        return None

    logger.info("Generating stability visualization...")

    exp_config = _load_experiment_config()
    A = np.array(exp_config.get("quadratic_A", [[1.0]]), dtype=float)
    b = np.array(exp_config.get("quadratic_b", [1.0]), dtype=float)
    x_star = np.linalg.solve(A, b)
    optimal_value = float(0.5 * x_star.T @ A @ x_star - b.T @ x_star)

    starting_points = exp_config.get(
        "stability_starting_points",
        [-50.0, -10.0, -5.0, 0.0, 0.1, 5.0, 10.0, 50.0],
    )
    step_sizes = exp_config.get(
        "stability_step_sizes",
        [0.01, 0.05, 0.1, 0.2, 0.5, 0.9],
    )
    max_iter = int(exp_config.get("max_iterations", 500))
    tol = float(exp_config.get("tolerance", 1e-8))

    obj_func, grad_func = make_quadratic_problem(A, b)

    # Build error matrix: rows=starting points, cols=step sizes
    error_matrix = np.zeros((len(starting_points), len(step_sizes)))
    for i, x0 in enumerate(starting_points):
        for j, alpha in enumerate(step_sizes):
            result = gradient_descent(
                initial_point=np.array([float(x0)]),
                objective_func=obj_func,
                gradient_func=grad_func,
                step_size=float(alpha),
                max_iterations=max_iter,
                tolerance=tol,
            )
            err = abs(result.objective_value - optimal_value)
            error_matrix[i, j] = np.log10(max(err, 1e-16))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={"width_ratios": [2, 1]})

    # Left: heatmap
    im = ax1.imshow(error_matrix, aspect="auto", cmap="RdYlGn_r",
                    vmin=-16, vmax=0, interpolation="nearest")
    ax1.set_xticks(range(len(step_sizes)))
    ax1.set_xticklabels([f"α={s}" for s in step_sizes], fontsize=10)
    ax1.set_yticks(range(len(starting_points)))
    ax1.set_yticklabels([f"x₀={x:g}" for x in starting_points], fontsize=10)
    ax1.set_xlabel("Step Size", fontsize=11, fontweight="medium")
    ax1.set_ylabel("Starting Point", fontsize=11, fontweight="medium")
    ax1.set_title("Numerical Stability Heatmap\nlog₁₀ |f(x) − f(x*)|  (darker green = more accurate)",
                  fontsize=12, fontweight="bold", pad=12)

    # Annotate cells with values
    for i in range(len(starting_points)):
        for j in range(len(step_sizes)):
            val = error_matrix[i, j]
            color = "white" if val > -4 else "black"
            ax1.text(j, i, f"{val:.0f}", ha="center", va="center",
                     fontsize=8, fontweight="bold", color=color)

    cbar = fig.colorbar(im, ax=ax1, fraction=0.046, pad=0.04)
    cbar.set_label("log₁₀ |error|", fontsize=10)

    # Right: stability score summary from JSON
    import json
    with open(stability_path, "r") as f:
        stability_data = json.load(f)

    score = stability_data["stability_score"]
    ax2.barh([0], [score], color=VIZ_CONFIG["colors"]["success"], alpha=0.85, height=0.4)
    ax2.barh([0], [1.0], color=VIZ_CONFIG["colors"]["neutral"], alpha=0.15, height=0.4)
    ax2.set_xlim(0, 1.1)
    ax2.set_yticks([0])
    ax2.set_yticklabels(["Overall"])
    ax2.set_xlabel("Stability Score", fontsize=11, fontweight="medium")
    ax2.set_title(f"Stability Score: {score:.2f}", fontsize=12, fontweight="bold")
    ax2.text(score + 0.02, 0, f"{score:.2f}", va="center", fontsize=12, fontweight="bold")

    # Summary stats below
    all_cells = error_matrix.flatten()
    ax2.text(0.05, -0.8, f"Cells tested: {len(all_cells)}", fontsize=10,
             transform=ax2.get_yaxis_transform())
    ax2.text(0.05, -1.2, f"Min error: 10^{all_cells.min():.0f}", fontsize=10,
             transform=ax2.get_yaxis_transform())
    ax2.text(0.05, -1.6, f"Max error: 10^{all_cells.max():.0f}", fontsize=10,
             transform=ax2.get_yaxis_transform())
    ax2.set_ylim(-2.5, 0.8)
    ax2.grid(True, alpha=0.3, axis="x")

    plt.tight_layout()

    output_dir = project_root / "output" / "figures"
    plot_path = output_dir / "stability_analysis.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    logger.info(f"Saved stability visualization to: {plot_path}")
    return plot_path


def generate_benchmark_visualization(benchmark_path: Any) -> Any:
    """Generate dimensional scaling benchmark by running gradient_descent at d=1..50.

    Left: mean execution time (μs) per gradient_descent call vs problem dimension.
    Right: iterations to convergence vs problem dimension.
    Actually exercises the package at multiple dimensionalities.
    """
    logger = _get_logger()

    if not benchmark_path:
        return None

    logger.info("Generating benchmark visualization...")

    import time

    exp_config = _load_experiment_config()
    dimensions = exp_config.get("benchmark_dimensions", [1, 2, 5, 10, 20, 50])
    times_us = []
    iter_counts = []

    for d in dimensions:
        A = np.eye(d)
        b = np.ones(d)
        x0 = np.zeros(d)

        obj_func, grad_func = make_quadratic_problem(A, b)

        # Time 20 runs
        elapsed = []
        for _ in range(20):
            t0 = time.perf_counter()
            result = gradient_descent(
                initial_point=x0,
                objective_func=obj_func,
                gradient_func=grad_func,
                step_size=0.1,
                max_iterations=500,
                tolerance=1e-10,
            )
            elapsed.append(time.perf_counter() - t0)

        times_us.append(np.mean(elapsed) * 1e6)  # microseconds
        iter_counts.append(result.iterations)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=VIZ_CONFIG["figure"]["figsize_double"])

    color1 = VIZ_CONFIG["colors"]["primary"]
    color2 = VIZ_CONFIG["colors"]["secondary"]

    # Left: Execution time vs dimension
    ax1.bar(range(len(dimensions)), times_us,
            tick_label=[str(d) for d in dimensions],
            color=color1, alpha=0.85)
    ax1.set_xlabel("Problem Dimension (d)", fontsize=11, fontweight="medium")
    ax1.set_ylabel("Execution Time (μs)", fontsize=11, fontweight="medium")
    ax1.set_title("Execution Time vs Problem Dimension\ngradient_descent() wall-clock scaling",
                  fontsize=12, fontweight="bold", pad=12)
    ax1.grid(True, alpha=0.3, axis="y")
    for i, val in enumerate(times_us):
        ax1.text(i, val + max(times_us) * 0.02, f"{val:.0f}μs",
                 ha="center", va="bottom", fontsize=9, fontweight="bold")

    # Right: Iterations vs dimension
    ax2.bar(range(len(dimensions)), iter_counts,
            tick_label=[str(d) for d in dimensions],
            color=color2, alpha=0.85)
    ax2.set_xlabel("Problem Dimension (d)", fontsize=11, fontweight="medium")
    ax2.set_ylabel("Iterations to Convergence", fontsize=11, fontweight="medium")
    ax2.set_title("Convergence Iterations vs Dimension\nα=0.1, tol=10⁻¹⁰, identity Hessian",
                  fontsize=12, fontweight="bold", pad=12)
    ax2.grid(True, alpha=0.3, axis="y")
    for i, val in enumerate(iter_counts):
        ax2.text(i, val + max(iter_counts) * 0.02, str(val),
                 ha="center", va="bottom", fontsize=9, fontweight="bold")

    plt.tight_layout()

    output_dir = project_root / "output" / "figures"
    plot_path = output_dir / "performance_benchmark.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    logger.info(f"Saved benchmark visualization to: {plot_path}")
    return plot_path


def generate_analysis_dashboard(results: Any, stability_path: Any = None, benchmark_path: Any = None) -> Any:
    """Generate comprehensive analysis dashboard."""
    logger = _get_logger()
    logger.info("Generating analysis dashboard...")

    try:
        # Ensure output directory structure exists
        output_dir = project_root / "output" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Collect output summary (may fail if output dirs are empty/missing
        # or if infrastructure is not available and collect_output_statistics is undefined)
        try:
            output_statistics = collect_output_statistics(
                project_root, project_name="code_project"
            )
        except (OSError, ValueError, TypeError, KeyError, NameError) as stats_err:
            logger.debug(f"Output statistics collection failed (non-fatal): {stats_err}")
            output_statistics = {}

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
            html_content += """
            <div class="metric">
                <h3>Numerical Stability</h3>
                <p>Stability analysis completed</p>
                <p>Report: <a href="reports/stability_analysis.json">stability_analysis.json</a></p>
            </div>
            """

        if benchmark_path:
            html_content += """
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

        logger.info(f"Saved analysis dashboard to: {dashboard_path}")
        return dashboard_path

    except (OSError, ValueError, TypeError, NameError) as e:
        logger.warning(f"Failed to generate dashboard: {e}")
        return None
    except Exception as e:  # noqa: BLE001 — catch infrastructure-specific exceptions
        logger.warning(f"Unexpected error generating dashboard: {e}")
        return None


def validate_generated_outputs() -> Any:
    """Validate integrity of generated analysis outputs."""
    logger = _get_logger()
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
        logger.warning(f"Output validation failed: {e}")
        return None
    except (OSError, ValueError, TypeError) as e:
        logger.warning(f"Unexpected error during output validation: {e}")
        return None


def save_validation_report(validation_report: Any) -> Any:
    """Save validation report to file."""
    logger = _get_logger()

    if not validation_report:
        return None

    try:
        output_dir = project_root / "output" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        report_path = output_dir / "output_validation.json"
        import json

        with open(report_path, "w") as f:
            json.dump(validation_report, f, indent=2, default=str)

        logger.info(f"Saved validation report to: {report_path}")
        return report_path

    except (OSError, json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning(f"Failed to save validation report: {e}")
        return None


def register_figure() -> None:
    """Register the generated figures for manuscript reference."""
    logger = _get_logger()

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

        # Add scientific analysis figures (always generated)
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
            logger.info(f"Registered figure with label: {label}")

    except ImportError as e:
        logger.warning(f"Figure manager not available: {e}")
    except (OSError, ValueError, TypeError) as e:
        logger.warning(f"Failed to register figures: {e}")


def main() -> None:
    """Main analysis function."""
    apply_visualization_style()
    logger = _get_logger()

    def log_info(msg: str) -> None:
        logger.info(msg)

    def log_warning(msg: str) -> None:
        logger.warning(msg)

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
        if INFRASTRUCTURE_AVAILABLE:
            checkpoint_dir = project_root / "output" / "checkpoints"
            CheckpointManager(checkpoint_dir)  # Initialize checkpoint manager
            log_info("Checkpoint manager initialized")

        # Performance monitoring (decorator-based; not used as context manager)
        from contextlib import nullcontext

        with nullcontext():
            log_info(
                "Performance monitoring available"
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
            stability_plot = None
            benchmark_plot = None
            dashboard_path = None

            # Scientific analysis (works with or without infrastructure)
            log_info("Running scientific analysis...")
            log_info("Numerical stability analysis...")
            stability_path = run_stability_analysis()

            log_info("Performance benchmarking...")
            benchmark_path = run_performance_benchmarking()

            # Generate scientific visualizations
            log_info("Generating scientific visualizations...")
            stability_plot = generate_stability_visualization(stability_path)
            benchmark_plot = generate_benchmark_visualization(benchmark_path)

            # Generate comprehensive dashboard (requires infrastructure)
            if INFRASTRUCTURE_AVAILABLE:
                log_info("Generating analysis dashboard...")
                dashboard_path = generate_analysis_dashboard(
                    results, stability_path, benchmark_path
                )
            else:
                log_warning(
                    "Infrastructure not available - skipping dashboard generation"
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

            # Generate publishing materials (requires infrastructure for citations)
            log_info("Generating publishing materials...")
            publishing_metadata = extract_optimization_metadata(results)
            if publishing_metadata and INFRASTRUCTURE_AVAILABLE:
                citations = generate_citations_from_metadata(publishing_metadata)
                save_publishing_materials(publishing_metadata, citations)
            elif publishing_metadata:
                log_info("Skipping citation generation (infrastructure not available)")

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
                except (OSError, ImportError, ValueError) as e:
                    log_warning(f"Publishing demonstration failed: {e}")

        # Performance metrics not available (monitor_performance is a decorator)
        if INFRASTRUCTURE_AVAILABLE:
            log_info("Pipeline completed with infrastructure support")

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
        logger.error(f"Import error: {e}", exc_info=True)
        logger.error("Suggestions:")
        logger.error("  - Run from repo root so infrastructure is importable")
        logger.error("  - Ensure dependencies are installed (use `uv sync`)")
        raise

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}", exc_info=True)
        logger.error("Suggestions:")
        logger.error("  - Ensure project structure is correct")
        logger.error("  - Ensure analysis outputs directory is writable")
        raise

    except Exception as e:  # noqa: BLE001 - top-level main handler with isinstance dispatching
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
        logger.error(error_msg, exc_info=True)
        logger.error("Suggestions:")
        logger.error("  - Check system requirements and dependencies")
        logger.error("  - Review error logs for detailed information")
        logger.error("  - Ensure sufficient disk space and memory")
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

    except (KeyError, ValueError, TypeError, AttributeError) as e:
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

    except (KeyError, ValueError, TypeError, ImportError, NameError) as e:
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

    except (OSError, json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
        if INFRASTRUCTURE_AVAILABLE:
            logger = get_logger(__name__)
            logger.warning(f"Failed to save publishing materials: {e}")


if __name__ == "__main__":
    main()
