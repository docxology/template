"""Numeric payload and sweep sampling for the interactive dashboard."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .experiment_config import ExperimentConfig, load_experiment_config
from .optimizer import quadratic_function, simulate_trajectory
from .project_paths import _DEFAULT_ROOT as PROJECT_ROOT
from .sweeps import AlphaSweepConfig, run_alpha_sweep


def load_yaml_defaults(_path: Path) -> ExperimentConfig:
    """Load experiment defaults from ``manuscript/config.yaml``."""
    return load_experiment_config(PROJECT_ROOT)


def to_diagonal_A(diag: list[float]) -> np.ndarray:
    """Convert this object to diagonal A."""
    return np.diag(np.array(diag, dtype=np.float64))


def compute_payload(args, *, sweep_runner=run_alpha_sweep) -> dict:
    """Process compute payload."""
    A = to_diagonal_A(args.A)
    b = np.array(args.b, dtype=np.float64)
    x_star = np.linalg.solve(A, b)
    f_star = float(quadratic_function(x_star, A=A, b=b))
    eig = np.linalg.eigvalsh(A)
    stable_bound = float(2.0 / eig.max())

    trajectories: dict[str, dict] = {}
    for alpha in args.step_sizes:
        traj = simulate_trajectory(
            float(alpha),
            max_iter=min(args.max_iter, 200),
            A=A,
            b=b,
            initial_point=np.array(args.x0, dtype=np.float64),
        )
        trajectories[f"{float(alpha):.4f}"] = {
            "iterations": list(traj["iterations"]),
            "objectives": list(traj["objectives"]),
        }

    sweep = sweep_runner(
        AlphaSweepConfig(
            alpha_min=float(args.alpha_sweep_min),
            alpha_max=float(args.alpha_sweep_max),
            alpha_num=int(args.alpha_sweep_num),
            A=A,
            b=b,
            initial_point=np.array(args.x0, dtype=np.float64),
            max_iterations=int(args.max_iter),
            tolerance=float(args.tol),
        )
    )

    xs = np.linspace(args.landscape_x_min, args.landscape_x_max, args.landscape_num)
    fs = []
    for x in xs:
        xv = np.zeros_like(b)
        xv[0] = x
        fs.append(float(quadratic_function(xv, A=A, b=b)))

    return {
        "step_sizes": [float(a) for a in args.step_sizes],
        "A_diagonal": [float(v) for v in args.A],
        "b": [float(v) for v in args.b],
        "x0": [float(v) for v in args.x0],
        "x_star": x_star.tolist(),
        "f_star": f_star,
        "eigenvalues": eig.tolist(),
        "condition_number": float(eig.max() / eig.min()),
        "stable_step_bound": stable_bound,
        "trajectories": trajectories,
        "alpha_sweep": {
            "alphas": sweep.alphas,
            "iterations": sweep.iterations,
            "final_dist": sweep.final_dist,
            "final_obj": sweep.final_obj,
            "diverged": sweep.diverged,
        },
        "landscape": {"x": xs.tolist(), "f": fs},
    }


__all__ = ["compute_payload", "load_yaml_defaults", "to_diagonal_A"]
