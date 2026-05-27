"""Stability and benchmark figure generators."""

from __future__ import annotations

import json
import time
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from ..optimizer import gradient_descent, make_quadratic_problem
from ..sweeps import stability_error_matrix
from ..viz_config import VIZ_CONFIG
from ._common import experiment_config, get_logger, project_root


def generate_stability_visualization(stability_path: Any) -> Any:
    """Generate heatmap of optimizer accuracy across starting points and step sizes."""
    logger = get_logger()
    if not stability_path:
        return None

    logger.info("Generating stability visualization...")
    exp_config = experiment_config()
    starting_points = list(exp_config.stability_starting_points)
    step_sizes = list(exp_config.stability_step_sizes)
    error_matrix = stability_error_matrix(exp_config)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={"width_ratios": [2, 1]})
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

    for i in range(len(starting_points)):
        for j in range(len(step_sizes)):
            val = error_matrix[i, j]
            color = "white" if val > -4 else "black"
            ax1.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=8, fontweight="bold", color=color)

    cbar = fig.colorbar(im, ax=ax1, fraction=0.046, pad=0.04)
    cbar.set_label("log₁₀ |error|", fontsize=10)

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

    all_cells = error_matrix.flatten()
    ax2.text(0.05, -0.8, f"Cells tested: {len(all_cells)}", fontsize=10, transform=ax2.get_yaxis_transform())
    ax2.text(0.05, -1.2, f"Min error: 10^{all_cells.min():.0f}", fontsize=10, transform=ax2.get_yaxis_transform())
    ax2.text(0.05, -1.6, f"Max error: 10^{all_cells.max():.0f}", fontsize=10, transform=ax2.get_yaxis_transform())
    ax2.set_ylim(-2.5, 0.8)
    ax2.grid(True, alpha=0.3, axis="x")
    plt.tight_layout()

    output_dir = project_root() / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_dir / "stability_analysis.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    logger.info("Saved stability visualization to: %s", plot_path)
    return plot_path


def generate_benchmark_visualization(benchmark_path: Any) -> Any:
    """Generate dimensional scaling benchmark by running gradient_descent at d=1..50."""
    logger = get_logger()
    if not benchmark_path:
        return None

    del benchmark_path
    logger.info("Generating benchmark visualization...")
    exp_config = experiment_config()
    dimensions = list(exp_config.benchmark_dimensions)
    times_us: list[float] = []
    iter_counts: list[int] = []

    for d in dimensions:
        A = np.eye(d)
        b = np.ones(d)
        x0 = np.zeros(d)
        obj_func, grad_func = make_quadratic_problem(A, b)
        elapsed = []
        last_result = None
        for _ in range(20):
            t0 = time.perf_counter()
            last_result = gradient_descent(
                initial_point=x0,
                objective_func=obj_func,
                gradient_func=grad_func,
                step_size=0.1,
                max_iterations=500,
                tolerance=1e-10,
            )
            elapsed.append(time.perf_counter() - t0)
        times_us.append(float(np.mean(elapsed) * 1e6))
        iter_counts.append(last_result.iterations if last_result else 0)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=VIZ_CONFIG["figure"]["figsize_double"])
    color1 = VIZ_CONFIG["colors"]["primary"]
    color2 = VIZ_CONFIG["colors"]["secondary"]

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
    output_dir = project_root() / "output" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_dir / "performance_benchmark.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close()

    logger.info("Saved benchmark visualization to: %s", plot_path)
    return plot_path


__all__ = ["generate_benchmark_visualization", "generate_stability_visualization"]
