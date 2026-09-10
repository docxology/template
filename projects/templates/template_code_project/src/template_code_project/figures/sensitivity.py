"""Step-size sensitivity figure generator."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt

from ..experiment_config import ExperimentConfig
from ..optimizer import quadratic_optimum
from ..sweeps import sensitivity_sweep
from ..viz_config import VIZ_CONFIG
from ._common import experiment_config, get_logger, project_root


def generate_step_size_sensitivity_plot(results: Any, config: ExperimentConfig | None = None) -> Any:
    """Generate step size sensitivity analysis with expanded range."""
    del results  # sweep uses unified α grid from sweeps.sensitivity_sweep
    logger = get_logger()
    logger.info("Generating step size sensitivity plot...")

    cfg = config or experiment_config()
    A = cfg.A_array()
    b = cfg.b_array()
    _, f_star = quadratic_optimum(A, b)

    sweep = sensitivity_sweep(cfg)
    sweep_alphas = sweep.alphas
    sweep_iters = sweep.iterations
    sweep_obj_vals = sweep.final_obj

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=VIZ_CONFIG["figure"]["figsize_double"])
    color_primary = VIZ_CONFIG["colors"]["primary"]
    color_secondary = VIZ_CONFIG["colors"]["secondary"]
    color_success = VIZ_CONFIG["colors"]["success"]

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
    ax2.legend(loc="upper right", fontsize=VIZ_CONFIG["fonts"]["legend"])
    ax2.set_xscale("log")
    ax2.set_ylim(f_star - 0.1, 0.1)
    plt.tight_layout()

    output_dir = project_root() / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_dir / "step_size_sensitivity.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    logger.info("Saved step size sensitivity plot to: %s", plot_path)
    return plot_path


__all__ = ["generate_step_size_sensitivity_plot"]
