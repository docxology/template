"""Convergence trajectory figure generators."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from ..experiment_config import ExperimentConfig
from ..optimizer import quadratic_optimum
from ..viz_config import VIZ_CONFIG, agency_category
from ._common import experiment_config, get_logger, project_root, save_figure_data


def generate_convergence_plot(results: Any, config: ExperimentConfig | None = None) -> Any:
    """Generate convergence plot showing objective value vs iteration."""
    logger = get_logger()
    logger.info("Generating convergence plot...")

    cfg = config or experiment_config()
    A = cfg.A_array()
    b = cfg.b_array()
    _, f_star = quadratic_optimum(A, b)

    fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure"]["figsize_single"])
    step_sizes = list(results.keys())
    plot_data: dict[str, object] = {}

    for step_size in step_sizes:
        result = results[step_size]
        category, color = agency_category(step_size)
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
    ax.set_title("Gradient Descent Convergence Analysis\nQuadratic Minimization", pad=15)
    ax.legend(
        loc="upper right",
        fontsize=VIZ_CONFIG["fonts"]["legend"],
        title="Learning Rate",
        title_fontsize=VIZ_CONFIG["fonts"]["legend"],
    )
    ax.set_ylim(bottom=-0.7, top=10)
    plt.tight_layout()

    output_dir = project_root() / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_dir / "convergence_plot.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    save_figure_data(plot_data, "convergence_plot", project_root() / "output")
    logger.info("Saved convergence plot to: %s", plot_path)
    return plot_path


def generate_convergence_rate_plot(results: Any, config: ExperimentConfig | None = None) -> Any:
    """Generate convergence rate comparison plot."""
    logger = get_logger()
    logger.info("Generating convergence rate comparison plot...")

    cfg = config or experiment_config()
    A = cfg.A_array()
    b = cfg.b_array()
    _, f_star = quadratic_optimum(A, b)
    conv_tol = float(cfg.convergence_tolerance)

    fig, ax = plt.subplots(figsize=VIZ_CONFIG["figure"]["figsize_single"])
    step_sizes = list(results.keys())

    for step_size in step_sizes:
        category, color = agency_category(step_size)
        result = results[step_size]
        history = result.objective_history or []
        iterations = list(range(len(history)))
        errors = [abs(obj - f_star) for obj in history]
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
    ax.set_title("Convergence Rate Comparison\nLinear Convergence on Logarithmic Scale", pad=15)
    ax.legend(
        loc="upper right",
        fontsize=VIZ_CONFIG["fonts"]["legend"],
        title="Learning Rate",
        title_fontsize=VIZ_CONFIG["fonts"]["legend"],
    )
    ax.set_yscale("log")
    ax.set_ylim(1e-12, 1e4)
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

    output_dir = project_root() / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_dir / "convergence_rate_comparison.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    logger.info("Saved convergence rate comparison plot to: %s", plot_path)
    return plot_path


__all__ = ["generate_convergence_plot", "generate_convergence_rate_plot"]
