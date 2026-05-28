"""Algorithm complexity figure generator."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from ..experiment_config import ExperimentConfig
from ..optimizer import quadratic_optimum
from ..viz_config import VIZ_CONFIG, agency_category
from ._common import experiment_config, get_logger, project_root


def generate_complexity_visualization(results: Any, config: ExperimentConfig | None = None) -> Any:
    """Generate algorithm performance analysis with four informative panels."""
    logger = get_logger()
    logger.info("Generating algorithm complexity visualization...")

    cfg = config or experiment_config()
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

    theoretical_complexity: list[float] = []
    contraction_factors: list[float] = []
    for alpha in step_sizes:
        rho = abs(1 - alpha)
        contraction_factors.append(rho)
        if 0 < rho < 1:
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

    bar_colors = [agency_category(s)[1] for s in step_sizes]
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
        y=0.5,
        color=VIZ_CONFIG["colors"]["neutral"],
        linestyle=":",
        linewidth=1,
        alpha=0.6,
        label="ρ = 0.5 (α = 0.5)",
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
    output_dir = project_root() / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_dir / "algorithm_complexity.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    logger.info("Saved algorithm complexity visualization to: %s", plot_path)
    return plot_path


__all__ = ["generate_complexity_visualization"]
