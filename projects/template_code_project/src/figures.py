"""Figure generators for the template_code_project exemplar.

Publication-quality figure generation: matplotlib style, colorblind-safe
palette, agency-category classification, and six ``generate_*`` functions
referenced by ``manuscript/03_results.md``.
"""
# ruff: noqa: E402

import json
import logging
from pathlib import Path
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np

try:
    from .experiment_config import ExperimentConfig, load_experiment_config
    from .optimizer import (
        gradient_descent,
        make_quadratic_problem,
        quadratic_optimum,
        simulate_trajectory,
    )
except ImportError:  # pragma: no cover - supports direct module execution
    from experiment_config import ExperimentConfig, load_experiment_config  # type: ignore[no-redef]
    from optimizer import (  # type: ignore[no-redef]
        gradient_descent,
        make_quadratic_problem,
        quadratic_optimum,
        simulate_trajectory,
    )


# Logger: prefer the infrastructure logger, fall back to stdlib.
try:
    from infrastructure.core.logging.utils import get_logger as _infra_get_logger

    def _get_logger() -> logging.Logger:
        return _infra_get_logger(__name__)
except ImportError:  # pragma: no cover

    def _get_logger() -> logging.Logger:
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger


# Project root: projects/template_code_project/
project_root = Path(__file__).resolve().parent.parent


def _experiment_config() -> ExperimentConfig:
    return load_experiment_config(project_root)


# =============================================================================
# VISUALIZATION CONFIGURATION - Accessibility & Publication Quality
# =============================================================================
# Colorblind-safe palette (IBM Design Language / Wong palette)
# Tested for deuteranopia, protanopia, and tritanopia accessibility
VIZ_CONFIG: Dict[str, Any] = {
    "colors": {
        "primary": "#0072B2",  # Blue (safe for all color blindness)
        "secondary": "#D55E00",  # Vermillion/Orange
        "tertiary": "#009E73",  # Bluish green
        "quaternary": "#CC79A7",  # Reddish purple
        "neutral": "#999999",  # Gray for reference lines
        "success": "#009E73",  # Green (same as tertiary)
        "warning": "#F0E442",  # Yellow
        "error": "#D55E00",  # Same as secondary
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


def apply_visualization_style() -> None:
    """Apply global matplotlib style for publication-quality, accessible figures."""
    plt.rcParams.update(
        {
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
        }
    )


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


def generate_convergence_plot(results: Any, config: ExperimentConfig | None = None) -> Any:
    """Generate convergence plot showing objective value vs iteration.

    Uses agency-category colors and handles divergent trajectories.
    """
    logger = _get_logger()
    logger.info("Generating convergence plot...")

    cfg = config or _experiment_config()
    A = cfg.A_array()
    b = cfg.b_array()
    _, f_star = quadratic_optimum(A, b)

    fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure"]["figsize_single"])

    step_sizes = list(results.keys())
    plot_data = {}

    for step_size in step_sizes:
        result = results[step_size]
        category, color = _agency_category(step_size)

        history = result.objective_history or []
        iterations = list(range(len(history)))
        objectives = np.array(history, dtype=float)
        objectives = np.clip(objectives, -10, 100)

        ax.plot(
            iterations,
            objectives,
            color=color,
            linewidth=VIZ_CONFIG["lines"]["linewidth"],
            label=f"α = {step_size} ({category})",
            marker="o",
            markersize=VIZ_CONFIG["lines"]["markersize"],
            markeredgewidth=VIZ_CONFIG["lines"]["markeredgewidth"],
            markerfacecolor="white",
            markevery=max(1, len(iterations) // 8) if iterations else 1,
        )
        plot_data[str(step_size)] = {
            "category": category,
            "iterations": iterations,
            "objectives": [float(o) for o in objectives],
        }

    ax.axhline(
        y=f_star,
        color=VIZ_CONFIG["colors"]["neutral"],
        linestyle="--",
        linewidth=2,
        alpha=0.8,
        label=f"Optimal: f(x*) = {f_star:.4g}",
    )

    ax.set_xlabel("Iteration")
    ax.set_ylabel("Objective Value f(x)")
    ax.set_title(
        "Gradient Descent Convergence Analysis\nQuadratic Minimization",
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
    plt.savefig(plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    # Save companion data
    _save_figure_data(plot_data, "convergence_plot", project_root / "output")

    logger.info(f"Saved convergence plot to: {plot_path}")
    return plot_path


# simulate_trajectory is imported from src/optimizer — no reimplementation here.
# It delegates to gradient_descent() and returns {"iterations": [...], "objectives": [...]}.


def generate_step_size_sensitivity_plot(results: Any, config: ExperimentConfig | None = None) -> Any:
    """Generate step size sensitivity analysis with expanded range."""
    logger = _get_logger()
    logger.info("Generating step size sensitivity plot...")

    cfg = config or _experiment_config()
    A = cfg.A_array()
    b = cfg.b_array()
    x0 = cfg.x0()
    _, f_star = quadratic_optimum(A, b)

    sweep_alphas = [0.005, 0.01, 0.02, 0.05, 0.08, 0.1, 0.15, 0.2, 0.3, 0.4]
    sweep_iters = []
    sweep_obj_vals = []

    for alpha in sweep_alphas:
        traj = simulate_trajectory(
            alpha,
            max_iter=500,
            A=A,
            b=b,
            initial_point=x0,
        )
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
    for x, y in [
        (sweep_alphas[0], sweep_iters[0]),
        (sweep_alphas[4], sweep_iters[4]),
        (sweep_alphas[-1], sweep_iters[-1]),
    ]:
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
        y=f_star,
        color=color_success,
        linestyle="--",
        linewidth=2.5,
        alpha=0.9,
        label=f"Optimal f(x*) = {f_star:.4g}",
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
        f"Solution Quality vs Step Size\nAll stable step sizes reach f(x*)={f_star:.4g}",
        pad=12,
    )
    ax2.legend(
        loc="upper right",
        fontsize=VIZ_CONFIG["fonts"]["legend"],
    )
    ax2.set_xscale("log")
    ax2.set_ylim(f_star - 0.1, 0.1)

    plt.tight_layout()

    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_dir / "step_size_sensitivity.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    logger.info(f"Saved step size sensitivity plot to: {plot_path}")
    return plot_path


def generate_convergence_rate_plot(results: Any, config: ExperimentConfig | None = None) -> Any:
    """Generate convergence rate comparison plot."""
    logger = _get_logger()
    logger.info("Generating convergence rate comparison plot...")

    cfg = config or _experiment_config()
    A = cfg.A_array()
    b = cfg.b_array()
    _, f_star = quadratic_optimum(A, b)
    conv_tol = float(cfg.convergence_tolerance)

    fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure"]["figsize_single"])

    step_sizes = list(results.keys())

    for step_size in step_sizes:
        category, color = _agency_category(step_size)
        result = results[step_size]
        history = result.objective_history or []
        iterations = list(range(len(history)))
        objectives = history

        errors = [abs(obj - f_star) for obj in objectives]

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
            markevery=max(1, max_plot_iter // 8) if max_plot_iter else 1,
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
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_dir / "convergence_rate_comparison.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    logger.info(f"Saved convergence rate comparison plot to: {plot_path}")
    return plot_path


def generate_complexity_visualization(results: Any, config: ExperimentConfig | None = None) -> Any:
    """Generate algorithm performance analysis with 4 informative panels."""
    logger = _get_logger()
    logger.info("Generating algorithm complexity visualization...")

    cfg = config or _experiment_config()
    conv_tol = float(cfg.convergence_tolerance)
    log_tol = float(np.log10(conv_tol))
    _, f_star = quadratic_optimum(cfg.A_array(), cfg.b_array())

    step_sizes = list(results.keys())
    iterations = [results[step_size].iterations for step_size in step_sizes]

    log_errors = []
    for step_size in step_sizes:
        obj_val = results[step_size].objective_value
        err = abs(obj_val - f_star)
        log_errors.append(np.log10(max(err, 1e-16)))

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
    bar_colors_2 = [success_color if le < log_tol else theory_color if le < -3 else bar_color for le in log_errors]
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
    ax4.axhline(
        y=0.5, color=VIZ_CONFIG["colors"]["neutral"], linestyle=":", linewidth=1, alpha=0.6, label="ρ = 0.5 (α = 0.5)"
    )
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
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_dir / "algorithm_complexity.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    logger.info(f"Saved algorithm complexity visualization to: {plot_path}")
    return plot_path


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

    exp_config = _experiment_config()
    A = exp_config.A_array()
    b = exp_config.b_array()
    _, optimal_value = quadratic_optimum(A, b)

    starting_points = list(exp_config.stability_starting_points)
    step_sizes = list(exp_config.stability_step_sizes)
    max_iter = int(exp_config.max_iterations)
    tol = float(exp_config.tolerance)

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
    im = ax1.imshow(error_matrix, aspect="auto", cmap="RdYlGn_r", vmin=-16, vmax=0, interpolation="nearest")
    ax1.set_xticks(range(len(step_sizes)))
    ax1.set_xticklabels([f"α={s}" for s in step_sizes], fontsize=10)
    ax1.set_yticks(range(len(starting_points)))
    ax1.set_yticklabels([f"x₀={x:g}" for x in starting_points], fontsize=10)
    ax1.set_xlabel("Step Size", fontsize=11, fontweight="medium")
    ax1.set_ylabel("Starting Point", fontsize=11, fontweight="medium")
    ax1.set_title(
        "Numerical Stability Heatmap\nlog₁₀ |f(x) − f(x*)|  (darker green = more accurate)",
        fontsize=12,
        fontweight="bold",
        pad=12,
    )

    # Annotate cells with values
    for i in range(len(starting_points)):
        for j in range(len(step_sizes)):
            val = error_matrix[i, j]
            color = "white" if val > -4 else "black"
            ax1.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=8, fontweight="bold", color=color)

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
    ax2.text(0.05, -0.8, f"Cells tested: {len(all_cells)}", fontsize=10, transform=ax2.get_yaxis_transform())
    ax2.text(0.05, -1.2, f"Min error: 10^{all_cells.min():.0f}", fontsize=10, transform=ax2.get_yaxis_transform())
    ax2.text(0.05, -1.6, f"Max error: 10^{all_cells.max():.0f}", fontsize=10, transform=ax2.get_yaxis_transform())
    ax2.set_ylim(-2.5, 0.8)
    ax2.grid(True, alpha=0.3, axis="x")

    plt.tight_layout()

    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
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

    exp_config = _experiment_config()
    dimensions = list(exp_config.benchmark_dimensions)
    times_us: list[float] = []
    iter_counts: list[int] = []

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

        times_us.append(float(np.mean(elapsed) * 1e6))  # microseconds
        iter_counts.append(result.iterations)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=VIZ_CONFIG["figure"]["figsize_double"])

    color1 = VIZ_CONFIG["colors"]["primary"]
    color2 = VIZ_CONFIG["colors"]["secondary"]

    # Left: Execution time vs dimension
    ax1.bar(range(len(dimensions)), times_us, tick_label=[str(d) for d in dimensions], color=color1, alpha=0.85)
    ax1.set_xlabel("Problem Dimension (d)", fontsize=11, fontweight="medium")
    ax1.set_ylabel("Execution Time (μs)", fontsize=11, fontweight="medium")
    ax1.set_title(
        "Execution Time vs Problem Dimension\ngradient_descent() wall-clock scaling",
        fontsize=12,
        fontweight="bold",
        pad=12,
    )
    ax1.grid(True, alpha=0.3, axis="y")
    for i, val in enumerate(times_us):
        ax1.text(i, val + max(times_us) * 0.02, f"{val:.0f}μs", ha="center", va="bottom", fontsize=9, fontweight="bold")

    # Right: Iterations vs dimension
    ax2.bar(range(len(dimensions)), iter_counts, tick_label=[str(d) for d in dimensions], color=color2, alpha=0.85)
    ax2.set_xlabel("Problem Dimension (d)", fontsize=11, fontweight="medium")
    ax2.set_ylabel("Iterations to Convergence", fontsize=11, fontweight="medium")
    ax2.set_title(
        "Convergence Iterations vs Dimension\nα=0.1, tol=10⁻¹⁰, identity Hessian",
        fontsize=12,
        fontweight="bold",
        pad=12,
    )
    ax2.grid(True, alpha=0.3, axis="y")
    for i, val in enumerate(iter_counts):
        ax2.text(i, val + max(iter_counts) * 0.02, str(val), ha="center", va="bottom", fontsize=9, fontweight="bold")

    plt.tight_layout()

    output_dir = project_root / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_dir / "performance_benchmark.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    logger.info(f"Saved benchmark visualization to: {plot_path}")
    return plot_path
