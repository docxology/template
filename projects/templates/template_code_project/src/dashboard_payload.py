"""Numeric payload and sweep sampling for the interactive dashboard."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from .experiment_config import ExperimentConfig, load_experiment_config
from .optimizer import quadratic_function, simulate_trajectory
from .project_paths import _DEFAULT_ROOT as PROJECT_ROOT
from .sweeps import AlphaSweepConfig, run_alpha_sweep

DASHBOARD_PAYLOAD_SCHEMA_VERSION = 1


class DashboardPayloadError(ValueError):
    """Raised when a dashboard payload is structurally incomplete."""


def validate_dashboard_payload(payload: Mapping[str, Any]) -> tuple[str, ...]:
    """Return schema findings for a dashboard payload.

    The validator checks the producer/consumer contract without asserting a
    scientific result. Infinite distances are valid divergence diagnostics;
    missing fields, NaNs, and mismatched chart-vector lengths are not.
    """
    required = (
        "schema_version",
        "step_sizes",
        "A_diagonal",
        "b",
        "x0",
        "x_star",
        "f_star",
        "eigenvalues",
        "condition_number",
        "stable_step_bound",
        "trajectories",
        "alpha_sweep",
        "landscape",
    )
    issues = [f"missing payload field: {key}" for key in required if key not in payload]
    if payload.get("schema_version") != DASHBOARD_PAYLOAD_SCHEMA_VERSION:
        issues.append("unsupported dashboard payload schema_version")
    for key in ("step_sizes", "A_diagonal", "b", "x0", "x_star", "eigenvalues"):
        values = payload.get(key)
        if not isinstance(values, list) or not values:
            issues.append(f"{key} must be a non-empty list")
            continue
        if any(not isinstance(value, (int, float)) or math.isnan(float(value)) for value in values):
            issues.append(f"{key} contains a non-numeric or NaN value")
    for key in ("f_star", "condition_number", "stable_step_bound"):
        value = payload.get(key)
        if not isinstance(value, (int, float)) or math.isnan(float(value)):
            issues.append(f"{key} must be a numeric scalar")
    trajectories = payload.get("trajectories")
    if isinstance(trajectories, dict):
        for name, trajectory in trajectories.items():
            if not isinstance(trajectory, dict) or not {"iterations", "objectives"} <= trajectory.keys():
                issues.append(f"trajectory {name} is missing iterations/objectives")
            elif len(trajectory["iterations"]) != len(trajectory["objectives"]):
                issues.append(f"trajectory {name} has mismatched vector lengths")
    else:
        issues.append("trajectories must be a mapping")
    sweep = payload.get("alpha_sweep")
    if isinstance(sweep, dict):
        keys = ("alphas", "iterations", "final_dist", "final_obj", "diverged")
        lengths = [len(sweep.get(key, ())) for key in keys]
        if any(key not in sweep for key in keys):
            issues.append("alpha_sweep is missing a chart vector")
        elif len(set(lengths)) != 1:
            issues.append("alpha_sweep chart vectors have mismatched lengths")
    else:
        issues.append("alpha_sweep must be a mapping")
    landscape = payload.get("landscape")
    if isinstance(landscape, dict):
        if len(landscape.get("x", ())) != len(landscape.get("f", ())):
            issues.append("landscape chart vectors have mismatched lengths")
    else:
        issues.append("landscape must be a mapping")
    return tuple(issues)


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

    payload = {
        "schema_version": DASHBOARD_PAYLOAD_SCHEMA_VERSION,
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
    issues = validate_dashboard_payload(payload)
    if issues:
        raise DashboardPayloadError("dashboard payload schema failed: " + "; ".join(issues))
    return payload


__all__ = [
    "DASHBOARD_PAYLOAD_SCHEMA_VERSION",
    "DashboardPayloadError",
    "compute_payload",
    "load_yaml_defaults",
    "to_diagonal_A",
    "validate_dashboard_payload",
]
